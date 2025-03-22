# OUTDATED



# Domain Layer Documentation

The domain layer is the heart of the application, containing the core business logic, rules, and domain-specific concepts for insurance analytics. This layer is designed following domain-driven design principles to encapsulate insurance industry knowledge and processing rules.

## Domain Structure

```
domain/
├── components/            # Domain-specific UI component logic
│   ├── __init__.py
│   ├── button_callbacks.py
│   ├── button_helpers.py
│   └── ui_configs.py
├── insurers/              # Insurance company domain logic
│   ├── __init__.py
│   ├── callbacks.py
│   └── service.py
├── lines/                 # Insurance lines (types) domain logic
│   ├── __init__.py
│   ├── callbacks.py
│   ├── components.py
│   ├── service.py
│   └── tree.py
├── metrics/               # Insurance metrics and formulas
│   ├── __init__.py
│   ├── callbacks.py
│   ├── components.py
│   ├── formulas.py
│   └── service.py
└── period/                # Time period handling
    ├── __init__.py
    └── service.py
```

## Key Domain Concepts

### Insurance Metrics

Metrics are the fundamental numerical indicators used to analyze insurance business performance. The metrics system supports several types:

1. **Base Metrics**: Directly extracted from insurance reports (premiums, losses, etc.)
2. **Calculated Metrics**: Derived from base metrics using formulas (ratios, growth, etc.)

#### Metric Definitions

Metrics are defined in `metrics/formulas.py` with a structure that includes:
- Dependencies (what other metrics are needed for calculation)
- Computation function
- Applicable reporting forms
- Visibility flag

```python
METRICS_DEFINITIONS = {
    'direct_premiums': (*raw('direct_premiums'), {'0420162'}, True),
    'net_loss_ratio': (*divide('net_losses', 'net_premiums'), set(), True),
    # ...
}
```

A set of helper functions (`raw`, `add`, `subtract`, `divide`) provide convenient ways to define metric calculations.

### Insurance Lines

Insurance lines represent different types of insurance products organized in a hierarchical structure. The lines module handles:

1. **Line Hierarchy**: Parent-child relationships between insurance lines
2. **Line Selection**: User selection with proper propagation through the hierarchy
3. **Line Ordering**: Proper ordering for display and calculation

The `Tree` class in `lines/tree.py` provides the core hierarchical structure, with operations for traversing, filtering, and manipulating the tree.

### Insurers

The insurers domain handles insurance companies data:

1. **Insurer Ranking**: Ranking companies by various metrics
2. **Market Share Calculation**: Determining each insurer's market share
3. **Top-N Selection**: Selecting top performers by chosen metrics

### Time Periods

The period domain handles time-based analysis, supporting various period types:

1. **YTD (Year-to-Date)**: Cumulative values from beginning of year to selected quarter
2. **YoY-Q (Year-over-Year Quarterly)**: Same quarter comparison across years
3. **YoY-Y (Year-over-Year Yearly)**: Annual comparison at same quarter
4. **QoQ (Quarter-over-Quarter)**: Adjacent quarters comparison
5. **MAT (Moving Annual Total)**: Rolling 12-month performance

## Domain Services

### MetricsService

The `MetricsService` handles all metrics-related operations:

#### Key Methods

##### calculate_metrics
```python
def calculate_metrics(
    self, df: pd.DataFrame, selected_metrics: List[str],
    required_metrics: List[str], reporting_form: str
) -> pd.DataFrame:
```
Calculates derived metrics based on base metrics using the formulas defined in `METRICS_DEFINITIONS`.

**Parameters:**
- `df`: DataFrame containing base metrics data
- `selected_metrics`: Metrics selected for display
- `required_metrics`: All metrics required for calculations (including dependencies)
- `reporting_form`: Reporting form identifier ('0420158' or '0420162')

**Returns:**
- DataFrame with additional calculated metrics

##### calculate_growth
```python
def calculate_growth(self, df: pd.DataFrame, num_periods: int) -> pd.DataFrame:
```
Calculates period-over-period growth metrics with appropriate capping for outliers.

