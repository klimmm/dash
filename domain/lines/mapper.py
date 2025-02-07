import json

from config.main_config import LINES_162_DICTIONARY, LINES_158_DICTIONARY


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