import logging
import re

from typing import Dict
import pandas as pd

logger = logging.getLogger(__name__)


def is_file_within_criteria(
    filename: str,
    year_threshold: int,
    quarter_threshold: int
) -> bool:
    """
    Check if the file is within the specified year and quarter criteria.

    Args:
        filename (str): The filename to check.
        year_threshold (int): The year threshold.
        quarter_threshold (int): The quarter threshold.

    Returns:
        bool: True if the file is within the criteria, False otherwise.
    """
    match = re.search(r'(\d{4})_(\d)\.csv$', filename)
    if match:
        year, quarter = map(int, match.groups())
        is_within_criteria = (year > year_threshold) or (
            year == year_threshold and quarter > quarter_threshold
        )
        if not is_within_criteria:
            logger.debug(f'File {filename} skipped: year={year}, quarter={quarter}, '
                         f'thresholds: year>{year_threshold}, quarter>{quarter_threshold}')
        return is_within_criteria
    logger.warning(f'Filename {filename} does not match expected format (YYYY_Q.csv)')
    return False


def log_unmapped_lines(df: pd.DataFrame, mapping: Dict[str, str], filename: str = None) -> None:
    """
    Log unmapped insurance lines with enhanced tracking.
    
    Args:
        df (pd.DataFrame): The DataFrame containing insurance lines
        mapping (Dict[str, str]): Mapping dictionary for insurance lines
        filename (str, optional): Source filename for the data
    """
    unique_lines = df['insurance_line'].unique()
    unmapped_lines = [line for line in unique_lines if line not in mapping]

    if unmapped_lines:
        source_info = f" in file {filename}" if filename else ""
        formatted_unmapped_lines = [f"'{line}' (count: {df[df['insurance_line'] == line].shape[0]})"
                                  for line in unmapped_lines]
        formatted_list = '\n'.join(formatted_unmapped_lines)
        logger.critical(f'Unmapped insurance lines{source_info}:\n{formatted_list}')

        # Log detailed information about unmapped entries
        for line in unmapped_lines:
            unmapped_entries = df[df['insurance_line'] == line]
            logger.debug(f"Detailed info for unmapped line '{line}'{source_info}:")
            logger.debug(f"Years: {sorted(unmapped_entries['year'].dropna().astype(int).unique())}")
            logger.debug(f"Quarters: {sorted(unmapped_entries['quarter'].dropna().astype(int).unique())}")

            # Handle mixed type insurers safely
            insurers = unmapped_entries['insurer'].unique()
            # Convert all insurers to strings and handle NaN values
            formatted_insurers = [str(ins) if pd.notna(ins) else 'NaN' for ins in insurers]
            logger.debug(f"Insurers: {sorted(formatted_insurers)}")
    else:
        source_info = f" for {filename}" if filename else ""
        logger.info(f'All insurance lines were successfully mapped{source_info}.')