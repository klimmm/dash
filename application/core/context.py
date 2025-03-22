class ProcessingContext:
    """Manages all state and data for the processing pipeline.

    Centralizes data frames, processing parameters, and results in a single context
    object to simplify state management and provide a clear API for data access.
    """

    def __init__(self, config):
        # Configuration
        self.config = config
        self.columns = config.columns
        self.default_values = config.default_values

        # Data frames
        self.df_158 = None
        self.df_162 = None
        self.processed_df = None

        # Processing parameters
        self.end_q = self.default_values.END_QUARTER
        self.period_type = self.default_values.PERIOD_TYPE
        self.num_periods = self.default_values.NUMBER_OF_PERIODS
        self.lines = self.default_values.LINES
        self.metrics = self.default_values.METRICS
        self.value_types = self.default_values.VALUE_TYPES
        self.reporting_form = self.default_values.REPORTING_FORM
        self.insurers = self.default_values.INSURERS

        # Visualization parameters
        self.index_cols = self.default_values.INDEX_COL
        self.pivot_cols = self.default_values.PIVOT_COL
        self.split_cols = self.default_values.SPLIT_COLS

        # Results
        self.quarters = []
        self.filtered_quarters = []
        self.result_dfs = []

        self.view_mode = self.default_values.VIEW_MODE
        self.view_metrics = self.default_values.VIEW_METRICS
        self.top_insurers = []
        self.updated_trigger = []

    def set_dataframes(self, df_158, df_162):
        """Set source dataframes."""
        self.df_158, self.df_162 = df_158, df_162

    def get_dataframe(self, reporting_form):
        """Get appropriate dataframe based on form."""
        return self.df_162 if reporting_form == '0420162' else self.df_158

    def update_state(self, **kwargs):
        """Universal state setter for any combination of state properties.

        Only updates attributes if the provided value is not None.

        Args:
            **kwargs: Any state property and value to set

        Returns:
            The processed_df if provided, to maintain pipeline chaining
        """
        # Store original dataframe to return at the end
        return_df = None
        if 'processed_df' in kwargs and kwargs['processed_df'] is not None:
            return_df = kwargs['processed_df']
            if self.columns.YEAR_QUARTER in return_df.columns:
                self.quarters = sorted(return_df[self.columns.YEAR_QUARTER].unique(), reverse=True)

        # Handle dataframe for filtered quarters
        if 'filtered_quarters_df' in kwargs and kwargs['filtered_quarters_df'] is not None:
            df = kwargs.pop('filtered_quarters_df')  # Remove from kwargs to avoid setting as attribute
            return_df = df  # Save for returning to maintain pipeline
            if self.columns.YEAR_QUARTER in df.columns:
                self.filtered_quarters = sorted(df[self.columns.YEAR_QUARTER].unique(), reverse=True)

        # Set all provided attributes, but only if they're not None
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
            elif not hasattr(self, key):
                raise AttributeError(f"ProcessingContext has no attribute '{key}'")

        # Always return the DataFrame if one was provided, to maintain the pipeline
        return return_df

    def is_processing_ready(self):
        """Check if processing data is ready."""
        return self.processed_df is not None

    def is_visualization_ready(self):
        """Check if visualization data is ready."""
        return len(self.result_dfs) > 0