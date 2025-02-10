from __future__ import annotations

import logging
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, cast, Dict, List, TypeVar, Optional

import dash
from colorama import Fore, Style, init

# Initialize colorama and logging
init(autoreset=True)
CALLBACK = 25
logging.addLevelName(CALLBACK, 'CALLBACK')

T = TypeVar('T')


# Custom formatter for callbacks
class CallbackFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if getattr(record, 'is_callback', False):
            return str(record.msg)
        return super().format(record)


# Configure logger with custom formatter
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(CallbackFormatter())
logger.addHandler(handler)
logger.propagate = False  # Prevent double logging


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

    def reset_sequence(self) -> None:
        self.current_sequence = []
        self.last_process_ui_time = datetime.now()
        self.total_time = 0.0

    def add_execution(self, name: str, execution_time: float) -> None:
        current_time = datetime.now()
        execution = CallbackExecution(name, execution_time, current_time)

        self.current_sequence.append(execution)
        self.total_time += execution_time

        if name == 'process_ui':
            # Log summary and reset after process_ui
            logger.log(CALLBACK,
                       self._format_sequence_summary(),
                       extra={'is_callback': True}
                      )
            self.reset_sequence()

    def _format_sequence_summary(self) -> str:
        callbacks_str = ', '.join(f"{c.name}:{c.execution_time:.2f}ms"
                                  for c in self.current_sequence)
        return (f"{Fore.BLUE}Sequence Summary | "
                f"Total Time: {self.total_time:.2f}ms | "
                f"Callbacks: {len(self.current_sequence)} | "
                f"Sequence: [{callbacks_str}]{Style.RESET_ALL}")


# Global tracker instance
callback_tracker = CallbackTracker()


def _get_context(ctx: dash.callback_context) -> Dict[str, Any]:
    """Extract essential callback context."""
    trigger_info: Dict[str, Any] = (
        ctx.triggered and ctx.triggered[0][
         'prop_id'] != '.' and ctx.triggered[0] or
        {'prop_id': list(ctx.inputs.keys())[0],
         'value': list(ctx.inputs.values())[0]} if ctx.inputs else
        {'prop_id': 'initial_load', 'value': None})

    return {
        'trigger': trigger_info['prop_id'].split('.')[0],
        'value': trigger_info['value'],
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'caller': f"{traceback.extract_stack()[-2].filename}:{traceback.extract_stack()[-2].lineno}",
        'outputs': [str(o) for o in getattr(ctx, 'outputs_list', [])],
        'no_updates': []
    }


def _format_message(time_ms: float, ctx: Dict[str, Any], name: str,
                    result: Optional[Any] = None,
                    error: Optional[Exception] = None) -> str:
    """Format callback log message."""
    DEFAULT = Fore.LIGHTBLACK_EX
    parts = [
        f"{DEFAULT if name == 'process_ui' else DEFAULT}Callback:{name}{Style.RESET_ALL}",
        f"{DEFAULT if name == 'process_ui' else DEFAULT}Execution: {time_ms:.2f}ms{Style.RESET_ALL}"
    ]

    # Add sequence timing info
    if name != 'process_ui':
        parts.append(f"{DEFAULT}Sequence Total: {callback_tracker.total_time:.2f}ms{Style.RESET_ALL}")

    # Status handling
    if isinstance(error, dash.exceptions.PreventUpdate):
        parts.extend([
            f"{DEFAULT}Status: {Fore.LIGHTBLUE_EX}Prevented{Style.RESET_ALL}",
            f"{DEFAULT}Reason: Update prevented{Style.RESET_ALL}"
        ])
    elif error:
        parts.extend([
            f"{DEFAULT}Status: {Fore.RED}Error{Style.RESET_ALL}",
            f"Error: {str(error)}{Style.RESET_ALL}"
        ])
    else:
        parts.append(f"{DEFAULT}Status: Completed{Style.RESET_ALL}")

    # Context info
    parts.extend([
        f"{DEFAULT}Time: {ctx['time']}{Style.RESET_ALL}",
        f"{DEFAULT}Trigger: {ctx['trigger']}{Style.RESET_ALL}",
        f"{DEFAULT}Outputs: [{', '.join(ctx['outputs'])}]{Style.RESET_ALL}"
    ])

    return ' | '.join(parts)


def log_callback(func: Callable[..., T]) -> Callable[..., T]:
    """Log callback execution with error handling."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        ctx = _get_context(dash.callback_context)
        start = time.time()
        logger = logging.getLogger(__name__)
        orig_level = logger.level
        logger.setLevel(CALLBACK)

        try:
            result = func(*args, **kwargs)
            time_ms = (time.time() - start) * 1000

            # Track callback execution
            msg = _format_message(time_ms, ctx, func.__name__, result=result)
            logger.log(CALLBACK, msg, extra={'is_callback': True})

            callback_tracker.add_execution(func.__name__, time_ms)

            if time_ms > 1000:
                logger.warning(
                    f"Slow callback: {func.__name__} took {time_ms:.2f}ms",
                    extra={'is_callback': True})
            return result

        except Exception as e:
            time_ms = (time.time() - start) * 1000
            msg = _format_message(time_ms, ctx, func.__name__, error=e)
            level = CALLBACK if isinstance(
                e, dash.exceptions.PreventUpdate) else logging.ERROR
            logger.log(level, msg, extra={'is_callback': True})
            raise

        finally:
            logger.setLevel(orig_level)

    return wrapper


def error_handler(func: Callable[..., T]) -> Callable[..., T]:
    """Handle callback errors gracefully."""
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