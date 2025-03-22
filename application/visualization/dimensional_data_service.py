# application/services/data_processing_service.py
import pandas as pd
import itertools


class DimensionalDataService:
    """Handles the generation of dimensional data combinations and result segmentation.

    This class is responsible for creating multi-dimensional data structures
    based on specified dimensions and segmentation criteria.

    Responsibilities:
    - Creating combinations of dimension values
    - Filtering and segmenting data by specified split columns
    - Handling dynamic insurer ordering (e.g., top-N insurers)
    - Producing formatted result dataframes with proper categorical types
    """

    def __init__(self, insurers_service):
        self.columns = insurers_service.config.columns
        self.logger = insurers_service.logger
        self.get_ordered_insurers = insurers_service.get_ordered_insurers

    def process_dimensional_data(
        self,
        processed_df,
        selected_insurers,
        ordered_lines,
        ordered_metrics,
        ordered_value_types,
        ordered_quarters,
        split_cols,
        max_combinations=5
    ):
        """Create multi-dimensional results based on insurers and dimension splits."""

        # Get ordered insurers for the initial configuration
        ordered_insurers = self.get_ordered_insurers(
            processed_df,
            selected_insurers,
            ordered_metrics)

        dimension_config = {
            self.columns.LINE: ordered_lines,
            self.columns.METRIC: ordered_metrics,
            self.columns.INSURER: ordered_insurers,
            self.columns.VALUE_TYPE: ordered_value_types,
            self.columns.YEAR_QUARTER: ordered_quarters
        }

        split_values = {col: dimension_config[col]
                        for col in split_cols
                        if col in dimension_config}
        self.logger.debug(f"split_cols {split_cols}")
        self.logger.debug(f"split_values {split_values}")
        self.logger.debug(f"selected_insurers {selected_insurers}")
        split_combinations = [
            dict(zip(split_cols, combo))
            for combo in itertools.product(*split_values.values())]
        self.logger.debug(f"split_combinations {split_combinations}")

        # Limit the number of combinations to process
        split_combinations = split_combinations[:max_combinations]
        self.logger.debug(f"Limited to {len(split_combinations)} combinations")

        result_dfs = []

        for split_combo in split_combinations:
            self.logger.debug(f"split_combo {split_combo}")

            current_split_config = dimension_config.copy()

            if selected_insurers[0].startswith('top-'):
                filtered_df = processed_df
                for col, val in split_combo.items():
                    filtered_df = filtered_df[filtered_df[col] == val]
                current_dim_insurers = self.get_ordered_insurers(
                        filtered_df, selected_insurers, ordered_metrics)
                current_split_config[self.columns.INSURER] = current_dim_insurers

            for col in split_combo.keys():
                current_split_config[col] = [split_combo[col]]

            # Create all dimension combinations for this segment
            dimension_combinations = pd.DataFrame(
                list(itertools.product(
                    *[vals for vals in current_split_config.values()])),
                columns=list(current_split_config.keys()))

            # Get existing combinations from the input dataframe for these dimensions
            existing_combos = processed_df[list(current_split_config.keys())].drop_duplicates()

            # Filter dimension_combinations to only keep existing combinations
            dimension_combinations = pd.merge(
                dimension_combinations,
                existing_combos,
                how='inner',
                on=list(current_split_config.keys())
            )

            # Merge with actual data (now using inner join since we know combinations exist)
            current_split_data = pd.merge(
                dimension_combinations,
                processed_df,
                on=list(current_split_config.keys()),
                how='inner')

            # Apply consistent formatting and sorting
            for col, vals in current_split_config.items():
                if vals is not None:
                    current_split_data[col] = current_split_data[col].astype(
                        pd.CategoricalDtype(vals, ordered=True))

            current_split_data = current_split_data.sort_values(
                by=list(current_split_config.keys()))

            # Format time periods consistently
            current_split_data[self.columns.YEAR_QUARTER] = (
                current_split_data[self.columns.YEAR_QUARTER].astype(
                    str) + 'T00:00:00').astype('category')

            result_dfs.append((current_split_data, list(split_combo.keys()), list(split_combo.values())))

        return result_dfs