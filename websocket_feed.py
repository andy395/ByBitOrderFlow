from pybit.unified_trading import WebSocket
import pandas as pd
import os

# File path to store live data
file_path = 'data/BTCUSD2024-12-10.csv'

# Set up WebSocket feed
ws = WebSocket(testnet=False, channel_type="inverse")

# Function to handle incoming WebSocket messages
def handle_message(message):
    if "data" in message and isinstance(message["data"], list):
        trades = message["data"]
        trade_list = []

        for trade in trades:
            trade_data = {
                "timestamp": int(trade["T"]) // 1000,  # Convert milliseconds to seconds
                "sym": "BTCUSD",
                "side": trade["S"],  # Buy or Sell
                "size": float(trade["v"]),
                "price": float(trade["p"]),
                "tickDirection": trade["L"],
                "tradeid": trade["i"]
            } 
            trade_list.append(trade_data)
        print(trade_data)
        # Convert to DataFrame
        trade_df = pd.DataFrame(trade_list)

        # Append to CSV file
        if not os.path.isfile(file_path):
            trade_df.to_csv(file_path, index=False, mode='w')  # Create new file with headers
        else:
            trade_df.to_csv(file_path, index=False, mode='a', header=False)  # Append without headers

# Subscribe to Bybit trade stream
ws.trade_stream(symbol="BTCUSD", callback=handle_message)

# Keep the script running
print("WebSocket feed is running. Press Ctrl+C to stop.")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("WebSocket feed stopped.")
    ws.close()

"""  "timestamp": int(trade["T"]) // 1000,  # Convert milliseconds to seconds,
                "SYM": "BTCUSD",
                "side": trade["S"],  # Buy or Sell
                "size": float(trade["v"]),
                "price": float(trade["p"]),
                "tickDirection": float(trade["L"]),
                "tradeid": float(trade["i"]) """
