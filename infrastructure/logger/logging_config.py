from __future__ import annotations
import logging
import os
import time
import inspect
from dataclasses import dataclass
from functools import wraps
from logging.handlers import RotatingFileHandler, MemoryHandler
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, cast, Protocol, List
import psutil
from colorama import Fore, Style, init
import functools

init(autoreset=True)
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)

# Core configuration
MONITORING_ENABLED = True
_timer_states: Dict[str, bool] = {}

# Logger cache to prevent duplicate logger instances
_LOGGERS: Dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    Always returns the same logger instance for a given name.
    """
    global _LOGGERS
    if name not in _LOGGERS:
        logger = logging.getLogger(name)
        # Store in cache
        _LOGGERS[name] = logger
    return _LOGGERS[name]


class AccessibleMemoryHandler(MemoryHandler):
    """Extended MemoryHandler that provides access to its buffer"""

    def __init__(self, max_entries: int = 1000):
        # Initialize without a target handler (we'll use this as a permanent store)
        super().__init__(capacity=max_entries, target=None)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.setLevel(logging.DEBUG)

    @property
    def log_entries(self) -> List[str]:
        """Get formatted log entries from the buffer"""
        if not self.formatter:
            return [str(record.msg) for record in self.buffer]
        return [self.formatter.format(record) for record in self.buffer]


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED,
        'CALLBACK': Fore.CYAN  # Add support for CALLBACK level
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        return f"{color}{super().format(record)}{Style.RESET_ALL}"

class CallbackFormatter(logging.Formatter):

    """Special formatter that omits the logger name for callback logs"""
    def format(self, record):
        # Check if this is a callback log
        is_callback = getattr(record, 'is_callback', False) or record.levelname == 'CALLBACK'

        # For callback logs, use a format without the logger name
        if is_callback:
            old_format = self._style._fmt
            self._style._fmt = '%(message)s'  # Format without module name
            result = super().format(record)
            self._style._fmt = old_format  # Restore original format
            return result

        # For non-callback logs, use normal formatting
        return super().format(record)
class ColoredCallbackFormatter(ColoredFormatter):
    """Special formatter that omits the logger name for callback logs while preserving colors"""
    def format(self, record):
        # Check if this is a callback log
        is_callback = getattr(record, 'is_callback', False) or record.levelname == 'CALLBACK'

        # For callback logs, use a format without the logger name but keep colors
        if is_callback:
            old_format = self._style._fmt
            self._style._fmt = '%(message)s'  # Format without module name
            color = self.COLORS.get(record.levelname, '')
            result = f"{color}{super(ColoredFormatter, self).format(record)}{Style.RESET_ALL}"
            self._style._fmt = old_format  # Restore original format
            return result

        # For non-callback logs, use normal colored formatting
        return super().format(record)



class ModuleLogger:
    def _get_caller_module(self) -> str:
        frame = inspect.currentframe()
        if not frame:
            return "unknown"

        logger_module = inspect.getmodule(frame)
        logger_name = logger_module.__name__ if logger_module else "unknown"

        while frame := frame.f_back:
            if module := inspect.getmodule(frame):
                if module.__name__ != logger_name:
                    return module.__name__
        return "unknown"

    def __getattr__(self, name: str) -> Callable:
        if name in ('debug', 'info', 'warning', 'error', 'critical', 'exception'):
            def log_method(msg: str, *args, **kwargs) -> None:
                # Use get_logger instead of logging.getLogger
                logger = get_logger(self._get_caller_module())
                getattr(logger, name)(msg, *args, **kwargs)
            return log_method
        elif name == 'log':
            def log_method(level: int, msg: str, *args, **kwargs) -> None:
                # Use get_logger instead of logging.getLogger
                logger = get_logger(self._get_caller_module())
                logger.log(level, msg, *args, **kwargs)
            return log_method
        raise AttributeError(f"'ModuleLogger' object has no attribute '{name}'")


# Use get_logger to create module logger
logger = ModuleLogger()


def setup_logging(
    console_level: int = logging.DEBUG,
    file_level: int = logging.DEBUG,
    log_file: str = 'app.log',
    fsevents_level: int = logging.INFO
) -> AccessibleMemoryHandler:
    """
    Set up logging for the entire application.
    This should be called once at the start of the application.
    """
    # Clear ALL existing handlers from ALL loggers to prevent duplication
    for logger_name in list(logging.root.manager.loggerDict.keys()):
        for handler in logging.getLogger(logger_name).handlers[:]:
            logging.getLogger(logger_name).removeHandler(handler)

    # Clear root logger handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Ensure logs directory exists - use script directory as base
    script_dir = Path(__file__).parent.absolute()
    log_dir = script_dir / 'logs'
    log_dir.mkdir(exist_ok=True, parents=True)

    # Use the custom CallbackFormatter for console logs
    handlers = [
        (RotatingFileHandler(str(log_dir / log_file), maxBytes=10*1024*1024, backupCount=5),
         CallbackFormatter('%(name)s - %(message)s'),  # Use special formatter
         file_level),
        (logging.StreamHandler(),
         ColoredCallbackFormatter('%(name)s - %(message)s'),  # Use colored version
         console_level),
        (AccessibleMemoryHandler(max_entries=1000),
         CallbackFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
         logging.DEBUG)
    ]

    root.setLevel(logging.DEBUG)

    for handler, formatter, level in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(level)
        root.addHandler(handler)

    # Configure module levels
    module_levels = {
        'domain': logging.INFO,
        'application': logging.INFO,
        'callbacks': logging.INFO,
        'presentation': logging.WARNING
    }

    for name, level in module_levels.items():
        # Use get_logger to ensure consistent logger instances
        get_logger(name).setLevel(level)
        # Set propagate to True to use root handlers
        get_logger(name).propagate = True

    return handlers[2][0]



class TimerWrapper(Protocol[T_co]):
    def __call__(self, *args: Any, **kwargs: Any) -> T_co: ...
    def enable(self, enabled: bool = True) -> None: ...


@dataclass
class MemoryStats:
    rss: float  # Resident Set Size - actual physical memory used
    vms: float  # Virtual Memory Size - total virtual memory allocated
    percent: float
    system_used: float

    @classmethod
    def capture(cls) -> 'MemoryStats':
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        return cls(
            rss=mem.rss / (1024 * 1024),  # MB
            vms=mem.vms / (1024 * 1024),  # MB
            percent=process.memory_percent(),
            system_used=psutil.virtual_memory().percent
        )


def timer(func: Optional[Callable] = None, *, monitor_memory: bool = True, enabled: bool = True):
    def decorator(func: Callable[..., T]) -> TimerWrapper[T_co]:
        timer_key = f"timer_{func.__name__}"
        _timer_states[timer_key] = enabled

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not _timer_states[timer_key] or not MONITORING_ENABLED:
                return func(*args, **kwargs)

            start_time = time.time()
            start_mem = MemoryStats.capture() if monitor_memory else None
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            if monitor_memory and start_mem:
                end_mem = MemoryStats.capture()
                delta_rss = end_mem.rss - start_mem.rss
                print(
                    f"{Fore.LIGHTBLACK_EX}{func.__name__}: "
                    f"RSS={end_mem.rss:.1f}MB (Δ{delta_rss:+.1f}MB) | "
                    f"Process: {end_mem.percent:.1f}% | "
                    f"System: {end_mem.system_used:.1f}% | "
                    f"Time: {duration*1000:.2f}ms{Style.RESET_ALL}"
                )
                if delta_rss > start_mem.rss * 0.5:
                    print(f"{Fore.YELLOW}High memory increase in {func.__name__}: "
                          f"RSS: +{(delta_rss/start_mem.rss)*100:.0f}% | "
                          f"VMS: {end_mem.vms:.1f}MB{Style.RESET_ALL}")
            else:
                print(f"{Fore.LIGHTBLACK_EX}{func.__name__}: Time: {duration*1000:.2f}ms{Style.RESET_ALL}")

            return result

        wrapper.enable = lambda enabled=True: _timer_states.update({timer_key: enabled})
        return cast(TimerWrapper[T_co], wrapper)

    return decorator(func) if func else decorator



def pipe_timer(name=None):
    """Custom timer decorator that preserves the specified name or uses original function name"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided name or get function name
            display_name = name or getattr(func, '__name__', 'unnamed_step')

            # Capture start metrics
            start_time = time.time()
            start_mem = MemoryStats.capture()

            # Execute the function
            result = func(*args, **kwargs)

            # Calculate metrics
            duration = time.time() - start_time
            end_mem = MemoryStats.capture()
            delta_rss = end_mem.rss - start_mem.rss

            # Print performance info with the actual name
            print(
                f"{Fore.LIGHTBLACK_EX}{display_name}: "
                f"RSS={end_mem.rss:.1f}MB (Δ{delta_rss:+.1f}MB) | "
                f"Process: {end_mem.percent:.1f}% | "
                f"System: {end_mem.system_used:.1f}% | "
                f"Time: {duration*1000:.2f}ms{Style.RESET_ALL}"
            )

            return result
        return wrapper
    return decorator

def pipe_with_logging(df, func, *args, **kwargs):
    step_name = getattr(func, '__name__', 'unnamed_step')

    # Use the custom pipe_timer with the original function name
    @pipe_timer(name=step_name)
    def timed_func(dataframe):
        return func(dataframe, *args, **kwargs)

    # Execute the timed function
    result = timed_func(df)

    return result