from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar, cast

import dash
from colorama import Fore, Style

# Import from enhanced logging_config
from .logging_config import get_logger, timer

T = TypeVar('T')

# Constants
CALLBACK = 25  # Custom log level
logging.addLevelName(CALLBACK, 'CALLBACK')


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

        if name == 'render_visualization_components':
            callbacks_str = ', '.join(
                f"{c.name}:{c.execution_time:.2f}ms"
                for c in self.current_sequence)
            # Use get_logger instead of direct logging.getLogger
            callback_logger.log(
                CALLBACK,
                f"{Fore.LIGHTBLACK_EX}Sequence Summary | "
                f"{Fore.BLUE}Total Time: {self.total_time:.2f}ms "
                f"{Fore.LIGHTBLACK_EX}| Callbacks: {len(self.current_sequence)} | "
                f"Sequence: [{callbacks_str}]{Style.RESET_ALL}",
                extra={'is_callback': True})
            self._reset_sequence()


# Use get_logger from logging_config
callback_logger = get_logger('callbacks')
callback_tracker = CallbackTracker()


def dash_callback(func: Callable[..., T]) -> Callable[..., T]:
    """
    Combined decorator that both logs callback execution and handles errors.
    This combines the functionality of log_callback and error_handler.

    Args:
        func: The callback function to decorate

    Returns:
        Decorated function with both logging and error handling
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Log callback part (from log_callback)
        ctx = dash.callback_context
        trigger_info = (ctx.triggered and ctx.triggered[0]['prop_id'] != '.'
                        and ctx.triggered[0] or
                        {'prop_id': next(iter(ctx.inputs)), 'value':
                        next(iter(ctx.inputs.values()))}
                        if ctx.inputs else {'prop_id': 'initial_load',
                                            'value': None})

        start = time.time()
        # Always use the same logger instance via get_logger
        # This is critical for preventing duplication
        logger = get_logger('callbacks')
        orig_level = logger.level
        logger.setLevel(CALLBACK)

        try:
            # Execute the callback function
            result = func(*args, **kwargs)

            # Log successful execution
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
            # Handle PreventUpdate separately (just log it)
            logger.log(
                CALLBACK,
                f"{Fore.LIGHTBLACK_EX}Callback:{func.__name__} | "
                f"{Fore.LIGHTBLUE_EX}PreventUpdate{Style.RESET_ALL}",
                extra={'is_callback': True})
            raise

        except Exception as e:
            # Error handling part (from error_handler)
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)

            # Get information about the callback outputs
            if hasattr(func, 'callback') and hasattr(func.callback, 'output'):
                outputs = func.callback.output

                # Handle both single and multiple outputs
                if isinstance(outputs, (list, tuple)):
                    # For multiple outputs, create appropriate error responses
                    error_result = []
                    for output in outputs:
                        # Create appropriate default error value based on component property
                        if hasattr(output, 'component_property'):
                            prop = output.component_property
                            if prop == 'children':
                                error_result.append(f"Error in {func.__name__}: {str(e)}")
                            elif prop == 'figure':
                                error_result.append({
                                    'data': [],
                                    'layout': {
                                        'title': f"Error in {func.__name__}",
                                        'annotations': [{
                                            'text': str(e),
                                            'x': 0.5,
                                            'y': 0.5,
                                            'showarrow': False,
                                            'font': {'color': 'red'}
                                        }]
                                    }
                                })
                            elif prop == 'data':
                                error_result.append([])
                            elif prop == 'options':
                                error_result.append([])
                            elif prop in ['style', 'className']:
                                error_result.append({'color': 'red'})
                            elif prop == 'disabled':
                                error_result.append(False)
                            else:
                                error_result.append(None)
                        else:
                            error_result.append(None)
                    return cast(T, tuple(error_result))
                else:
                    # For single output
                    prop = getattr(outputs, 'component_property', None)
                    if prop == 'children':
                        return cast(T, f"Error in {func.__name__}: {str(e)}")
                    elif prop == 'figure':
                        return cast(T, {
                            'data': [],
                            'layout': {
                                'title': f"Error in {func.__name__}",
                                'annotations': [{
                                    'text': str(e),
                                    'x': 0.5,
                                    'y': 0.5,
                                    'showarrow': False,
                                    'font': {'color': 'red'}
                                }]
                            }
                        })
                    elif prop == 'data':
                        return cast(T, [])
                    elif prop == 'options':
                        return cast(T, [])
                    elif prop in ['style', 'className']:
                        return cast(T, {'color': 'red'})
                    elif prop == 'disabled':
                        return cast(T, False)
                    else:
                        return cast(T, None)

            # Fallback for cases where callback info isn't available
            return cast(T, f"Error in {func.__name__}: {str(e)}")

        finally:
            # Restore the original log level
            logger.setLevel(orig_level)

    return wrapper


# Use the timer decorator from logging_config for performance monitoring
@timer(monitor_memory=True)
def measure_callback_performance(func: Callable) -> Any:
    """
    Utility function to measure callback performance using the timer
    decorator from logging_config.
    """
    return func()


def configure_callback_logger():
    """
    Configure the callback logger.
    This is now much simpler since we're using the centralized logging config.
    """
    # Get the callbacks logger that's already correctly set up
    logger = get_logger('callbacks')
    logger.setLevel(CALLBACK)

    # Ensure propagation is enabled to use root handlers
    logger.propagate = True

    return logger