**Parameters:**
- `df`: DataFrame with insurance metrics
- `num_periods`: Number of periods to include

**Returns:**
- DataFrame with additional growth metrics

##### get_required_metrics
```python
def get_required_metrics(self, selected_metrics: List[str]) -> List[str]:
```
Determines all metrics required for calculations, resolving dependencies.

**Parameters:**
- `selected_metrics`: User-selected metrics

**Returns:**
- Complete list of metrics needed for calculations

### LinesService

The `LinesService` encapsulates operations related to insurance lines:

#### Key Methods

##### get_ordered_lines
```python
def get_ordered_lines(self, selected_lines: List[str], reporting_form: str) -> List[str]:
```
Returns lines in a hierarchical order based on the tree structure.

**Parameters:**
- `selected_lines`: User-selected insurance lines
- `reporting_form`: Reporting form identifier

**Returns:**
- Ordered list of lines

##### handle_parent_child_selections
```python
def handle_parent_child_selections(
    self, selected_nodes: List[str],
    trigger_node: Optional[List[str]] = None,
    detailize: bool = False
) -> List[str]:
```
Handles selection logic when parents or children are selected/deselected.

**Parameters:**
- `selected_nodes`: Currently selected nodes
- `trigger_node`: Node that triggered the selection change
- `detailize`: Whether to replace parent selections with children

**Returns:**
- Updated selection list

### Tree

The `Tree` class in `lines/tree.py` implements the hierarchical structure for insurance lines:

#### Key Methods

##### get_descendants
```python
def get_descendants(self, node: str) -> Set[str]:
```
Gets all descendants (children, grandchildren, etc.) of a node.

##### get_ancestors
```python
def get_ancestors(self, node: str) -> Set[str]:
```
Gets all ancestors (parents, grandparents, etc.) of a node.

##### get_ordered_nodes
```python
def get_ordered_nodes(self, selected_nodes: List[str]) -> List[str]:
```
Returns nodes in hierarchical order based on the tree structure.

### InsurerService

The `InsurerService` handles insurer-related business logic:

#### Key Methods

##### get_ordered_insurers
```python
def get_ordered_insurers(
    self, df: pd.DataFrame, selected_metrics: List[str],
    selected_insurers: List[str] = None, top_n: int = None
) -> List[str]:
```
Orders insurers based on metrics and selection criteria.

**Parameters:**
- `df`: DataFrame with insurer data
- `selected_metrics`: Metrics used for ranking
- `selected_insurers`: User-selected insurers (optional)
- `top_n`: Number of top insurers to include (optional)

**Returns:**
- Ordered list of insurer IDs

##### calculate_market_share
```python
def calculate_market_share(self, df: pd.DataFrame) -> pd.DataFrame:
```
Calculates market share metrics for insurance data.

**Parameters:**
- `df`: DataFrame with insurer data

**Returns:**
- DataFrame with additional market share columns

### PeriodService

The `PeriodService` handles time period calculations and transformations:

#### Key Methods

##### calculate_period_type
```python
def calculate_period_type(
    self, df: pd.DataFrame, end_quarter: str,
    num_periods_selected: int, period_type: str
) -> pd.DataFrame:
```
Transforms data based on selected period type (YTD, YoY, QoQ, etc.).

**Parameters:**
- `df`: DataFrame with time-series data
- `end_quarter`: Ending quarter for analysis
- `num_periods_selected`: Number of periods to include
- `period_type`: Period type identifier ('ytd', 'yoy-q', 'yoy-y', 'qoq', 'mat')

**Returns:**
- Transformed DataFrame with appropriate period calculations

##### get_start_quarter
```python
def get_start_quarter(
    self, end_quarter: YearQuarter, period_type: str,
    num_periods: int, available_quarters: Set[YearQuarter]
) -> Optional[YearQuarter]:
```
Determines the starting quarter based on period type and available data.

**Parameters:**
- `end_quarter`: Target end quarter
- `period_type`: Analysis period type
- `num_periods`: Number of periods to analyze
- `available_quarters`: Set of available quarters

