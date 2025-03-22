# OUTDATED



# Processing Module Documentation

The processing module is the heart of the data transformation pipeline in the application. It's responsible for filtering, transforming, aggregating, and preparing data for visualization.

## Module Structure

```
application/processing/
├── __init__.py
├── analytics_service.py
├── callbacks.py
├── filtering_service.py
├── filtering.py (consider consolidating with filtering_service.py)
├── helpers.py
└── transformations.py
```

## Key Components

### AnalyticsService

The `AnalyticsService` class is responsible for data analysis operations including ranking, formatting, and calculating aggregations.

#### Methods

##### add_rank_column
```python
def add_rank_column(self, df: pd.DataFrame) -> pd.DataFrame:
```
Adds ranking information to the data frame, including calculating ranks and rank changes for each year_quarter/line/metric combination.

**Parameters:**
- `df`: pandas DataFrame containing insurance data

**Returns:**
- DataFrame with additional rank and rank change columns

##### format_ranks
```python
def format_ranks(self, df: pd.DataFrame) -> pd.DataFrame:
```
Formats rank values for display, including handling of special values and creating formatted rank change indicators.

**Parameters:**
- `df`: pandas DataFrame with rank information

**Returns:**
- DataFrame with formatted rank values

##### add_top_n_rows
```python
def add_top_n_rows(self, df: pd.DataFrame, selected_lines: List[str]) -> pd.DataFrame:
```
Adds aggregated top-N rows to data for market comparison.

**Parameters:**
- `df`: pandas DataFrame with insurer data
- `selected_lines`: List of selected insurance lines

**Returns:**
- DataFrame with additional top-N aggregated rows

### FilteringService

The `FilteringService` class handles all data filtering operations, working with other services to apply business rules to data selection.

#### Methods

##### filter_by_lines_metrics_and_date_range
```python
def filter_by_lines_metrics_and_date_range(
    self, df: pd.DataFrame, selected_lines: List[str],
    required_metrics: List[str], start_quarter: str, end_quarter: str
) -> pd.DataFrame:
```
Filters data by selected lines, metrics and date range.

**Parameters:**
- `df`: pandas DataFrame with insurance data
- `selected_lines`: List of selected insurance lines
- `required_metrics`: List of required metrics
- `start_quarter`: Starting quarter string (YYYY-Q format)
- `end_quarter`: Ending quarter string (YYYY-Q format)

**Returns:**
- Filtered DataFrame

##### filter_by_insurer
```python
def filter_by_insurer(
    self, df: pd.DataFrame, selected_insurers: List[str],
    top_n: int, metrics: List[str]
) -> pd.DataFrame:
```
Filters data by selected insurers or top-N insurers.

**Parameters:**
- `df`: pandas DataFrame with insurance data
- `selected_insurers`: List of selected insurer IDs
- `top_n`: Number of top insurers to include (if top-N selection is active)
- `metrics`: List of metrics used for ranking

**Returns:**
- Filtered DataFrame

##### filter_by_num_periods
```python
def filter_by_num_periods(self, df: pd.DataFrame, num_periods: int) -> pd.DataFrame:
```
Filters data to include only the most recent periods.

**Parameters:**
- `df`: pandas DataFrame with insurance data
- `num_periods`: Number of most recent periods to include

**Returns:**
- Filtered DataFrame

##### filter_by_value_type
```python
def filter_by_value_type(self, df: pd.DataFrame, view_metrics_state: List[str]) -> pd.DataFrame:
```
Filters data by value type based on selected view modes.

**Parameters:**
- `df`: pandas DataFrame with insurance data
- `view_metrics_state`: List of active view modes

**Returns:**
- Filtered DataFrame

### Transformations

The transformations module contains functions for reshaping and preparing data for visualization.

#### Functions

##### split_reindex_and_sort_df
```python
def split_reindex_and_sort_df(
    df: pd.DataFrame, selected_metrics: List[str],
    selected_lines: List[str], reporting_form: str,
    split_col: List[str] = None, selected_insurers: List[str] = None,
    top_n: int = None, dimension_handlers: Dict = None
) -> List[pd.DataFrame]:
```
Splits, reindexes, and sorts data based on multiple dimensions for visualization.

This complex function:
1. Creates ordered dimension values using domain services
2. Splits data by specified columns (if any)
3. Builds a complete grid of all dimension combinations
4. Merges with original data to handle missing values
5. Applies categorical ordering for proper sorting
6. Formats ranks for display

