import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if conn.is_connected():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed.")
    except mysql.connector.Error as e:
        print(f"❌ Error connecting to database: {e}")
    finally:
        if conn:
            conn.close()

test_db_connection()
