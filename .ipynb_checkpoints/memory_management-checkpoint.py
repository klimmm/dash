# memory_management.py
import gc
import weakref
from typing import Dict, List, Any
import psutil
import os
from functools import wraps
import pandas as pd
import numpy as np

class MemoryManager:
    def __init__(self):
        self._cached_data: Dict[str, weakref.ref] = {}
        self._dataframe_cache: Dict[str, pd.DataFrame] = {}
        self.memory_threshold = 0.85  # 85% memory usage threshold

    def clear_cache(self):
        """Clear all cached data and trigger garbage collection"""
        self._cached_data.clear()
        self._dataframe_cache.clear()
        gc.collect()

    def check_memory_usage(self) -> float:
        """Check current memory usage percentage"""
        process = psutil.Process(os.getpid())
        return process.memory_percent()

    def is_memory_critical(self) -> bool:
        """Check if memory usage is above threshold"""
        return self.check_memory_usage() > self.memory_threshold

    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage"""
        for col in df.columns:
            col_type = df[col].dtype

            if col_type == 'object':
                if df[col].nunique() / len(df[col]) < 0.5:  # If less than 50% unique values
                    df[col] = df[col].astype('category')

            elif col_type == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')

            elif col_type == 'int64':
                df[col] = pd.to_numeric(df[col], downcast='integer')

        return df

    def cache_dataframe(self, key: str, df: pd.DataFrame) -> pd.DataFrame:
        """Cache optimized DataFrame with memory monitoring"""
        if self.is_memory_critical():
            self.clear_cache()

        optimized_df = self.optimize_dataframe(df.copy())
        self._dataframe_cache[key] = optimized_df
        return optimized_df

    def get_cached_dataframe(self, key: str) -> pd.DataFrame:
        """Retrieve cached DataFrame"""
        return self._dataframe_cache.get(key)

memory_manager = MemoryManager()

def monitor_memory(func):
    """Decorator to monitor memory usage and clear cache if necessary"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if memory_manager.is_memory_critical():
            memory_manager.clear_cache()
            gc.collect()

        result = func(*args, **kwargs)

        # If result is DataFrame, optimize i
        if isinstance(result, pd.DataFrame):
            result = memory_manager.optimize_dataframe(result)

        return resul
    return wrapper

def chunk_processor(func):
    """Decorator to process large DataFrames in chunks"""
    @wraps(func)
    def wrapper(df, *args, **kwargs):
        if len(df) > 100000:  # Process in chunks if DataFrame is large
            chunk_size = 50000
            chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
            results = []

            for chunk in chunks:
                result = func(chunk, *args, **kwargs)
                if isinstance(result, pd.DataFrame):
                    results.append(result)

            if results:
                return pd.concat(results, ignore_index=True)
            return results

        return func(df, *args, **kwargs)
    return wrapper