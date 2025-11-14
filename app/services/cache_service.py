import redis.asyncio as redis
import json
import hashlib
from typing import Optional
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class CacheService:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
    
    def _make_key(self, question: str) -> str:
        """Создаём ключ из хеша вопроса"""
        return f"faq:{hashlib.md5(question.encode()).hexdigest()}"
    
    async def get(self, question: str) -> Optional[dict]:
        """Получаем закешированный ответ"""
        key = self._make_key(question)
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"Cache HIT for question")
                return json.loads(cached)
            logger.info(f"Cache MISS for question")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, question: str, answer_data: dict):
        """Сохраняем ответ в кеш"""
        key = self._make_key(question)
        try:
            await self.redis.setex(
                key,
                settings.redis_ttl,
                json.dumps(answer_data, ensure_ascii=False)
            )
            logger.info(f"Cached answer for {settings.redis_ttl}s")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def health_check(self) -> bool:
        """Проверка доступности Redis"""
        try:
            await self.redis.ping()
            return True
        except:
            return False