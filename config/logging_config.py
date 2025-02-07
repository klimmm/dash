from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Any, List

import psutil
from colorama import Fore, Back, Style, init

init(autoreset=True)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def timer(func: Callable) -> Callable:
    """Time function execution"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not wrapper.enabled:
            return func(*args, **kwargs)
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")
        return result
    wrapper.enabled = True
    return wrapper
def timerx(func: Callable) -> Callable:
    """Time function execution"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not wrapper.enabled:
            return func(*args, **kwargs)
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")
        return result
    wrapper.enabled = True
    return wrapper
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

@dataclass
class MemoryStats:
    """Memory statistics container"""
    rss: float
    vms: float
    percent: float
    system_used: float

class LoggerFactory:
    """Logger configuration factory"""
    @staticmethod
    def create_handler(filepath: str, formatter: logging.Formatter, 
                      level: int = logging.DEBUG) -> RotatingFileHandler:
        handler = RotatingFileHandler(filepath, maxBytes=10*1024*1024, backupCount=5)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler

    @staticmethod
    def configure(name: str, handlers: List[logging.Handler], 
                 level: int, propagate: bool = True) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = propagate
        return logger

def setup_logging(console_level=logging.DEBUG, file_level=logging.DEBUG,
                 log_file='app.log', fsevents_level=logging.INFO) -> None:
    """Configure application logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    handlers = [
        LoggerFactory.create_handler(
            str(log_dir / log_file),
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_level
        ),
        logging.StreamHandler()
    ]
    handlers[1].setLevel(console_level)
    handlers[1].setFormatter(ColoredFormatter('%(name)s - %(levelname)s - %(message)s'))

    # Configure root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(min(console_level, file_level))
    for handler in handlers:
        root.addHandler(handler)

    # Module-specific logger levels
    logger_config = {
        'application': logging.WARNING,
        'application.components.insurance_lines_tree': logging.WARNING,
        'constants': logging.WARNING,
        'callbacks': logging.DEBUG,
        'domain': logging.WARNING,
        'callbacks.buttons_callbacks': logging.WARNING,
        'fsevents': fsevents_level,
    }

    for name, level in logger_config.items():
        logging.getLogger(name).setLevel(level)

class MemoryMonitor:
    """Memory monitoring utility"""
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = self.last_check = time.time()
        self.check_interval = 60

    def get_stats(self) -> MemoryStats:
        mem = self.process.memory_info()
        return MemoryStats(
            rss=mem.rss / (1024 * 1024),
            vms=mem.vms / (1024 * 1024),
            percent=self.process.memory_percent(),
            system_used=psutil.virtual_memory().percent
        )

    def log(self, tag: str, logger: logging.Logger) -> None:
        try:
            stats = self.get_stats()
            logger.info(
                f"Memory at {tag}: RSS={stats.rss:.1f}MB, "
                f"Process=%{stats.percent:.1f}, System=%{stats.system_used:.1f}"
            )
            self.last_check = time.time()
        except Exception as e:
            logger.error(f"Error monitoring memory: {str(e)}")

memory_monitor = MemoryMonitor()

def monitor_memory(func: Callable) -> Callable:
    """Memory usage monitoring decorator"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        start_mem = memory_monitor.get_stats()
        peak_mem = start_mem
        logger = logging.getLogger(__name__)

        def update_peak():
            nonlocal peak_mem
            current = memory_monitor.get_stats()
            if current.rss > peak_mem.rss:
                peak_mem = current
            return current

        try:
            return func(*args, **kwargs)
        finally:
            end_mem = update_peak()
            duration = time.time() - start_time
            
            logger.warning(
                f"\nMemory {func.__name__}:"
                f"\n  Current: RSS={end_mem.rss:.1f}MB, VMS={end_mem.vms:.1f}MB"
                f"\n  Peak:    RSS={peak_mem.rss:.1f}MB, VMS={peak_mem.vms:.1f}MB"
                f"\n  Change:  RSS={end_mem.rss - start_mem.rss:+.1f}MB"
                f"\n  Process: {end_mem.percent:.1f}%"
                f"\n  System:  {end_mem.system_used:.1f}%"
                f"\n  Time:    {duration:.3f}s"
            )

            if end_mem.rss > start_mem.rss * 1.5:
                logger.warning(
                    f"High memory increase in {func.__name__}"
                    f" (+{((end_mem.rss/start_mem.rss)-1)*100:.0f}%)"
                )
    return wrapper