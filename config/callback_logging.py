from __future__ import annotations
import logging
import time
import dash
import traceback
from colorama import Fore, Style, init
from typing import Any, Callable, Dict, List, Union
from functools import wraps

# Initialize colorama and setup constants
init(autoreset=True)
CALLBACK = 25
logging.addLevelName(CALLBACK, 'CALLBACK')

def setup_callback_logging(level: int = CALLBACK) -> None:
    """Configure enhanced callback-specific logging"""
    root_logger = logging.getLogger()
    callback_logger = logging.getLogger('callbacks')

    try:
        callback_handler = logging.StreamHandler()
        callback_handler.setLevel(level)
        callback_handler.setFormatter(logging.Formatter('%(name)s - %(message)s'))
        callback_handler.addFilter(lambda record: getattr(record, 'is_callback', False))

        # Update existing handlers to exclude callback logs
        for handler in root_logger.handlers[:]:
            if isinstance(handler.formatter, logging.Formatter):
                handler.addFilter(lambda record: not getattr(record, 'is_callback', False))

        root_logger.addHandler(callback_handler)
        if level < root_logger.getEffectiveLevel():
            root_logger.setLevel(level)
        callback_logger.setLevel(level)

        logging.debug("Callback logging setup completed")
    except Exception as e:
        logging.error(f"Failed to setup callback logging: {str(e)}")
        raise

def get_callback_context(ctx: dash.callback_context) -> Dict[str, Any]:
    """Get callback context information with enhanced output analysis"""
    # Check if there are any triggered inputs
    if ctx.triggered and ctx.triggered[0]['prop_id'] != '.':
        trigger_info = ctx.triggered[0]
    # Check if there are any inputs at all
    elif ctx.inputs and list(ctx.inputs.values()):
        trigger_info = {'prop_id': list(ctx.inputs.keys())[0], 'value': list(ctx.inputs.values())[0]}
    else:
        trigger_info = {'prop_id': 'initial_load', 'value': None}

    caller_info = traceback.extract_stack()[-2]
    
    # Enhanced output processing
    outputs = []
    no_update_indices = []
    
    # Get outputs from context
    output_specs = getattr(ctx, 'outputs_list', [])
    outputs = [str(output) for output in output_specs]
    
    return {
        'trigger': trigger_info['prop_id'].split('.')[0],
        'trigger_value': trigger_info['value'],
        'start_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'caller_info': f"{caller_info.filename}:{caller_info.lineno}",
        'outputs': outputs,
        'no_update_outputs': no_update_indices,
    }


def format_callback_message(execution_time: float,
                            context: Dict[str, Any],
                            callback_name: str,
                            result: Any = None,
                            error: Exception = None,
                            message_no_update: str = None
                            ) -> str:
    DEFAULT_COLOR = Fore.LIGHTBLACK_EX

    # Start with execution time
    parts = [f"{Fore.GREEN}Execution: {execution_time:.2f}ms{Style.RESET_ALL}"]

    # Status formatting
    if isinstance(error, dash.exceptions.PreventUpdate):
        status = f"{Fore.LIGHTBLUE_EX}Prevented{Style.RESET_ALL}"
        reason = message_no_update or 'Update prevented'
        parts.extend([
            f"{DEFAULT_COLOR}Status: {status}",
            f"{DEFAULT_COLOR}Reason: {reason}{Style.RESET_ALL}"
        ])
    elif error:
        status = f"{Fore.RED}Error{Style.RESET_ALL}"
        parts.extend([
            f"{DEFAULT_COLOR}Status: {status}",
            f"Error: {str(error)}{Style.RESET_ALL}"
        ])
    else:
        parts.append(f"{DEFAULT_COLOR}Status: {Fore.LIGHTBLACK_EX}Completed{Style.RESET_ALL}")

    # Add context information with default color
    parts.extend([
        f"{DEFAULT_COLOR}Callback: {callback_name}{Style.RESET_ALL}",
        f"{DEFAULT_COLOR}Time: {Fore.LIGHTBLACK_EX}{context['start_timestamp']}{Style.RESET_ALL}",
        f"{DEFAULT_COLOR}Trigger: {Fore.LIGHTBLACK_EX}{context['trigger']}{Style.RESET_ALL}"
    ])

    # Enhanced output formatting with properly colored IDs
    def format_output(output_str: str) -> str:
        """Format individual output with colored component ID"""
        try:
            # Convert string representation to dictionary safely
            output_dict = eval(output_str, {'__builtins__': {}}, {})
            if isinstance(output_dict, dict) and 'id' in output_dict:
                # Return only the ID in cyan color
                return f"{Fore.LIGHTBLACK_EX}{output_dict['id']}{Style.RESET_ALL}"
            return output_str
        except:
            return output_str

    # Format outputs list maintaining color codes
    outputs_str = [format_output(str(output)) for output in context['outputs']]
    parts.append(f"{DEFAULT_COLOR}Outputs: [{', '.join(outputs_str)}]{Style.RESET_ALL}")

    # Result formatting with accurate update status
    if not error and result is not None:
        formatted_result = format_data(result)

        # Update status formatting
        update_status = []
        no_update_indices = context.get('no_update_outputs', [])

        if isinstance(result, (list, tuple)):
            for idx, _ in enumerate(result):
                is_no_update = idx in no_update_indices
                status_color = Fore.LIGHTBLUE_EX if is_no_update else Fore.LIGHTBLACK_EX
                update_status.append(
                    f"{idx}:{status_color}{'NoUpdate' if is_no_update else 'Updated'}{Style.RESET_ALL}"
                )
        else:
            is_no_update = 0 in no_update_indices
            status_color = Fore.LIGHTBLUE_EX if is_no_update else Fore.LIGHTBLACK_EX
            update_status.append(
                f"0:{status_color}{'NoUpdate' if is_no_update else 'Updated'}{Style.RESET_ALL}"
            )

        status_str = f" [{', '.join(update_status)}]"

        # Truncate long results
        if len(formatted_result) > 200:
            formatted_result = f"{formatted_result[:197]}..."

        parts.append(f"{DEFAULT_COLOR}Result: {status_str}{Style.RESET_ALL}")

    # Join parts with default color separator
    return ' | '.join(parts)


