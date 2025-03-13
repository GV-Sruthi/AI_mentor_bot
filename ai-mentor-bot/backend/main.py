from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import openai  # For GPT-4
import json
import mysql.connector
import os
import re
from dotenv import load_dotenv
import requests  # For making HTTP requests to Code Llama API

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# Get API keys and passwords from environment variables
mysql_password = os.getenv("MYSQL_PASSWORD")
openai.api_key = os.getenv("OPENAI_API_KEY")
codellama_api_url = os.getenv("CODELLAMA_API_URL")  # URL for Code Llama API

# Define Pydantic models for request bodies
class Message(BaseModel):
    message: str

class StudyPlan(BaseModel):
    user_id: str
    topic: str
    description: str

@app.get("/")
def read_root():
    return {"message": "AI Mentor Bot Backend Running Successfully"}

# Function to determine which model to use
def select_model(user_message: str) -> str:
    if re.search(r"code|python|debug|algorithm|function|program|script|error", user_message, re.IGNORECASE):
        return "CodeLlama"  # Code Llama for coding-related queries
    else:
        return "GPT-4"  # GPT-4 for general knowledge or guidance

# Process message from the user
@app.post("/process_message")
async def process_message(message: Message):
    try:
        user_message = message.message
        
        selected_model = select_model(user_message)
        if selected_model == "GPT-4":
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful and knowledgeable AI assistant."},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            reply = response.choices[0].message['content']
            model_name = "GPT-4"
        elif selected_model == "CodeLlama":
            response = requests.post(
                codellama_api_url,
                json={"message": user_message},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                reply = response.json().get("reply", "Sorry, I couldn't understand your query.")
            else:
                reply = f"Error: Code Llama API responded with status code {response.status_code}"
            model_name = "Code Llama"

        
        return {"reply": f"🤖 [{model_name}] - {reply}"}
        
    except Exception as e:
        return {"reply": f"Error: {str(e)}"}


@app.post("/create_study_plan/")
def create_study_plan(study_plan: StudyPlan):
    try:
        # Connect to MySQL
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_password,
            database="ai_mentor_bot"
        )
        cursor = db.cursor()
        
        cursor.execute(
            "INSERT INTO study_plans (user_id, topic, description) VALUES (%s, %s, %s)",
            (study_plan.user_id, study_plan.topic, study_plan.description)
        )
        db.commit()
        cursor.close()
        db.close()
        
        return {"message": "Study plan created successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
