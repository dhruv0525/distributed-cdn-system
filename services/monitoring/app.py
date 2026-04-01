from fastapi import FastAPI
import requests

app = FastAPI()

REGISTRY_URL = "http://registry:8000"

logs = []

metrics = {
    "total_requests": 0,
    "purge_requests": 0
}


@app.get("/")
def root():
    return {"message": "Monitoring Service is running"}


@app.get("/nodes-status")
def nodes_status():
    try:
        nodes = requests.get(f"{REGISTRY_URL}/nodes").json()
    except:
        return {"error": "Registry not reachable"}

    status = {}

    for node in nodes:
        status[node["id"]] = node.get("status", "Unknown")

    return status


@app.get("/metrics")
def get_metrics():
    return metrics


@app.get("/logs")
def get_logs():
    return logs


@app.post("/log")
def add_log(entry: dict):
    logs.append(entry)
    return {"message": "Log added"}


@app.post("/metrics/update")
def update_metrics(data: dict):
    for key in data:
        if key in metrics:
            metrics[key] += data[key]
        else:
            metrics[key] = data[key]

    return {"message": "Metrics updated"}