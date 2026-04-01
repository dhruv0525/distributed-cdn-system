from fastapi import FastAPI
import requests

app = FastAPI()

# IMPORTANT: use docker service name
REGISTRY_URL = "http://registry:8000"


@app.get("/")
def root():
    return {"message": "Purge Service is running"}


@app.post("/purge")
def purge(data: dict):
    file_name = data.get("file")

    if not file_name:
        return {"error": "File name required"}

    try:
        nodes = requests.get(f"{REGISTRY_URL}/nodes").json()
    except:
        return {"error": "Registry not reachable"}

    results = []

    for node in nodes:
        try:
            url = f"{node['url']}/cache/{file_name}"
            res = requests.delete(url, timeout=2)

            if res.status_code == 200:
                results.append({"node": node["id"], "status": "Success"})
            else:
                results.append({"node": node["id"], "status": "Failed"})

        except:
            results.append({"node": node["id"], "status": "Error"})

    return {
        "message": "Purge completed",
        "file": file_name,
        "results": results
    }