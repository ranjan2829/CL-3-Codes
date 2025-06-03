from fyers_apiv3 import fyersModel
import time
import logging
import os
import numpy as np
from datetime import datetime
import pandas as pd
from collections import deque
import signal
from tabulate import tabulate
import pytz
import sys
import random
from colorama import Fore, Back, Style, init
import shutil

# Initialize colorama
init()

# Setup logging
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Logs')
os.makedirs(logs_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, f'rest_orderbook_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', 
                    handlers=[logging.StreamHandler(), logging.FileHandler(log_file_path)])
logger = logging.getLogger(__name__)

# Symbol to track
SYMBOL = "NSE:NIFTY25JUNFUT"

# Data storage
historical_data = deque(maxlen=100)  # Store recent history for stochastic modeling

# CSV for data storage
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"stochastic_orderbook_{SYMBOL.replace(':', '_')}_{timestamp}.csv"

# Graceful shutdown handler
def signal_handler(sig, frame):
    print(f"\n{Fore.YELLOW}Data collection stopped by user.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Data saved to: {csv_filename}{Style.RESET_ALL}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def fetch_orderbook(fyers):
    """Fetch orderbook data using REST API instead of WebSocket"""
    try:
        # Prepare request data
        data = {
            "symbol": SYMBOL,
            "ohlcv_flag": "1"
        }
        
        # Make API call
        response = fyers.depth(data=data)
        
        # Check if response is valid
        if response and response.get('s') == 'ok' and 'd' in response and SYMBOL in response['d']:
            # Extract orderbook data
            symbol_data = response['d'][SYMBOL]
            
            # Create orderbook snapshot
            current_time = int(time.time())
            orderbook = {
                'timestamp': current_time,
                'datetime': datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'),
                'total_buy_qty': symbol_data.get('totalbuyqty', 0),
                'total_sell_qty': symbol_data.get('totalsellqty', 0),
            }
            
            # Process bid data
            bids = symbol_data.get('bids', [])
            bid_prices = [bid.get('price') for bid in bids]
            bid_quantities = [bid.get('volume') for bid in bids]
            bid_orders = [bid.get('ord') for bid in bids]
            
            # Process ask data
            asks = symbol_data.get('ask', [])
            ask_prices = [ask.get('price') for ask in asks]
            ask_quantities = [ask.get('volume') for ask in asks]
            ask_orders = [ask.get('ord') for ask in asks]
            
            # Add to orderbook
            orderbook['bid_prices'] = bid_prices
            orderbook['ask_prices'] = ask_prices
            orderbook['bid_quantities'] = bid_quantities
            orderbook['ask_quantities'] = ask_quantities
            orderbook['bid_orders'] = bid_orders
            orderbook['ask_orders'] = ask_orders
            
            # Add OHLC data
            orderbook['open'] = symbol_data.get('o', 0)
            orderbook['high'] = symbol_data.get('h', 0)
            orderbook['low'] = symbol_data.get('l', 0)
            orderbook['close'] = symbol_data.get('c', 0)
            orderbook['ltp'] = symbol_data.get('ltp', 0)
            orderbook['volume'] = symbol_data.get('v', 0)
            orderbook['change_percent'] = symbol_data.get('chp', 0)
            
            # Add top of book data
            if bid_prices and ask_prices:
                orderbook['top_bid'] = bid_prices[0]
                orderbook['top_ask'] = ask_prices[0]
                orderbook['mid_price'] = (bid_prices[0] + ask_prices[0]) / 2
                orderbook['spread'] = ask_prices[0] - bid_prices[0]
                orderbook['spread_bps'] = (orderbook['spread'] / orderbook['mid_price']) * 10000
            
            return orderbook
            
        else:
            logger.error(f"Error in API response: {response}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching orderbook: {str(e)}")
        return None

def calculate_stochastic_metrics(orderbook_history):
    """Calculate stochastic metrics based on order book history"""
    # Need at least 2 orderbooks for calculations
    if len(orderbook_history) < 2:
        return {}
    
    # Get current and previous orderbooks
    current_ob = orderbook_history[-1]
    previous_ob = orderbook_history[-2]
    
    # Time difference
    dt = current_ob['timestamp'] - previous_ob['timestamp']
    if dt == 0:
        dt = 0.001  # Avoid division by zero
    
    # Calculate drift (v) - rate of change of liquidity
    bid_drift = (current_ob['total_buy_qty'] - previous_ob['total_buy_qty']) / dt
    ask_drift = (current_ob['total_sell_qty'] - previous_ob['total_sell_qty']) / dt
    
    # Calculate volatility (σ) if we have enough data
    bid_volatility = 0
    ask_volatility = 0
    
    if len(orderbook_history) >= 5:
        # Extract recent quantities
        recent_bid_qty = [ob['total_buy_qty'] for ob in list(orderbook_history)[-5:]]
        recent_ask_qty = [ob['total_sell_qty'] for ob in list(orderbook_history)[-5:]]
        
        # Calculate standard deviation of rate of change
        bid_changes = [(recent_bid_qty[i] - recent_bid_qty[i-1]) for i in range(1, len(recent_bid_qty))]
        ask_changes = [(recent_ask_qty[i] - recent_ask_qty[i-1]) for i in range(1, len(recent_ask_qty))]
        
        bid_volatility = np.std(bid_changes) if bid_changes else 0
        ask_volatility = np.std(ask_changes) if ask_changes else 0
    
    # Calculate the Wiener process component (dW)
    # This is effectively the residual random component
    bid_wiener = (current_ob['total_buy_qty'] - previous_ob['total_buy_qty']) - (bid_drift * dt)
    ask_wiener = (current_ob['total_sell_qty'] - previous_ob['total_sell_qty']) - (ask_drift * dt)
    
    # Calculate imbalance metrics
    flow_imbalance = bid_drift - ask_drift
    price_pressure = flow_imbalance / (bid_volatility + ask_volatility + 0.0001)  # Avoid division by zero
    
    # Return all stochastic metrics
    return {
        'bid_drift': bid_drift,
        'ask_drift': ask_drift,
        'flow_imbalance': flow_imbalance,
        'bid_volatility': bid_volatility,
        'ask_volatility': ask_volatility,
        'bid_wiener': bid_wiener,
        'ask_wiener': ask_wiener,
        'price_pressure': price_pressure
    }

def display_orderbook(orderbook, stochastic_metrics=None, first_display=True):
    """Display orderbook with stochastic model insights in terminal with in-place updates"""
    
    if not orderbook:
        if first_display:
            print(f"{Fore.YELLOW}Waiting for orderbook data...{Style.RESET_ALL}")
        return
    
    # Get terminal size
    terminal_width, _ = shutil.get_terminal_size()
    
    # Only clear screen on first display
    if first_display:
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Save the starting position for updates
        print("\033[s", end="", flush=True)
    else:
        # Return to the saved position
        print("\033[u", end="", flush=True)
        
        # Clear to the end of the screen
        print("\033[J", end="", flush=True)
    
    # Header
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * min(80, terminal_width-2)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT} STOCHASTIC ORDER BOOK ANALYSIS: {SYMBOL} {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT} {orderbook['datetime']} {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * min(80, terminal_width-2)}{Style.RESET_ALL}\n")
    
    # Market data
    price_color = Fore.GREEN if orderbook.get('change_percent', 0) >= 0 else Fore.RED
    print(f"LTP: {price_color}{orderbook.get('ltp', 0)} ({orderbook.get('change_percent', 0):+.2f}%){Style.RESET_ALL} | "
          f"Volume: {orderbook.get('volume', 0):,}")
    print(f"OHLC: {orderbook.get('open', 0)} / {orderbook.get('high', 0)} / {orderbook.get('low', 0)} / {orderbook.get('close', 0)}")
    print()
    
    # Order book display
    bid_prices = orderbook.get('bid_prices', [])[:5]  # Top 5 levels
    ask_prices = orderbook.get('ask_prices', [])[:5]  # Top 5 levels
    bid_qtys = orderbook.get('bid_quantities', [])[:5]
    ask_qtys = orderbook.get('ask_quantities', [])[:5]
    bid_orders = orderbook.get('bid_orders', [])[:5]
    ask_orders = orderbook.get('ask_orders', [])[:5]
    
    # Pad arrays if needed
    while len(bid_prices) < 5:
        bid_prices.append(None)
        bid_qtys.append(0)
        bid_orders.append(0)
    
    while len(ask_prices) < 5:
        ask_prices.append(None)
        ask_qtys.append(0)
        ask_orders.append(0)
    
    # Create order book table
    book_data = []
    
    # Add asks (in reverse order to show highest ask at the top)
    for i in range(4, -1, -1):
        price = ask_prices[i] if i < len(ask_prices) and ask_prices[i] is not None else "-"
        qty = ask_qtys[i] if i < len(ask_qtys) and ask_qtys[i] is not None else 0
        orders = ask_orders[i] if i < len(ask_orders) and ask_orders[i] is not None else 0
        
        # Format with color
        price_str = f"{Fore.RED}{price}{Style.RESET_ALL}"
        qty_str = f"{Fore.RED}{qty:,}{Style.RESET_ALL}"
        orders_str = f"{Fore.RED}{orders}{Style.RESET_ALL}"
        
        book_data.append(["", "", "", price_str, qty_str, orders_str])
    
    # Add spread row
    if 'spread' in orderbook:
        spread = orderbook['spread']
        spread_bps = orderbook['spread_bps']
        book_data.append(["", "", "", 
                         f"{Fore.YELLOW}{Style.BRIGHT}SPREAD: {spread:.1f} ({spread_bps:.1f} bps){Style.RESET_ALL}", 
                         "", ""])
    
    # Add bids
    for i in range(5):
        price = bid_prices[i] if i < len(bid_prices) and bid_prices[i] is not None else "-"
        qty = bid_qtys[i] if i < len(bid_qtys) and bid_qtys[i] is not None else 0
        orders = bid_orders[i] if i < len(bid_orders) and bid_orders[i] is not None else 0
        
        # Format with color
        price_str = f"{Fore.GREEN}{price}{Style.RESET_ALL}"
        qty_str = f"{Fore.GREEN}{qty:,}{Style.RESET_ALL}"
        orders_str = f"{Fore.GREEN}{orders}{Style.RESET_ALL}"
        
        book_data.append([price_str, qty_str, orders_str, "", "", ""])
    
    # Display order book
    print(tabulate(
        book_data,
        headers=["Bid Price", "Quantity", "Orders", "Ask Price", "Quantity", "Orders"],
        tablefmt="pretty"
    ))
    
    # Summary metrics
    print(f"\n{Fore.CYAN}{Style.BRIGHT}ORDER BOOK SUMMARY{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Total Buy Qty: {orderbook['total_buy_qty']:,}{Style.RESET_ALL} | "
          f"{Fore.RED}Total Sell Qty: {orderbook['total_sell_qty']:,}{Style.RESET_ALL}")
    
    # Calculate order book imbalance
    total_bid = orderbook['total_buy_qty']
    total_ask = orderbook['total_sell_qty']
    if (total_bid + total_ask) > 0:
        obi = (total_bid - total_ask) / (total_bid + total_ask)
        obi_color = Fore.GREEN if obi > 0 else Fore.RED
        print(f"Order Book Imbalance: {obi_color}{obi:.4f}{Style.RESET_ALL}")
    
    # Stochastic model insights
    if stochastic_metrics:
        s = stochastic_metrics
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}STOCHASTIC MODEL ANALYSIS{Style.RESET_ALL}")
        
        # Create stochastic metrics table
        stoch_table = [
            ["Metric", "Bid Side", "Ask Side", "Interpretation"],
            ["Drift (v)", f"{s['bid_drift']:.2f}", f"{s['ask_drift']:.2f}", "Rate of change in liquidity"],
            ["Volatility (σ)", f"{s['bid_volatility']:.2f}", f"{s['ask_volatility']:.2f}", "Unpredictability of flow"],
            ["Wiener (dW)", f"{s['bid_wiener']:.2f}", f"{s['ask_wiener']:.2f}", "Random component"],
            ["Flow Imbalance", f"{s['flow_imbalance']:.2f}", "", "Net pressure (bid-ask drift)"],
            ["Price Pressure", f"{s['price_pressure']:.4f}", "", "Directional signal strength"]
        ]
        
        print(tabulate(stoch_table, headers="firstrow", tablefmt="pretty"))
        
        # Market prediction based on stochastic model
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}MODEL INTERPRETATION{Style.RESET_ALL}")
        
        # Interpret flow imbalance
        flow_imbalance = s['flow_imbalance']
        if flow_imbalance > 0:
            direction = f"{Fore.GREEN}BULLISH{Style.RESET_ALL}"
            strength = min(abs(flow_imbalance) / (s['bid_volatility'] + 0.0001) * 20, 100)
        else:
            direction = f"{Fore.RED}BEARISH{Style.RESET_ALL}"
            strength = min(abs(flow_imbalance) / (s['ask_volatility'] + 0.0001) * 20, 100)
        
        print(f"Predicted Direction: {direction} with {strength:.0f}% confidence")
        
        # Liquidity stability assessment
        vol_ratio = (s['bid_volatility'] + s['ask_volatility']) / (abs(s['bid_drift']) + abs(s['ask_drift']) + 0.0001)
        
        if vol_ratio > 5:
            stability = f"{Fore.RED}Very Unstable{Style.RESET_ALL}"
        elif vol_ratio > 2:
            stability = f"{Fore.YELLOW}Unstable{Style.RESET_ALL}"
        elif vol_ratio > 1:
            stability = f"{Fore.YELLOW}Moderately Stable{Style.RESET_ALL}"
        else:
            stability = f"{Fore.GREEN}Stable{Style.RESET_ALL}"
        
        print(f"Liquidity Stability: {stability} (Volatility Ratio: {vol_ratio:.2f})")
        
        # Impact prediction
        impact = (s['bid_volatility'] + s['ask_volatility']) / (total_bid + total_ask + 0.0001) * 10000
        print(f"Estimated Price Impact: {impact:.4f} pts per 10,000 units")
    
    # Data collection status
    print(f"\n{Fore.BLUE}Data being collected to: {csv_filename}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Press Ctrl+C to stop data collection{Style.RESET_ALL}")
    
    # Flush stdout to ensure immediate display
    sys.stdout.flush()

