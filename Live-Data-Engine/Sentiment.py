import newsapi
import tweepy
import redis
import duckdb
import datetime
import json
import logging
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Logs')
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../Data')
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, f'sentiment_{datetime.datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', 
                    handlers=[logging.StreamHandler(), logging.FileHandler(log_file_path)])
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

NEWS_API_KEY = "your_news_api_key"
TWITTER_API_KEY = "your_twitter_api_key"
TWITTER_API_SECRET = "your_twitter_api_secret"
TWITTER_ACCESS_TOKEN = "your_twitter_access_token"
TWITTER_ACCESS_SECRET = "your_twitter_access_secret"

def get_db_path(symbol: str) -> str:
    sanitized_symbol = symbol.replace("NSE:", "").replace(":", "_").replace("-", "_")
    return os.path.join(data_dir, f"{sanitized_symbol}.db")

def setup_database(symbol: str):
    db_path = get_db_path(symbol)
    conn = duckdb.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_data(
            symbol VARCHAR, fetch_time TIMESTAMP, source VARCHAR, sentiment_score DOUBLE, text VARCHAR
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

def store_in_redis(symbol: str, data: dict, data_type: str):
    try:
        key = f"{data_type}:{symbol}:{datetime.datetime.now().strftime('%Y%m%d')}"
        redis_client.set(key, json.dumps(data))
        redis_client.expire(key, 86400)
        return True
    except Exception as e:
        logger.error(f"Redis store failed: {str(e)}")
        return False

def store_sentiment_in_duckdb(symbol: str, source: str, sentiment_score: float, text: str):
    db_path = get_db_path(symbol)
    conn = duckdb.connect(db_path)
    try:
        conn.execute("INSERT INTO sentiment_data VALUES(?, ?, ?, ?, ?)", 
                     (symbol, datetime.datetime.now(), source, sentiment_score, text))
        return 1
    except Exception as e:
        logger.error(f"DuckDB store failed: {str(e)}")
        return 0
    finally:
        conn.close()

def fetch_news_sentiment(symbol: str, analyzer: SentimentIntensityAnalyzer):
    try:
        news_client = newsapi.NewsApiClient(api_key=NEWS_API_KEY)
        articles = news_client.get_everything(q=symbol, language='en', sort_by='relevancy', page_size=10)
        results = []
        for article in articles.get("articles", []):
            text = article.get("title", "") + " " + article.get("description", "")
            sentiment = analyzer.polarity_scores(text)
            score = sentiment["compound"]
            store_sentiment_in_duckdb(symbol, "news", score, text)
            results.append({"text": text, "sentiment_score": score})
        store_in_redis(symbol, results, "news_sentiment")
        log_to_redis(symbol, "SUCCESS", f"Fetched {len(results)} news sentiments", len(results))
        return results
    except Exception as e:
        log_to_redis(symbol, "ERROR", f"News sentiment fetch failed: {str(e)}")
        return []

def fetch_tweet_sentiment(symbol: str, analyzer: SentimentIntensityAnalyzer):
    try:
        auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        api = tweepy.API(auth)
        tweets = tweepy.Cursor(api.search_tweets, q=symbol, lang="en").items(10)
        results = []
        for tweet in tweets:
            text = tweet.text
            sentiment = analyzer.polarity_scores(text)
            score = sentiment["compound"]
            store_sentiment_in_duckdb(symbol, "tweet", score, text)
            results.append({"text": text, "sentiment_score": score})
        store_in_redis(symbol, results, "tweet_sentiment")
        log_to_redis(symbol, "SUCCESS", f"Fetched {len(results)} tweet sentiments", len(results))
        return results
    except Exception as e:
        log_to_redis(symbol, "ERROR", f"Tweet sentiment fetch failed: {str(e)}")
        return []

def sentiment_module(symbols=None):
    if symbols is None:
        symbols = ["SBIN.NS", "RELIANCE.NS"]
    elif isinstance(symbols, str):
        symbols = [symbols]
    
    analyzer = SentimentIntensityAnalyzer()
    results = {}
    for symbol in symbols:
        setup_database(symbol)
        news_sentiment = fetch_news_sentiment(symbol, analyzer)
        tweet_sentiment = fetch_tweet_sentiment(symbol, analyzer)
        results[symbol] = {
            "news_sentiment": news_sentiment,
            "tweet_sentiment": tweet_sentiment
        }
        print(f"\n{symbol} News Sentiment:")
        for item in news_sentiment:
            print(f"Text: {item['text'][:50]}... Sentiment: {item['sentiment_score']}")
        print(f"\n{symbol} Tweet Sentiment:")
        for item in tweet_sentiment:
            print(f"Text: {item['text'][:50]}... Sentiment: {item['sentiment_score']}")
    return results

def main():
    symbols = ["SBIN.NS", "RELIANCE.NS"]
    sentiment_module(symbols)

if __name__ == "__main__":
    main()