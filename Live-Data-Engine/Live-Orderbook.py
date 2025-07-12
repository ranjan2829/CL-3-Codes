from fyers_apiv3 import fyersModel
import time, os, numpy as np, signal, sys
from datetime import datetime
from collections import deque
from tabulate import tabulate
from colorama import Fore, Style, init
import shutil
init()

SYMBOL = "NSE:NIFTY25JULFUT"
historical_data = deque(maxlen=100)
price_history = deque(maxlen=60)

def signal_handler(sig, frame):
    print(f"\n{Fore.YELLOW}Stopped{Style.RESET_ALL}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def fetch_orderbook(fyers):
    try:
        response = fyers.depth({"symbol": SYMBOL, "ohlcv_flag": "1"})
        if response and response.get('s') == 'ok' and SYMBOL in response['d']:
            data = response['d'][SYMBOL]
            bids = data.get('bids', [])
            asks = data.get('ask', [])
            
            orderbook = {
                'timestamp': int(time.time()),
                'datetime': datetime.now().strftime('%H:%M:%S'),
                'ltp': data.get('ltp', 0),
                'total_buy_qty': data.get('totalbuyqty', 0),
                'total_sell_qty': data.get('totalsellqty', 0),
                'bid_prices': [b.get('price') for b in bids],
                'ask_prices': [a.get('price') for a in asks],
                'bid_quantities': [b.get('volume') for b in bids],
                'ask_quantities': [a.get('volume') for a in asks],
                'bid_orders': [b.get('ord', 0) for b in bids],
                'ask_orders': [a.get('ord', 0) for a in asks],
                'open': data.get('o', 0),
                'high': data.get('h', 0), 
                'low': data.get('l', 0),
                'close': data.get('c', 0),
                'volume': data.get('v', 0),
                'change_percent': data.get('chp', 0)
            }
            
            if orderbook['bid_prices'] and orderbook['ask_prices']:
                orderbook['top_bid'] = orderbook['bid_prices'][0]
                orderbook['top_ask'] = orderbook['ask_prices'][0]
                orderbook['spread'] = orderbook['top_ask'] - orderbook['top_bid']
                orderbook['mid_price'] = (orderbook['top_bid'] + orderbook['top_ask']) / 2
                orderbook['spread_bps'] = (orderbook['spread'] / orderbook['mid_price']) * 10000
            
            return orderbook
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_metrics(history):
    if len(history) < 2:
        return {}
    
    current, previous = history[-1], history[-2]
    dt = max(current['timestamp'] - previous['timestamp'], 0.001)
    
    bid_drift = (current['total_buy_qty'] - previous['total_buy_qty']) / dt
    ask_drift = (current['total_sell_qty'] - previous['total_sell_qty']) / dt
    
    bid_volatility = ask_volatility = 0
    if len(history) >= 5:
        bid_changes = [history[i]['total_buy_qty'] - history[i-1]['total_buy_qty'] for i in range(-4, 0)]
        ask_changes = [history[i]['total_sell_qty'] - history[i-1]['total_sell_qty'] for i in range(-4, 0)]
        bid_volatility = np.std(bid_changes)
        ask_volatility = np.std(ask_changes)
    
    flow_imbalance = bid_drift - ask_drift
    price_pressure = flow_imbalance / (bid_volatility + ask_volatility + 0.0001)
    
    return {
        'bid_drift': bid_drift, 
        'ask_drift': ask_drift, 
        'flow_imbalance': flow_imbalance,
        'bid_volatility': bid_volatility, 
        'ask_volatility': ask_volatility, 
        'price_pressure': price_pressure,
        'bid_wiener': (current['total_buy_qty'] - previous['total_buy_qty']) - (bid_drift * dt),
        'ask_wiener': (current['total_sell_qty'] - previous['total_sell_qty']) - (ask_drift * dt)
    }

def generate_sparkline(data, width=30, min_val=None, max_val=None):
    """Generate a sparkline chart from data"""
    if not data or len(data) < 2:
        return "Collecting data..."
    if min_val is None:
        min_val = min(data)
    if max_val is None:
        max_val = max(data)
    if min_val == max_val:
        return '─' * width
    blocks = ' ▁▂▃▄▅▆▇█'
    scaled_data = []
    for point in data:
        if max_val == min_val:
            scaled_point = 4
        else:
            scaled_point = int(((point - min_val) / (max_val - min_val)) * 8)
        scaled_data.append(scaled_point)
    if len(scaled_data) > width:
        indices = np.linspace(0, len(scaled_data)-1, width).astype(int)
        scaled_data = [scaled_data[i] for i in indices]
    while len(scaled_data) < width:
        scaled_data.append(scaled_data[-1] if scaled_data else 4)
    return ''.join(blocks[point] for point in scaled_data)

def create_price_chart(prices, width=40, height=10):
    """Create a more detailed ASCII chart for price data"""
    if len(prices) < 2:
        return ["Collecting price data..."]
    
    # Calculate min and max for scaling
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    if price_range < 0.1:  # Minimum range of 0.1 points
        avg_price = (max_price + min_price) / 2
        min_price = avg_price - 0.05
        max_price = avg_price + 0.05
    chart = []
    for i in range(height, 0, -1):
        # Calculate price level for this row
        price_level = min_price + (max_price - min_price) * (i - 1) / (height - 1)
        
        # Add price label
        row = f"{price_level:.1f} "
        for j, price in enumerate(prices):
            if j >= width:
                break
            normalized_price = (price - min_price) / (max_price - min_price) * (height - 1)
            row_price_level = (i - 1)
            
            if abs(normalized_price - row_price_level) < 0.5:
                row += "o"
            elif j > 0 and j < len(prices) - 1:
                prev_price = prices[j-1]
                normalized_prev = (prev_price - min_price) / (max_price - min_price) * (height - 1)
                
                if ((normalized_prev <= row_price_level and normalized_price >= row_price_level) or
                    (normalized_prev >= row_price_level and normalized_price <= row_price_level)):
                    row += "|"
                else:
                    row += " "
            else:
                row += " "
        
        chart.append(row)
    time_axis = "     " + "".join(["-" for _ in range(min(width, len(prices)))])
    chart.append(time_axis)
    current_price = prices[-1] if prices else 0
    chart.append(f"Current: {current_price:.2f} | Time span: {len(prices)} seconds")
    
    return chart

def display_pretty(orderbook, metrics=None, first_display=True):
    if not orderbook:
        return
    
    # Get terminal size
    terminal_width, terminal_height = shutil.get_terminal_size()
    
    # Add price to history
    if 'ltp' in orderbook:
        price_history.append(orderbook['ltp'])
    
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Header with market data
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * min(70, terminal_width)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT} NIFTY ORDER BOOK ANALYSIS: {SYMBOL} {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT} {orderbook['datetime']} {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * min(70, terminal_width)}{Style.RESET_ALL}")
    
    # Market data
    price_color = Fore.GREEN if orderbook.get('change_percent', 0) >= 0 else Fore.RED
    print(f"LTP: {price_color}{orderbook.get('ltp', 0)} ({orderbook.get('change_percent', 0):+.2f}%){Style.RESET_ALL}")
    print(f"OHLC: {orderbook.get('open', 0)} / {orderbook.get('high', 0)} / {orderbook.get('low', 0)} / {orderbook.get('close', 0)}")
    
    # Price chart
    print(f"\n{Fore.CYAN}{Style.BRIGHT}PRICE CHART (Last 60 seconds){Style.RESET_ALL}")
    chart_width = min(60, terminal_width - 10)  # Leave space for labels
    
    if len(price_history) >= 2:
        chart_height = min(8, terminal_height // 4)  # Use about 1/4 of terminal height
        
        # Generate sparkline for quick view
        sparkline = generate_sparkline(price_history, width=chart_width)
        print(f"{Fore.YELLOW}{sparkline}{Style.RESET_ALL}")
        
        # Generate detailed chart
        price_chart = create_price_chart(price_history, width=chart_width, height=chart_height)
        for line in price_chart:
            print(line)
    else:
        print("Collecting price data for chart...")
    
    # Order book table
    print(f"\n{Fore.CYAN}{Style.BRIGHT}ORDER BOOK{Style.RESET_ALL}")
    bid_prices = orderbook.get('bid_prices', [])[:5]  # Top 5 levels
    ask_prices = orderbook.get('ask_prices', [])[:5]  # Top 5 levels
    bid_qtys = orderbook.get('bid_quantities', [])[:5]
    ask_qtys = orderbook.get('ask_quantities', [])[:5]
    bid_orders = orderbook.get('bid_orders', [])[:5]
    ask_orders = orderbook.get('ask_orders', [])[:5]
    
    # Create order book table
    book_data = []
    
    # Add asks (in reverse order to show highest ask at the top)
    for i in range(min(5, len(ask_prices))-1, -1, -1):
        book_data.append([
            "", "", "", 
            f"{Fore.RED}{ask_prices[i]}{Style.RESET_ALL}", 
            f"{Fore.RED}{ask_qtys[i]:,}{Style.RESET_ALL}", 
            f"{Fore.RED}{ask_orders[i]}{Style.RESET_ALL}"
        ])
    
    # Add spread row
    if 'spread' in orderbook:
        book_data.append([
            "", "", "", 
            f"{Fore.YELLOW}{Style.BRIGHT}SPREAD: {orderbook['spread']:.2f} ({orderbook.get('spread_bps', 0):.1f} bps){Style.RESET_ALL}", 
            "", ""
        ])
    
    # Add bids
    for i in range(min(5, len(bid_prices))):
        book_data.append([
            f"{Fore.GREEN}{bid_prices[i]}{Style.RESET_ALL}", 
            f"{Fore.GREEN}{bid_qtys[i]:,}{Style.RESET_ALL}", 
            f"{Fore.GREEN}{bid_orders[i]}{Style.RESET_ALL}",
            "", "", ""
        ])
    
    # Display order book
    print(tabulate(
        book_data,
        headers=["Bid Price", "Quantity", "Orders", "Ask Price", "Quantity", "Orders"],
        tablefmt="simple"  # Use simple format to save space
    ))
    
    # Summary metrics
    print(f"\n{Fore.CYAN}{Style.BRIGHT}ORDER BOOK SUMMARY{Style.RESET_ALL}")
    total_bid = orderbook['total_buy_qty']
    total_ask = orderbook['total_sell_qty']
    
    # Compact summary on one line
    print(f"{Fore.GREEN}Buy: {total_bid:,}{Style.RESET_ALL} | "
          f"{Fore.RED}Sell: {total_ask:,}{Style.RESET_ALL}", end="")
    
    if (total_bid + total_ask) > 0:
        obi = (total_bid - total_ask) / (total_bid + total_ask)
        obi_color = Fore.GREEN if obi > 0 else Fore.RED
        print(f" | OBI: {obi_color}{obi:.4f}{Style.RESET_ALL}")
    else:
        print()
    
    # Display stochastic metrics
    if metrics:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}FLOW ANALYSIS{Style.RESET_ALL}")
        
        # Compact flow metrics table
        flow_table = [
            ["Metric", "Bid", "Ask", "Interpretation"],
            ["Drift", f"{metrics['bid_drift']:.0f}", f"{metrics['ask_drift']:.0f}", "Rate of change"],
            ["Volatility", f"{metrics['bid_volatility']:.0f}", f"{metrics['ask_volatility']:.0f}", "Unpredictability"],
            ["Flow Imbalance", f"{metrics['flow_imbalance']:.0f}", "", "Pressure (bid-ask)"]
        ]
        
        print(tabulate(flow_table, headers="firstrow", tablefmt="simple"))
        
        # Market prediction
        flow_imbalance = metrics['flow_imbalance']
        direction = f"{Fore.GREEN}BULLISH{Style.RESET_ALL}" if flow_imbalance > 0 else f"{Fore.RED}BEARISH{Style.RESET_ALL}"
        strength = min(abs(flow_imbalance) / (metrics['bid_volatility'] + metrics['ask_volatility'] + 0.0001) * 100, 100)
        
        print(f"\n{Fore.YELLOW}Signal: {direction} ({strength:.0f}% strength) | Press Ctrl+C to exit{Style.RESET_ALL}")
    
    # Flush output buffer to ensure display updates
    sys.stdout.flush()

def main():
    print(f"{Fore.GREEN}Starting Fyers Orderbook Analyzer with Live Charts{Style.RESET_ALL}")
    
    # Access token for Fyers API
    client_id = "QGP6MO6UJQ-100"
    access_token = ""
    # Initialize Fyers API client
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, is_async=False, log_path="")
    
    first_display = True
    
    while True:
        try:
            # Fetch orderbook data
            orderbook = fetch_orderbook(fyers)
            
            if orderbook:
                # Add to historical data for analysis
                historical_data.append(orderbook)
                
                # Calculate stochastic metrics if we have enough data
                metrics = None
                if len(historical_data) >= 2:
                    metrics = calculate_metrics(historical_data)
                
                # Display pretty orderbook with chart
                display_pretty(orderbook, metrics, first_display)
                
                # After first display, switch to update mode
                if first_display:
                    first_display = False
            else:
                print(f"{Fore.YELLOW}No data received. Retrying...{Style.RESET_ALL}")
            
            # Faster refresh for more responsive charts
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            signal_handler(None, None)
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            time.sleep(2)

if __name__ == "__main__":
    main()