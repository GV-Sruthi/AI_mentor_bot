from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai  # For GPT-4
import json
import mysql.connector
import os
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

@app.post("/process_message")
async def process_message(message: Message):
    user_message = message.message.lower()

    try:
        if "code" in user_message or "programming" in user_message:
            # Call Code Llama API
            response = requests.post(
                codellama_api_url,
                json={"prompt": user_message, "max_tokens": 500, "temperature": 0.7}
            )
            if response.status_code == 200:
                codellama_response = response.json().get("response", "I couldn't find a suitable response.")
            else:
                codellama_response = f"Code Llama API Error: {response.status_code}"
                
            reply = f"📝 Here's some help with your code:\n\n{codellama_response}"
        
        else:
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

        
        return {"reply": reply}
    
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
