import json
import os
import re
from typing import Dict, Tuple

import pandas as pd

from infrastructure.logger import logger, timer


@timer
def load_insurance_dataframes(config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and preprocess insurance datasets for forms 162 and 158.
    Returns two dataframes: df_162 and df_158

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing (df_158, df_162)

    Raises:
        Exception: If there's an error loading or processing the datasets
    """
    columns = config.columns
    app_config = config.app_config
    dtype_map = {
        columns.METRIC: 'object',
        'linemain': 'object',
        columns.LINE: 'object',
        columns.INSURER: 'object',
        columns.VALUE: 'float64'
    }

    try:
        # Load 158 dataset
        df_158 = pd.read_csv(app_config.DATA_FILE_158, dtype=dtype_map)
        df_158[columns.YEAR_QUARTER] = pd.to_datetime(df_158[columns.YEAR_QUARTER])
        df_158[columns.METRIC] = df_158[columns.METRIC].fillna(0)
        # Rename linemain to line if present
        if 'linemain' in df_158.columns:
            df_158 = df_158.rename(columns={'linemain': columns.LINE})

        # Load 162 dataset
        df_162 = pd.read_csv(app_config.DATA_FILE_162, dtype=dtype_map)
        df_162[columns.YEAR_QUARTER] = pd.to_datetime(df_162[columns.YEAR_QUARTER])
        df_162[columns.METRIC] = df_162[columns.METRIC].fillna(0)
        return df_158, df_162
    except Exception as e:
        print(f"Failed to load datasets: {str(e)}")
        raise


def load_json(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data: Dict = json.load(f)
        logger.debug(f"Successfully loaded {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        raise


# @timer
def save_df_to_csv(df: pd.DataFrame, filename: str, AppConfig, max_rows: int = 1000) -> None:
    """
    Save a DataFrame to CSV file with the first N rows, handling special characters in filenames.
    Args:
        df (pd.DataFrame): The DataFrame to save
        filename (str): The base name of the file to save to
        max_rows (int): The maximum number of rows to save (default: 1000)
    """
    def sanitize_filename(name: str) -> str:
        """Sanitize filename by replacing Cyrillic and special characters."""
        transliteration = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        # Convert to lowercase and transliterate
        name = name.lower()
        for cyr, lat in transliteration.items():
            name = name.replace(cyr, lat)
        # Replace spaces and special characters with underscores
        return re.sub(r'[^\w\-_.]', '_', name)

    output_dir = AppConfig.OUTPUT_CSV_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize filename
    base_name = os.path.splitext(filename)[0]  # Remove extension if present
    safe_name = sanitize_filename(base_name)

    # Prepare data
    n_rows = min(max_rows, len(df))
    df_to_save_ordered = df.head(n=n_rows)

    # Generate safe filepath
    full_path_ordered = os.path.join(output_dir, f"{safe_name}.csv")

    # Save file
    df_to_save_ordered.to_csv(full_path_ordered, index=False)
    logger.debug(f"Saved {n_rows} ordered rows to {full_path_ordered}")


def log_dataframe_info(df: pd.DataFrame, step_name: str) -> None:
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