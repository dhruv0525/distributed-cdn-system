"""
Traffic Manager — main entry point for the CDN system.

Responsibilities:
  1. Accept client file requests via GET /route
  2. Fetch active edge nodes from the Service Registry
  3. Select the best node based on client location
  4. Forward the request to the selected node with retry + failover
  5. Return the edge node's response to the client
"""

import asyncio
import uuid
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# App & constants
# ---------------------------------------------------------------------------

app = FastAPI(title="Traffic Manager")

# Internal Docker service base URLs
REGISTRY_URL = "http://registry:8000"

EDGE_NODES = {
    "asia":    "http://edge-c:8000",
    "europe":  "http://edge-b:8000",
    "america": "http://edge-a:8000",
}

# Used when location header is absent or unrecognised
DEFAULT_NODE = "http://edge-a:8000"

# Delays (seconds) between successive retry attempts on the same node
RETRY_DELAYS = [0.5, 1.0, 2.0]


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def log(request_id: str, message: str) -> None:
    """Print a structured log line tied to a specific request."""
    print(f"[{request_id}] {message}")


# ---------------------------------------------------------------------------
# Service Registry
# ---------------------------------------------------------------------------

async def fetch_nodes() -> list:
    """
    Retrieve the list of active edge nodes from the Service Registry.

    Returns a list of node dicts, each expected to contain at least a "url" key.
    Raises HTTP 502/503/504 if the registry is unreachable or returns an error.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{REGISTRY_URL}/nodes")
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service Registry timed out")

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Service Registry returned error: {exc.response.status_code}",
        )

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service Registry is unavailable")


# ---------------------------------------------------------------------------
# Node selection
# ---------------------------------------------------------------------------

def order_nodes(location: Optional[str], nodes: list) -> list[str]:
    """
    Build a prioritised list of edge node URLs for a given client location.

    Strategy:
      - Map the location header to a preferred node via EDGE_NODES.
      - Place the preferred node first, then append the remaining active nodes
        as ordered fallbacks.
      - If the registry returned no active nodes, fall back to the static
        EDGE_NODES list so the system always has candidates to try.
    """
    # Determine the preferred node from the location header
    preferred = DEFAULT_NODE
    if location:
        preferred = EDGE_NODES.get(location.lower().strip(), DEFAULT_NODE)

    # Extract URLs of nodes currently registered as active
    active_urls = [
        node["url"]
        for node in nodes
        if isinstance(node, dict) and "url" in node
    ]

    # Build ordered list: preferred first, then the remaining active nodes
    ordered = [preferred] if preferred in active_urls else []
    ordered += [url for url in active_urls if url != preferred]

    # Safety fallback: if the registry is empty use the static node list
    if not ordered:
        ordered = list(EDGE_NODES.values())

    return ordered


# ---------------------------------------------------------------------------
# Edge node communication
# ---------------------------------------------------------------------------

async def try_node(
    client: httpx.AsyncClient,
    node_url: str,
    file: str,
    request_id: str,
) -> dict:
    """
    Attempt to fetch a file from a single edge node.

    Retries up to len(RETRY_DELAYS) times with increasing delays on transient
    network errors. Raises immediately (without retrying) when the node reports
    BUSY, since waiting will not resolve a capacity issue — the caller should
    try a different node instead.

    Raises:
        _NodeBusy   – node responded with status "BUSY"
        _NodeFailed – node failed after all retry attempts
    """
    headers = {"X-Request-ID": request_id}

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        log(request_id, f"Attempt {attempt}/{len(RETRY_DELAYS)} → {node_url}")

        try:
            response = await client.get(
                f"{node_url}/fetch",
                params={"file": file},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            # A BUSY status means the node is overloaded — switch immediately
            if isinstance(data, dict) and data.get("status") == "BUSY":
                log(request_id, f"Node {node_url} is BUSY — switching node")
                raise _NodeBusy(node_url)

            # Successful response
            return data

        except _NodeBusy:
            raise  # Let the caller handle node switching

        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
            log(request_id, f"Attempt {attempt} failed for {node_url} — {exc}")

            is_last_attempt = attempt == len(RETRY_DELAYS)
            if is_last_attempt:
                raise _NodeFailed(node_url, str(exc))

            log(request_id, f"Retrying in {delay}s ...")
            await asyncio.sleep(delay)

    raise _NodeFailed(node_url, "exhausted retries")  # Defensive safety net


async def fetch_from_edge(
    ordered_nodes: list[str],
    file: str,
    request_id: str,
) -> tuple[str, dict]:
    """
    Try each node in priority order until one succeeds.

    On _NodeBusy or _NodeFailed the current node is skipped and the next one
    is tried. If every node fails, raises HTTP 503.

    Returns:
        (selected_node_url, response_data) from the first successful node.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        for node_url in ordered_nodes:
            try:
                data = await try_node(client, node_url, file, request_id)
                log(request_id, f"Success — served by {node_url}")
                return node_url, data

            except (_NodeBusy, _NodeFailed) as exc:
                log(request_id, f"Skipping {node_url} — {exc}")
                continue

    # All nodes exhausted
    log(request_id, "All edge nodes failed — returning 503")
    raise HTTPException(
        status_code=503,
        detail="All edge nodes are unavailable or busy. Please try again later.",
    )


# ---------------------------------------------------------------------------
# Route endpoint
# ---------------------------------------------------------------------------

@app.get("/route")
async def route(
    file: str = Query(..., description="Name of the file to retrieve"),
    x_client_location: Optional[str] = Header(None, description="Client geographic region"),
) -> JSONResponse:
    """
    Main routing endpoint.

    Flow:
      1. Generate a unique request ID for end-to-end tracing.
      2. Fetch active nodes from the Service Registry.
      3. Order nodes by client location preference.
      4. Forward the request to the best available node (with retry + failover).
      5. Return the edge response alongside routing metadata.
    """
    request_id = str(uuid.uuid4())

    log(request_id, f"Incoming request — file={file!r} location={x_client_location!r}")

    # Step 1: get live node list from registry
    nodes = await fetch_nodes()

    # Step 2: build prioritised node order for this client
    ordered_nodes = order_nodes(x_client_location, nodes)
    log(request_id, f"Node order: {ordered_nodes}")

    # Step 3: forward request with retry + failover
    selected_node, edge_response = await fetch_from_edge(ordered_nodes, file, request_id)

    # Echo X-Request-ID in the response header for client-side tracing
    return JSONResponse(
        content={
            "request_id":    request_id,
            "file":          file,
            "location":      x_client_location,
            "selected_node": selected_node,
            "data":          edge_response,
        },
        headers={"X-Request-ID": request_id},
    )


# ---------------------------------------------------------------------------
# Internal sentinel exceptions
# Never raised beyond fetch_from_edge — all client-facing errors are HTTPExceptions.
# ---------------------------------------------------------------------------

class _NodeFailed(Exception):
    """Raised when a node fails all retry attempts."""
    def __init__(self, url: str, reason: str):
        self.url = url
        super().__init__(f"Node {url} failed: {reason}")


class _NodeBusy(Exception):
    """Raised when a node explicitly reports it is BUSY."""
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Node {url} is BUSY")