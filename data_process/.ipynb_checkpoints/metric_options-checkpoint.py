from constants.filter_options import VALUE_METRICS_OPTIONS, AVERAGE_VALUE_METRICS_OPTIONS, RATIO_METRICS_OPTIONS, MARKET_SHARE_METRICS_OPTIONS, Q_TO_Q_CHANGE_METRICS_OPTIONS, Q_TO_Q_CHANGE_METRICS_OPTIONS_REINSURANCE, VALUE_METRICS_OPTIONS_REINSURANCE

from typing import List, Dict, Tuple


def get_metric_options(primary_y_metric: List[str], secondary_y_metric: List[str], reinsurance_tab_state: bool) -> Tuple[List[Dict], List[Dict]]:
    """
    Determines appropriate metric options based on the provided primary and secondary metrics.

    Args:
        primary_y_metric (List[str]): List of primary metric values
        secondary_y_metric (List[str]): List of secondary metric values

    Returns:
        Tuple[List[Dict], List[Dict]]: A tuple containing:
            - primary_y_metric_options: List of metric options for primary axis
            - secondary_y_metric_options: List of metric options for secondary axis

    Notes:
        - If secondary_y_metric is empty, returns all metric options except those used for primary
        - If primary_y_metric results in empty options, returns all available options for primary
        - If secondary_y_metric would result in same list as primary, returns all other options instead
    """


    if not reinsurance_tab_state:
    # Define all available options
        all_options = [
            VALUE_METRICS_OPTIONS,
            AVERAGE_VALUE_METRICS_OPTIONS,
            RATIO_METRICS_OPTIONS,
            MARKET_SHARE_METRICS_OPTIONS,
            Q_TO_Q_CHANGE_METRICS_OPTIONS
        ]

    else:
        all_options = [
            VALUE_METRICS_OPTIONS_REINSURANCE,
            Q_TO_Q_CHANGE_METRICS_OPTIONS_REINSURANCE
        ]



    def find_metric_options(metric_list: List[str]) -> List[Dict]:
        if not metric_list:
            return []

        # Check the first metric in the list to determine which options to use
        metric = metric_list[0]

        # Check each metric options list to find where the metric belongs
        for options_list in all_options:
            # Check if the metric exists in any of the options
            if any(option['value'] == metric for option in options_list):
                return options_lis

        return []  # Return empty list if no matching options found

    def get_all_other_options(exclude_options: List[Dict]) -> List[Dict]:
        """Helper function to get all options except the excluded ones"""
        combined_options = []
        for options in all_options:
            if options != exclude_options:
                combined_options.extend(options)
        return combined_options

    # Get primary metric options
    primary_y_metric_options = find_metric_options(primary_y_metric)

    # If primary options are empty, return all options for primary
    if not primary_y_metric_options:
        primary_y_metric_options = []
        for options in all_options:
            primary_y_metric_options.extend(options)

    # Handle secondary metric options
    if not secondary_y_metric:
        # If secondary_y_metric is empty, combine all options except primary
        secondary_y_metric_options = get_all_other_options(primary_y_metric_options)
    else:
        # Find the specific options for secondary metric
        secondary_y_metric_options = find_metric_options(secondary_y_metric)

        # If secondary options are from the same list as primary,
        # or if secondary options are empty,
        # return all other options instead
        if secondary_y_metric_options == primary_y_metric_options or not secondary_y_metric_options:
            secondary_y_metric_options = get_all_other_options(primary_y_metric_options)

    return primary_y_metric_options, secondary_y_metric_options