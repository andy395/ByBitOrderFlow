import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# File path to read data
file_path = 'data/BTCUSD2024-12-10.csv'

# Define 5-minute bin size and price bin size
price_bin_size = 50

# Function to process CSV and prepare data
def process_csv():
    try:
        # Load the CSV
        df = pd.read_csv(file_path)

        # Convert the timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        # Define 5-minute intervals
        df['5min_bin'] = df['timestamp'].dt.floor('5T')

        # Group prices into $50 increments
        df['price_bin'] = (df['price'] // price_bin_size) * price_bin_size

        # Separate data into buy and sell trades
        buy_data = df[df['side'] == 'Buy']
        sell_data = df[df['side'] == 'Sell']

        # Aggregate buy and sell volumes by 5-minute bin and price bin
        buy_agg = buy_data.groupby(['5min_bin', 'price_bin'])['size'].sum().reset_index(name='buy_volume')
        sell_agg = sell_data.groupby(['5min_bin', 'price_bin'])['size'].sum().reset_index(name='sell_volume')

        # Merge buy and sell data
        agg_data = pd.merge(buy_agg, sell_agg, on=['5min_bin', 'price_bin'], how='outer').fillna(0)

        # Calculate volume delta (buy volume - sell volume)
        agg_data['volume_delta'] = agg_data['buy_volume'] - agg_data['sell_volume']

        # Calculate Cumulative Volume Delta (CVD)
        cvd = agg_data.groupby('5min_bin')['volume_delta'].sum().cumsum().reset_index(name='cumulative_volume_delta')

        # Calculate OHLC data for price
        ohlc = df.groupby('5min_bin').agg(
            open_price=('price', 'first'),
            high_price=('price', 'max'),
            low_price=('price', 'min'),
            close_price=('price', 'last')
        ).reset_index()

        return agg_data, cvd, ohlc
    except Exception as e:
        print(f"Error processing CSV: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Function to update the chart dynamically
def update_chart(frame):
    agg_data, cvd, ohlc = process_csv()

    if agg_data.empty:
        return  # Skip if no data

    # Clear the current plots
    ax[0].clear()
    ax[1].clear()

    # Plot the Footprint Chart
    time_bins = agg_data['5min_bin'].unique()
    for time_bin in time_bins:
        candle_data = agg_data[agg_data['5min_bin'] == time_bin]
        ohlc_data = ohlc[ohlc['5min_bin'] == time_bin]

        if not ohlc_data.empty:
            open_price = ohlc_data['open_price'].values[0]
            close_price = ohlc_data['close_price'].values[0]
            high_price = ohlc_data['high_price'].values[0]
            low_price = ohlc_data['low_price'].values[0]

            # Candlestick rectangle
            ax[0].plot([time_bin, time_bin], [low_price, high_price], color='black', linewidth=1)
            ax[0].add_patch(plt.Rectangle(
                (time_bin, min(open_price, close_price)),
                width=pd.Timedelta('5 minutes'),
                height=abs(open_price - close_price),
                color='green' if close_price > open_price else 'red',
                alpha=0.6
            ))

        # Volume deltas
        price_bins = candle_data['price_bin']
        volume_deltas = candle_data['volume_delta']
        for price_bin, delta in zip(price_bins, volume_deltas):
            color = 'green' if delta > 0 else 'red'
            ax[0].add_patch(plt.Rectangle(
                (time_bin, price_bin),
                width=pd.Timedelta('5 minutes'),
                height=50,
                color=color,
                alpha=0.6
            ))

    # Format footprint chart
    ax[0].set_title("Footprint Chart with Live Updates")
    ax[0].set_ylabel("Price ($)")
   # ax[0].invert_yaxis()
    ax[0].grid(True, linestyle='--', alpha=0.5)

    # Plot Cumulative Volume Delta (CVD)
    ax[1].plot(cvd['5min_bin'], cvd['cumulative_volume_delta'], color='blue', linewidth=1.5, label='CVD')
    ax[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax[1].set_title("Cumulative Volume Delta (CVD)")
    ax[1].set_xlabel("Time (5-minute intervals)")
    ax[1].legend()
    ax[1].grid(True, linestyle='--', alpha=0.5)

# Set up the Matplotlib figure and axes
fig, ax = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [4, 1]})

# Use Matplotlib's FuncAnimation for live updates
ani = FuncAnimation(fig, update_chart, interval=5000)  # Update every 5 seconds

# Show the plot
plt.show()
