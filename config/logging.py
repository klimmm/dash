from __future__ import annotations

import logging
import os
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, cast

import dash
import psutil
from colorama import Fore, Style, init

init(autoreset=True)
T = TypeVar('T')

# Constants
CALLBACK = 25
logging.addLevelName(CALLBACK, 'CALLBACK')
MONITORING_ENABLED = True
_timer_states: Dict[str, bool] = {}




class DashDebugHandler(logging.Handler):
    def __init__(self, max_entries: int = 1000):
        super().__init__()
        self.log_entries = deque(maxlen=max_entries)
        self.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.formatter.format(record)
            self.log_entries.append(msg)
        except Exception as e:
            print(f"Error in debug handler: {e}")
            self.handleError(record)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        return f"{color}{super().format(record)}{Style.RESET_ALL}"


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the configured handlers and formatters"""
    return logging.getLogger(name)


def setup_logging(console_level: int = logging.DEBUG,
                  file_level: int = logging.DEBUG,
                  log_file: str = 'app.log',
                  fsevents_level: int = logging.INFO
                  ) -> DashDebugHandler:
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create handlers
    handlers = [
        RotatingFileHandler(str(log_dir / log_file),
                            maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler(),
        DashDebugHandler()
    ]

    # Configure formatters for all handlers
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = ColoredFormatter(
        '%(name)s - %(levelname)s - %(message)s')
    debug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set formatters and levels
    handlers[0].setFormatter(file_formatter)
    handlers[0].setLevel(file_level)

    handlers[1].setFormatter(console_formatter)
    handlers[1].setLevel(console_level)

    handlers[2].setFormatter(debug_formatter)  # Add formatter for debug handler
    handlers[2].setLevel(logging.DEBUG)  # Ensure debug handler captures all levels

    # Configure root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)
    for handler in handlers:
        root.addHandler(handler)

    # Configure module loggers
    module_levels = {
        'app': logging.WARNING, 'constants': logging.WARNING,
        'callbacks': logging.WARNING, 'core': logging.DEBUG, 'core.table': logging.DEBUG, 
        'config': logging.DEBUG, 'fsevents': fsevents_level
    }
    for name, level in module_levels.items():
        logging.getLogger(name).setLevel(level)

    return handlers[2]


@dataclass
class MemoryStats:
    rss: float
    vms: float
    percent: float
    system_used: float

    @classmethod
    def capture(cls) -> 'MemoryStats':
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        return cls(
            rss=mem.rss / (1024 * 1024),
            vms=mem.vms / (1024 * 1024),
            percent=process.memory_percent(),
            system_used=psutil.virtual_memory().percent
        )


@contextmanager
def _disable_monitoring() -> Generator[None, None, None]:
    global MONITORING_ENABLED
    previous, MONITORING_ENABLED = MONITORING_ENABLED, False
    try:
        yield
    finally:
        MONITORING_ENABLED = previous


def timer(func: Callable[..., T]) -> Callable[..., T]:
    timer_key = f"timer_{func.__name__}"
    _timer_states[timer_key] = True

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not _timer_states[timer_key]:
            return func(*args, **kwargs)
        start = time.time()
        result = func(*args, **kwargs)
        logger.warning(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")  # Changed to warning
        return result

    wrapper.enable = lambda enabled=True: _timer_states.update({timer_key: enabled})
    return wrapper


def monitor_memory(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not MONITORING_ENABLED:
            return func(*args, **kwargs)

        start_time = time.time()
        start_mem = MemoryStats.capture()
        try:
            return func(*args, **kwargs)
        finally:
            end_mem = MemoryStats.capture()
            duration = time.time() - start_time
            delta_rss = end_mem.rss - start_mem.rss

            logger.warning(
                f"{Fore.LIGHTBLACK_EX}Memory {func.__name__}: "
                f"RSS={end_mem.rss:.1f}MB (Δ{delta_rss:+.1f}MB) | "
                f"Process: {end_mem.percent:.1f}% | "
                f"System: {end_mem.system_used:.1f}% | "
                f"Time: {duration:.3f}s{Style.RESET_ALL}")

            if delta_rss > start_mem.rss * 0.5:
                logger.warning(
                    f"{Fore.YELLOW}High memory increase in {func.__name__} "
                    f"(+{(delta_rss/start_mem.rss)*100:.0f}%){Style.RESET_ALL}")
    return wrapper


@dataclass
class CallbackExecution:
    name: str
    execution_time: float
    timestamp: datetime


class CallbackTracker:
    def __init__(self) -> None:
        self.current_sequence: List[CallbackExecution] = []
        self.last_process_ui_time: Optional[datetime] = None
        self.total_time: float = 0.0

    def _reset_sequence(self) -> None:
        self.current_sequence = []
        self.last_process_ui_time = datetime.now()
        self.total_time = 0.0

    def _add_execution(self, name: str, execution_time: float) -> None:
        self.current_sequence.append(
            CallbackExecution(name, execution_time, datetime.now()))
        self.total_time += execution_time

        if name == 'generate_data_tables':
            callbacks_str = ', '.join(
                f"{c.name}:{c.execution_time:.2f}ms" for c in self.current_sequence)
            logger.log(
                CALLBACK,
                f"{Fore.LIGHTBLACK_EX}Sequence Summary | "
                f"{Fore.BLUE}Total Time: {self.total_time:.2f}ms "
                f"{Fore.LIGHTBLACK_EX}| Callbacks: {len(self.current_sequence)} | "
                f"Sequence: [{callbacks_str}]{Style.RESET_ALL}",
                extra={'is_callback': True})
            self._reset_sequence()


def log_callback(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        ctx = dash.callback_context
        trigger_info = (ctx.triggered and ctx.triggered[0]['prop_id'] != '.'
                        and
                        ctx.triggered[0] or
                        {'prop_id': next(iter(ctx.inputs)), 'value':
                         next(iter(ctx.inputs.values()))}
                        if ctx.inputs else {'prop_id': 'initial_load',
                                            'value': None})

        start = time.time()
        orig_level = logger.level
        logger.setLevel(CALLBACK)

        try:
            result = func(*args, **kwargs)
            time_ms = (time.time() - start) * 1000

            logger.log(
                CALLBACK,
                f"{Fore.LIGHTBLACK_EX}Callback:{func.__name__} | Completed | "
                f"Time: {time_ms:.2f}ms | {time.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Trigger: {trigger_info['prop_id'].split('.')[0]}{Style.RESET_ALL}",
                extra={'is_callback': True})

            callback_tracker._add_execution(func.__name__, time_ms)

            if time_ms > 1000:
                logger.warning(f"Slow callback: {func.__name__} {time_ms:.2f}ms")
            return result

        except dash.exceptions.PreventUpdate:
            time_ms = (time.time() - start) * 1000
            logger.log(
                CALLBACK,
                f"{Fore.LIGHTBLACK_EX}Callback:{func.__name__} | "
                f"{Fore.LIGHTBLUE_EX}PreventUpdate{Style.RESET_ALL}",
                extra={'is_callback': True})
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}",
                         extra={'is_callback': True})
            raise
        finally:
            logger.setLevel(orig_level)
    return wrapper


def error_handler(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except dash.exceptions.PreventUpdate:
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            # Return a generic error tuple that's properly typed
            return cast(T, ({}, "Error occurred"))
    return wrapper


# Initialize globals
callback_tracker = CallbackTracker()
logger = get_logger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter())
logger.addHandler(handler)
logger.propagate = False