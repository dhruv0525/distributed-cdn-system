from fastapi import FastAPI
from typing import Dict
import time
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Node Storage
# -------------------------------
nodes: Dict[str, dict] = {
    "edge-a": {
        "id": "edge-a",
        "url": "http://edge-a:8000",
        "region": "America",
        "last_heartbeat": time.time(),
        "status": "Healthy"
    },
    "edge-b": {
        "id": "edge-b",
        "url": "http://edge-b:8000",
        "region": "Europe",
        "last_heartbeat": time.time(),
        "status": "Healthy"
    },
    "edge-c": {
        "id": "edge-c",
        "url": "http://edge-c:8000",
        "region": "Asia",
        "last_heartbeat": time.time(),
        "status": "Healthy"
    }
}

HEARTBEAT_TIMEOUT = 10

# -------------------------------
# UPDATE STATUS
# -------------------------------
def update_status():
    now = time.time()
    for node in nodes.values():
        if now - node["last_heartbeat"] > HEARTBEAT_TIMEOUT:
            node["status"] = "Down"

# -------------------------------
# ROUTES
# -------------------------------
@app.get("/")
def root():
    return {"message": "Service Registry is running"}

@app.get("/nodes")
def get_nodes():
    update_status()
    return list(nodes.values())

@app.post("/register")
def register_node(node: dict):
    node_id = node["id"]

    nodes[node_id] = {
        "id": node_id,
        "url": node["url"],
        "region": node["region"],
        "last_heartbeat": time.time(),
        "status": "Healthy"
    }

    return {"message": "Node registered", "node": nodes[node_id]}

@app.post("/heartbeat")
def heartbeat(data: dict):
    node_id = data.get("id")
    status = data.get("status", "Healthy")

    if node_id in nodes:
        nodes[node_id]["last_heartbeat"] = time.time()
        nodes[node_id]["status"] = status
        return {"message": "Heartbeat updated"}

    return {"error": "Node not found"}