def log_callback(func: Callable) -> Callable:
    """Decorator for comprehensive callback logging with error handling"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        callback_name = func.__name__
        module_name = func.__module__
        ctx = dash.callback_context
        start_time = time.time()
        context = get_callback_context(ctx)

        logger = logging.getLogger(module_name if module_name != "__main__" else "callbacks")
        original_level = logger.level
        logger.setLevel(CALLBACK)

        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # Enhanced NoUpdate detection
            def is_no_update(value):
                """Helper to detect NoUpdate in various forms"""
                if hasattr(value, '__class__'):
                    class_str = str(value.__class__)
                    return ('NoUpdate' in class_str or 
                           isinstance(value, dash._callback.NoUpdate))
                return False

            # Detect NoUpdate in results
            if isinstance(result, (list, tuple)):
                for idx, value in enumerate(result):
                    if is_no_update(value):
                        context['no_update_outputs'].append(idx)
            elif is_no_update(result):
                context['no_update_outputs'].append(0)

            message = format_callback_message(execution_time, context, callback_name, result=result)
            logger.log(CALLBACK, message, extra={'is_callback': True})

            if execution_time > 1000:
                logger.warning(
                    f"Slow callback detected: {callback_name} took {execution_time:.2f}ms",
                    extra={'is_callback': True}
                )
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            is_prevent_update = isinstance(e, dash.exceptions.PreventUpdate)

            message = format_callback_message(
                execution_time, context, callback_name,
                error=e,
                message_no_update="Update prevented by callback" if is_prevent_update else None
            )

            logger.log(
                CALLBACK if is_prevent_update else logging.ERROR,
                message,
                extra={'is_callback': True}
            )
            raise

        finally:
            logger.setLevel(original_level)

    return wrapper


def format_data(data, max_items=2, depth=0, max_depth=3):
    """Simplified unified data formatter with improved readability"""

    # Handle maximum recursion depth
    if depth >= max_depth:
        return f"{type(data).__name__}(...)"

    # Handle None and primitive types
    if data is None or isinstance(data, (bool, int, float)):
        return str(data)

    # Handle strings
    if isinstance(data, str):
        return f"'{data[:47]}...'" if len(data) > 50 else f"'{data}'"

    # Handle sequences (lists, tuples)
    if isinstance(data, (list, tuple)):
        if not data:
            return '[]' if isinstance(data, list) else '()'

        # Format items
        items = [format_data(item, max_items, depth + 1, max_depth) 
                 for item in data[:max_items]]

        # Add length indicator if truncated
        if len(data) > max_items:
            items.append(f"...({len(data)} total)")

        return f"[{', '.join(items)}]" if isinstance(data, list) else f"({', '.join(items)})"

    # Handle dictionaries
    if isinstance(data, dict):
        if not data:
            return '{}'

        # Format key-value pairs
        pairs = [f"{k}: {format_data(v, max_items, depth + 1, max_depth)}" 
                 for k, v in list(data.items())[:max_items]]

        # Add length indicator if truncated
        if len(data) > max_items:
            pairs.append(f"...({len(data)} total)")

        return f"{{{', '.join(pairs)}}}"

    # Handle objects
    return f"{type(data).__name__}({str(data)})"