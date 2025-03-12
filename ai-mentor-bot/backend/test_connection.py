import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

try:
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    
    if connection.is_connected():
        print("✅ Successfully connected to MySQL database!")
except Error as e:
    print(f"❌ Error while connecting to MySQL: {e}")
    connection = None  # Make sure connection is defined
finally:
    if connection and connection.is_connected():
        connection.close()
        print("✅ MySQL connection closed.")
