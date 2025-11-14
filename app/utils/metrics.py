import time
from functools import wraps
from typing import Callable
from app.utils.logger import logger


def track_time(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.2f}s")
        return result, elapsed
    return wrapper