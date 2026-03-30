from fastapi import FastAPI, Header
import requests
import time

app = FastAPI()

# Simple in-memory cache
cache = {}

ORIGIN_URL = "http://origin:8000"

# -------------------------
# FETCH FILE (MAIN LOGIC)
# -------------------------
@app.get("/fetch")
def fetch_file(file: str, x_request_id: str = Header(None)):

    print(f"[{x_request_id}] Request for file: {file}")

    # Simulate load (optional)
    # time.sleep(0.1)

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

    try:
        response = requests.get(f"{ORIGIN_URL}/get-file/{file}")
        data = response.json()

        # Store in cache
        cache[file] = data

        return {
            "status": "MISS",
            "file": file,
            "data": data
        }

    except:
        return {
            "status": "ERROR",
            "message": "Failed to fetch from origin"
        }


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


@app.get("/")
def root():
    return {"message": "Edge Node running"}