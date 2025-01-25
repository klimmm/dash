from __future__ import annotations
import logging
import time
import os
import psutil
from enum import IntEnum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Any, Callable
from colorama import Fore, Back, Style, init
from dataclasses import dataclass
from functools import wraps

class LogLevel(IntEnum):
    """Enumeration for debug levels with backwards compatibility"""
    NONE = 0
    BASIC = 1
    VERBOSE = 2

debug_level = LogLevel.NONE
init(autoreset=True)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

class ColoredFormatter(logging.Formatter):
    """Basic colored formatter for log levels"""
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

def setup_logging(console_level=logging.DEBUG, file_level=logging.DEBUG,
                 log_file='app.log', fsevents_level=logging.INFO):
    """Configure logging with standard formatters"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = ColoredFormatter('%(name)s - %(levelname)s - %(message)s')
    memory_formatter = logging.Formatter('%(asctime)s - %(message)s')

    # Configure root logger
    file_handler = LoggerFactory.create_rotating_handler(
        str(log_dir / log_file), file_formatter, file_level
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    root_logger = LoggerFactory.configure_logger(
        '', [file_handler, console_handler],
        min(console_level, file_level)
    )

    # Configure memory logger
    memory_file_handler = LoggerFactory.create_rotating_handler(
        str(log_dir / 'memory_profile.log'),
        memory_formatter,
        logging.DEBUG  # Keep file logging at DEBUG level
    )

    # Create a new console handler for memory logger that respects console_level
    memory_console_handler = logging.StreamHandler()
    memory_console_handler.setFormatter(memory_formatter)
    memory_console_handler.setLevel(console_level)  # Use the same console_level

    memory_logger = LoggerFactory.configure_logger(
        'memory_profiler',
        [memory_file_handler, memory_console_handler],
        logging.DEBUG,  # Keep overall logger level at DEBUG for file logging
        False
    )

    # Configure module-specific loggers
    logger_levels = {
        'application': logging.WARNING,
        'application.callbacks': logging.WARNING,
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
        'data_process': logging.WARNING,
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



def track_callback(logger_name: str, callback_name: str, ctx) -> tuple[float, dict]:
    """Track callback execution start with enhanced debugging"""
    trigger_info = ctx.triggered[0]
    import traceback
    stack = traceback.extract_stack()
    caller_info = stack[-2]

    logger = get_logger(logger_name)
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

def format_data(data):
    """Format data for logging with focus on key information"""
    if isinstance(data, tuple):
        # Extract and show the actual categories from the tuple
        categories = [item for item in data if isinstance(item, str)]
        return f"{', '.join(categories)}"

    elif isinstance(data, dict):
        if 'df' in data and 'prev_ranks' in data:
            # Special handling for DataFrames and rankings
            df_info = {}
            if isinstance(data['df'], list):
                df_info['rows'] = len(data['df'])
                if data['df'] and isinstance(data['df'][0], dict):
                    df_info['columns'] = list(data['df'][0].keys())
            elif hasattr(data['df'], 'shape'):  # pandas DataFrame
                df_info['shape'] = data['df'].shape
                df_info['columns'] = list(data['df'].columns)
                
            ranks_info = {}
            if isinstance(data['prev_ranks'], dict):
                ranks_info['items'] = len(data['prev_ranks'])
                ranks_info['value_type'] = type(next(iter(data['prev_ranks'].values()))).__name__ if data['prev_ranks'] else 'empty'
                
            return (f"<DataFrame: {df_info}, "
                   f"Rankings: {ranks_info}>")

        elif 'display' in data:
            return f"Display: {data['display']}" 
            
    elif isinstance(data, list):
        if data and isinstance(data[0], dict) and set(data[0].keys()) == {'label', 'value'}:
            # For dropdown options, show first few actual values
            values = [opt['value'] for opt in data[:3]]
            return f"Options: {', '.join(values)}..."
            
    elif isinstance(data, str):
        return f"'{data}'"
        
    return str(data)


def track_callback_end(logger_name: str, callback_name: str, 
                      start_info: tuple[float, dict], result=None, 
                      error=None, message_no_update=None) -> None:
    """Log comprehensive callback execution information with color coding"""
    logger = get_logger(logger_name)
    start_time, context = start_info
    execution_time = (time.time() - start_time) * 1000


    # Define colors for different statuses
    STATUS_COLORS = {
        'Completed': Fore.GREEN,
        'Prevented': Fore.LIGHTBLUE_EX,
        'Error': Fore.RED,
        'Default': Fore.WHITE
    }

    # Create colored message parts
    parts = [
        f"Callback: {callback_name}",
        f"Time: {context['start_timestamp']}",
        f"Trigger: {context['trigger']}",
        # f"Value: {format_data(context['trigger_value'])}",
        f"Execution: {execution_time:.2f}ms"
    ]

    # Add status and result with appropriate colors
    if error:
        status_color = STATUS_COLORS['Error']
        parts.extend([
            f"{status_color}Status: Error{Style.RESET_ALL}",
            f"{status_color}Error: {str(error)}{Style.RESET_ALL}"
        ])
        logger.error(" | ".join(parts), exc_info=True)
    elif message_no_update:
        status_color = STATUS_COLORS['Prevented']
        parts.extend([
            f"{status_color}Status: Prevented{Style.RESET_ALL}",
            f"{status_color}Reason: {message_no_update}{Style.RESET_ALL}"
        ])
        logger.info(" | ".join(parts))
    else:
        status_color = STATUS_COLORS['Completed']
        parts.append(f"{status_color}Status: Completed{Style.RESET_ALL}")
        if result:
            parts.append(f"{status_color}Result: {format_data(result)}{Style.RESET_ALL}")
        logger.info(" | ".join(parts))

    # Log slow callback warning separately
    if execution_time > 1000:
        logger.warning(f"Slow callback detected: {callback_name} took {execution_time:.2f}ms")

def callback_error_handler(func):
    """Decorator to handle callback errors uniformly"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper



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