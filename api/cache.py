import redis
from api.config import settings

def get_redis():
    return redis.Redis.from_url(settings.REDIS_URL)