# process_files.
import re
import logging
import pandas as pd
from typing import List, Any
from tqdm import tqdm
from stage_1_config import Config
from stage_1_processors import CSVProcessor
from stage_1_utils import log_unmapped_lines, is_file_within_criteria

logger = logging.getLogger(__name__)


def combine_and_clean_data(all_data: List[pd.DataFrame], config: Config) -> pd.DataFrame:

    logger.info("Starting combine_and_clean_data function")

    final_df = pd.concat(all_data, ignore_index=True)

    final_df = final_df.reindex(columns=['insurer', 'year', 'quarter',
                                         'datatype', 'insurance_line', 'value'])

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

    final_df = (
        final_df.groupby(
            ['insurer', 'year', 'quarter', 'datatype', 'insurance_line']
        )
        ['value']
        .sum()
        .reset_index()
        .sort_values(
            ['year', 'quarter', 'datatype', 'insurance_line', 'insurer']
        )
    )

    return final_df


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


def process_files(config: Config) -> pd.DataFrame:
    all_data = []

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
        if is_file_within_criteria(filename.name, config['year_threshold'],
                                   config['quarter_threshold']):
            df = csv_processor.read_file(filename)
            df_processed = csv_processor.process_file(df, filename, config)
            if df_processed is not None:
                # Log unmapped lines for each file individually
                log_unmapped_lines(df_processed,
                                   config['insurance_lines_mapping'],
                                   filename.name)
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