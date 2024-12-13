import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get MySQL credentials from environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# MySQL connection setup
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD
)

# Create a cursor to execute SQL commands
cursor = db.cursor()

# Step 1: Create the Database
try:
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
    print(f"Database '{MYSQL_DATABASE}' created or already exists.")
except mysql.connector.Error as err:
    print(f"Error creating database: {err}")

# Step 2: Switch to the Database
try:
    cursor.execute(f"USE {MYSQL_DATABASE}")
    print(f"Switched to database '{MYSQL_DATABASE}'.")
except mysql.connector.Error as err:
    print(f"Error switching to database: {err}")


# Step 3: Create the Table
create_table_query = """
DROP TABLE trades;
"""
try:
    cursor.execute(create_table_query)
    print("Table 'trades' dropped.")
except mysql.connector.Error as err:
    print(f"Error dropping table: {err}")
# Step 3: Create the Table
create_table_query = """
CREATE TABLE IF NOT EXISTS trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp INT NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    size DECIMAL(18, 8) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    tickDirection VARCHAR(15) NOT NULL,
    tradeid VARCHAR(40) NOT NULL,
    UNIQUE (tradeid)
);
"""
try:
    cursor.execute(create_table_query)
    print("Table 'trades' created or already exists.")
except mysql.connector.Error as err:
    print(f"Error creating table: {err}")

# Close the connection
cursor.close()
db.close()
