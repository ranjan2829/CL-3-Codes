from fyers_apiv3 import fyersModel
import redis, duckdb, datetime, json, logging, os
from typing import Dict, Any

logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Logs')
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Data')
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, f'historical_{datetime.datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', 
                    handlers=[logging.StreamHandler(), logging.FileHandler(log_file_path)])
logger = logging.getLogger(__name__)

FYERS_CLIENT_ID = "QGP6MO6UJQ-100"
FYERS_ACCESS_TOKEN = ""
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

VALID_MINUTE_RESOLUTIONS = {1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 120, 180, 240}
VALID_SECOND_RESOLUTIONS = {1, 5, 10, 15, 30}
MIN_DATA_DATE = datetime.datetime(2017, 7, 3)
MAX_MINUTE_DAYS = 100
MAX_DAILY_DAYS = 366
MAX_SECONDS_TRADING_DAYS = 30

def get_db_path(symbol: str) -> str:
    sanitized_symbol = symbol.replace("NSE:", "").replace(":", "_").replace("-", "_")
    return os.path.join(data_dir, f"{sanitized_symbol}.db")

def setup_database(symbol: str):
    db_path = get_db_path(symbol)
    conn = duckdb.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_data(
            symbol VARCHAR, timestamp BIGINT, open DOUBLE, high DOUBLE, 
            low DOUBLE, close DOUBLE, volume BIGINT, oi BIGINT, fetch_time TIMESTAMP
        )
    """)
    conn.close()

def log_to_redis(symbol: str, status: str, message: str, record_count: int = 0):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "symbol": symbol,
        "status": status,
        "message": message,
        "record_count": record_count
    }
    log_key = f"log:{symbol}:{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    redis_client.hset(log_key, mapping=log_entry)
    redis_client.expire(log_key, 604800)

def store_in_redis(symbol: str, data: Dict[str, Any]):
    try:
        key = f"stock:{symbol}:{datetime.datetime.now().strftime('%Y%m%d')}"
        redis_client.set(key, json.dumps(data))
        redis_client.expire(key, 86400)
        return True
    except Exception as e:
        logger.error(f"Redis store failed: {str(e)}")
        return False

def store_in_duckdb(symbol: str, candles: list, oi_enabled: bool = False):
    db_path = get_db_path(symbol)
    conn = duckdb.connect(db_path)
    try:
        records = [
            (symbol, c[0], c[1], c[2], c[3], c[4], c[5], c[6] if oi_enabled and len(c) > 6 else None, datetime.datetime.now())
            for c in candles
        ]
        conn.executemany("INSERT INTO stock_data VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", records)
        return len(records)
    except Exception as e:
        logger.error(f"DuckDB store failed: {str(e)}")
        return 0
    finally:
        conn.close()

def is_derivative_symbol(symbol: str) -> bool:
    return "FUT" in symbol or "OPT" in symbol

def validate_time_range(resolution: str, days: int, start_time: datetime.datetime) -> bool:
    if resolution == "1D" and days > MAX_DAILY_DAYS:
        return False
    if resolution.isdigit() and int(resolution) in VALID_SECOND_RESOLUTIONS and days * (5 / 7) > MAX_SECONDS_TRADING_DAYS:
        return False
    if resolution.isdigit() and int(resolution) in VALID_MINUTE_RESOLUTIONS and days > MAX_MINUTE_DAYS:
        return False
    if start_time < MIN_DATA_DATE:
        return False
    return resolution in ["1D"] or (resolution.isdigit() and int(resolution) in VALID_MINUTE_RESOLUTIONS | VALID_SECOND_RESOLUTIONS)

def fetch_historical_data(symbols=None, resolution="1", days=1, oi_flag=0):
    if symbols is None:
        symbols = ["NSE:NIFTY25MAYFUT"]
    elif isinstance(symbols, str):
        symbols = [symbols]
    
    fyers = fyersModel.FyersModel(client_id=FYERS_CLIENT_ID, is_async=False, 
                                 token=FYERS_ACCESS_TOKEN, log_path=logs_dir)
    end_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
    start_time = end_time - datetime.timedelta(days=days)

    if not validate_time_range(resolution, days, start_time):
        return {symbol: None for symbol in symbols}

    results = {}
    for symbol in symbols:
        effective_oi_flag = oi_flag if is_derivative_symbol(symbol) else 0
        setup_database(symbol)
        data = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "0",
            "range_from": str(int(start_time.timestamp())),
            "range_to": str(int(end_time.timestamp())),
            "cont_flag": "1",
            "oi_flag": str(effective_oi_flag)
        }
        try:
            response = fyers.history(data=data)
            if response.get("s") == "ok":
                candles = response.get("candles", [])
                redis_success = store_in_redis(symbol, response)
                record_count = store_in_duckdb(symbol, candles, oi_enabled=effective_oi_flag)
                status = "SUCCESS" if redis_success and record_count > 0 else "PARTIAL_SUCCESS"
                log_to_redis(symbol, status, f"Data fetched. Records: {record_count}", record_count)
                results[symbol] = response
            else:
                log_to_redis(symbol, "ERROR", f"API error: {response.get('message', 'Unknown error')}")
                results[symbol] = None
        except Exception as e:
            log_to_redis(symbol, "ERROR", f"Fetch failed: {str(e)}")
            results[symbol] = None
    return results

def main():
    symbols = ["NSE:SBIN-EQ", "NSE:RELIANCE-EQ", "NSE:NIFTY25MAYFUT"]
    responses = fetch_historical_data(symbols, resolution="1", days=10, oi_flag=1)
    for symbol, response in responses.items():
        print(f"{symbol}: {len(response.get('candles', [])) if response else 'Failed'}")

if __name__ == "__main__":
    main()