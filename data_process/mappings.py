import json
import re
from config.logging_config import get_logger
from config.main_config import (
    INSURERS_DICTIONARY,
    LINES_162_DICTIONARY,
    LINES_158_DICTIONARY
    )

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


def map_line(line_code):
    # Load first JSON file
    with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as f:
        insurance_data1 = json.load(f)

    # Load second JSON file
    with open(LINES_158_DICTIONARY, 'r', encoding='utf-8') as f:
        insurance_data2 = json.load(f)

    # Combine the two dictionaries
    # If there are duplicate keys, the second file will override the firs
    combined_data = {**insurance_data1, **insurance_data2}

    # Create the mapping dictionary
    LINE_MAPPING = {category: data['label'] for category, data in combined_data.items()}

    # Handle both list and single inputs
    if isinstance(line_code, list):
        return [LINE_MAPPING.get(code, code) for code in line_code]

    return LINE_MAPPING.get(line_code, line_code)