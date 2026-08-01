import os
from dotenv import load_dotenv
import redis

load_dotenv()
redis_url = os.getenv("REDIS_URL")
if redis_url:
    try:
        r = redis.Redis.from_url(redis_url)
        r.flushdb()
        print("Successfully flushed Redis DB for testing.")
    except Exception as e:
        print(f"Error flushing redis: {e}")
else:
    print("No REDIS_URL found.")
