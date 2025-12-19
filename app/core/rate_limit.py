import redis
from datetime import datetime
from typing import Optional
from ..core.config import settings

class RateLimitManager:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    
    def check_limits(self, user_id: str, dimension: str, limit: int, 
                    window_seconds: int) -> bool:
        """Multi-dimensional rate limit check"""
        key = f"ratelimit:{user_id}:{dimension}"
        current = self.redis_client.get(key)
        
        if current is None:
            pipeline = self.redis_client.pipeline()
            pipeline.setex(key, window_seconds, 1)
            pipeline.execute()
            return True
        
        if int(current) >= limit:
            return False
        
        self.redis_client.incr(key)
        return True
    
    def consume_tokens(self, user_id: str, tokens: int) -> bool:
        """Token bucket for AI cost control"""
        key = f"token_bucket:{user_id}"
        bucket = self.redis_client.get(key)
        
        if bucket is None:
            self.redis_client.setex(key, 3600, settings.max_tokens_per_hour - tokens)
            return True
        
        remaining = int(bucket)
        if remaining < tokens:
            return False
        
        self.redis_client.decrby(key, tokens)
        return True
    
    def reset_quota(self, user_id: str):
        """Reset quota (for admin operations)"""
        pattern = f"ratelimit:{user_id}:*"
        for key in self.redis_client.scan_iter(match=pattern):
            self.redis_client.delete(key)
        self.redis_client.delete(f"token_bucket:{user_id}")

rate_limiter = RateLimitManager()