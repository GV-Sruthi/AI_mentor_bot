from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

@app.post("/ask-ai")
def ask_ai(request: dict):
    return {"response": f"AI Response to: {request['prompt']}"}