def save_to_csv(orderbook, stochastic_metrics):
    """Save orderbook and stochastic metrics to CSV"""
    try:
        # Create DataFrame row
        row = {
            'timestamp': orderbook['timestamp'],
            'datetime': orderbook['datetime'],
            'total_buy_qty': orderbook['total_buy_qty'],
            'total_sell_qty': orderbook['total_sell_qty']
        }
        
        # Add market data
        for field in ['ltp', 'open', 'high', 'low', 'close', 'volume', 'change_percent']:
            if field in orderbook:
                row[field] = orderbook[field]
        
        # Add top of book data
        if 'top_bid' in orderbook:
            row['top_bid'] = orderbook['top_bid']
            row['top_ask'] = orderbook['top_ask'] 
            row['mid_price'] = orderbook['mid_price']
            row['spread'] = orderbook['spread']
            row['spread_bps'] = orderbook['spread_bps']
        
        # Add stochastic metrics
        if stochastic_metrics:
            row['bid_drift'] = stochastic_metrics['bid_drift']
            row['ask_drift'] = stochastic_metrics['ask_drift'] 
            row['flow_imbalance'] = stochastic_metrics['flow_imbalance']
            row['bid_volatility'] = stochastic_metrics['bid_volatility']
            row['ask_volatility'] = stochastic_metrics['ask_volatility']
            row['price_pressure'] = stochastic_metrics['price_pressure']
        
        # Create DataFrame
        df = pd.DataFrame([row])
        
        # Check if file exists
        file_exists = os.path.isfile(csv_filename)
        
        # Write to CSV
        df.to_csv(csv_filename, mode='a', header=not file_exists, index=False)
        
    except Exception as e:
        logger.error(f"Error saving to CSV: {str(e)}")

