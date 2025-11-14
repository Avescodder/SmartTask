import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logger():
    logger = logging.getLogger("smarttask")
    logger.setLevel(getattr(logging, settings.log_level))
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    logger.addHandler(handler)
    return logger


logger = setup_logger()