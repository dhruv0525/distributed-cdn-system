from fastapi import FastAPI

app = FastAPI()

# Fake file storage
FILES = {
    "test.jpg": {"content": "This is test image"},
    "video.mp4": {"content": "This is video file"}
}

@app.get("/get-file/{file}")
def get_file(file: str):
    if file in FILES:
        return FILES[file]
    return {"message": "File not found"}

@app.get("/")
def root():
    return {"message": "Origin server running"}