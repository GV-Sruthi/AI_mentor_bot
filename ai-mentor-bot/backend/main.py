from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

# Get password from environment variable
mysql_password = os.getenv("MYSQL_PASSWORD")

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="ai_mentor_bot"
)
cursor = db.cursor()

class StudyPlan(BaseModel):
    user_id: str
    topic: str
    description: str

@app.get("/")
def read_root():
    return {"message": "AI Mentor Bot Backend Running Successfully"}

@app.post("/create_study_plan/")
def create_study_plan(study_plan: StudyPlan):
    try:
        cursor.execute(
            "INSERT INTO study_plans (user_id, topic, description) VALUES (%s, %s, %s)",
            (study_plan.user_id, study_plan.topic, study_plan.description)
        )
        db.commit()
        return {"message": "Study plan created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
