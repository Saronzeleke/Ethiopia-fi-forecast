import logging
from typing import Any, Optional
import traceback

def setup_logging(level: str = 'INFO') -> logging.Logger:
    """Configure logging for the project"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ethiopia_fi_forecast.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def safe_execute(func, *args, **kwargs) -> Optional[Any]:
    """Safely execute a function with comprehensive error handling"""
    logger = logging.getLogger(__name__)
    try:
        return func(*args, **kwargs)
    except ValueError as e:
        logger.error(f"Value error in {func.__name__}: {e}")
        raise
    except KeyError as e:
        logger.error(f"Key error in {func.__name__}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in {func.__name__}: {e}")
        logger.error(traceback.format_exc())
        raise