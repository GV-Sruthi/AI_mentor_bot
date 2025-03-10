from fastapi import FastAPI
import openai

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "AI Mentor Bot Backend is Running"}

@app.post("/ask-ai")
async def ask_ai(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"response": response['choices'][0]['message']['content']}
