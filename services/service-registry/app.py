from fastapi import FastAPI

app = FastAPI()

# -------------------------------
# Static Node Registry (TEMPORARY)
# -------------------------------
# Later you can make this dynamic,
# but for now this is enough to make system work

NODES = [
    {"id": "edge-a", "url": "http://edge-a:8000", "region": "America"},
    {"id": "edge-b", "url": "http://edge-b:8000", "region": "Europe"},
    {"id": "edge-c", "url": "http://edge-c:8000", "region": "Asia"},
]

# -------------------------------
# GET /nodes
# -------------------------------
@app.get("/nodes")
def get_nodes():
    return NODES


# -------------------------------
# (Optional future use)
# -------------------------------
@app.post("/register")
def register_node(node: dict):
    NODES.append(node)
    return {"message": "Node registered", "node": node}


@app.get("/")
def root():
    return {"message": "Service Registry is running"}