**Returns:**
- Starting quarter identifier or None if invalid/insufficient data

## Domain Component Logic

The `components` package contains domain-specific UI component logic:

### Button Callbacks

`button_callbacks.py` implements domain-specific button behavior:

#### Key Functions

##### setup_button_click_callbacks
```python
def setup_button_click_callbacks(
    app: dash.Dash, button_groups: Dict[str, html.Div],
    config_dict: Dict[str, Dict[str, Any]]
) -> None:
```
Initializes button click callbacks with domain-specific behavior.

##### setup_data_state_callbacks
```python
def setup_data_state_callbacks(
    app: dash.Dash, button_groups: Dict[str, html.Div],
    config_dict: Dict[str, Dict[str, Any]]
) -> None:
```
Sets up callbacks to update button states based on data changes.

### UI Configurations

`ui_configs.py` contains domain-specific configurations for UI elements:

```python
UI_ELEMENT_DOMAIN_CONFIG = {
    'button_groups': {
        'view-metrics': {
            'options': ['change', 'market-share', 'rank'],
            'multi_select': True,
            'default': DefaultValues.VIEW_METRICS
        },
        # ...
    },
    # ...
}
```

These configurations define business-specific UI behaviors like:
- Available insurance metrics groupings
- Default industry selections
- Period type options based on business needs

## Domain Callbacks

Each domain package contains `callbacks.py` that implements domain-specific Dash callbacks:

### Insurers Callbacks

```python
def setup_insurer_selection(app: dash.Dash) -> None:
```
Sets up callbacks for insurer selection, handling business rules like top-N selection.

### Lines Callbacks

```python
def setup_line_selection(app: dash.Dash) -> None:
```
Sets up callbacks for insurance line selection, handling hierarchical selection rules.

### Metrics Callbacks

```python
def setup_metric_selection(app: dash.Dash) -> None:
```
Sets up callbacks for metric selection, ensuring proper grouping and dependencies.

## Domain Layer Integration

The domain layer is designed to be independent of the presentation and application layers, with clear interfaces for integration:

1. **Service Interfaces**: Each domain package exports services with well-defined methods
2. **Callback Setup Functions**: Domain-specific callbacks are registered through setup functions
3. **Domain Models**: Types like `YearQuarter` provide strong typing for domain concepts

## Best Practices for Domain Layer Development

1. **Keep Business Logic in Domain Layer**: All insurance-specific calculations, rules, and validations should reside in the domain layer
2. **Use Domain Types**: Define and use domain-specific types (like `YearQuarter`) for strong typing
3. **Encapsulate Complex Logic**: Complex business rules should be encapsulated in appropriate service methods
4. **Follow Single Responsibility**: Each service should focus on a specific domain concept
5. **Maintain Layer Independence**: The domain layer should not depend on application or presentation layers

## Domain-Specific Validation Rules

Several business rules are enforced throughout the domain layer:

1. **Metric Dependencies**: Metrics can only be calculated if all dependencies are available
2. **Period Type Constraints**: Different period types require specific data availability
3. **Line Hierarchy Rules**: Parent-child relationships must be maintained when selecting lines
4. **Insurer Selection Rules**: Top-N selection follows specific ordering rules

## Extending the Domain Layer

### Adding New Metrics

To add a new metric:

1. Add the metric definition to `metrics/formulas.py`:
```python
'new_metric': (*divide('numerator_metric', 'denominator_metric'), set(), True),
```

2. Add metric to a group in `metrics/components.py` if needed:
```python
METRIC_GROUPS = {
    'group_name': {
        # ...
        'new_metric': {"label": "New Metric Label", "default": False},
    }
}
```

### Adding New Insurance Lines

To add new insurance lines:

1. Update the appropriate line dictionary JSON file
2. The Tree class will automatically incorporate the new lines

### Adding New Period Types

To add a new period type:

1. Add a new option to `UI_ELEMENT_DOMAIN_CONFIG['button_groups']['period-type']`
2. Implement the calculation logic in `PeriodService.calculate_period_type`
3. Add start quarter calculation in `PeriodService.get_start_quarter`