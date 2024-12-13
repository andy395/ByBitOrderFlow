import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MySQL connection details from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# MySQL connection setup
def connect_db():
    print("Connecting to the database...")
    try:
        db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        print("Connected to the database!")
        return db  # Return the connection object if successful
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Invalid username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: Database does not exist.")
        else:
            print(f"Error: {err}")
        return None  # Return None if connection fails
