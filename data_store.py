import time
from functools import lru_cache
import pandas as pd

from application import (
    DATA_FILE_158, DATA_FILE_162,
    DEFAULT_REPORTING_FORM, get_logger,
    map_insurer
)

# Initialize logging
logger = get_logger(__name__)

class InsuranceDataStore:
    """Manages loading, preprocessing, and caching of insurance datasets and their options"""

    def __init__(self):
        logger.info("Initializing InsuranceDataStore...")
        self._dtype_map = {
            'datatypec': 'object',
            'linemain': 'object',
            'insurer': 'object',
            'value': 'float64'
        }
        self._load_datasets()
        self._initialize_options()

    def _load_datasets(self):
        """Load and preprocess all datasets"""
        self.datasets = {}
        for form_id, file_path in [('162', DATA_FILE_162), ('158', DATA_FILE_158)]:
            start_time = time.time()
            logger.info(f"Loading dataset {form_id}...")

            try:
                df = pd.read_csv(file_path, dtype=self._dtype_map)
                df['year_quarter'] = pd.to_datetime(df['year_quarter'])
                df['metric'] = df['metric'].fillna(0)
                self.datasets[form_id] = df.sort_values('year_quarter', ascending=True)
                logger.debug(f"Dataset {form_id} loaded in {time.time() - start_time:.2f}s")
            except Exception as e:
                logger.error(f"Failed to load dataset {form_id}: {str(e)}")
                raise

    def _initialize_options(self):
        """Initialize quarter and insurer selection options"""
        start_time = time.time()

        self.quarter_options = {}
        self.insurer_options = {}

        for form_id in self.datasets:
            df = self.datasets[form_id]
            form_name = f'0420{form_id}'

            # Quarter options
            periods = pd.PeriodIndex(df['year_quarter'].dt.to_period('Q')).unique()
            self.quarter_options[form_name] = [
                {'label': p.strftime('%YQ%q'), 'value': p.strftime('%YQ%q')}
                for p in periods
            ]

            # Insurer options
            metrics = ['direct_premiums', 'inward_premiums'] if form_id == '162' else ['total_premiums']
            latest_data = df[
                (df['metric'].isin(metrics)) &
                (df['linemain'] == 'все линии') &
                (df['year_quarter'] == df['year_quarter'].max())
            ]

            pivot = latest_data.pivot_table(
                index='insurer',
                columns='metric',
                values='value',
                aggfunc='sum',
                fill_value=0
            )

            if form_id == '162':
                pivot['total_premiums'] = pivot['direct_premiums'] + pivot['inward_premiums']

            sorted_insurers = pivot.sort_values('total_premiums', ascending=False).index
            self.insurer_options[form_name] = [
                {'label': map_insurer(insurer), 'value': insurer}
                for insurer in sorted_insurers
            ]

        # Set initial options
        self.initial_quarter_options = self.quarter_options[DEFAULT_REPORTING_FORM]
        self.initial_insurer_options = self.insurer_options[DEFAULT_REPORTING_FORM]

        logger.debug(f"Options initialized in {time.time() - start_time:.2f}s")

    @lru_cache(maxsize=2)
    def get_dataframe(self, reporting_form: str) -> pd.DataFrame:
        """Get cached dataframe by reporting form"""
        key = reporting_form[-3:]
        return self.datasets[key].copy()