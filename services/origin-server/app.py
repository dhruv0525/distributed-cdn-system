from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse
import os
import time
import hashlib
import requests
import logging
import json
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("origin-server")

app = FastAPI(title="Origin Server", description="CDN Origin Server - stores and serves original files")

# Folder where files are stored
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

# File metadata storage (version tracking)
METADATA_FILE = "files/metadata.json"

# Purge service URL
PURGE_SERVICE_URL = os.getenv("PURGE_SERVICE_URL", "http://purge-service:8000")


# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────

def load_metadata():
    """Load file metadata from JSON file"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    """Save file metadata to JSON file"""
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def calculate_hash(content: bytes) -> str:
    """Calculate MD5 hash of file content"""
    return hashlib.md5(content).hexdigest()


def notify_purge_service(filename: str, request_id: str = "N/A"):
    """Notify purge service to clear cached copies of updated file"""
    try:
        response = requests.post(
            f"{PURGE_SERVICE_URL}/purge",
            json={"filename": filename},
            timeout=3
        )
        if response.status_code == 200:
            logger.info(f"[{request_id}] Purge service notified successfully for: {filename}")
        else:
            logger.warning(f"[{request_id}] Purge service returned: {response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"[{request_id}] Purge service not reachable (may not be running yet)")
    except requests.exceptions.Timeout:
        logger.warning(f"[{request_id}] Purge service timed out")
    except Exception as e:
        logger.warning(f"[{request_id}] Could not notify purge service: {str(e)}")


# ─────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Service is running", "service": "origin-server"}


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.get("/health")
def health():
    logger.info("Health check called")
    total_files = len([
        f for f in os.listdir(FILES_DIR)
        if f != "metadata.json"
    ])
    return {
        "status": "healthy",
        "service": "origin-server",
        "total_files": total_files,
        "timestamp": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────
# GET FILE
# ─────────────────────────────────────────
@app.get("/get-file")
def get_file(
    filename: str,
    x_request_id: Optional[str] = Header(default="N/A")
):
    request_id = x_request_id
    logger.info(f"[{request_id}] GET /get-file → filename: {filename}")

    # Security check - prevent path traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        logger.warning(f"[{request_id}] Invalid filename attempted: {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join(FILES_DIR, filename)

    # Check if file exists
    if not os.path.exists(filepath):
        logger.warning(f"[{request_id}] File not found: {filename}")
        raise HTTPException(
            status_code=404,
            detail=f"'{filename}' not found on origin server"
        )

    # Simulate origin server latency
    logger.info(f"[{request_id}] Simulating origin latency (2s)...")
    time.sleep(2)

    # Get file metadata
    metadata = load_metadata()
    file_info = metadata.get(filename, {})
    file_hash = file_info.get("hash", "unknown")
    version = file_info.get("version", 1)

    logger.info(f"[{request_id}] Serving file: {filename} | version: {version} | hash: {file_hash}")

    return FileResponse(
        path=filepath,
        filename=filename,
        headers={
            "X-File-Hash": file_hash,
            "X-File-Version": str(version),
            "X-Request-ID": request_id,
            "X-Served-By": "origin-server"
        }
    )


# ─────────────────────────────────────────
# UPLOAD FILE
# ─────────────────────────────────────────
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    x_request_id: Optional[str] = Header(default="N/A")
):
    request_id = x_request_id
    logger.info(f"[{request_id}] UPLOAD called → filename: {file.filename}")

    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")

    if ".." in file.filename or "/" in file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join(FILES_DIR, file.filename)
    content = await file.read()

    # Check if file already exists (update vs new upload)
    is_update = os.path.exists(filepath)

    # Save the file
    with open(filepath, "wb") as f:
        f.write(content)

    # Calculate hash
    file_hash = calculate_hash(content)

    # Update metadata with version tracking
    metadata = load_metadata()
    current_version = metadata.get(file.filename, {}).get("version", 0)
    new_version = current_version + 1

    metadata[file.filename] = {
        "filename": file.filename,
        "hash": file_hash,
        "version": new_version,
        "size_bytes": len(content),
        "uploaded_at": datetime.utcnow().isoformat(),
        "is_update": is_update
    }
    save_metadata(metadata)

    logger.info(f"[{request_id}] File saved: {file.filename} | version: {new_version} | hash: {file_hash}")

    # Notify purge service if this is an update
    if is_update:
        logger.info(f"[{request_id}] File updated — notifying purge service")
        notify_purge_service(file.filename, request_id)

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "hash": file_hash,
        "version": new_version,
        "size_bytes": len(content),
        "is_update": is_update,
        "timestamp": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────
# LIST ALL FILES
# ─────────────────────────────────────────
@app.get("/files")
def list_files():
    metadata = load_metadata()
    files = [
        f for f in os.listdir(FILES_DIR)
        if f != "metadata.json"
    ]
    result = []
    for f in files:
        info = metadata.get(f, {})
        result.append({
            "filename": f,
            "hash": info.get("hash", "unknown"),
            "version": info.get("version", 1),
            "size_bytes": info.get("size_bytes", 0),
            "uploaded_at": info.get("uploaded_at", "unknown")
        })

    logger.info(f"Files listed: {len(result)} files")
    return {"total": len(result), "files": result}


# ─────────────────────────────────────────
# FILE INFO / METADATA
# ─────────────────────────────────────────
@app.get("/file-info")
def file_info(filename: str):
    logger.info(f"File info requested for: {filename}")
    metadata = load_metadata()

    if filename not in metadata:
        raise HTTPException(
            status_code=404,
            detail=f"No metadata found for '{filename}'"
        )

    return metadata[filename]


# ─────────────────────────────────────────
# DELETE FILE
# ─────────────────────────────────────────
# @app.delete("/delete-file")
# def delete_file(filename: str):
#     logger.info(f"DELETE called for: {filename}")
#     filepath = os.path.join(FILES_DIR, filename)

#     if not os.path.exists(filepath):
#         raise HTTPException(
#             status_code=404,
#             detail=f"'{filename}' not found"
#         )

#     os.remove(filepath)

#     # Remove from metadata
#     metadata = load_metadata()
#     if filename in metadata:
#         del metadata[filename]
#         save_metadata(metadata)

#     logger.info(f"File deleted: {filename}")
#     return {"message": f"'{filename}' deleted successfully"}




# ─────────────────────────────────────────
# COMPATIBILITY ENDPOINT
# (for edge nodes calling /files/{filename})
# ─────────────────────────────────────────
@app.get("/files/{filename}")
def get_file_by_path(
    filename: str,
    x_request_id: Optional[str] = Header(default="N/A")
):
    request_id = x_request_id
    logger.info(f"[{request_id}] GET /files/{filename} → redirecting to get-file logic")

    # Security check
    if ".." in filename or "\\" in filename:
        logger.warning(f"[{request_id}] Invalid filename attempted: {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = os.path.join(FILES_DIR, filename)

    if not os.path.exists(filepath):
        logger.warning(f"[{request_id}] File not found: {filename}")
        raise HTTPException(
            status_code=404,
            detail=f"'{filename}' not found on origin server"
        )

    # Simulate origin latency
    logger.info(f"[{request_id}] Simulating origin latency (2s)...")
    time.sleep(2)

    # Get metadata
    metadata = load_metadata()
    file_info = metadata.get(filename, {})
    file_hash = file_info.get("hash", "unknown")
    version = file_info.get("version", 1)

    logger.info(f"[{request_id}] Serving: {filename} | version: {version} | hash: {file_hash}")

    return FileResponse(
        path=filepath,
        filename=filename,
        headers={
            "X-File-Hash": file_hash,
            "X-File-Version": str(version),
            "X-Request-ID": request_id,
            "X-Served-By": "origin-server"
        }
    )