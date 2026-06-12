import redis
import os
from dotenv import load_dotenv
load_dotenv()

# Redis is used only for sessions and rate-limit counters. Application data
# (users, cards, progress) lives in Postgres — see database.py.
redis_url_0 = os.getenv('REDIS_URL_0', 'redis://localhost:6379/0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

r0 = redis.Redis.from_url(redis_url_0, decode_responses=True, password=REDIS_PASSWORD)
