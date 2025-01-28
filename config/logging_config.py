from __future__ import annotations
import logging
import time
import dash
import os
import psutil
from enum import IntEnum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Any, Callable, Optional
from colorama import Fore, Back, Style, init
from dataclasses import dataclass
from functools import wraps
import traceback

# Initialize colorama
init(autoreset=True)

# Custom log level for callbacks
CALLBACK = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(CALLBACK, 'CALLBACK')

class LogLevel(IntEnum):
    """Enumeration for debug levels with backwards compatibility"""
    NONE = 0
    BASIC = 1
    VERBOSE = 2

debug_level = LogLevel.NONE

class ColoredFormatter(logging.Formatter):
    """Colored formatter for log levels"""
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.WHITE,
        'CALLBACK': Fore.LIGHTBLACK_EX,  # Added specific color for callbacks
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }

    def format(self, record: logging.LogRecord) -> str:
        formatted_message = super().format(record)
        return f"{self.COLORS.get(record.levelname, '')}{formatted_message}{Style.RESET_ALL}"

class CallbackFilter(logging.Filter):
    """Filter to separate callback logs from regular logs"""
    def __init__(self, for_callbacks: bool):
        super().__init__()
        self.for_callbacks = for_callbacks
        
    def filter(self, record):
        is_callback = getattr(record, 'is_callback', False)
        # Always allow callback logs regardless of module level when callback handler is used
        if self.for_callbacks and is_callback:
            return True
        return is_callback if self.for_callbacks else not is_callback

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

def track_callback_end(logger_name: str, callback_name: str, 
                      start_info: tuple[float, dict], result=None, 
                      error=None, message_no_update=None) -> None:
    """Log callback execution completion"""
    # Use module-specific logger instead of root logger
    logger = logging.getLogger(logger_name)
    start_time, context = start_info
    execution_time = (time.time() - start_time) * 1000
    extra = {'is_callback': True}
    
    # Colors for both field names and their values
    FIELD_COLORS = {
        'callback': {
            'label': Fore.LIGHTBLACK_EX,
            'value': Fore.LIGHTBLACK_EX
        },
        'time': {
            'label': Fore.LIGHTBLACK_EX,
            'value': Fore.LIGHTBLACK_EX
        },
        'trigger': {
            'label': Fore.LIGHTBLACK_EX,
            'value': Fore.LIGHTBLACK_EX
        },
        'execution': {
            'label': Fore.GREEN,
            'value': Fore.GREEN
        },
        'outputs': {
            'label': Fore.LIGHTBLACK_EX,
            'value': Fore.LIGHTBLACK_EX
        },
        'result': {
            'label': Fore.LIGHTBLACK_EX,
            'value': Fore.LIGHTBLACK_EX
        }
    }
    
    STATUS_COLORS = {
        'Completed': Fore.BLUE,
        'Prevented': Fore.LIGHTBLUE_EX,
        'Error': Fore.RED,
        'Default': Fore.WHITE
    }

    # Apply colors to both field names and values
    parts = [
        f"{FIELD_COLORS['execution']['label']}Execution:{Style.RESET_ALL} {FIELD_COLORS['execution']['value']}{execution_time:.2f}ms{Style.RESET_ALL}",
        f"{FIELD_COLORS['callback']['label']}Callback:{Style.RESET_ALL} {FIELD_COLORS['callback']['value']}{callback_name}{Style.RESET_ALL}",
        f"{FIELD_COLORS['time']['label']}Time:{Style.RESET_ALL} {FIELD_COLORS['time']['value']}{context['start_timestamp']}{Style.RESET_ALL}",
        f"{FIELD_COLORS['trigger']['label']}Trigger:{Style.RESET_ALL} {FIELD_COLORS['trigger']['value']}{context['trigger']}{Style.RESET_ALL}",
        f"{FIELD_COLORS['outputs']['label']}Outputs:{Style.RESET_ALL} {FIELD_COLORS['outputs']['value']}{' | '.join(context['outputs']) if context['outputs'] else 'None'}{Style.RESET_ALL}"
    ]

    if isinstance(error, dash.exceptions.PreventUpdate):
        # Handle PreventUpdate without logging error
        status_color = STATUS_COLORS['Prevented']
        parts.extend([
            f"{status_color}Status: Update Prevented{Style.RESET_ALL}",
            f"{status_color}Reason: {message_no_update or 'Update prevented by callback'}{Style.RESET_ALL}"
        ])
        # Use CALLBACK level instead of error
        logger.log(CALLBACK, " | ".join(parts), extra=extra)
    elif error:
        # Handle actual errors
        status_color = STATUS_COLORS['Error']
        parts.extend([
            f"{status_color}Status: Error{Style.RESET_ALL}",
            f"{status_color}Error: {str(error)}{Style.RESET_ALL}"
        ])
        logger.error(" | ".join(parts), extra=extra)
    else:
        # Handle successful completion
        status_color = STATUS_COLORS['Completed']
        parts.append(f"{status_color}Status: Completed{Style.RESET_ALL}")
        result_str = format_data(result) if result is not None else 'None'
        parts.append(f"{FIELD_COLORS['result']['label']}Result:{Style.RESET_ALL} {FIELD_COLORS['result']['value']}{result_str}{Style.RESET_ALL}")
        logger.log(CALLBACK, " | ".join(parts), extra=extra)
    
    if execution_time > 1000:
        logger.warning(f"Slow callback detected: {callback_name} took {execution_time:.2f}ms", 
                      extra=extra)

