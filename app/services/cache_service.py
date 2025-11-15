import redis.asyncio as redis
import json
import hashlib
from typing import Optional
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class CacheService:
    def __init__(self):
        self._redis = None
    
    async def _get_redis(self):
        """Lazy initialization of Redis connection"""
        if self._redis is None:
            try:
                self._redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    decode_responses=True
                )
                await self._redis.ping()
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis
    
    def _make_key(self, question: str) -> str:
        """Create normalized cache key from question"""
        normalized = ' '.join(question.lower().strip().split())
        hash_key = hashlib.md5(normalized.encode()).hexdigest()
        return f"faq:{hash_key}"
    
    async def get(self, question: str) -> Optional[dict]:
        """Get cached answer for question"""
        key = self._make_key(question)
        try:
            redis_client = await self._get_redis()
            cached = await redis_client.get(key)
            
            if cached:
                logger.info(f"Cache HIT for question: {question[:50]}...")
                return json.loads(cached)
            
            logger.info(f"Cache MISS for question: {question[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, question: str, answer_data: dict):
        """Cache answer for question with TTL"""
        key = self._make_key(question)
        try:
            redis_client = await self._get_redis()
            
            json_data = json.dumps(answer_data, ensure_ascii=False)
            
            await redis_client.setex(
                key,
                settings.redis_ttl,
                json_data
            )
            
            logger.info(f"Cached answer for {settings.redis_ttl}s")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def health_check(self) -> bool:
        """Check if Redis is accessible"""
        try:
            redis_client = await self._get_redis()
            await redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            try:
                await self._redis.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")