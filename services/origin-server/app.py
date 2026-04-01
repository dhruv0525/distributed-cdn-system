from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import time
import hashlib
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("origin-server")

app = FastAPI()

# Folder where files are stored
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

# Purge service URL (not hardcoded - uses environment variable)
PURGE_SERVICE_URL = os.getenv("PURGE_SERVICE_URL", "http://purge-service:8000")


# ─────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Service is running"}


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.get("/health")
def health():
    logger.info("Health check called")
    return {"status": "healthy", "service": "origin-server"}


# ─────────────────────────────────────────
# GET FILE
# ─────────────────────────────────────────
@app.get("/get-file")
def get_file(filename: str, request_id: str = "N/A"):
    logger.info(f"[{request_id}] GET /get-file called for: {filename}")

    filepath = os.path.join(FILES_DIR, filename)

    if not os.path.exists(filepath):
        logger.warning(f"[{request_id}] File not found: {filename}")
        raise HTTPException(
            status_code=404,
            detail=f"{filename} not found on origin server"
        )

    # Simulate origin server latency (~2 seconds)
    logger.info(f"[{request_id}] Simulating origin delay (2s)...")
    time.sleep(2)

    # Calculate MD5 hash for versioning
    with open(filepath, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    logger.info(f"[{request_id}] Returning file: {filename}, hash: {file_hash}")

    return FileResponse(
        path=filepath,
        filename=filename,
        headers={
            "X-File-Hash": file_hash,
            "X-Request-ID": request_id
        }
    )


# ─────────────────────────────────────────
# UPLOAD FILE
# ─────────────────────────────────────────
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logger.info(f"UPLOAD called for file: {file.filename}")

    filepath = os.path.join(FILES_DIR, file.filename)
    content = await file.read()

    # Save the file
    with open(filepath, "wb") as f:
        f.write(content)

    # Calculate hash
    file_hash = hashlib.md5(content).hexdigest()
    logger.info(f"File saved: {file.filename}, hash: {file_hash}")

    # Notify purge service to clear old cached copies
    try:
        purge_response = requests.post(
            f"{PURGE_SERVICE_URL}/purge",
            json={"filename": file.filename},
            timeout=3
        )
        logger.info(f"Purge service notified: {purge_response.status_code}")
    except Exception as e:
        logger.warning(f"Could not notify purge service: {e}")

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "hash": file_hash
    }


# ─────────────────────────────────────────
# LIST ALL FILES (for testing)
# ─────────────────────────────────────────
@app.get("/files")
def list_files():
    files = os.listdir(FILES_DIR)
    logger.info(f"Files listed: {files}")
    return {"files": files}