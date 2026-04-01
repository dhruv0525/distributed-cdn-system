from fastapi import FastAPI, Header
import requests
import time
from collections import OrderedDict
import uuid
import asyncio  # ADDED: for async non-blocking sleep
import os
import threading

app = FastAPI()

# -------------------------
# Configuration
# -------------------------
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000")
NODE_ID      = os.getenv("NODE_ID", "edge-node-b")
NODE_REGION  = os.getenv("NODE_REGION", "europe")
NODE_URL     = os.getenv("NODE_URL", "http://edge-b:8000")

# Cache settings
CACHE_TTL = 30
CACHE_SIZE = 5

# -------------------------
# LOAD SHEDDING & FAILURE
# -------------------------
active_connections = 0
MAX_CONNECTIONS = 2
active_connections_lock = threading.Lock()
FAILURE_MODE = False

# LRU Cache
cache = OrderedDict()

# Metrics
metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0
}

ORIGIN_URL = os.getenv("ORIGIN_URL", "http://origin:8000")

# -------------------------
# Registration & Heartbeat
# -------------------------
def register_with_registry():
    payload = {"id": NODE_ID, "region": NODE_REGION, "url": NODE_URL}
    for attempt in range(5):
        try:
            r = requests.post(f"{REGISTRY_URL}/register", json=payload, timeout=3)
            if r.status_code == 200:
                print(f"[REGISTRY] Registered as {NODE_ID}")
                return
        except Exception as e:
            print(f"[REGISTRY] Attempt {attempt+1} failed: {e}")
        time.sleep(2)
    print("[REGISTRY] Could not register — continuing anyway")

def heartbeat_loop():
    while True:
        try:
            r = requests.post(f"{REGISTRY_URL}/heartbeat", json={"id": NODE_ID}, timeout=3)
            print(f"[HEARTBEAT] Status: {r.status_code}")
        except Exception as e:
            print(f"[HEARTBEAT] Failed: {e}")
        time.sleep(10)

@app.on_event("startup")
def on_startup():
    register_with_registry()
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()


# -------------------------
# FETCH FILE (MAIN LOGIC)
# -------------------------
@app.get("/fetch")

# CHANGED: def → async def (for concurrency)
async def fetch_file(file: str, x_request_id: str = Header(None)):
    global active_connections
    global FAILURE_MODE

    if FAILURE_MODE:
        return {"status": "ERROR", "file": file, "message": "Node failure simulated"}

    with active_connections_lock:
        if active_connections >= MAX_CONNECTIONS:
            return {"status": "BUSY", "file": file, "message": "Edge node overloaded"}
        active_connections += 1

    try:
        # ADDED: Generate Request ID if missing
        if not x_request_id:
            x_request_id = str(uuid.uuid4())[:8]

        start_time = time.time()
        metrics["total_requests"] += 1

        # CHANGED: structured logging format
        print(f"[{x_request_id}] [EDGE-B] [REQUEST] file={file} active={active_connections}")

        # CHANGED: non-blocking delay (instead of time.sleep)
        await asyncio.sleep(1)

        current_time = time.time()

        # 1. Check cache
        if file in cache:
            data, timestamp = cache[file]

            if current_time - timestamp < CACHE_TTL:
                metrics["cache_hits"] += 1
                print(f"[{x_request_id}] [EDGE-B] [HIT] file={file}")
                cache.move_to_end(file)

                latency = round((time.time() - start_time) * 1000, 2)
                print(f"[{x_request_id}] [EDGE-B] [RESPONSE] latency={latency}ms")

                return {
                    "status": "HIT",
                    "file": file,
                    "data": data,
                    "request_id": x_request_id,
                    "latency_ms": latency
                }
            else:
                print(f"[{x_request_id}] [EDGE-B] [EXPIRED] file={file}")
                del cache[file]

        # 2. Cache miss
        metrics["cache_misses"] += 1
        print(f"[{x_request_id}] [EDGE-B] [MISS] file={file} → origin")

        try:
            response = requests.get(
                f"{ORIGIN_URL}/get-file/{file}",
                headers={"X-Request-ID": x_request_id}
            )
            data = response.json()

            cache[file] = (data, current_time)

            # LRU eviction
            if len(cache) > CACHE_SIZE:
                removed = cache.popitem(last=False)
                print(f"[{x_request_id}] [EDGE-B] [LRU-EVICT] removed={removed[0]}")

            latency = round((time.time() - start_time) * 1000, 2)
            print(f"[{x_request_id}] [EDGE-B] [RESPONSE] latency={latency}ms")

            return {
                "status": "MISS",
                "file": file,
                "data": data,
                "request_id": x_request_id,
                "latency_ms": latency
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "message": "Failed to fetch from origin",
                "request_id": x_request_id
            }

    finally:
        with active_connections_lock:
            active_connections -= 1


# -------------------------
# METRICS API
# -------------------------
@app.get("/metrics")
def get_metrics():

    # ADDED: Cache hit ratio (important for demo/frontend)
    hit_ratio = 0
    if metrics["total_requests"] > 0:
        hit_ratio = metrics["cache_hits"] / metrics["total_requests"]

    return {
        **metrics,
        "cache_hit_ratio": round(hit_ratio, 2)  # ADDED
    }


# -------------------------
# FAILURE INJECTION
# -------------------------
@app.post("/fail")
def fail_node():
    global FAILURE_MODE
    FAILURE_MODE = True
    return {"status": "failure_mode_enabled", "node_id": NODE_ID}

@app.post("/recover")
def recover_node():
    global FAILURE_MODE
    FAILURE_MODE = False
    return {"status": "failure_mode_disabled", "node_id": NODE_ID}

# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/health")
def health():
    return {
        "status": "healthy" if not FAILURE_MODE else "unhealthy",
        "node_id": NODE_ID,
        "region": NODE_REGION,
        "active_connections": active_connections,
        "max_connections": MAX_CONNECTIONS
    }


# -------------------------
# CACHE INVALIDATION
# -------------------------
@app.delete("/cache/{file}")
def delete_cache(file: str):
    if file in cache:
        del cache[file]
        return {"message": f"{file} removed from cache"}
    return {"message": "file not in cache"}


# -------------------------
# ROOT
# -------------------------
@app.get("/")
def root():
    return {"message": "Edge Node running"}
