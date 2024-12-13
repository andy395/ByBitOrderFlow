from database_utils import connect_db
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox

# Define price bin size and default time range
price_bin_size = 50
time_bin_interval = '5T'  # 5 minutes
default_time_range = 3  # Default to the last 3 hours
chart_initialized = False

# Connect to MySQL and fetch data for the given range
def fetch_data_from_db(hours):
    try:
        db = connect_db()
        query = f"""
        SELECT timestamp, price, size, side
        FROM trades
        WHERE timestamp >= UNIX_TIMESTAMP(NOW() - INTERVAL {hours} HOUR);
        """
        df = pd.read_sql(query, con=db)
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

# Plot the chart dynamically
def update_chart(frame):

    # Fetch data for the current time range
    df = fetch_data_from_db(current_time_range)
    if df.empty:
        print("No new data retrieved.")
        return

    agg_data, ohlc_data = aggregate_data(df)

       # y_limits_cvd = ax_cvd.get_ylim()

    # Clear the current plots
    ax_main.clear()
    ax_cvd.clear()

    # Plot footprint chart
    time_bins = ohlc_data['5min_bin'].unique()
    for time_bin in time_bins:
        candle_data = agg_data[agg_data['5min_bin'] == time_bin]
        ohlc = ohlc_data[ohlc_data['5min_bin'] == time_bin]

        if not ohlc.empty:
            open_price = ohlc['open_price'].values[0]
            close_price = ohlc['close_price'].values[0]
            high_price = ohlc['high_price'].values[0]
            low_price = ohlc['low_price'].values[0]
            ax_main.plot([time_bin, time_bin], [low_price, high_price], color='black', linewidth=3)
            ax_main.add_patch(Rectangle(
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
            ax_main.add_patch(Rectangle(
                (time_bin, price_bin),
                pd.Timedelta('5 minutes'),
                price_bin_size,
                color=color,
                alpha=0.6
            ))
            # Annotate volume delta
            ax_main.text(
                time_bin + pd.Timedelta('2.5 minutes'),
                price_bin + price_bin_size / 2,
                f"{volume_delta/1000:.1f}k",
                color='black',
                ha='center',
                va='center',
                fontsize=6
            )

    # Volume delta (cumulative)
    cvd = agg_data.groupby('5min_bin')['volume_delta'].sum().cumsum().reset_index()
    ax_cvd.plot(cvd['5min_bin'], cvd['volume_delta'], color='blue', linewidth=1.5, label='Cumulative Volume Delta')
    ax_cvd.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax_cvd.set_ylabel('CVD')
    ax_cvd.set_xlabel('Time')
    ax_cvd.legend()
    ax_cvd.grid(True, linestyle='--', alpha=0.5)

    # Restore zoom location if initialized


    

# Update time range dynamically from the TextBox
def on_text_submit(text):
    global current_time_range
    try:
        current_time_range = int(text)
        print(f"Time range updated to: {current_time_range} hours")
        update_chart(None)  # Trigger an immediate update
    except ValueError:
        print("Invalid input. Please enter a valid integer.")

# Set up Matplotlib figure and shared axes
fig, (ax_main, ax_cvd) = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [4, 1]}, sharex=True)

# Add a TextBox for time range input
axbox = plt.axes([0.15, 0.95, 0.1, 0.03])  # Position of the TextBox
text_box = TextBox(axbox, "Time Range (hrs):", initial=str(default_time_range))
text_box.on_submit(on_text_submit)

# Initialize global variables
current_time_range = default_time_range

# Use FuncAnimation for live updates every 15 seconds
ani = FuncAnimation(fig, update_chart, interval=15000)  # 15000ms = 15 seconds

plt.tight_layout()
plt.show()
