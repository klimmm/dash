from functools import lru_cache
from typing import Dict, List
import pandas as pd

from config.logging import get_logger
from core.insurers.mapper import map_insurer

logger = get_logger(__name__)

EXCLUDED_INSURERS = frozenset(['top-5', 'top-10', 'top-20', 'total'])


@lru_cache(maxsize=1024)
def cached_map_insurer(insurer: str) -> str:
    return map_insurer(insurer)


def get_insurer_options(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate insurer options for UI."""
    value_sums = df.groupby('insurer')['value'].sum()
    insurers = value_sums.sort_values(ascending=False).index.tolist()
    return [{'label': cached_map_insurer(ins), 'value': ins}
            for ins in insurers if ins not in EXCLUDED_INSURERS]