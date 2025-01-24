import logging
import os
import time
import psutil
from dataclasses import dataclass
from typing import Callable, Any
from functools import wraps


@dataclass
class MemoryStats:
    """Data class for memory statistics"""
    rss: float
    vms: float
    percent: float
    system_used: float


class MemoryMonitor:
    """Memory monitoring utility class"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = self.last_check = time.time()
        self.check_interval = 60

    def get_memory_usage(self) -> MemoryStats:
        mem = self.process.memory_info()
        return MemoryStats(
            rss=mem.rss / (1024 * 1024),
            vms=mem.vms / (1024 * 1024),
            percent=self.process.memory_percent(),
            system_used=psutil.virtual_memory().percent
        )

    def log_memory(self, tag: str, logger: logging.Logger) -> None:
        try:
            stats = self.get_memory_usage()
            logger.info(
                f"Memory at {tag}: RSS={stats.rss:.1f}MB, "
                f"Process=%{stats.percent:.1f}, System=%{stats.system_used:.1f}"
            )

            self.last_check = time.time()

        except Exception as e:
            logger.error(f"Error monitoring memory: {str(e)}")

memory_monitor = MemoryMonitor()


def monitor_memory(func: Callable) -> Callable:
    """Monitor memory usage of decorated functions"""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        start_mem = memory_monitor.get_memory_usage()
        try:
            return func(*args, **kwargs)
        finally:
            end_mem = memory_monitor.get_memory_usage()
            print(
                f"Memory {func.__name__}: Current={end_mem.rss:.1f}MB, "
                f"Change={end_mem.rss - start_mem.rss:+.1f}MB, "
                f"Time={time.time()-start_time:.3f}s"
            )

    return wrapper