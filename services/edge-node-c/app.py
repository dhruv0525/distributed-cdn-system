from fastapi import FastAPI, Header
import requests
import time
import threading

app = FastAPI()

# Simple in-memory cache
cache = {}

ORIGIN_URL = "http://origin:8000"
REGISTRY_URL = "http://registry:8000"
NODE_ID = "edge-c"

# State variables
is_failed = False
active_requests = 0
requests_lock = threading.Lock()
MAX_CONCURRENT = 2


# -------------------------
# HEARTBEAT THREAD
# -------------------------
def send_heartbeat():
    while True:
        try:
            with requests_lock:
                current_load = active_requests

            if is_failed:
                status = "Down"
            elif current_load >= MAX_CONCURRENT:
                status = "Busy"
            else:
                status = "Healthy"

            requests.post(
                f"{REGISTRY_URL}/heartbeat",
                json={"id": NODE_ID, "status": status},
                timeout=2
            )

        except Exception as e:
            print(f"[HEARTBEAT] Failed: {e}")

        time.sleep(5)


@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=send_heartbeat, daemon=True)
    thread.start()


# -------------------------
# FETCH FILE
# -------------------------
@app.get("/fetch")
def fetch_file(file: str, x_request_id: str = Header(None)):
    global is_failed, active_requests

    if is_failed:
        return {"status": "ERROR", "message": "Node is offline"}

    with requests_lock:
        if active_requests >= MAX_CONCURRENT:
            print(f"[{x_request_id}] BUSY - overload")
            return {"status": "BUSY", "message": "Too many concurrent requests"}
        active_requests += 1

    try:
        time.sleep(1)  # simulate load

        print(f"[{x_request_id}] Request for file: {file}")

        # Cache HIT
        if file in cache:
            print(f"[{x_request_id}] Cache HIT")
            return {
                "status": "HIT",
                "file": file,
                "data": cache[file]
            }

        print(f"[{x_request_id}] Cache MISS → fetching from origin")

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

        data = {"content": response.text}
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
        with requests_lock:
            active_requests -= 1


# -------------------------
# HEALTH
# -------------------------
@app.get("/health")
def health():
    return {
        "status": "healthy" if not is_failed else "down",
        "active_requests": active_requests,
        "max_concurrent": MAX_CONCURRENT
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
# FAILURE SIMULATION
# -------------------------
@app.post("/fail")
def fail_node():
    global is_failed
    is_failed = True
    return {"status": "failed"}


@app.post("/recover")
def recover_node():
    global is_failed
    is_failed = False
    return {"status": "recovered"}


@app.get("/")
def root():
    return {"message": "Edge Node C running"}