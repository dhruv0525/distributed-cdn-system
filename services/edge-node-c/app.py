from fastapi import FastAPI, Header
import requests
import time
import threading
import os

app = FastAPI()

# Simple in-memory cache
cache = {}

ORIGIN_URL = "http://origin:8000"
REGISTRY_URL = "http://registry:8000"
NODE_ID = "edge-c"

# State variables for node simulation
is_failed = False
active_requests = 0
requests_lock = threading.Lock()
MAX_CONCURRENT = 2

# -------------------------
# HEARTBEAT BACKGROUND THREAD
# -------------------------
def send_heartbeat():
    while True:
        try:
            # Determine current status
            status = "Down" if is_failed else "Healthy"
            
            # If load shedding is actively happening, we can mark it as Busy
            if not is_failed and active_requests >= MAX_CONCURRENT:
                status = "Busy"
                
            requests.post(
                f"{REGISTRY_URL}/heartbeat",
                json={"id": NODE_ID, "status": status},
                timeout=2
            )
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")
            
        time.sleep(5)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=send_heartbeat, daemon=True)
    thread.start()

# -------------------------
# FETCH FILE (MAIN LOGIC)
# -------------------------
@app.get("/fetch")
def fetch_file(file: str, x_request_id: str = Header(None)):
    global is_failed, active_requests

    # Failure simulation
    if is_failed:
        return {"status": "ERROR", "message": "Node is offline"}

    # Load shedding / concurrency limit
    with requests_lock:
        if active_requests >= MAX_CONCURRENT:
            return {"status": "BUSY", "message": "Too many concurrent requests"}
        active_requests += 1

    try:
        # Simulate processing delay so concurrent requests can pile up
        time.sleep(1)

        print(f"[{x_request_id}] Request for file: {file}")

        # 1. Check cache
        if file in cache:
            print(f"[{x_request_id}] Cache HIT")
            return {
                "status": "HIT",
                "file": file,
                "data": cache[file]
            }

        # 2. Cache miss → fetch from origin
        print(f"[{x_request_id}] Cache MISS → fetching from origin")

        # Correct endpoint + query param
        response = requests.get(
            f"{ORIGIN_URL}/get-file",
            params={"filename": file},
            headers={"X-Request-ID": x_request_id} if x_request_id else {}
        )

        # If origin returns error, don't cache it
        if response.status_code != 200:
            print(f"[{x_request_id}] Origin error: {response.status_code}")
            return {
                "status": "ERROR",
                "message": "Origin returned error",
                "code": response.status_code
            }

        # Correct response handling
        data = {
            "content": response.text
        }

        # Store in cache
        cache[file] = data

        return {
            "status": "MISS",
            "file": file,
            "data": data
        }

    except Exception as e:
        print(f"[{x_request_id}] Exception: {e}")
        return {
            "status": "ERROR",
            "message": "Failed to fetch from origin"
        }
    finally:
        # Ensure we always decrement the active counter
        with requests_lock:
            active_requests -= 1

# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/health")
def health():
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
# FAIL AND RECOVER SIMULATION
# -------------------------
@app.post("/fail")
def fail_node():
    global is_failed
    is_failed = True
    return {"status": "failed", "message": "Node is now generating ERRORs"}

@app.post("/recover")
def recover_node():
    global is_failed
    is_failed = False
    return {"status": "recovered", "message": "Node is now operating normally"}

@app.get("/")
def root():
    return {"message": "Edge Node C running"}