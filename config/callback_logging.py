from __future__ import annotations
import logging
import time
import dash
import traceback
from colorama import Fore, Style, init
from typing import Any, Callable, List, Optional, Dict, Tuple
from functools import wraps

# Initialize colorama
init(autoreset=True)

# Custom log level for callbacks
CALLBACK = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(CALLBACK, 'CALLBACK')

class CallbackFormatter(logging.Formatter):
    """Specific formatter for callback logs with customized colors"""
    def __init__(self):
        super().__init__('%(name)s - %(message)s')
        
    def format(self, record):
        # Replace 'None' module name with empty string and color the module name
        if record.name == 'root':
            record.name = ''
        else:
            record.name = f"{Fore.LIGHTBLACK_EX}{record.name}{Style.RESET_ALL}"
        return super().format(record)

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

def setup_callback_logging(level: int = CALLBACK) -> None:
    """Configure callback-specific logging"""
    # Create callback handler with specific formatter
    callback_handler = logging.StreamHandler()
    callback_handler.setLevel(level)
    callback_handler.setFormatter(CallbackFormatter())
    callback_handler.addFilter(CallbackFilter(for_callbacks=True))

    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove any existing callback handlers
    for handler in root_logger.handlers[:]:
        if isinstance(handler.formatter, CallbackFormatter):
            root_logger.removeHandler(handler)
        else:
            # Add callback filter to non-callback handlers to prevent duplicate logs
            handler.addFilter(CallbackFilter(for_callbacks=False))
    
    # Add new callback handler
    root_logger.addHandler(callback_handler)
    
    # Update root logger level if needed
    current_level = root_logger.getEffectiveLevel()
    if level < current_level:
        root_logger.setLevel(level)

    # Configure callback logger
    callback_logger = logging.getLogger('callbacks')
    callback_logger.setLevel(level)

def format_data(data: Any) -> str:
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

def track_callback(logger_name: str, callback_name: str, ctx: dash.callback_context) -> Tuple[float, Dict]:
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

def track_callback_end(logger_name: str, callback_name: str, 
                      start_info: Tuple[float, Dict], result: Any = None, 
                      error: Exception = None, message_no_update: str = None) -> None:
    """Log callback execution completion"""
    logger = logging.getLogger(logger_name if logger_name != "__main__" else "callbacks")
    start_time, context = start_info
    execution_time = (time.time() - start_time) * 1000
    extra = {'is_callback': True}
    
    # Colors for both field names and their values
    FIELD_COLORS = {
        'callback': {'label': Fore.LIGHTBLACK_EX, 'value': Fore.LIGHTBLACK_EX},
        'time': {'label': Fore.LIGHTBLACK_EX, 'value': Fore.LIGHTBLACK_EX},
        'trigger': {'label': Fore.LIGHTBLACK_EX, 'value': Fore.LIGHTBLACK_EX},
        'execution': {'label': Fore.GREEN, 'value': Fore.GREEN},
        'outputs': {'label': Fore.LIGHTBLACK_EX, 'value': Fore.LIGHTBLACK_EX},
        'result': {'label': Fore.LIGHTBLACK_EX, 'value': Fore.LIGHTBLACK_EX}
    }
    
    STATUS_COLORS = {
        'Completed': Fore.BLUE,
        'Prevented': Fore.LIGHTBLUE_EX,
        'Error': Fore.RED,
        'Default': Fore.WHITE
    }

    # Start with execution time and determine status
    status_part = None
    error_part = None
    if isinstance(error, dash.exceptions.PreventUpdate):
        status_color = STATUS_COLORS['Prevented']
        status_part = f"{Fore.LIGHTBLACK_EX}Status:{Style.RESET_ALL} {status_color}Prevented{Style.RESET_ALL}"
        error_part = f"{Fore.LIGHTBLACK_EX}Reason:{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{message_no_update or 'Update prevented by callback'}{Style.RESET_ALL}"
    elif error:
        status_color = STATUS_COLORS['Error']
        status_part = f"{Fore.LIGHTBLACK_EX}Status:{Style.RESET_ALL} {status_color}Error{Style.RESET_ALL}"
        error_part = f"{status_color}Error: {str(error)}{Style.RESET_ALL}"
    else:
        status_color = STATUS_COLORS['Completed']
        status_part = f"{Fore.LIGHTBLACK_EX}Status:{Style.RESET_ALL} {status_color}Completed{Style.RESET_ALL}"

    # Apply colors to fields and build parts array
    parts = [
        f"{FIELD_COLORS['execution']['label']}Execution:{Style.RESET_ALL} {FIELD_COLORS['execution']['value']}{execution_time:.2f}ms{Style.RESET_ALL}",
        status_part,
        f"{Fore.LIGHTBLACK_EX}Callback:{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{callback_name}{Style.RESET_ALL}",
        f"{FIELD_COLORS['time']['label']}Time:{Style.RESET_ALL} {FIELD_COLORS['time']['value']}{context['start_timestamp']}{Style.RESET_ALL}",
        f"{FIELD_COLORS['trigger']['label']}Trigger:{Style.RESET_ALL} {FIELD_COLORS['trigger']['value']}{context['trigger']}{Style.RESET_ALL}",
        f"{FIELD_COLORS['outputs']['label']}Outputs:{Style.RESET_ALL} {FIELD_COLORS['outputs']['value']}{' | '.join(context['outputs']) if context['outputs'] else 'None'}{Style.RESET_ALL}"
    ]

    if error_part:
        parts.append(error_part)
    elif result is not None:
        result_str = format_data(result) if result is not None else 'None'
        parts.append(f"{FIELD_COLORS['result']['label']}Result:{Style.RESET_ALL} {FIELD_COLORS['result']['value']}{result_str}{Style.RESET_ALL}")

    # Log with appropriate level
    log_level = logging.ERROR if error and not isinstance(error, dash.exceptions.PreventUpdate) else CALLBACK
    logger.log(log_level, " | ".join(parts), extra=extra)
    
    if execution_time > 1000:
        logger.warning(f"Slow callback detected: {callback_name} took {execution_time:.2f}ms", 
                      extra=extra)

def log_callback(func: Callable) -> Callable:
    """Decorator for logging callback execution"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
                track_callback_end(
                    module_name,
                    callback_name,
                    start_info,
                    error=e,
                    message_no_update="Update prevented by callback"
                )
                raise
            else:
                track_callback_end(module_name, callback_name, start_info, error=e)
                raise
    return wrapper

def get_triggered_index(ctx: dash.callback_context, button_values: List[str], 
                       prefix: str) -> Optional[int]:
    """Helper function to get the index of triggered button"""
    if not ctx.triggered:
        return None
    triggered = ctx.triggered[0]["prop_id"].split(".")[0]
    return next((i for i, val in enumerate(button_values) 
                 if f"{prefix}{val}" == triggered), None)