

def get_column_options(x_column_selected: str, series_column_selected: str, group_column_selected: str, reinsurance_tab_state: bool):
    # Define base column options based on tab state
    if not reinsurance_tab_state:
        all_columns = ['year_quarter', 'metric', 'insurer', 'linemain']
    else:
        all_columns = ['year_quarter', 'metric', 'linemain', 'reinsurance_geography', 'reinsurance_type', 'reinsurance_form']


    # X column gets all options
    x_column_options = all_columns

    # Series column gets all options except x_column_selected
    series_column_options = [col for col in all_columns if col != x_column_selected]

    # Group column gets all options except x_column_selected and series_column_selected
    group_column_options = [col for col in all_columns
                          if col != x_column_selected and col != series_column_selected]

    return x_column_options, series_column_options, group_column_options