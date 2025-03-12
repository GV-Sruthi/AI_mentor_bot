import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host="us-east.connect.psdb.cloud",
        user="<your-username>",
        password="<your-password>",
        database="<your-database-name>",
        ssl_ca="path/to/ssl-cert.pem"  # Optional if not working without it
    )
    
    if connection.is_connected():
        print("✅ Connected to MySQL database successfully!")
except Error as e:
    print(f"❌ Error while connecting to MySQL: {e}")
finally:
    if connection.is_connected():
        connection.close()
        print("✅ Connection closed.")
