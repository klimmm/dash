import json
import re
from typing import Dict

from config.app_config import INSURERS_DICTIONARY
from config.logging import get_logger

logger = get_logger(__name__)


def map_insurer(insurer_code: str) -> str:
    """Map insurer codes to their corresponding names.

    Args:
        insurer_code: The insurer code to map

    Returns:
        str: The mapped insurer name or the original code if not found
    """
    # Load the insurer mapping from the JSON file
    with open(INSURERS_DICTIONARY, 'r', encoding='utf-8') as f:
        data = json.load(f)
        INSURER_MAPPING: Dict[str, str] = {
            item['reg_number']: item['short_name']
            for item in data
        }

    INSURER_MAPPING['total'] = 'Весь рынок'
    INSURER_MAPPING['others'] = 'Остальные'

    # Regular expressions to match 'top-X' and 'top-Y-benchmark' patterns
    top_pattern = re.compile(r'^top-(\d+)$')
    benchmark_pattern = re.compile(r'^top-(\d+)-benchmark$')

    # Check for 'top-X' pattern
    top_match = top_pattern.match(insurer_code)
    if top_match:
        n = top_match.group(1)
        return f'Топ {n}'

    # Check for 'top-Y-benchmark' pattern
    benchmark_match = benchmark_pattern.match(insurer_code)
    if benchmark_match:
        n = benchmark_match.group(1)
        return f'Топ {n} Бенчмарк'

    # Fallback to the existing mapping or return the original insurer_code
    return INSURER_MAPPING.get(insurer_code, insurer_code)