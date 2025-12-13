from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import Callable

logger = getLogger(__name__)
logger.setLevel("INFO")


def with_logging(fn: Callable):
    def wrapper(*args, **kwargs):
        module = Path(fn.__code__.co_filename).stem
        logger.info(f"{module}.{fn.__name__}")
        result = fn(*args, **kwargs)
        logger.info(" ✅")
        return result

    return wrapper
