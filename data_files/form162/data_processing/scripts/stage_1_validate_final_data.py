import pandas as pd
import datetime


def clean_and_validate_final_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate the final DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to clean and validate.

    Returns:
        pd.DataFrame: The cleaned and validated DataFrame.
    """
    df = ensure_correct_data_types(df)
    df = remove_future_dates(df)
    df = sort_final_dataframe(df)
    return df


def ensure_correct_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all columns have the correct data type.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The DataFrame with corrected data types.
    """
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
    df['quarter'] = pd.to_numeric(df['quarter'], errors='coerce').astype('Int64')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df


def remove_future_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove future dates from the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The DataFrame with future dates removed.
    """
    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_quarter = (current_date.month - 1) // 3 + 1

    return df[
        ((df['year'] < current_year) |
        ((df['year'] == current_year) & (df['quarter'] <= current_quarter)))
    ]


def sort_final_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort the final DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to sort.

    Returns:
        pd.DataFrame: The sorted DataFrame.
    """
    return df.sort_values(['year', 'quarter', 'datatype', 'insurance_line', 'insurer', 'value_type'])