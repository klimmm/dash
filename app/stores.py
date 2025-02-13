from typing import List

from dash import dcc, html  # type: ignore

from config.default_values import DEFAULT_BUTTON_VALUES, DEFAULT_CHECKED_LINES
from config.logging import get_logger

logger = get_logger(__name__)


def create_stores() -> List[html.Div]:
    """Create store components for app state management."""
    return [
        dcc.Store(id='filter-state-store', storage_type='memory'),
        dcc.Store(id='filtered-insurers-data-store', storage_type='memory'),
        dcc.Store(id='metrics-store', data=[], storage_type='memory'),
        dcc.Store(id='nodes-expansion-state',
                  data={'states': {}}, storage_type='memory'),
        dcc.Store(id='periods-data-table-selected',
                  data=DEFAULT_BUTTON_VALUES['periods'],
                  storage_type='memory'),
        dcc.Store(id='period-type-selected',
                  data=DEFAULT_BUTTON_VALUES['period_type'],
                  storage_type='memory'),
        dcc.Store(id='processed-data-store', storage_type='memory'),
        dcc.Store(id='reporting-form-selected',
                  data=DEFAULT_BUTTON_VALUES['reporting_form'],
                  storage_type='memory'),
        dcc.Store(id='selected-insurers-store', storage_type='memory'),
        dcc.Store(id='selected-lines-store',
                  data=DEFAULT_CHECKED_LINES, storage_type='memory'),
        dcc.Store(id='table-split-mode-selected',
                  data=DEFAULT_BUTTON_VALUES['split_mode'],
                  storage_type='memory'),
        dcc.Store(id='pivot-column-selected',
                  data=DEFAULT_BUTTON_VALUES['pivot_column'],
                  storage_type='memory'),
        dcc.Store(id='view-metrics-selected',
                  data=DEFAULT_BUTTON_VALUES['view_metrics'],
                  storage_type='memory'),
        dcc.Store(id='top-insurers-selected',
                  data=DEFAULT_BUTTON_VALUES['top_n'],
                  storage_type='memory')
        
    ]

