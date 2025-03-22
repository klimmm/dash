# process_csv_first_stage.csv
import logging
import warnings
import sys

import pandas as pd
from pathlib import Path
from typing import Union

from stage_1_config import Config, get_config
from stage_1_process_files import process_files
from stage_1_process_pivot_table import process_and_melt_pivot_table
from stage_1_validate_final_data import clean_and_validate_final_data


warnings.filterwarnings(
    'ignore',
    message='Series.__getitem__ treating keys as positions is deprecated',
    category=FutureWarning
)

warnings.filterwarnings(
    'ignore',
    message='Downcasting behavior in `replace`',
    category=FutureWarning
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler('logs/log_1st_stage.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def log_dataframe_info(df: pd.DataFrame, stage: str) -> None:
    """
    Log information about the DataFrame at a specific stage of processing.

    Args:
        df (pd.DataFrame): The DataFrame to log information about.
        stage (str): The stage of processing being logged.
    """
    logger.info(f'{stage} - DataFrame info:')
    logger.info(f'Shape: {df.shape}')
    logger.info(f'Columns: {df.columns.tolist()}')
    logger.info(f'Data types:\n{df.dtypes}')
    logger.info(f'Quarter dtype: {df["quarter"].dtype}')
    logger.info(f'Unique quarter values: {sorted(df["quarter"].unique())}')
    logger.info(f'Year dtype: {df["year"].dtype}')
    logger.info(f'Unique year values: {sorted(df["year"].unique())}')


def log_summary_statistics(df: pd.DataFrame, data_type: str) -> None:
    """
    Log summary statistics of the final DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to summarize.
        data_type (str): The type of data being summarized.
    """
    logger.info(f'Summary statistics for {data_type}:')
    logger.info(f'Total number of rows: {len(df)}')
    logger.info(f'Unique insurers: {df["insurer"].nunique()}')
    logger.info(f'Years covered: {sorted(df["year"].unique())}')
    logger.info(f'Quarters covered: {sorted(df["quarter"].unique())}')
    logger.info(f'Datatypes covered: {df["datatype"].unique()}')
    #logger.info(f'Number of unique insurance lines: {df["insurance_line"].nunique()}')

    logger.info('Column data types:')
    for column in df.columns:
        logger.info(f'Column "{column}" has dtype: {df[column].dtype}')


def save_output(df: pd.DataFrame, output_file: Union[str, Path]) -> None:
    """
    Save the DataFrame to two separate CSV files based on value_type.

    Args:
        df (pd.DataFrame): The DataFrame to be saved.
        output_file (Union[str, Path]): The base path for the output files.
    """
    output_file = Path(output_file)  # Convert to Path object if it's a string

    # Split the DataFrame based on value_type
    df_net = df[df['value_type'] == 'value_net']
    df_ytd = df[df['value_type'] == 'value_ytd']

    # Create file names
    file_stem = output_file.stem
    file_suffix = output_file.suffix
    net_file = output_file.with_name(f'{file_stem}_net{file_suffix}')
    ytd_file = output_file.with_name(f'{file_stem}_ytd{file_suffix}')

    # Save the DataFrames
    df_net.to_csv(net_file, index=False)
    df_ytd.to_csv(ytd_file, index=False)

    logger.info(f'Net values output saved to {net_file}')
    logger.info(f'YTD values output saved to {ytd_file}')


def main(config: Config) -> None:
    try:
        logger.info('Starting insurance data processing...')

        final_df = process_files(config)
        logger.info(f"Data shape after process_files: {final_df.shape}")

        log_dataframe_info(final_df, 'Before processing')

        final_df = process_and_melt_pivot_table(final_df)
        logger.info(f"Data shape after pivot processing: {final_df.shape}")

        log_dataframe_info(final_df, 'After processing')

        final_df = clean_and_validate_final_data(final_df)
        logger.info(f"Data shape after cleaning: {final_df.shape}")

        if final_df.empty:
            logger.error("DataFrame is empty before saving!")
        else:
            logger.info(f"Preparing to save DataFrame with shape: {final_df.shape}")
            save_output(final_df, config['output_file'])
            logger.info("Save completed successfully")

        log_summary_statistics(final_df[final_df['value_type'] == 'value_net'], 'Net Values')
        log_summary_statistics(final_df[final_df['value_type'] == 'value_ytd'], 'YTD Values')

        logger.info('Insurance data processing completed successfully.')

    except Exception as e:
        logger.error(f'An error occurred during processing: {str(e)}')
        logger.exception('Traceback:')
        sys.exit(1)


if __name__ == '__main__':
    try:
        config = get_config()
        main(config)

    except Exception as e:
        logger.error(f'An error occurred: {str(e)}')
        logger.exception('Traceback:')
        sys.exit(1)