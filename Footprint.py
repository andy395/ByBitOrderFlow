from pybit.unified_trading import WebSocket
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
from datetime import datetime

# File path to store data
file_path = 'data/BTCUSD2024-09-01.csv'

# Global DataFrame for storing live data
live_data = pd.DataFrame(columns=["timestamp", "symbol", "side", "size", "price"])

# WebSocket setup
ws = WebSocket(testnet=False, channel_type="inverse")

# Function to handle incoming WebSocket messages
def handle_message(message):
    global live_data
    # Ensure the message contains trade data
    if "data" in message and isinstance(message["data"], list):
        trades = message["data"]
        # Prepare a list to store extracted trade data
        trade_list = []
        
        # Extract relevant fields from the message
        for trade in trades:
            trade_data = {
                "timestamp": pd.to_datetime(trade["T"], unit="ms"),  # Convert time to datetime
                "symbol": trade["s"],
                "side": trade["S"],  # Buy or Sell
                "size": float(trade["v"]),  # Trade size
                "price": float(trade["p"]),  # Trade price
            }
            trade_list.append(trade_data)
        
        # Convert to DataFrame and append to live data
        trade_df = pd.DataFrame(trade_list)
        live_data = pd.concat([live_data, trade_df], ignore_index=True)

        # Save to CSV file
        if not os.path.isfile(file_path):
            trade_df.to_csv(file_path, index=False, mode='w')  # Write header
        else:
            trade_df.to_csv(file_path, index=False, mode='a', header=False)  # Append without header

# Subscribe to the trade stream
ws.trade_stream(symbol="BTCUSD", callback=handle_message)

# Function to update the chart
def update_chart(frame):
    global live_data
    if live_data.empty:
        return  # Skip if no data

    # Process the live data for charting
    live_data["5min_bin"] = live_data["timestamp"].dt.floor("5T")
    price_bin_size = 50
    live_data["price_bin"] = (live_data["price"] // price_bin_size) * price_bin_size

    # Calculate buy and sell volumes
    buy_data = live_data[live_data["side"] == "Buy"]
    sell_data = live_data[live_data["side"] == "Sell"]

    buy_agg = buy_data.groupby(["5min_bin", "price_bin"])["size"].sum().reset_index(name="buy_volume")
    sell_agg = sell_data.groupby(["5min_bin", "price_bin"])["size"].sum().reset_index(name="sell_volume")

    agg_data = pd.merge(buy_agg, sell_agg, on=["5min_bin", "price_bin"], how="outer").fillna(0)
    agg_data["volume_delta"] = agg_data["buy_volume"] - agg_data["sell_volume"]

    cvd = agg_data.groupby("5min_bin")["volume_delta"].sum().cumsum().reset_index(name="cumulative_volume_delta")

    # Clear and redraw the chart
    ax1.clear()
    ax2.clear()

    # Plot the footprint chart
    for time_bin in agg_data["5min_bin"].unique():
        candle_data = agg_data[agg_data["5min_bin"] == time_bin]
        price_bins = candle_data["price_bin"]
        volume_deltas = candle_data["volume_delta"]
        for price_bin, delta in zip(price_bins, volume_deltas):
            color = "green" if delta > 0 else "red"
            ax1.barh(price_bin, delta, color=color, alpha=0.6)

    ax1.set_title("Footprint Chart")
    ax1.set_xlabel("Volume Delta")
    ax1.set_ylabel("Price ($50 increments)")
    ax1.grid(True, linestyle="--", alpha=0.5)

    # Plot the cumulative volume delta
    ax2.plot(cvd["5min_bin"], cvd["cumulative_volume_delta"], color="blue", label="CVD")
    ax2.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax2.set_title("Cumulative Volume Delta (CVD)")
    ax2.set_xlabel("Time (5-minute bins)")
    ax2.set_ylabel("CVD")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

# Set up the Matplotlib figure and axes
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={"height_ratios": [4, 1]})

# Use Matplotlib's FuncAnimation for live updates
ani = FuncAnimation(fig, update_chart, interval=5000)  # Update every 5 seconds

# Show the plot
try:
    print("Listening to WebSocket and updating chart... Press Ctrl+C to stop.")
    plt.show()
except KeyboardInterrupt:
    print("Stopped WebSocket stream.")
    ws.close()
