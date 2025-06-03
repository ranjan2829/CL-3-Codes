from fyers_apiv3.FyersWebsocket.tbt_ws import FyersTbtSocket, SubscriptionModes
import time
import logging
import os
from datetime import datetime

# Setup logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Logs')
os.makedirs(logs_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, f'live_orderbook_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', 
                    handlers=[logging.StreamHandler(), logging.FileHandler(log_file_path)])
logger = logging.getLogger(__name__)

# Store last timestamp to track per-second data
last_timestamp = {}
second_data = {}

def onopen():
    """
    Callback function to subscribe to data type and symbols upon WebSocket connection.
    """
    logger.info("Connection opened")
    
    # Subscribe to both depth and quotes for full data
    symbols = ['NSE:NIFTY25JUNFUT']
    
    # Subscribe to market depth
    fyers.subscribe(symbol_tickers=symbols, channelNo='1', mode=SubscriptionModes.DEPTH)
    
    # Also subscribe to quotes for tick data
    fyers.subscribe(symbol_tickers=symbols, channelNo='2', mode=SubscriptionModes.QUOTE)
    
    # Enable both channels
    fyers.switchChannel(resume_channels=['1', '2'], pause_channels=[])
    
    logger.info(f"Subscribed to {symbols}")
    
    # Keep the socket running to receive real-time data
    fyers.keep_running()

def on_depth_update(ticker, message):
    """
    Callback function to handle depth data.
    """
    # Get current timestamp in seconds
    current_time = int(time.time())
    symbol = ticker.split(':')[-1] if ':' in ticker else ticker
    
    # Initialize tracking for this symbol if not already done
    if symbol not in last_timestamp:
        last_timestamp[symbol] = current_time
        second_data[symbol] = {
            'depth': [],
            'quotes': []
        }
    
    # Create a depth snapshot
    depth_snapshot = {
        'timestamp': message.timestamp,
        'total_buy_qty': message.tbq,
        'total_sell_qty': message.tsq,
        'bid_prices': message.bidprice,
        'ask_prices': message.askprice,
        'bid_quantities': message.bidqty,
        'ask_quantities': message.askqty,
    }
    
    # Add to current second's data
    second_data[symbol]['depth'].append(depth_snapshot)
    
    # If a new second has started, process the previous second's data
    if current_time > last_timestamp[symbol]:
        process_second_data(symbol, last_timestamp[symbol])
        last_timestamp[symbol] = current_time
        second_data[symbol] = {
            'depth': [depth_snapshot],
            'quotes': []
        }

def on_quote_update(ticker, message):
    """
    Callback function to handle quote data (price ticks).
    """
    current_time = int(time.time())
    symbol = ticker.split(':')[-1] if ':' in ticker else ticker
    
    # Initialize tracking for this symbol if not already done
    if symbol not in last_timestamp:
        last_timestamp[symbol] = current_time
        second_data[symbol] = {
            'depth': [],
            'quotes': []
        }
    
    # Create a quote snapshot
    quote_snapshot = {
        'timestamp': message.timestamp,
        'ltp': message.ltp,
        'volume': message.vol_traded_today,
        'open': message.open_price,
        'high': message.high_price,
        'low': message.low_price,
        'close': message.close_price,
    }
    
    # Add to current second's data
    second_data[symbol]['quotes'].append(quote_snapshot)
    
    # If a new second has started, process the previous second's data
    if current_time > last_timestamp[symbol]:
        process_second_data(symbol, last_timestamp[symbol])
        last_timestamp[symbol] = current_time
        second_data[symbol] = {
            'depth': [],
            'quotes': [quote_snapshot]
        }

def process_second_data(symbol, timestamp):
    """
    Process and store all data received in the past second.
    """
    data = second_data[symbol]
    
    if not data['quotes'] and not data['depth']:
        return
    
    # Calculate aggregated metrics for the second
    second_summary = {
        'symbol': symbol,
        'timestamp': timestamp,
        'datetime': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # Process quote data if available
    if data['quotes']:
        # Get the latest quote
        latest_quote = data['quotes'][-1]
        second_summary.update({
            'last_price': latest_quote['ltp'],
            'volume': latest_quote['volume'],
            'open': latest_quote['open'],
            'high': latest_quote['high'],
            'low': latest_quote['low'],
            'close': latest_quote['close'],
            'tick_count': len(data['quotes']),
        })
    
    # Process depth data if available
    if data['depth']:
        # Get the latest depth
        latest_depth = data['depth'][-1]
        second_summary.update({
            'total_buy_qty': latest_depth['total_buy_qty'],
            'total_sell_qty': latest_depth['total_sell_qty'],
            'buy_sell_ratio': latest_depth['total_buy_qty'] / latest_depth['total_sell_qty'] if latest_depth['total_sell_qty'] > 0 else float('inf'),
            'top_bid': latest_depth['bid_prices'][0] if latest_depth['bid_prices'] else None,
            'top_ask': latest_depth['ask_prices'][0] if latest_depth['ask_prices'] else None,
            'depth_updates': len(data['depth']),
        })
    
    # Log the per-second summary
    logger.info(f"Per-second data: {second_summary}")
    
    # Here you could also save the data to a database or file
    # store_second_data(second_summary)

def onerror(message):
    """
    Callback function to handle WebSocket errors.
    """
    logger.error(f"WebSocket error: {message}")

def onclose(message):
    """
    Callback function to handle WebSocket connection close events.
    """
    logger.info(f"Connection closed: {message}")

def onerror_message(message):
    """
    Callback function for error message events from the server.
    """
    logger.error(f"Error message from server: {message}")

# Initialize the Fyers WebSocket
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb1BuSGNmcHlYcHEzMzVXbXNlQkN4WW1FT3RNRHBwNjZPdjVtMjhrLWQxaFE0eHgtQWdOc2JkVnZSZXNEVHNQdlcwMzhtZnVNbWFrTHBnTFRaRkswUTJFYzMyQnB0eVA0a1V4YUhqZF9pdk9PZXdLYz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJkZWNhY2RhZDNmNzdjMGNkYTE0OThlNzY1MzdiMTMyYjcxNGMyZTg0NmQzNDFmMmZiYzkzZmY1YSIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDE4NSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ4OTk3MDAwLCJpYXQiOjE3NDg5MjI4NDQsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0ODkyMjg0NCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.DEUwHCRwK7GO-E869LO1EKSGRxjygcu4tesq5vj0Grw"

fyers = FyersTbtSocket(
    access_token=access_token,
    write_to_file=False,
    log_path=logs_dir,
    on_open=onopen,
    on_close=onclose,
    on_error=onerror,
    on_depth_update=on_depth_update,
    on_quote_update=on_quote_update,  # Add quote handler
    on_error_message=onerror_message
)

# Establish a connection to the Fyers WebSocket
if __name__ == "__main__":
    try:
        logger.info("Starting Live Orderbook data collection")
        fyers.connect()
    except KeyboardInterrupt:
        logger.info("Stopping data collection due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")