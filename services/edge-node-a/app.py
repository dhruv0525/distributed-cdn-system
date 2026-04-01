from fastapi import FastAPI, Header, HTTPException
from collections import OrderedDict
import requests
import time
import threading
import os

app = FastAPI()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ORIGIN_URL        = os.getenv("ORIGIN_URL",   "http://origin:8000")
REGISTRY_URL      = os.getenv("REGISTRY_URL", "http://registry:8000")
NODE_ID           = os.getenv("NODE_ID",       "edge-node-a")
NODE_REGION       = os.getenv("NODE_REGION",   "asia")
NODE_URL          = os.getenv("NODE_URL",      "http://edge-a:8000")

CACHE_TTL         = int(os.getenv("CACHE_TTL",        "60"))
CACHE_MAX_SIZE    = int(os.getenv("CACHE_MAX_SIZE",    "100"))
SIMULATED_LATENCY = float(os.getenv("SIMULATED_LATENCY", "0.1"))

# ─────────────────────────────────────────────
# LOAD SHEDDING & FAILURE
# ─────────────────────────────────────────────
active_connections = 0
MAX_CONNECTIONS = 2
active_connections_lock = threading.Lock()
FAILURE_MODE = False


# ─────────────────────────────────────────────
# LRU CACHE WITH TTL
# ─────────────────────────────────────────────
class LRUCache:
    def __init__(self, max_size: int, ttl: int):
        self.max_size = max_size
        self.ttl      = ttl
        self._store   = OrderedDict()
        self._lock    = threading.Lock()

    def get(self, key: str):
        with self._lock:
            if key not in self._store:
                return None
            entry = self._store[key]
            if time.time() - entry["stored_at"] > self.ttl:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return entry["data"]

    def set(self, key: str, value):
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = {"data": value, "stored_at": time.time()}
            if len(self._store) > self.max_size:
                evicted_key, _ = self._store.popitem(last=False)
                print(f"[CACHE][LRU-EVICT] Evicted: {evicted_key}")

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def info(self):
        with self._lock:
            return {
                "size":     len(self._store),
                "max_size": self.max_size,
                "ttl":      self.ttl
            }


cache = LRUCache(max_size=CACHE_MAX_SIZE, ttl=CACHE_TTL)


# ─────────────────────────────────────────────
# REGISTRY — register + heartbeat
# ─────────────────────────────────────────────
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
            r = requests.post(
                f"{REGISTRY_URL}/heartbeat",
                json={"id": NODE_ID},
                timeout=3
            )
            print(f"[HEARTBEAT] Status: {r.status_code}")
        except Exception as e:
            print(f"[HEARTBEAT] Failed: {e}")
        time.sleep(10)


# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    register_with_registry()
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.get("/fetch")
def fetch_file(file: str, x_request_id: str = Header(None)):
    global active_connections
    global FAILURE_MODE

    if FAILURE_MODE:
        return {"status": "ERROR", "file": file, "message": "Node failure simulated"}

    with active_connections_lock:
        if active_connections >= MAX_CONNECTIONS:
            return {"status": "BUSY", "file": file, "message": "Edge node overloaded"}
        active_connections += 1

    try:
        print(f"[{x_request_id}] FETCH → file='{file}'")

        cached = cache.get(file)
        if cached is not None:
            print(f"[{x_request_id}] Cache HIT")
            time.sleep(SIMULATED_LATENCY)
            return {
                "status":     "HIT",
                "file":       file,
                "node":       NODE_ID,
                "request_id": x_request_id,
                "data":       cached,
            }

        print(f"[{x_request_id}] Cache MISS → fetching from origin")
        try:
            response = requests.get(
                f"{ORIGIN_URL}/get-file/{file}",
                headers={"x-request-id": x_request_id or ""},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            cache.set(file, data)
            print(f"[{x_request_id}] Stored '{file}' in cache")
            return {
                "status":     "MISS",
                "file":       file,
                "node":       NODE_ID,
                "request_id": x_request_id,
                "data":       data,
            }
        except requests.exceptions.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Origin error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=503, detail="Origin unreachable")
    finally:
        with active_connections_lock:
            active_connections -= 1


# ─────────────────────────────────────────────
# FAILURE INJECTION
# ─────────────────────────────────────────────
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

@app.get("/health")
def health():
    return {
        "status": "healthy" if not FAILURE_MODE else "unhealthy",
        "node_id": NODE_ID,
        "region": NODE_REGION,
        "active_connections": active_connections,
        "max_connections": MAX_CONNECTIONS,
        "cache":  cache.info()
    }


@app.delete("/cache/{file}")
def delete_cache(file: str, x_request_id: str = Header(None)):
    deleted = cache.delete(file)
    if deleted:
        print(f"[{x_request_id}] PURGE: '{file}' removed")
        return {"message": f"'{file}' purged", "node": NODE_ID}
    print(f"[{x_request_id}] PURGE: '{file}' not in cache")
    return {"message": f"'{file}' not in cache", "node": NODE_ID}


@app.get("/cache")
def cache_status():
    return {"node": NODE_ID, "cache_info": cache.info()}


@app.get("/")
def root():
    return {"message": f"Edge Node A running", "node": NODE_ID, "region": NODE_REGION}