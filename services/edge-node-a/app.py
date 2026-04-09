from fastapi import FastAPI, Header
import requests
import threading
import time
import os

app = FastAPI()

# -------------------------
# CONFIG
# -------------------------
ORIGIN_URL = os.getenv("ORIGIN_URL", "http://origin:8000")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://registry:8000")
NODE_ID = os.getenv("NODE_ID", "edge-a")  # change via docker

# -------------------------
# CACHE
# -------------------------
cache = {}
is_failed = False
# -------------------------
# HEARTBEAT THREAD
# -------------------------
def send_heartbeat():
    while True:
        try:
            requests.post(
                f"{REGISTRY_URL}/heartbeat",
                json={
                    "id": NODE_ID,
                    "status": "Down" if is_failed else "Healthy"
                },
                timeout=2
            )
        except Exception as e:
            print(f"[{NODE_ID}] Heartbeat failed: {e}")

        time.sleep(5)


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=send_heartbeat, daemon=True)
    thread.start()

# -------------------------
# FAIL NODE
# -------------------------
@app.post("/fail")
def fail_node():
    global is_failed
    is_failed = True
    return {"status": "failed", "message": f"{NODE_ID} is now offline"}


# -------------------------
# RECOVER NODE
# -------------------------
@app.post("/recover")
def recover_node():
    global is_failed
    is_failed = False
    return {"status": "recovered", "message": f"{NODE_ID} is now healthy"}

# -------------------------
# FETCH FILE
# -------------------------
@app.get("/fetch")
def fetch_file(file: str, x_request_id: str = Header(None)):

    if is_failed:
        return {"status": "ERROR", "message": "Node is offline"}

    print(f"[{x_request_id}] [{NODE_ID}] Request for file: {file}")

    # 1. Cache check
    if file in cache:
        print(f"[{x_request_id}] [{NODE_ID}] Cache HIT")
        return {
            "status": "HIT",
            "file": file,
            "data": cache[file]
        }

    # 2. Cache miss → fetch from origin
    print(f"[{x_request_id}] [{NODE_ID}] Cache MISS → fetching from origin")

    try:
        response = requests.get(
            f"{ORIGIN_URL}/get-file",
            params={"filename": file},
            headers={"X-Request-ID": x_request_id} if x_request_id else {}
        )

        if response.status_code != 200:
            return {
                "status": "ERROR",
                "message": "Origin returned error",
                "code": response.status_code
            }

        data = {
            "content": response.text
        }

        cache[file] = data

        return {
            "status": "MISS",
            "file": file,
            "data": data
        }

    except Exception as e:
        print(f"[{x_request_id}] [{NODE_ID}] Exception: {e}")
        return {
            "status": "ERROR",
            "message": "Failed to fetch from origin"
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
# HEALTH
# -------------------------
@app.get("/health")
def health():
    return {"status": "healthy", "node": NODE_ID}

# -------------------------
# ROOT
# -------------------------
@app.get("/")
def root():
    return {"message": f"{NODE_ID} running"}