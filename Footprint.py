import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# File path
file_path = 'data/BTCUSD2024-12-10.csv'

# Load the trade history data
df = pd.read_csv(file_path)

# Convert the timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

# Define 5-minute intervals
df['5min_bin'] = df['timestamp'].dt.floor('5T')

# Group prices into $50 increments
price_bin_size = 50
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

# Visualise the footprint chart with CVD
def plot_footprint_chart_with_cvd(data, ohlc_data, cvd_data, time_bins):
    fig, ax = plt.subplots(2, 1, figsize=(16, 12), sharex=True, gridspec_kw={'height_ratios': [4, 1]})
    
    # Plot Footprint Chart
    for time_bin in time_bins:
        # Filter data for the specific 5-minute candle
        candle_data = data[data['5min_bin'] == time_bin]
        ohlc = ohlc_data[ohlc_data['5min_bin'] == time_bin]
        
        # OHLC info
        open_price = ohlc['open_price'].values[0]
        close_price = ohlc['close_price'].values[0]
        high_price = ohlc['high_price'].values[0]
        low_price = ohlc['low_price'].values[0]

        # Draw the candlestick rectangle (Open-Close)
        ax[0].plot([time_bin, time_bin], [low_price, high_price], color='black', linewidth=1)
        ax[0].add_patch(plt.Rectangle(
            (time_bin, min(open_price, close_price)),
            width=pd.Timedelta('5 minutes'),
            height=abs(open_price - close_price),
            color='green' if close_price > open_price else 'red',
            alpha=0.6
        ))
        
        # Compute aggregated volume delta for each price bin
        price_bins = candle_data['price_bin']
        volume_deltas = candle_data['volume_delta']
        
        # Plot volume deltas as rectangles
        for price_bin, delta in zip(price_bins, volume_deltas):
            color = 'green' if delta > 0 else 'red'
            ax[0].add_patch(plt.Rectangle(
                (time_bin, price_bin),
                width=pd.Timedelta('5 minutes'),
                height=price_bin_size,
                color=color,
                alpha=0.6
            ))
    
    # Format footprint chart
    ax[0].set_ylabel('Price ($)')
    ax[0].set_title('Footprint Chart with Cumulative Volume Delta')
    ax[0].grid(True, linestyle='--', alpha=0.5)
    
    # Plot Cumulative Volume Delta
    ax[1].plot(cvd_data['5min_bin'], cvd_data['cumulative_volume_delta'], color='blue', linewidth=1.5, label='Cumulative Volume Delta')
    ax[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax[1].set_ylabel('CVD')
    ax[1].set_xlabel('Time (5-minute intervals)')
    ax[1].legend()
    ax[1].grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()

# Get unique time bins
unique_bins = agg_data['5min_bin'].unique()

# Plot the chart
plot_footprint_chart_with_cvd(agg_data, ohlc, cvd, unique_bins)
