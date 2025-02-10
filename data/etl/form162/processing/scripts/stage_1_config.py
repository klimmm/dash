import logging
import json
import re
import os

from pathlib import Path
from typing import Dict, List, Any, TypedDict


logger = logging.getLogger(__name__)


def check_required_files(files: List[str]) -> None:
    """
    Check if required files exist.

    Args:
        files (List[str]): List of file paths to check.

    Raises:
        FileNotFoundError: If any of the required files are not found.
    """
    for file in files:
        if not os.path.exists(file):
            raise FileNotFoundError(f'Required file {file} not found.')


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        Dict[str, Any]: The contents of the JSON file as a dictionary.

    Raises:
        FileNotFoundError: If the specified file is not found.
        json.JSONDecodeError: If there's an error decoding the JSON file.
    """
    check_required_files([file_path])
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as json_error:
        logger.error(f'Error decoding JSON file {file_path}: {str(json_error)}')
        raise


def standardize_value(value: Any, value_replacements: Dict[str, str]) -> str:
    """
    Standardize and clean string values.
    Args:
        value (Any): The value to be standardized.
        value_replacements (Dict[str, str]): Dictionary of replacement patterns.
    Returns:
        str: The standardized and cleaned string value.
    """
    try:
        value_str = str(value).lower()
        # Remove 'Unnamed: X' patterns
        value_str = re.sub(
            r'\bUnnamed(?:\s*:\s*\d+)?\b', 
            '', 
            value_str, 
            flags=re.IGNORECASE
        )
        # Remove specific words and characters
        value_str = value_str.replace('единица', '')
        value_str = value_str.replace('nan', '')
        value_str = value_str.translate(str.maketrans('', '', '*«»-,():"'))
        value_str = ' '.join(value_str.split())

        # Remove all trailing digits and spaces
        value_str = re.sub(r'\s*\d+(\s+\d+)*$', '', value_str)

        # Apply replacements from JSON file
        for old, new in value_replacements.items():
            value_str = value_str.replace(old, new)

        return value_str.strip()

    except Exception as error:
        logger.warning(f'Error in standardize_value: {str(error)}')
        return str(value)


def standardize_dict_keys(d: Dict[str, Any],
                          value_replacements: Dict[str, str]) -> Dict[str, Any]:
    """
    Standardize all keys in the given dictionary.
    """
    return {standardize_value(k, value_replacements): v for k, v in d.items()}


class Config(TypedDict):
    folder_path: Path
    output_file: Path
    year_threshold: int
    quarter_threshold: int
    datatype_mapping: Dict[str, str]
    value_replacements: Dict[str, str]
    header_replacements: Dict[str, str]
    insurance_lines_mapping: Dict[str, str]


# Load all JSON files first
value_replacements = load_json_file('mapping/value_replacements.json')
header_replacements = load_json_file('mapping/header_replacements.json')
raw_insurance_lines_mapping = load_json_file('mapping/preprocessed_insurance_lines_mapping.json')
insurance_lines_mapping = standardize_dict_keys(raw_insurance_lines_mapping, value_replacements)

# Default configuration values
config = Config(
    folder_path=Path('../scraping/csv_files'),
    output_file=Path('intermediate_data/1st_162.csv'),
    year_threshold=2017,
    quarter_threshold=4,
    datatype_mapping=load_json_file('mapping/datatype_mapping.json'),
    value_replacements=value_replacements,
    header_replacements=header_replacements,
    insurance_lines_mapping=insurance_lines_mapping
)


def get_config() -> Dict[str, Any]:
    """
    Return the configuration as a dictionary.
    """
    return {
        'folder_path': config['folder_path'],
        'output_file': config['output_file'],
        'year_threshold': config['year_threshold'],
        'quarter_threshold': config['quarter_threshold'],
        'datatype_mapping': config['datatype_mapping'],
        'value_replacements': config['value_replacements'],
        'header_replacements': config['header_replacements'],
        'insurance_lines_mapping': config['insurance_lines_mapping']
    }