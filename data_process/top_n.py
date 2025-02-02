from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from data_process.io import save_df_to_csv
from config.logging_config import get_logger, memory_monitor

logger = get_logger(__name__)


def timer(func):
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {(end-start)*1000:.2f}ms to execute")
        return result
    return wrapper


@timer
def add_top_n_rows(df, top_n_list=[5, 10, 20]):
    """
    Performance-optimized version that still avoids SettingWithCopyWarning
    """
    # Pre-filter excluded insurers once - use loc for boolean indexing
    group_by_cols = [col for col in df.columns if col not in ['insurer', 'value']]
    filtered_df = df.loc[df['insurer'] != 'total'].copy()

    # Store the original df in the list
    dfs = [df]

    for n in top_n_list:
        if n == 999:
            continue

        # Compute ranks directly and create new DataFrame in one step
        ranked_df = filtered_df.assign(
            rank=lambda x: x.groupby(group_by_cols)['value'].rank(
                method='first', 
                ascending=False
            )
        )

        # Filter and aggregate in one step
        top_n_df = (ranked_df[ranked_df['rank'] <= n]
                   .groupby(group_by_cols, observed=True)
                   .agg({'value': 'sum'})
                   .assign(insurer=f'top-{n}')
                   .reset_index())

        dfs.append(top_n_df)

    return pd.concat(dfs, ignore_index=True)