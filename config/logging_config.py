from __future__ import annotations
import logging
import time
from enum import IntEnum
from colorama import Fore, Back, Style, init
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Any, Callable
from config.memory_monitor import MemoryMonitor


init(autoreset=True)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for log levels"""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }

    def format(self, record: logging.LogRecord) -> str:
        formatted_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{formatted_message}{Style.RESET_ALL}"


class LoggerFactory:
    """Factory class for creating and configuring loggers"""
    @staticmethod
    def create_rotating_handler(filepath: str, formatter: logging.Formatter, 
                              level: int = logging.DEBUG) -> RotatingFileHandler:

        handler = RotatingFileHandler(filepath, maxBytes=10*1024*1024, backupCount=5)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler

    @staticmethod
    def configure_logger(name: str, handlers: List[logging.Handler], 
                        level: int, propagate: bool = True) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = propagate
        return logger


def setup_logging(console_level=logging.DEBUG, 
                  file_level=logging.DEBUG,
                  log_file='app.log', 
                  fsevents_level=logging.INFO):
    """Configure main application logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = ColoredFormatter('%(name)s - %(levelname)s - %(message)s')

    # Configure handlers
    file_handler = LoggerFactory.create_rotating_handler(
        str(log_dir / log_file), file_formatter, file_level
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # Clear existing handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure root logger
    root_logger.setLevel(min(console_level, file_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure module-specific loggers with their levels
    logger_levels = {
        'application': logging.WARNING,
        'application.components': {
            'insurance_lines_tree': logging.WARNING,
        },
        'charting': {
            'chart': logging.WARNING,
            'trace_generator': logging.WARNING,
            'color': logging.WARNING,
            'layout_manager': logging.WARNING,
            'helpers': logging.WARNING,
            'get_y_ranges': logging.WARNING,
        },
        'constants': logging.WARNING,
        'callbacks': logging.WARNING,
        'data_process.insurer_filters': logging.WARNING,
        'data_process.options': logging.WARNING,
        'data_process.table.data': logging.WARNING,
        'callbacks.buttons_callbacks': logging.WARNING,
        'data_process': logging.WARNING,
        'fsevents': fsevents_level,
    }

    # Configure module loggers
    for base_name, config in logger_levels.items():
        if isinstance(config, dict):
            for sub_name, level in config.items():
                logger = logging.getLogger(f"{base_name}.{sub_name}")
                logger.setLevel(level)
        else:
            logger = logging.getLogger(base_name)
            logger.setLevel(config)


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