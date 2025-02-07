import json
import re

from config.logging_config import get_logger
from config.main_config import INSURERS_DICTIONARY

logger = get_logger(__name__)


def map_insurer(insurer_code: str) -> str:
    # Load the insurer mapping from the JSON file
    with open(INSURERS_DICTIONARY, 'r', encoding='utf-8') as f:
        INSURER_MAPPING = {item['reg_number']: item['short_name'] for item in json.load(f)}

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
