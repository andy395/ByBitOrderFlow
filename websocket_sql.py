from pybit.unified_trading import WebSocket
from datetime import datetime
from database_utils import connect_db


# MySQL connection setup
db = connect_db()
cursor = db.cursor()

# WebSocket setup
ws = WebSocket(testnet=False, channel_type="inverse")

# Insert trade data into MySQL
def save_trade_to_db(trade_data):
    sql = """
        INSERT INTO trades (timestamp, symbol, side, size, price, tickDirection, tradeid)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (
                int(trade_data["T"]) // 1000,  # Convert milliseconds to seconds
                trade_data["s"],
                trade_data["S"],  
                float(trade_data["v"]),
                float(trade_data["p"]),
                trade_data["L"],
                trade_data["i"]
    )
    cursor.execute(sql, values)
    db.commit()
    print(trade_data)
# WebSocket message handler
def handle_message(message):
    if "data" in message and isinstance(message["data"], list):
        for trade in message["data"]:
            save_trade_to_db(trade)

# Subscribe to trade stream
ws.trade_stream(symbol="BTCUSD", callback=handle_message)

print("WebSocket feed running. Press Ctrl+C to stop.")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Stopping WebSocket feed.")
    ws.close()
    db.close()
