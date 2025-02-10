import json
from typing import Dict, List, Union

from config.app_config import LINES_158_DICTIONARY, LINES_162_DICTIONARY


def map_line(line_code: Union[str, List[str]]) -> Union[str, List[str]]:
    """Map line codes to their corresponding labels.

    Args:
        line_code: Either a single line code string or a list of line code strings

    Returns:
        Either a single mapped label string or a list of mapped label strings
    """
    # Load first JSON file
    with open(LINES_162_DICTIONARY, 'r', encoding='utf-8') as f:
        insurance_data1: Dict[str, Dict[str, str]] = json.load(f)

    # Load second JSON file
    with open(LINES_158_DICTIONARY, 'r', encoding='utf-8') as f:
        insurance_data2: Dict[str, Dict[str, str]] = json.load(f)

    # Combine the two dictionaries
    combined_data: Dict[str, Dict[str, str]] = {
        **insurance_data1, **insurance_data2
    }

    # Create the mapping dictionary
    LINE_MAPPING: Dict[str, str] = {
        category: data['label'] 
        for category, data in combined_data.items()
    }

    # Handle both list and single inputs
    if isinstance(line_code, list):
        return [LINE_MAPPING.get(code, code) for code in line_code]
    return LINE_MAPPING.get(line_code, line_code)