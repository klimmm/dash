# process_files.
import re
import logging
import pandas as pd
from typing import Dict, List, Any
from tqdm import tqdm
from stage_1_config import Config
from stage_1_processors import CSVProcessor

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


def combine_and_clean_data(all_data: List[pd.DataFrame], config: Config) -> pd.DataFrame:

    logger.info("Starting combine_and_clean_data function")

    final_df = pd.concat(all_data, ignore_index=True)

    final_df = final_df.reindex(columns=['insurer', 'year', 'quarter', 'datatype', 'insurance_line', 'value'])

    final_df['value'] = pd.to_numeric(final_df['value'], errors='coerce')
    final_df['quarter'] = pd.to_numeric(final_df['quarter'], errors='coerce')
    final_df['year'] = pd.to_numeric(final_df['year'], errors='coerce')
    final_df = final_df.dropna(subset=['value'])
    final_df['insurer'] = final_df['insurer'].apply(format_insurer_code)

    log_unmapped_lines(final_df, config['insurance_lines_mapping'])

    final_df['insurance_line'] = final_df['insurance_line'].map(config['insurance_lines_mapping'])
    logger.debug(f"Unique values in 'insurance_line' after mapping: {final_df['insurance_line'].unique()}")

    if 'insurer' in final_df['insurance_line'].values:
        logger.warning("'insurer' found in 'insurance_line' column after cleaning")
    if 'Рег №' in final_df['insurance_line'].values:
        logger.warning("'рег №' found in 'insurance_line' column after cleaning")

    logger.info("Finished combine_and_clean_data function")

    return aggregate_and_sort_data(final_df)


def format_insurer_code(code: Any) -> str:
    if pd.isna(code):
        return code

    if code == 'all_insurers':
        return code

    try:
        return f'{int(code):04d}'
    except ValueError:
        logger.warning(f'Unable to format insurer code: {code}')
        return str(code)


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

def aggregate_and_sort_data(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(['insurer', 'year', 'quarter', 'datatype', 'insurance_line'])['value']
              .sum()
              .reset_index()
              .sort_values(['year', 'quarter', 'datatype', 'insurance_line', 'insurer']))


def process_files(config: Config) -> pd.DataFrame:
    all_data = []
    unmapped_by_file = {}  # Track unmapped lines by file

    csv_processor = CSVProcessor(
        exact_matches={'всего': 'all_lines'},
        header_replacements=config['header_replacements'],
        value_replacements=config['value_replacements']
    )

    csv_files = list(config['folder_path'].glob('*.csv'))
    total_files = len(csv_files)
    processed_files = 0
    skipped_files = 0

    for filename in tqdm(csv_files, desc='Processing files'):
        logger.info(f"Processing file: {filename}")
        if is_file_within_criteria(filename.name, config['year_threshold'], config['quarter_threshold']):
            df = csv_processor.read_file(filename)
            df_processed = csv_processor.process_file(df, filename, config)
            if df_processed is not None:
                # Log unmapped lines for each file individually
                log_unmapped_lines(df_processed, config['insurance_lines_mapping'], filename.name)
                all_data.append(df_processed)
                processed_files += 1
            else:
                logger.warning(f'No data processed for file: {filename}')
        else:
            skipped_files += 1
            logger.info(f"Skipped file: {filename}")

    logger.info(f'Total files found: {total_files}')
    logger.info(f'Files processed: {processed_files}')
    logger.info(f'Files skipped (did not meet criteria): {skipped_files}')
    logger.info(f'Files with no data: {total_files - processed_files - skipped_files}')
    
    if not all_data:
        raise ValueError('No data was processed from any file.')

    final_df = combine_and_clean_data(all_data, config)
    
    # Log final summary of all unmapped lines across all files
    logger.info("Final summary of unmapped lines across all files:")
    log_unmapped_lines(pd.concat(all_data, ignore_index=True), config['insurance_lines_mapping'])
    
    return final_df