def log_callback(func):
    """Decorator for logging callback execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        callback_name = func.__name__
        module_name = func.__module__
        ctx = dash.callback_context
        start_info = track_callback(module_name, callback_name, ctx)
        
        try:
            result = func(*args, **kwargs)
            track_callback_end(module_name, callback_name, start_info, result=result)
            return result
        except Exception as e:
            if isinstance(e, dash.exceptions.PreventUpdate):
                # Log PreventUpdate and re-raise
                track_callback_end(
                    module_name,
                    callback_name,
                    start_info,
                    error=e,
                    message_no_update="Update prevented by callback"
                )
                raise
            else:
                # Log other errors and re-raise
                track_callback_end(module_name, callback_name, start_info, error=e)
                raise
    return wrapper

def setup_logging(console_level=logging.DEBUG, 
                 file_level=logging.DEBUG,
                 callback_level=CALLBACK,
                 log_file='app.log', 
                 fsevents_level=logging.INFO):
    """Configure logging with separate control for callbacks"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = ColoredFormatter('%(name)s - %(levelname)s - %(message)s')
    callback_formatter = ColoredFormatter('%(message)s')

    # Configure handlers
    file_handler = LoggerFactory.create_rotating_handler(
        str(log_dir / log_file), file_formatter, file_level
    )
    file_handler.addFilter(CallbackFilter(for_callbacks=False))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(CallbackFilter(for_callbacks=False))

    callback_handler = logging.StreamHandler()
    callback_handler.setLevel(callback_level)
    callback_handler.setFormatter(callback_formatter)
    callback_handler.addFilter(CallbackFilter(for_callbacks=True))

    # Clear existing handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure root logger
    root_logger.setLevel(min(console_level, file_level, callback_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(callback_handler)

    # Configure module-specific loggers with their levels
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
        'callbacks.insurance_lines_selection_callbacks': logging.WARNING,
        'callbacks.process_data_callback': logging.WARNING,
        'callbacks.update_metric_callbacks': logging.DEBUG,
        'callbacks.buttons_callbacks': logging.WARNING,
        'callbacks.get_metrics': logging.WARNING,
        'callbacks.ui_callbacks': logging.WARNING,
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

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def format_data(data):
    """Format data for logging with focus on key information"""
    if isinstance(data, tuple):
        categories = [item for item in data if isinstance(item, str)]
        return f"{', '.join(categories)}"
    elif isinstance(data, dict):
        if 'df' in data and 'prev_ranks' in data:
            df_info = {}
            if isinstance(data['df'], list):
                df_info['rows'] = len(data['df'])
                if data['df'] and isinstance(data['df'][0], dict):
                    df_info['columns'] = list(data['df'][0].keys())
            elif hasattr(data['df'], 'shape'):
                df_info['shape'] = data['df'].shape
                df_info['columns'] = list(data['df'].columns)
            
            ranks_info = {}
            if isinstance(data['prev_ranks'], dict):
                ranks_info['items'] = len(data['prev_ranks'])
                ranks_info['value_type'] = type(next(iter(data['prev_ranks'].values()))).__name__ if data['prev_ranks'] else 'empty'
            return f"<DataFrame: {df_info}, Rankings: {ranks_info}>"
        elif 'display' in data:
            return f"Display: {data['display']}"
    elif isinstance(data, list):
        if data and isinstance(data[0], dict) and set(data[0].keys()) == {'label', 'value'}:
            values = [opt['value'] for opt in data[:3]]
            return f"Options: {', '.join(values)}..."
    elif isinstance(data, str):
        return f"'{data}'"
    return str(data)



def track_callback(logger_name: str, callback_name: str, ctx) -> tuple[float, dict]:
    """Track callback execution start"""
    trigger_info = ctx.triggered[0] if ctx.triggered else {'prop_id': 'no_trigger', 'value': None}
    stack = traceback.extract_stack()
    caller_info = stack[-2]
    
    # Get output IDs from callback context
    outputs = []
    if hasattr(ctx, 'outputs_list') and ctx.outputs_list:
        for output in ctx.outputs_list:
            if isinstance(output, str):
                outputs.append(output)
            elif isinstance(output, dict):
                outputs.append(str(output))
            else:
                outputs.append(str(output))
    
    return time.time(), {
        'trigger': trigger_info['prop_id'].split('.')[0],
        'trigger_value': trigger_info['value'],
        'start_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'caller_info': f"{caller_info.filename}:{caller_info.lineno}",
        'outputs': outputs
    }


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
def get_triggered_index(ctx: dash.callback_context, button_values: List[str], 
                       prefix: str) -> Optional[int]:
    """Helper function to get the index of triggered button"""
    if not ctx.triggered:
        return None
    triggered = ctx.triggered[0]["prop_id"].split(".")[0]
    return next((i for i, val in enumerate(button_values) 
                 if f"{prefix}{val}" == triggered), None)