def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}Starting Stochastic Order Book Analysis (REST API Mode){Style.RESET_ALL}")
    print(f"{Fore.YELLOW}This version uses REST API polling instead of WebSockets to avoid rate limits{Style.RESET_ALL}")
    
    # Access token for Fyers API
    client_id = "QGP6MO6UJQ-100"
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb1BuSGNmcHlYcHEzMzVXbXNlQkN4WW1FT3RNRHBwNjZPdjVtMjhrLWQxaFE0eHgtQWdOc2JkVnZSZXNEVHNQdlcwMzhtZnVNbWFrTHBnTFRaRkswUTJFYzMyQnB0eVA0a1V4YUhqZF9pdk9PZXdLYz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJkZWNhY2RhZDNmNzdjMGNkYTE0OThlNzY1MzdiMTMyYjcxNGMyZTg0NmQzNDFmMmZiYzkzZmY1YSIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDE4NSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ4OTk3MDAwLCJpYXQiOjE3NDg5MjI4NDQsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0ODkyMjg0NCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.DEUwHCRwK7GO-E869LO1EKSGRxjygcu4tesq5vj0Grw"
    
    # Initialize Fyers API client
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, is_async=False, log_path="")
    
    # Dynamic polling intervals to avoid rate limits
    base_interval = 2.0  # Base interval in seconds
    
    try:
        # Main data collection loop
        consecutive_errors = 0
        first_display = True  # Flag for first display
        
        # Wait for first successful data fetch before setting up the display
        print(f"{Fore.YELLOW}Waiting for initial data...{Style.RESET_ALL}")
        
        while True:
        
            try:
                # Fetch orderbook data
                orderbook = fetch_orderbook(fyers)
                
                if orderbook:
                    # Add to historical data
                    historical_data.append(orderbook)
                    
                    # Calculate stochastic metrics if we have enough data
                    stochastic_metrics = None
                    if len(historical_data) >= 2:
                        stochastic_metrics = calculate_stochastic_metrics(historical_data)
                    
                    # Display orderbook with update-in-place approach
                    display_orderbook(orderbook, stochastic_metrics, first_display)
                    if first_display:
                        first_display = False
                    
                    # Save to CSV
                    if stochastic_metrics:
                        save_to_csv(orderbook, stochastic_metrics)
                    
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Success - keep regular interval
                    base_interval = 2.0
                    
                else:   
                    # Increment error counter
                    consecutive_errors += 1
                    
                    # If we have too many consecutive errors, increase the interval
                    if consecutive_errors >= 5:
                        base_interval = min(base_interval * 2, 30.0)
                    else:
                        base_interval = max(base_interval - 0.5, 1.0)
                # Sleep for the current interval
                time.sleep(base_interval)
            except Exception as e:  
                logger.error(f"Error in main loop: {str(e)}")
                consecutive_errors += 1
                
                # If we have too many consecutive errors, increase the interval
                if consecutive_errors >= 5:
                    base_interval = min(base_interval * 2, 30.0)
                else:
                    base_interval = max(base_interval - 0.5, 1.0)
                
                # Sleep for the current interval
                time.sleep(base_interval)
               
            
           
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()