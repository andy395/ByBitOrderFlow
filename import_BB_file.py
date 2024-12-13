from database_utils import connect_db
import pandas as pd
import mysql.connector

# MySQL connection setup
db = connect_db()
cursor = db.cursor()


file_path = 'data/BTCUSD2024-12-12.csv'

# Read the CSV file
try:
    # Load the file into a DataFrame
    df = pd.read_csv(file_path)

    # Map the columns to the database table
    for index, row in df.iterrows():
        sql = """
        INSERT IGNORE INTO trades (timestamp, symbol, side, size, price, tickDirection, tradeid)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            int(row['timestamp']), 
            row['symbol'], 
            row['side'], 
            float(row['size']), 
            float(row['price']), 
            row['tickDirection'], 
            row['trdMatchID']
        )

        # Execute the insert statement
        cursor.execute(sql, values)

    # Commit the transaction
    db.commit()
    print("File imported successfully, duplicates ignored.")

except Exception as e:
    print(f"Error importing file: {e}")

# Close the connection
cursor.close()
db.close()