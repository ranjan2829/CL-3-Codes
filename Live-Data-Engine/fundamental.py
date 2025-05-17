import requests
import time
import random
import logging
import os
from datetime import datetime

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directory for HTML files
html_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Data/html')
os.makedirs(html_dir, exist_ok=True)

def get_fundamental_data(symbol, retries=3, base_delay=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    symbol_clean = symbol.replace('.NS', '')
    url = f"https://www.screener.in/company/{symbol_clean}/"
    
    for attempt in range(retries):
        try:
            delay = base_delay * (1.5 ** attempt) + random.uniform(1, 3)
            logger.info(f"Fetching {symbol} from {url}, attempt {attempt+1}/{retries}")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                raw_html = response.text
                
                # Save the raw HTML to a file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{symbol_clean}_{timestamp}.html"
                file_path = os.path.join(html_dir, filename)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(raw_html)
                
                logger.info(f"Saved HTML response to {file_path}")
                print(f"--- Raw HTML for {symbol} (first 500 chars) ---")
                print(raw_html[:500])  # print first 500 chars for quick check
                return raw_html
            
            elif response.status_code == 429:
                logger.warning(f"Rate limited (429) for {symbol}, attempt {attempt+1}/{retries}, waiting {delay:.2f} seconds")
                time.sleep(delay)
            else:
                logger.error(f"HTTP error {response.status_code} for {symbol}")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Error fetching {symbol}, attempt {attempt+1}/{retries}: {str(e)}")
            time.sleep(delay)
    
    logger.error(f"Failed to fetch data for {symbol} after {retries} attempts")
    return None

def main():
    print("Script started")
    tickers = ["TCS"]
    all_data = {}
    
    for i, ticker in enumerate(tickers):
        if i > 0:
            wait_time = random.uniform(5, 8)
            print(f"Waiting {wait_time:.2f} seconds before next request")
            time.sleep(wait_time)
        
        data = get_fundamental_data(ticker)
        all_data[ticker] = data
        
        print(f"\n{ticker} Fundamental Data (raw HTML saved to file):")
        if data is not None:
            print(f"First 500 chars: {data[:500]}")
        else:
            print("No data received")
    
    print("Script ended")
    return all_data

if __name__ == "__main__":
    main()