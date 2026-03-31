from fastapi import FastAPI, Header
import requests
import time
from collections import OrderedDict
import uuid
import asyncio  # ADDED: for async non-blocking sleep

app = FastAPI()

# Cache settings
CACHE_TTL = 30
CACHE_SIZE = 5

# LRU Cache
cache = OrderedDict()

# Metrics
metrics = {
    "total_requests": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "active_connections": 0
}

ORIGIN_URL = "http://origin:8000"


# -------------------------
# FETCH FILE (MAIN LOGIC)
# -------------------------
@app.get("/fetch")

# CHANGED: def → async def (for concurrency)
async def fetch_file(file: str, x_request_id: str = Header(None)):

    # ADDED: Generate Request ID if missing
    if not x_request_id:
        x_request_id = str(uuid.uuid4())[:8]

    start_time = time.time()

    metrics["total_requests"] += 1
    metrics["active_connections"] += 1

    # CHANGED: structured logging format
    print(f"[{x_request_id}] [EDGE-B] [REQUEST] file={file} active={metrics['active_connections']}")

    # CHANGED: non-blocking delay (instead of time.sleep)
    await asyncio.sleep(1)

    current_time = time.time()

    # 1. Check cache
    if file in cache:
        data, timestamp = cache[file]

        if current_time - timestamp < CACHE_TTL:
            metrics["cache_hits"] += 1

            # ADDED: structured log
            print(f"[{x_request_id}] [EDGE-B] [HIT] file={file}")

            cache.move_to_end(file)

            latency = round((time.time() - start_time) * 1000, 2)

            print(f"[{x_request_id}] [EDGE-B] [RESPONSE] latency={latency}ms")

            metrics["active_connections"] -= 1

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

        metrics["active_connections"] -= 1

        return {
            "status": "MISS",
            "file": file,
            "data": data,
            "request_id": x_request_id,
            "latency_ms": latency
        }

    except:
        metrics["active_connections"] -= 1

        return {
            "status": "ERROR",
            "message": "Failed to fetch from origin",
            "request_id": x_request_id
        }


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
# HEALTH CHECK
# -------------------------
@app.get("/health")
def health():

    # CHANGED: threshold reduced for testing/demo
    if metrics["active_connections"] >= 2:
        return {"status": "busy"}

    return {"status": "healthy"}


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
