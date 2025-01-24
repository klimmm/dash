import logging
from memory_profiler import memory_usage
from functools import wraps
from typing import Callable, Any
from enum import IntEnum
import time


class LogLevel(IntEnum):
    """Enumeration for debug levels with backwards compatibility"""
    NONE = 0
    BASIC = 1
    VERBOSE = 2


debug_level = LogLevel.NONE


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