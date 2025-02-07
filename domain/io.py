import json
import os
from typing import Dict

import pandas as pd

from config.logging_config import get_logger, timer
from config.main_config import DATA_FILE_162, DATA_FILE_158

logger = get_logger(__name__)


@timer
def load_insurance_dataframes():
    """
    Load and preprocess insurance datasets for forms 162 and 158.
    Returns two dataframes: df_162 and df_158
    """
    dtype_map = {
        'metric': 'object',
        'linemain': 'object',
        'insurer': 'object',
        'value': 'float64'
    }

    try:
        # Load 162 dataset
        df_162 = pd.read_csv(DATA_FILE_162, dtype=dtype_map)
        df_162['year_quarter'] = pd.to_datetime(df_162['year_quarter'])
        df_162['metric'] = df_162['metric'].fillna(0)

        # Load 158 dataset
        df_158 = pd.read_csv(DATA_FILE_158, dtype=dtype_map)
        df_158['year_quarter'] = pd.to_datetime(df_158['year_quarter'])
        df_158['metric'] = df_158['metric'].fillna(0)

        return df_162, df_158

    except Exception as e:
        print(f"Failed to load datasets: {str(e)}")
        raise


def load_json(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        raise

@timer
def save_df_to_csv(df, filename, max_rows=500):
    """
    Save a DataFrame to two CSV files - one with random rows and one with the first N rows.

    Args:
        df (pd.DataFrame): The DataFrame to save
        filename (str): The base name of the file to save to
        max_rows (int): The maximum number of rows to save (default: 1000)
    """
    output_dir = './outputs/intermediate'
    os.makedirs(output_dir, exist_ok=True)

    n_rows = min(max_rows, len(df))

    # Create both samples
    df_to_save = df.sample(n=n_rows)
    df_to_save_ordered = df.head(n=n_rows)

    # Generate filenames
    base_name = os.path.splitext(filename)[0]  # Remove extension if presen
    full_path_sample = os.path.join(output_dir, f"{base_name}_random.csv")
    full_path_ordered = os.path.join(output_dir, f"{base_name}_first.csv")

    # Save both files
    df_to_save.to_csv(full_path_sample, index=False)
    df_to_save_ordered.to_csv(full_path_ordered, index=False)

    logger.debug(f"Saved {n_rows} random rows to {full_path_sample}")
    logger.debug(f"Saved {n_rows} ordered rows to {full_path_ordered}")


def log_dataframe_info(df: pd.DataFrame, step_name: str):
    logger.debug(f"--- {step_name} ---")
    logger.debug(f"DataFrame shape: {df.shape}")
    logger.debug(f"Columns: {df.columns.tolist()}")
    for column in df.columns:
        unique_values = df[column].nunique()
        logger.debug(f"Unique values in '{column}': {unique_values}")
        if unique_values < 10:
            logger.debug(f"Unique values: {df[column].unique().tolist()}")
    logger.debug(f"First 5 rows:\n{df.head().to_string()}")
    logger.debug("-------------------")