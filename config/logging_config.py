from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from enum import IntEnum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional, Union, List, Callable, Any

import psutil
from colorama import Fore, Back, Style, init
# from memory_profiler import memory_usage
from functools import wraps

# Initialize colorama
init(autoreset=True)

class LogLevel(IntEnum):
    """Enumeration for debug levels with backwards compatibility"""
    NONE = 0
    BASIC = 1
    VERBOSE = 2

# Maintain backwards compatibility
DebugLevels = type('DebugLevels', (), {level.name: level.value for level in LogLevel})
debug_level = LogLevel.NONE

class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored console output with status-specific colors"""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    # Define colors for different callback statuses
    STATUS_COLORS = {
        'Completed': Fore.GREEN,  # Light green for completed
        'Prevented': Fore.LIGHTBLUE_EX,   # Light blue for prevented
        'Error': Fore.RED                 # Red for errors
    }

    def __init__(self, fmt: str = None, callback_color: bool = False):
        super().__init__(fmt)
        self.callback_color = callback_color

    def format(self, record: logging.LogRecord) -> str:
        formatted_message = super().format(record)
        
        if self.callback_color and record.name == 'callbacks':
            # Split the message into parts
            parts = formatted_message.split(' | ')
            colored_parts = []
            
            # Determine the status color
            status_color = Fore.WHITE  # Default color
            for status, color in self.STATUS_COLORS.items():
                if f"Status: {status}" in formatted_message:
                    status_color = color
                    break
            
            for part in parts:
                if part.startswith('Result:'):
                    # Use standard level color for result
                    colored_parts.append(f"{self.COLORS.get(record.levelname, '')}{part}{Style.RESET_ALL}")
                else:
                    # Color the entire part (both label and value) with status color
                    colored_parts.append(f"{status_color}{part}{Style.RESET_ALL}")
            
            return ' | '.join(colored_parts)
            
        return f"{self.COLORS.get(record.levelname, '')}{formatted_message}{Style.RESET_ALL}"




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



def setup_logging(console_level=logging.DEBUG, file_level=logging.DEBUG, 
                 log_file='app.log', fsevents_level=logging.INFO):
    """Configure logging with specified levels and handlers"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = ColoredFormatter('%(name)s - %(levelname)s - %(message)s')
    memory_formatter = logging.Formatter('%(asctime)s - %(message)s')
    callback_formatter = ColoredFormatter('%(name)s - %(levelname)s - %(message)s', callback_color=True)

    # Create common handlers
    file_handler = LoggerFactory.create_rotating_handler(
        str(log_dir / log_file), file_formatter, file_level
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # Configure root logger first
    root_logger = LoggerFactory.configure_logger(
        '', [file_handler, console_handler], 
        min(console_level, file_level)
    )

    # Configure callback logger with its own handler and blue color formatter
    callback_console_handler = logging.StreamHandler()
    callback_console_handler.setFormatter(callback_formatter)
    callback_console_handler.setLevel(console_level)

    callback_file_handler = LoggerFactory.create_rotating_handler(
        str(log_dir / 'callbacks.log'), 
        file_formatter  # Use standard file formatter for file logs
    )

    # Important: Set propagate=False to prevent callback logs from going through root logger
    callback_logger = LoggerFactory.configure_logger(
        'callbacks',
        [callback_file_handler, callback_console_handler],
        logging.DEBUG,
        propagate=False  # This is crucial to prevent double-logging
    )

    # Configure memory logger
    memory_logger = LoggerFactory.configure_logger(
        'memory_profiler',
        [
            LoggerFactory.create_rotating_handler(
                str(log_dir / 'memory_profile.log'), 
                memory_formatter
            ),
            logging.StreamHandler()
        ],
        logging.DEBUG,
        False
    )

    # Configure module-specific loggers
    logger_levels = {
        'app.app_layout': logging.DEBUG,
        'app.callbacks': {
            'app_layout_callbacks': logging.WARNING,
            'insurance_lines_callbacks': logging.WARNING,
            'filter_update_callbacks': logging.DEBUG,
        },
        'app.components': {
            'insurance_lines_tree': logging.WARNING,
            'period_filter': logging.WARNING,
            'range_filter': logging.WARNING,
            'dropdown': logging.WARNING,
            'dash_table': logging.WARNING,
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
        'data_process': logging.DEBUG,
        'fsevents': fsevents_level,
    }

    for base_name, config in logger_levels.items():
        if isinstance(config, dict):
            for sub_name, level in config.items():
                logger = logging.getLogger(f"{base_name}.{sub_name}")
                logger.setLevel(level)
        else:
            logger = logging.getLogger(base_name)
            logger.setLevel(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def custom_profile(func: Callable) -> Callable:
    """Profile function execution with memory usage tracking"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if debug_level < LogLevel.VERBOSE:
            return func(*args, **kwargs)

        memory_logger = get_logger('memory_profiler')
        initial_memory = memory_usage(-1, interval=0.1, timeout=1)[0]
        start_time = time.time()

        mem_usage = list(memory_usage(
            (func, args, kwargs), 
            interval=0.1, 
            timeout=None, 
            max_iterations=1
        ))
        result = func(*args, **kwargs)

        execution_time = time.time() - start_time
        memory_stats = {
            'initial': initial_memory,
            'final': mem_usage[-1],
            'min': min(mem_usage),
            'max': max(mem_usage),
            'change': mem_usage[-1] - initial_memory
        }

        memory_logger.debug(
            f"\nFunction '{func.__name__}' memory profile:\n"
            f"├─ Time and Memory Overview:\n"
            f"│  ├─ Execution time: {execution_time:.2f}s\n"
            f"│  ├─ Initial memory: {memory_stats['initial']:.1f} MiB\n"
            f"│  ├─ Final memory: {memory_stats['final']:.1f} MiB\n"
            f"│  ├─ Net change: {memory_stats['change']:.1f} MiB\n"
            f"│  └─ Memory range: {memory_stats['min']:.1f} MiB - {memory_stats['max']:.1f} MiB"
        )

        memory_logger.info(
            f"\nFunction: {func.__name__}\n"
            f"Memory range: {memory_stats['min']:.1f} MiB - {memory_stats['max']:.1f} MiB\n"
            f"Execution time: {execution_time:.2f}s\n"
        )

        return result
    return wrapper

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

def track_callback(logger_name: str, callback_name: str, ctx) -> tuple[float, dict]:
    """Track callback execution start with enhanced debugging"""
    trigger_info = ctx.triggered[0]
    # Add stack trace to help identify where the callback is being triggered from
    import traceback
    stack = traceback.extract_stack()
    caller_info = stack[-2]  # Get the caller's information

    logger = get_logger('callbacks')
    logger.debug(
        f"Callback '{callback_name}' triggered by '{trigger_info['prop_id']}' "
        f"from {caller_info.filename}:{caller_info.lineno}"
    )

    return time.time(), {
        'trigger': trigger_info['prop_id'].split('.')[0],
        'trigger_value': trigger_info['value'],
        'start_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'caller_info': f"{caller_info.filename}:{caller_info.lineno}"
    }

def format_value_for_logging(value: Any) -> str:
    """Format complex data structures for logging in a more readable way"""
    if isinstance(value, dict):
        # For dictionaries, summarize the keys and length
        return f"<Dict with {len(value)} keys: {', '.join(list(value.keys())[:5])}{'...' if len(value) > 5 else ''}>"
    elif isinstance(value, list):
        # For lists, show length and first few items
        return f"<List with {len(value)} items>"
    elif isinstance(value, str) and len(value) > 200:
        # Truncate long strings
        return f"{value[:200]}... (truncated)"
    return str(value)


def track_callback_end(logger_name: str, callback_name: str, 
                      start_info: tuple[float, dict], result=None, 
                      error=None, message_no_update=None) -> None:
    """Log comprehensive callback execution information without duplication"""
    logger = get_logger('callbacks')
    start_time, context = start_info
    execution_time = (time.time() - start_time) * 1000

    def format_data(data):
        """Format complex data for logging"""
        if isinstance(data, dict):
            if 'df' in data and 'prev_ranks' in data:
                df_length = len(data['df']) if isinstance(data['df'], list) else 'N/A'
                ranks_length = len(data['prev_ranks']) if isinstance(data['prev_ranks'], dict) else 'N/A'
                return f"<DataFrame with {df_length} rows, Rankings with {ranks_length} items>"
            return f"<Dict with {len(data)} keys: {', '.join(list(data.keys())[:3])}{'...' if len(data) > 3 else ''}>"
        elif isinstance(data, (tuple, list)):
            return f"<{type(data).__name__} with {len(data)} items>"
        elif isinstance(data, str) and len(data) > 100:
            return f"{data[:100]}..."
        return str(data)

    # Create base log message
    log_parts = [
        f"Callback: {callback_name}",
        f"Time: {context['start_timestamp']}",
        f"Trigger: {context['trigger']}",
        f"Value: {format_data(context['trigger_value'])}",
        f"Execution: {execution_time:.2f}ms"
    ]

    # Add status and any additional information
    if error:
        log_parts.extend([f"Status: Error", f"Error: {str(error)}"])
        logger.error(" | ".join(log_parts), exc_info=True)
    elif message_no_update:
        log_parts.extend([f"Status: Prevented", f"Reason: {message_no_update}"])
        logger.info(" | ".join(log_parts))
    else:
        log_parts.append(f"Status: Completed")
        if result:
            log_parts.append(f"Result: {format_data(result)}")
        logger.info(" | ".join(log_parts))

    # Log slow callback warning separately
    if execution_time > 1000:
        logger.warning(f"Slow callback detected: {callback_name} took {execution_time:.2f}ms")



# Export all required symbols
__all__ = [
    'setup_logging',
    'get_logger',
    'custom_profile',
    'set_debug_level',
    'DebugLevels',
    'track_callback',
    'track_callback_end',
    'monitor_memory',
    'memory_monitor'
]