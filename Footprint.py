
from database_utils import connect_db

# MySQL connection setup
db = connect_db()

import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# Define price bin size and time bin interval
price_bin_size = 50
time_bin_interval = '5T'  # 5 minutes

# Connect to MySQL and fetch data
def fetch_data_from_db():
    try:
        
 
        
        # Query to fetch data from the trades table
        query = """
        SELECT timestamp, price, size, side
        FROM trades
        WHERE timestamp >= UNIX_TIMESTAMP(NOW() - INTERVAL 12 HOUR);  -- Last 12 hours
        """
        
        # Fetch data into a DataFrame
        df = pd.read_sql(query, con=db)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['5min_bin'] = df['timestamp'].dt.floor(time_bin_interval)
        df['price_bin'] = (df['price'] // price_bin_size) * price_bin_size
        
        return df
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return pd.DataFrame()
    finally:
        if 'db' in locals() and db.is_connected():
            db.close()

# Aggregate data for footprint chart
def aggregate_data(df):
    buy_data = df[df['side'] == 'Buy']
    sell_data = df[df['side'] == 'Sell']

    buy_agg = buy_data.groupby(['5min_bin', 'price_bin'])['size'].sum().reset_index(name='buy_volume')
    sell_agg = sell_data.groupby(['5min_bin', 'price_bin'])['size'].sum().reset_index(name='sell_volume')

    agg_data = pd.merge(buy_agg, sell_agg, on=['5min_bin', 'price_bin'], how='outer').fillna(0)
    agg_data['volume_delta'] = agg_data['buy_volume'] - agg_data['sell_volume']

    ohlc = df.groupby('5min_bin').agg(
        open_price=('price', 'first'),
        high_price=('price', 'max'),
        low_price=('price', 'min'),
        close_price=('price', 'last')
    ).reset_index()

    return agg_data, ohlc

# Plot the footprint chart
def plot_footprint_chart(agg_data, ohlc_data):
    fig, ax = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

    # Footprint chart
    time_bins = ohlc_data['5min_bin'].unique()
    for time_bin in time_bins:
        candle_data = agg_data[agg_data['5min_bin'] == time_bin]
        ohlc = ohlc_data[ohlc_data['5min_bin'] == time_bin]

        if not ohlc.empty:
            open_price = ohlc['open_price'].values[0]
            close_price = ohlc['close_price'].values[0]
            high_price = ohlc['high_price'].values[0]
            low_price = ohlc['low_price'].values[0]

            # Candlestick
            ax[0].plot([time_bin, time_bin], [low_price, high_price], color='black', linewidth=1)
            ax[0].add_patch(Rectangle(
                (time_bin, min(open_price, close_price)),
                pd.Timedelta('5 minutes'),
                abs(open_price - close_price),
                color='green' if close_price > open_price else 'red',
                alpha=0.6
            ))

        # Footprint volumes
        for _, row in candle_data.iterrows():
            price_bin = row['price_bin']
            volume_delta = row['volume_delta']
            color = 'green' if volume_delta > 0 else 'red'
            ax[0].add_patch(Rectangle(
                (time_bin, price_bin),
                pd.Timedelta('5 minutes'),
                price_bin_size,
                color=color,
                alpha=0.6
            ))

    # Add labels, grid, and formatting
    ax[0].set_ylabel('Price ($)')
    ax[0].set_title('Footprint Chart with Volume Delta')
    ax[0].grid(True, linestyle='--', alpha=0.5)

    # Volume delta (cumulative)
    cvd = agg_data.groupby('5min_bin')['volume_delta'].sum().cumsum().reset_index()
    ax[1].plot(cvd['5min_bin'], cvd['volume_delta'], color='blue', linewidth=1.5, label='Cumulative Volume Delta')
    ax[1].axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax[1].set_ylabel('CVD')
    ax[1].set_xlabel('Time')
    ax[1].legend()
    ax[1].grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()

# Main workflow
df = fetch_data_from_db()
if not df.empty:
    agg_data, ohlc_data = aggregate_data(df)
    plot_footprint_chart(agg_data, ohlc_data)
else:
    print("No data retrieved from the database.")
