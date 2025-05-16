from fyers_apiv3 import fyersModel
import redis, duckdb, datetime, json, logging, os
from typing import Dict, Any
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Logs')
os.makedirs(logs_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, f'historical_{datetime.datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler(log_file_path)])
logger = logging.getLogger(__name__)
FYERS_CLIENT_ID = "QGP6MO6UJQ-100"
FYERS_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb0ozME43Y0JfR1hDTDRTUURLYl94UHlWZW1tSFdXM2EwcHBHQVByd3RYcjBDYS1qdnBwUGhpVDh3WXp4VzJqZ1I0U01mNEVmcjZtZGcwbjJoTUlIVEltWURLaTVXSkdHUER3dGtkSi0wQkZZQU9jYz0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJkZWNhY2RhZDNmNzdjMGNkYTE0OThlNzY1MzdiMTMyYjcxNGMyZTg0NmQzNDFmMmZiYzkzZmY1YSIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDE4NSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ3NDQxODAwLCJpYXQiOjE3NDc0MTgzODEsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NzQxODM4MSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.EsaqAyJsWDA8axQ9cOLBZ103-dqhTKvs5dIiygj1GAE"
REDIS_HOST, REDIS_PORT, REDIS_DB = "localhost", 6379, 0
DUCKDB_PATH = "../Data/fyers_data.db"
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
duckdb_conn = duckdb.connect(DUCKDB_PATH)

def setup_databases():
    duckdb_conn.execute("CREATE TABLE IF NOT EXISTS stock_data(symbol VARCHAR, timestamp BIGINT, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, volume BIGINT, fetch_time TIMESTAMP)")
    logger.info("DuckDB table setup completed")

def log_to_redis(symbol: str, status: str, message: str, record_count: int = 0):
    try:
        log_entry = {"timestamp": datetime.datetime.now().isoformat(), "symbol": symbol, "status": status, "message": message, "record_count": record_count}
        log_key = f"log:{symbol}:{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        redis_client.hset(log_key, mapping=log_entry)
        redis_client.expire(log_key, 604800)
        logger.info(f"Logged to Redis: {symbol} - {status}")
    except Exception as e:
        logger.error(f"Failed to log to Redis: {str(e)}")

def store_in_redis(symbol: str, data: Dict[str, Any]):
    try:
        key = f"stock:{symbol}:{datetime.datetime.now().strftime('%Y%m%d')}"
        redis_client.set(key, json.dumps(data))
        redis_client.expire(key, 86400)
        logger.info(f"Stored data in Redis for {symbol}")
        return True
    except Exception as e:
        logger.error(f"Failed to store in Redis: {str(e)}")
        return False

def store_in_duckdb(symbol: str, candles: list):
    try:
        records = [(symbol, c[0], c[1], c[2], c[3], c[4], c[5], datetime.datetime.now()) for c in candles]
        duckdb_conn.executemany("INSERT INTO stock_data VALUES(?, ?, ?, ?, ?, ?, ?, ?)", records)
        logger.info(f"Stored {len(records)} records in DuckDB for {symbol}")
        return len(records)
    except Exception as e:
        logger.error(f"Failed to store in DuckDB: {str(e)}")
        return 0

def fetch_historical_data(symbols=None, resolution="1", days=1):
    if symbols is None:
        symbols = ["NSE:NIFTY25MAYFUT"]
    elif isinstance(symbols, str):
        symbols = [symbols]
    fyers = fyersModel.FyersModel(client_id=FYERS_CLIENT_ID, is_async=False, token=FYERS_ACCESS_TOKEN, log_path=logs_dir)
    end_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
    start_time = end_time - datetime.timedelta(days=days)
    results = {}
    for symbol in symbols:
        data = {"symbol": symbol, "resolution": resolution, "date_format": "0", "range_from": str(int(start_time.timestamp())), "range_to": str(int(end_time.timestamp())), "cont_flag": "1"}
        try:
            response = fyers.history(data=data)
            if response.get("s") == "ok":
                candle_count = len(response.get("candles", []))
                logger.info(f"API Response: Successfully fetched {candle_count} candles for {symbol}")
                redis_success = store_in_redis(symbol, response)
                record_count = store_in_duckdb(symbol, response.get("candles", []))
                status = "SUCCESS" if redis_success and record_count > 0 else "PARTIAL_SUCCESS"
                log_to_redis(symbol=symbol, status=status, message=f"Data fetched successfully. Records: {record_count}", record_count=record_count)
                results[symbol] = response
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"API Error: {error_msg}")
                log_to_redis(symbol=symbol, status="ERROR", message=f"API error: {error_msg}")
                results[symbol] = None
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            log_to_redis(symbol=symbol, status="ERROR", message=f"Failed to fetch data: {str(e)}")
            results[symbol] = None
    return results

def main():
    try:
        setup_databases()
        symbols = ["NSE:SBIN-EQ", "NSE:RELIANCE-EQ"]
        responses = fetch_historical_data(symbols)
        for symbol, response in responses.items():
            if response:
                print(f"{symbol}: {len(response.get('candles', []))} candles fetched")
            else:
                print(f"{symbol}: Failed to fetch data")
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        duckdb_conn.close()

if __name__ == "__main__":
    main()