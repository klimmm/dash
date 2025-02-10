import pandas as pd
import numpy as np
import logging

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler('logs/logs_2nd_stage.log'),
        logging.StreamHandler()
    ]
)


def log_dataframe_state(df: pd.DataFrame, stage: str):
    """Enhanced logging function to track DataFrame state at each stage"""
    logging.info(f"\n{'='*20} DataFrame State: {stage} {'='*20}")
    logging.info(f"Current shape: {df.shape}")

    if len(df) > 0:
        for col in df.columns:
            unique_vals = df[col].nunique()
            null_count = df[col].isna().sum()
            non_null_count = df[col].notna().sum()
            logging.info(f"\nColumn: {col}")
            logging.info(f"- Unique values: {unique_vals}")
            logging.info(f"- Null values: {null_count}")
            logging.info(f"- Non-null values: {non_null_count}")

            if unique_vals < 50:  # Only show all values if there aren't too many
                # Handle NA values properly
                unique_values = df[col].unique()
                # Convert to list and handle NA values
                values_list = [str(x) if not pd.isna(x) else '<NA>' for x in unique_values]
                logging.info(f"- Values: {values_list}")
    else:
        logging.warning("DataFrame is empty!")


def level_insurance_line(file_path: str) -> pd.DataFrame:
    # Load data with logging
    logging.info("Starting data processing")
    df = load_csv(file_path)
    log_dataframe_state(df, "Initial Load")

    # Date conversion
    logging.info("Converting dates")
    df['year_quarter'] = pd.to_datetime(df['year'].astype(str) + '-' + 
                                        ((df['quarter'] - 1) * 3 + 1).astype(str) + '-01')
    df = df.drop(columns=['year', 'quarter'])
    log_dataframe_state(df, "After Date Conversion")

    # Split insurance lines
    logging.info("Splitting insurance lines")
    df[['level_0', 'level_1', 'level_2', 'level_3', 'level_4', 'level_5']] = \
        df['insurance_line'].apply(split_insurance_line).tolist()
    log_dataframe_state(df, "After Splitting Insurance Lines")

    # Filter level_5
    '''logging.info("Filtering level 5")
    rows_before = len(df)
    df = df[(df['level_5'].isna())]
    df = df[(df['level_4'].isna())]
    logging.info(f"Level 5 filter removed {rows_before - len(df)} rows")
    log_dataframe_state(df, "After Level 5 Filter")'''

    # Add line type
    df['line_type'] = np.where(df['level_1'].isin(['1', '2']), 'life', 'non-life')

    # Apply filters with logging
    logging.info("Applying main filters")
    rows_before = len(df)
    df = df[~df['insurance_line'].isin(['all_lines', '9', '10', '11'])]
    df = df[~df['level_1'].isin(['9', '10', '11'])]
    logging.info(f"Main filters removed {rows_before - len(df)} rows")

    # Process insurers
    df = df[(df['insurer'] != 'all_insurers') | 
            ((df['insurance_line'] == '5') & (df['year_quarter'] >= pd.Timestamp('2021-10-01')))]
    df = df.replace({'insurer': {'all_insurers': '0000'}})

    # Value processing
    rows_before = len(df)
    df = df[(df['value'] != 0) & (df['value'].notna())]
    logging.info(f"Value filter removed {rows_before - len(df)} rows")
    df['value'] = df['value'] / 1_000_000

    # Date filter
    rows_before = len(df)
    df = df[(df['year_quarter'] <= pd.Timestamp('2024-09-01'))]
    logging.info(f"Date filter removed {rows_before - len(df)} rows")

    # Sorting and final organization
    df['sort_key'] = df['insurance_line'].apply(create_sort_key)
    df = df.sort_values(by=['year_quarter', 'datatype', 'insurer', 'sort_key'])

    # Drop all level columns and sort_key
    df = df.drop(columns=['sort_key', 'level_0', 'level_1', 'level_2', 
                         'level_3', 'level_4', 'level_5'])
    df = df.rename(columns={'insurance_line': 'linemain', 'datatype': 'metric'})
    df = df[['year_quarter', 'metric', 'line_type', 'linemain', 'insurer', 'value']]

    # Final logging and save
    logging.info(f"lines unique: {df['linemain'].unique() }")
    log_dataframe_state(df, "Final State")
    df.to_csv('intermediate_data/2nd_162_net.csv', index=False)
    logging.info("Processing completed successfully")

    return df


def load_csv(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Successfully loaded {file_path}")
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise


def split_insurance_line(line):
    if line == 'all_lines':
        return ['all_lines', pd.NA, pd.NA, pd.NA, pd.NA, pd.NA]
    parts = line.split('.')
    num_parts = len(parts)
    result = [pd.NA] * 6
    for i in range(1, num_parts + 1):
        if i == 1:
            result[i] = parts[0]
        else:
            result[i] = '.'.join(parts[:i])
    return result


def create_sort_key(line):
    if line == 'all_lines':
        return (0,) * 5
    parts = line.split('.')
    return tuple(int(part) if part.isdigit() else float('inf') for part in parts + ['0'] * (5 - len(parts)))


if __name__ == "__main__":
    file_path = 'intermediate_data/1st_162_net.csv'
    level_insurance_line(file_path)