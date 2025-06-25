from fyers_apiv3 import fyersModel
import time, os, numpy as np, pandas as pd, signal, sys, psycopg2
from datetime import datetime
from collections import deque
from tabulate import tabulate
from colorama import Fore, Style, init
init()

SYMBOL = "NSE:NIFTY25JUNFUT"
historical_data = deque(maxlen=100)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'orderbook_db',
    'user': 'postgres',
    'password': 'password',
    'port': 5432
}

def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orderbook_data (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT,
            ltp REAL, total_buy_qty BIGINT, total_sell_qty BIGINT,
            bid_drift REAL, ask_drift REAL, flow_imbalance REAL,
            bid_volatility REAL, ask_volatility REAL, price_pressure REAL,
            top_bid REAL, top_ask REAL, spread REAL
        );
        SELECT create_hypertable('orderbook_data', 'time', if_not_exists => TRUE);
    """)
    conn.commit()
    return conn

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
                'ask_quantities': [a.get('volume') for a in asks]
            }
            
            if orderbook['bid_prices'] and orderbook['ask_prices']:
                orderbook['top_bid'] = orderbook['bid_prices'][0]
                orderbook['top_ask'] = orderbook['ask_prices'][0]
                orderbook['spread'] = orderbook['top_ask'] - orderbook['top_bid']
            
            return orderbook
        return None
    except:
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
        'bid_drift': bid_drift, 'ask_drift': ask_drift, 'flow_imbalance': flow_imbalance,
        'bid_volatility': bid_volatility, 'ask_volatility': ask_volatility, 'price_pressure': price_pressure
    }

def save_to_db(conn, orderbook, metrics):
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orderbook_data (time, symbol, ltp, total_buy_qty, total_sell_qty,
                                      bid_drift, ask_drift, flow_imbalance, bid_volatility,
                                      ask_volatility, price_pressure, top_bid, top_ask, spread)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            SYMBOL, orderbook['ltp'], orderbook['total_buy_qty'], orderbook['total_sell_qty'],
            metrics.get('bid_drift', 0), metrics.get('ask_drift', 0), metrics.get('flow_imbalance', 0),
            metrics.get('bid_volatility', 0), metrics.get('ask_volatility', 0), metrics.get('price_pressure', 0),
            orderbook.get('top_bid', 0), orderbook.get('top_ask', 0), orderbook.get('spread', 0)
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"DB Error: {e}")

def display_compact(orderbook, metrics):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{Fore.CYAN}NIFTY ORDERBOOK {orderbook['datetime']}{Style.RESET_ALL}")
    print(f"LTP: {Fore.GREEN}{orderbook['ltp']}{Style.RESET_ALL}")
    
    book_data = []
    bids, asks = orderbook['bid_prices'][:3], orderbook['ask_prices'][:3]
    bid_qtys, ask_qtys = orderbook['bid_quantities'][:3], orderbook['ask_quantities'][:3]
    
    for i in range(2, -1, -1):
        if i < len(asks):
            book_data.append(["", "", f"{Fore.RED}{asks[i]}{Style.RESET_ALL}", f"{Fore.RED}{ask_qtys[i]:,}{Style.RESET_ALL}"])
    
    book_data.append(["", "", f"{Fore.YELLOW}SPREAD{Style.RESET_ALL}", ""])
    
    for i in range(3):
        if i < len(bids):
            book_data.append([f"{Fore.GREEN}{bids[i]}{Style.RESET_ALL}", f"{Fore.GREEN}{bid_qtys[i]:,}{Style.RESET_ALL}", "", ""])
    
    print(tabulate(book_data, headers=["Bid", "Qty", "Ask", "Qty"], tablefmt="simple"))
    
    obi = (orderbook['total_buy_qty'] - orderbook['total_sell_qty']) / (orderbook['total_buy_qty'] + orderbook['total_sell_qty'] + 1)
    print(f"Buy: {orderbook['total_buy_qty']:,} | Sell: {orderbook['total_sell_qty']:,} | OBI: {obi:.3f}")
    if metrics:
        direction = f"{Fore.GREEN}↑BULL{Style.RESET_ALL}" if metrics['flow_imbalance'] > 0 else f"{Fore.RED}↓BEAR{Style.RESET_ALL}"
        print(f"Flow: {direction} | Drift: B{metrics['bid_drift']:.0f} A{metrics['ask_drift']:.0f}")
    print(f"{Fore.BLUE}DB: Connected | Ctrl+C to exit{Style.RESET_ALL}")
def check_connection(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return True
    except:
        return False
def main():
    client_id = "QGP6MO6UJQ-100"
    access_token = ""
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, is_async=False, log_path="")
    conn = init_db()
    print(f"{Fore.GREEN}Started TimescaleDB Orderbook{Style.RESET_ALL}")
    while True:
        try:
            if not check_connection(conn):
                conn = init_db()
            
            orderbook = fetch_orderbook(fyers)
            if orderbook:
                historical_data.append(orderbook)
                metrics = calculate_metrics(historical_data)
                
                save_to_db(conn, orderbook, metrics)
                display_compact(orderbook, metrics)
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            signal_handler(None, None)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()