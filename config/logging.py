from __future__ import annotations

import logging
import os
import time
import traceback
from contextlib import contextmanager
from collections import deque

from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, cast

import dash
import psutil
from colorama import Fore, Back, Style, init

init(autoreset=True)
T = TypeVar('T')

# Constants
CALLBACK = 25
logging.addLevelName(CALLBACK, 'CALLBACK')
MONITORING_ENABLED = True
_timer_states: Dict[str, bool] = {}


class DashDebugHandler(logging.Handler):
    """Simple handler that stores log entries for the debug panel"""

    def __init__(self, max_entries: int = 1000):
        super().__init__()
        self.log_entries = deque(maxlen=max_entries)
        # Set lowest possible level to capture everything
        self.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Ensure the record is formatted
            msg = self.formatter.format(record)
            print(f"Debug Panel received log: {msg}")  # Debugging line
            self.log_entries.append(msg)
        except Exception as e:
            print(f"Error in debug handler: {e}")  # Debugging line
            self.handleError(record)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        return f"{color}{super().format(record)}{Style.RESET_ALL}"


def setup_logging(console_level: int = logging.DEBUG,
                  file_level: int = logging.DEBUG,
                  log_file: str = 'app.log',
                  fsevents_level: int = logging.INFO) -> DashDebugHandler:
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create handlers
    file_handler = RotatingFileHandler(
        str(log_dir / log_file),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    console_handler = logging.StreamHandler()
    debug_handler = DashDebugHandler()  # Add simple debug handler

    # Configure handlers
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    file_handler.setLevel(file_level)

    console_handler.setFormatter(ColoredFormatter(
        '%(name)s - %(levelname)s - %(message)s'))
    console_handler.setLevel(console_level)

    # Configure root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)  # Set to DEBUG to ensure all logs are captured
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.addHandler(debug_handler)  # Add debug handler before setting module levels

    # Configure module loggers
    for name, level in {
        'app': logging.WARNING, 'constants': logging.WARNING,
        'callbacks': logging.DEBUG, 'core': logging.DEBUG,
        'fsevents': fsevents_level
    }.items():
        logging.getLogger(name).setLevel(level)

    return debug_handler


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the configured handlers and formatters"""
    return logging.getLogger(name)


@dataclass
class MemoryStats:
    """Memory statistics container"""
    rss: float
    vms: float
    percent: float
    system_used: float

    @classmethod
    def capture(cls) -> 'MemoryStats':
        """Capture current process memory statistics"""
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
    """Temporarily disable memory monitoring"""
    global MONITORING_ENABLED
    previous = MONITORING_ENABLED
    MONITORING_ENABLED = False
    try:
        yield
    finally:
        MONITORING_ENABLED = previous


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
        logger.info(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")
        return result

    def enable(enabled: bool = True) -> None:
        _timer_states[timer_key] = enabled

    wrapper.enable = enable  # type: ignore[attr-defined]
    return wrapper


def monitor_memory(func: Callable[..., T]) -> Callable[..., T]:
    """Monitor memory usage of a function"""
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

            # Use warning level to ensure visibility
            logger.warning(
                f"{Fore.LIGHTBLACK_EX}Memory {func.__name__}: | "
                f"Current: RSS={end_mem.rss:.1f}MB, VMS={end_mem.vms:.1f}MB | "
                f"Change: RSS={end_mem.rss - start_mem.rss:+.1f}MB | "
                f"Process: {end_mem.percent:.1f}% | "
                f"System: {end_mem.system_used:.1f}% | "
                f"Time: {duration:.3f}s{Style.RESET_ALL}")

            if end_mem.rss > start_mem.rss * 1.5:
                logger.warning(
                    f"{Fore.YELLOW}High memory increase in {func.__name__}"
                    f" (+{((end_mem.rss/start_mem.rss)-1)*100:.0f}%){Style.RESET_ALL}")
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

        if name == 'process_ui':
            logger.log(
                CALLBACK, self._format_sequence_summary(),
                extra={'is_callback': True})
            self._reset_sequence()

    def _format_sequence_summary(self) -> str:
        callbacks_str = ', '.join(f"{c.name}:{c.execution_time:.2f}ms"
                                  for c in self.current_sequence)

        return (
            f"{Fore.LIGHTBLACK_EX}Sequence Summary | "
            f"{Fore.BLUE}Total Time: {self.total_time:.2f}ms "
            f"{Fore.LIGHTBLACK_EX}| Callbacks: {len(self.current_sequence)} | "
            f"Sequence: [{callbacks_str}]{Style.RESET_ALL}")


def _get_context(ctx: dash.callback_context) -> Dict[str, Any]:
    trigger_info = (ctx.triggered and ctx.triggered[0]['prop_id'] != '.'
                    and ctx.triggered[0] or
                    {'prop_id': next(iter(ctx.inputs)), 'value': next(
                        iter(ctx.inputs.values()))} if ctx.inputs else
                    {'prop_id': 'initial_load', 'value': None})

    return {
        'trigger': trigger_info['prop_id'].split('.')[0],
        'value': trigger_info['value'],
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'caller': f"{traceback.extract_stack()[-2].filename}:{traceback.extract_stack()[-2].lineno}",
        'outputs': [str(o) for o in getattr(ctx, 'outputs_list', [])],
        'no_updates': []
    }


def log_callback(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        ctx = _get_context(dash.callback_context)
        start = time.time()
        orig_level = logger.level
        logger.setLevel(CALLBACK)

        try:
            result = func(*args, **kwargs)
            time_ms = (time.time() - start) * 1000

            msg = (
                f"{Fore.LIGHTBLACK_EX}Callback:{func.__name__} | "
                f"Completed | "
                f"Time: {time_ms:.2f}ms | "
                f"{ctx['time']} | "
                f"Trigger: {ctx['trigger']}{Style.RESET_ALL}")
            logger.log(CALLBACK, msg, extra={'is_callback': True})

            callback_tracker._add_execution(func.__name__, time_ms)

            if time_ms > 1000:
                logger.warning(f"Slow cllbck: {func.__name__} {time_ms:.2f}ms")
            return result

        except dash.exceptions.PreventUpdate:
            time_ms = (time.time() - start) * 1000
            msg = (
                f"{Fore.LIGHTBLACK_EX}Callback:{func.__name__} | "
                f"{Fore.LIGHTBLUE_EX}PreventUpdate "
                f"{Fore.LIGHTBLACK_EX}| Time: {time_ms:.2f}ms | "
                f"{ctx['time']} | "
                f"Trigger: {ctx['trigger']}{Style.RESET_ALL}")
            logger.log(CALLBACK, msg, extra={'is_callback': True})
            raise
        except Exception as e:
            time_ms = (time.time() - start) * 1000
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
            return cast(T, ({}, "Expand All"))
    return wrapper


# Initialize globals
callback_tracker = CallbackTracker()
logger = get_logger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter())
logger.addHandler(handler)
logger.propagate = False