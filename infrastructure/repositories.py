# infrastructure/repositories/insurance_repository.py
import pandas as pd
from typing import Tuple


class InsuranceRepository:
    def __init__(self, config):
        self.config = config

    def load_dataframes(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load and preprocess insurance datasets for forms 162 and 158.
        Returns two dataframes: df_162 and df_158
    
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing (df_158, df_162)
    
        Raises:
            Exception: If there's an error loading or processing the datasets
        """
        columns = self.config.columns
        app_config = self.config.app_config
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