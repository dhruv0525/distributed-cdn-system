from fastapi import FastAPI, Header
import requests

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

    # 1. Check cache
    if file in cache:
        print(f"[{x_request_id}] Cache HIT")
        return {
            "status": "HIT",
            "file": file,
            "data": cache[file].decode(errors="ignore")
        }

    # 2. Cache miss → fetch from origin
    print(f"[{x_request_id}] Cache MISS → fetching from origin")

    try:
        # ✅ FIX 1: Correct endpoint + query param
        response = requests.get(
            f"{ORIGIN_URL}/get-file",
            params={"filename": file},
            headers={"X-Request-ID": x_request_id} if x_request_id else {}
        )

        # ❌ If origin returns error, don't cache it
        if response.status_code != 200:
            print(f"[{x_request_id}] Origin error: {response.status_code}")
            return {
                "status": "ERROR",
                "message": "Origin returned error",
                "code": response.status_code
            }

        # ✅ FIX 2: Correct response handling
        data = response.content

        # Store in cache
        cache[file] = data

        return {
        "status": "MISS",
        "file": file,
        "data": data.decode(errors="ignore")
        }

    except Exception as e:
        print(f"[{x_request_id}] Exception: {e}")
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