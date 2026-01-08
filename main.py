from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/calculate")
def calculate(payload: dict):
    return {
        "message": "Server is running",
        "input": payload
    }