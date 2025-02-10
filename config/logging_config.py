from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps, partial
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Generator, List, TypeVar, Dict

import psutil
from colorama import Fore, Back, Style, init

init(autoreset=True)
T = TypeVar('T')

# Store timer states in a dictionary instead of function attributes
_timer_states: Dict[str, bool] = {}


class ColoredFormatter(logging.Formatter):
    """Colored log formatter"""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }

    def format(self, record: logging.LogRecord) -> str:
        return f"{self.COLORS.get(record.levelname, '')}{super().format(record)}{Style.RESET_ALL}"


def setup_logging(console_level: int = logging.DEBUG,
                  file_level: int = logging.DEBUG,
                  log_file: str = 'app.log',
                  fsevents_level: int = logging.INFO) -> None:
    """Configure application logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create and configure handlers
    file_handler = RotatingFileHandler(
        str(log_dir / log_file),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_handler.setLevel(file_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter(
        '%(name)s - %(levelname)s - %(message)s'))
    console_handler.setLevel(console_level)

    handlers: List[logging.Handler] = [file_handler, console_handler]

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(min(console_level, file_level))
    for handler in handlers:
        root.addHandler(handler)

    # Configure module loggers
    for name, level in {
        'app': logging.WARNING,
        'constants': logging.WARNING,
        'callbacks': logging.WARNING,
        'core': logging.WARNING,
        'fsevents': fsevents_level,
    }.items():
        logging.getLogger(name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def timer(func: Callable[..., T]) -> Callable[..., T]:
    """Time function execution (disabled by default)"""
    timer_key = f"timer_{func.__name__}"
    _timer_states[timer_key] = False

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not _timer_states[timer_key]:
            return func(*args, **kwargs)
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")
        return result

    def enable(enabled: bool = True) -> None:
        _timer_states[timer_key] = enabled

    wrapper.enable = enable  # type: ignore[attr-defined]
    return wrapper


def timerx(func: Callable[..., T]) -> Callable[..., T]:
    """Time function execution (disabled by default)"""
    timer_key = f"timerx_{func.__name__}"
    _timer_states[timer_key] = False

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not _timer_states[timer_key]:
            return func(*args, **kwargs)
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")
        return result

    def enable(enabled: bool = True) -> None:
        _timer_states[timer_key] = enabled

    wrapper.enable = enable  # type: ignore[attr-defined]
    return wrapper


@dataclass
class MemoryStats:
    """Memory statistics container"""
    rss: float
    vms: float
    percent: float
    system_used: float

    @classmethod
    def capture(cls, process: psutil.Process) -> 'MemoryStats':
        mem = process.memory_info()
        return cls(
            rss=mem.rss / (1024 * 1024),
            vms=mem.vms / (1024 * 1024),
            percent=process.memory_percent(),
            system_used=psutil.virtual_memory().percent
        )


class MemoryMonitor:
    """Memory monitoring utility"""

    def __init__(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.start_time = self.last_check = time.time()
        self.check_interval = 60

    def get_stats(self) -> MemoryStats:
        return MemoryStats.capture(self.process)

    def log(self, tag: str, logger: logging.Logger) -> None:
        try:
            stats = self.get_stats()
            logger.info(
                f"Memory at {tag}: RSS={stats.rss:.1f}MB, "
                f"Process=%{stats.percent:.1f}, System=%{stats.system_used:.1f}")
            self.last_check = time.time()
        except Exception as e:
            logger.error(f"Error monitoring memory: {str(e)}")


memory_monitor = MemoryMonitor()
MONITORING_ENABLED = False


@contextmanager
def disable_monitoring() -> Generator[None, None, None]:
    """Temporarily disable memory monitoring"""
    global MONITORING_ENABLED
    previous = MONITORING_ENABLED
    MONITORING_ENABLED = False
    try:
        yield
    finally:
        MONITORING_ENABLED = previous


def monitor_memory(func: Callable[..., T]) -> Callable[..., T]:
    """Monitor memory usage of a function"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not MONITORING_ENABLED:
            return func(*args, **kwargs)

        start_time = time.time()
        start_mem = peak_mem = memory_monitor.get_stats()
        logger = get_logger(__name__)

        try:
            return func(*args, **kwargs)
        finally:
            end_mem = memory_monitor.get_stats()
            duration = time.time() - start_time

            logger.warning(
                f"\nMemory {func.__name__}:"
                f"\n  Current: RSS={end_mem.rss:.1f}MB, VMS={end_mem.vms:.1f}MB"
                f"\n  Peak:    RSS={peak_mem.rss:.1f}MB, VMS={peak_mem.vms:.1f}MB"
                f"\n  Change:  RSS={end_mem.rss - start_mem.rss:+.1f}MB"
                f"\n  Process: {end_mem.percent:.1f}%"
                f"\n  System:  {end_mem.system_used:.1f}%"
                f"\n  Time:    {duration:.3f}s")

            if end_mem.rss > start_mem.rss * 1.5:
                logger.warning(
                    f"High memory increase in {func.__name__}"
                    f" (+{((end_mem.rss/start_mem.rss)-1)*100:.0f}%)")

    return wrapper