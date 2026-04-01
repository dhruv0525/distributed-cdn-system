from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Service is running"}
# minor update 