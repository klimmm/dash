import pandas as pd
from config.main_config import DATA_FILE_162, DATA_FILE_158

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