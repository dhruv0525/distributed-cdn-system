import asyncio
import uuid
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Traffic Manager")

# ✅ CORS (IMPORTANT for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGISTRY_URL = "http://registry:8000"

EDGE_NODES = {
    "asia": "http://edge-c:8000",
    "europe": "http://edge-b:8000",
    "america": "http://edge-a:8000",
}

DEFAULT_NODE = "http://edge-a:8000"

RETRY_DELAYS = [0.5, 1.0, 2.0]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(request_id: str, message: str):
    print(f"[{request_id}] {message}")


# ---------------------------------------------------------------------------
# Fetch nodes from registry
# ---------------------------------------------------------------------------

async def fetch_nodes() -> list:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{REGISTRY_URL}/nodes")
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise HTTPException(status_code=500, detail="Invalid registry response")

            return data

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Registry timeout")

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Registry unavailable")


# ---------------------------------------------------------------------------
# Node ordering
# ---------------------------------------------------------------------------

def order_nodes(location: Optional[str], nodes: list) -> list[str]:
    preferred = DEFAULT_NODE

    if location:
        preferred = EDGE_NODES.get(location.lower().strip(), DEFAULT_NODE)

    active_urls = [
        node.get("url")
        for node in nodes
        if isinstance(node, dict) and node.get("url")
    ]

    ordered = []

    if preferred in active_urls:
        ordered.append(preferred)

    ordered += [url for url in active_urls if url != preferred]

    if not ordered:
        ordered = list(EDGE_NODES.values())

    return ordered


# ---------------------------------------------------------------------------
# Edge call
# ---------------------------------------------------------------------------

async def try_node(client, node_url, file, request_id):
    headers = {"X-Request-ID": request_id}

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        log(request_id, f"Trying {node_url} (attempt {attempt})")

        try:
            response = await client.get(
                f"{node_url}/fetch",
                params={"file": file},
                headers=headers,
            )

            response.raise_for_status()
            data = response.json()

            status = data.get("status")

            if status == "BUSY":
                raise _NodeBusy(node_url)
            
            if status == "ERROR":
                raise _NodeFailed(node_url, "Node returned error")

            return data

        except _NodeBusy:
            raise

        except Exception as e:
            log(request_id, f"Error on {node_url}: {e}")

            if attempt == len(RETRY_DELAYS):
                raise _NodeFailed(node_url, str(e))

            await asyncio.sleep(delay)

    raise _NodeFailed(node_url, "retry exhausted")


async def fetch_from_edge(nodes, file, request_id):
    async with httpx.AsyncClient(timeout=10.0) as client:
        for node in nodes:
            try:
                data = await try_node(client, node, file, request_id)
                return node, data

            except (_NodeBusy, _NodeFailed):
                continue

    raise HTTPException(status_code=503, detail="All nodes failed")


# ---------------------------------------------------------------------------
# MAIN ROUTE
# ---------------------------------------------------------------------------

@app.get("/route")
async def route(
    file: str = Query(...),
    x_client_location: Optional[str] = Header(None),
):
    request_id = str(uuid.uuid4())

    log(request_id, f"Request file={file}, location={x_client_location}")

    nodes = await fetch_nodes()
    ordered_nodes = order_nodes(x_client_location, nodes)

    selected_node, data = await fetch_from_edge(ordered_nodes, file, request_id)

    return JSONResponse(
        content={
            "request_id": request_id,
            "file": file,
            "location": x_client_location,
            "selected_node": selected_node,
            "data": data,
        },
        headers={"X-Request-ID": request_id},
    )


# ---------------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "healthy", "service": "traffic-manager"}


# ---------------------------------------------------------------------------
# INTERNAL EXCEPTIONS
# ---------------------------------------------------------------------------

class _NodeFailed(Exception):
    def __init__(self, url, reason):
        super().__init__(f"{url} failed: {reason}")


class _NodeBusy(Exception):
    def __init__(self, url):
        super().__init__(f"{url} is BUSY")