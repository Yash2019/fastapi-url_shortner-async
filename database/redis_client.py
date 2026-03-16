import redis.asyncio as aioredis
from configure import config


redis = aioredis.from_url(
    config.REDIS_URL,
    
#Redis returns raw bytes like b"hello". With it, 
# you get clean str like "hello". Always set this.
    decode_responses = True 
)