import redis
import os

redis_url_0 = os.getenv('REDIS_URL_0', 'redis://localhost:6379/0')
redis_url_1 = os.getenv('REDIS_URL_1', 'redis://localhost:6379/1')

r0 = redis.Redis.from_url(redis_url_0, decode_responses=True)
r1 = redis.Redis.from_url(redis_url_1, decode_responses=True)