**Parameters:**
- `df`: pandas DataFrame with insurance data
- `selected_metrics`: List of selected metrics
- `selected_lines`: List of selected insurance lines
- `reporting_form`: Reporting form identifier
- `split_col`: Columns to split data by (optional)
- `selected_insurers`: List of selected insurer IDs (optional)
- `top_n`: Number of top insurers (optional)
- `dimension_handlers`: Custom dimension handling functions (optional)

**Returns:**
- List of DataFrames split according to the specified criteria

### Helpers

The helpers module provides utility functions used throughout the processing pipeline.

#### Functions

##### get_cols
```python
def get_cols(
    index_cols: List[str], pivot_cols: List[str],
    df: pd.DataFrame = None, top_n: int = None, 
    selected_insurers: List[str] = None,
    additional_pivot: List[str] = [Columns.YEAR_QUARTER, Columns.VALUE_TYPE]
) -> Tuple[List[str], List[str], List[str]]:
```
Determines which columns to use for indexing, pivoting, and splitting in visualizations.

This function:
1. Handles special case for top-N insurer selection
2. Sorts columns by cardinality for optimal visualization
3. Determines split columns based on index and pivot columns
4. Ensures required columns are included in the proper categories

**Parameters:**
- `index_cols`: Columns to use for indexing
- `pivot_cols`: Columns to use for pivoting
- `df`: pandas DataFrame with insurance data (optional)
- `top_n`: Number of top insurers (optional)
- `selected_insurers`: List of selected insurer IDs (optional)
- `additional_pivot`: Additional columns to include in pivot (optional)

**Returns:**
- Tuple of (index_cols, pivot_cols, split_cols)

### Callbacks

The callbacks module sets up the core data processing pipeline callbacks for the Dash application.

#### Functions

##### setup_process_data
```python
def setup_process_data(
    app: dash.Dash, df_158: pd.DataFrame, df_162: pd.DataFrame,
    end_quarter_options_158: List[YearQuarterOption],
    end_quarter_options_162: List[YearQuarterOption],
    available_quarters_158: Set[YearQuarter],
    available_quarters_162: Set[YearQuarter]
) -> None:
```
Sets up the main data processing callback that transforms raw data into processed data.

This function creates a callback that:
1. Selects appropriate dataset based on reporting form
2. Calculates date ranges based on selected period
3. Processes data through a series of transformation steps
4. Updates filter state for other components
5. Converts data to records for storage

**Parameters:**
- `app`: Dash application instance
- `df_158`: DataFrame for reporting form 158
- `df_162`: DataFrame for reporting form 162
- `end_quarter_options_158`: Quarter options for form 158
- `end_quarter_options_162`: Quarter options for form 162
- `available_quarters_158`: Available quarters for form 158
- `available_quarters_162`: Available quarters for form 162

##### setup_transform_data
```python
def setup_transform_data(app: dash.Dash):
```
Sets up the callback for transforming processed data based on visualization parameters.

This function creates a callback that:
1. Takes processed data and applies additional filtering
2. Determines appropriate columns for visualization layout
3. Splits, reindexes, and sorts data for display
4. Prepares data for visualization components

**Parameters:**
- `app`: Dash application instance

**Returns:**
- List of stores required for the callback

## Data Flow

The processing module implements a data pipeline that flows as follows:

1. **Initial Data Loading**: Raw data is loaded from CSV files
2. **Processing Pipeline**:
   ```python
   df = (filtering_service.filter_by_lines_metrics_and_date_range(...)
      .pipe(period_service.calculate_period_type, ...)
      .pipe(analytics_service.add_top_n_rows, ...)
      .pipe(metrics_service.calculate_metrics, ...)
      .pipe(analytics_service.add_rank_column)
      .pipe(insurer_service.calculate_market_share)
      .pipe(metrics_service.calculate_growth, ...)
      .pipe(filtering_service.filter_by_num_periods, ...))
   ```
3. **Transformation for Visualization**:
   ```python
   df = (filtering_service.filter_by_value_type(...)
      .pipe(filtering_service.filter_by_insurer, ...))
   
   dfs = split_reindex_and_sort_df(...)
   ```

## Best Practices

When working with the processing module:

1. **Service Composition**: Use functional composition with pandas pipe for clarity
2. **Error Handling**: Validate inputs and handle edge cases
3. **Performance**: Optimize operations on large datasets
4. **Logging**: Use the logger module for debugging and performance monitoring