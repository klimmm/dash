import dash
from dash import html, dcc, Input, Output, State, ALL, MATCH, dash_table, html, clientside_callback
import pandas as pd
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme, Symbol
import dash_bootstrap_components as dbc
from default_values import (
    DEFAULT_PREMIUM_LOSS_TYPES,
    DEFAULT_INSURER, DEFAULT_PRIMARY_METRICS, DEFAULT_SECONDARY_METRICS,
    DEFAULT_TABLE_METRIC, DEFAULT_EXPANDED_CATEGORIES, DEFAULT_CHART_TYPE, DEFAULT_SECONDARY_CHART_TYPE,
    DEFAULT_X_COL_INSURANCE, DEFAULT_SERIES_COL_INSURANCE, DEFAULT_GROUP_COL_INSURANCE,
    DEFAULT_CHECKED_CATEGORIES, DEFAULT_AGGREGATION_TYPE, DEFAULT_COMPARE_INSURER,
    DEFAULT_INSURER_REINSURANCE, DEFAULT_PRIMARY_METRICS_REINSURANCE, DEFAULT_SECONDARY_METRICS_REINSURANCE,
    DEFAULT_COMPARE_INSURER_REINSURANCE, DEFAULT_PREMIUM_LOSS_TYPES_REINSURANCE, DEFAULT_PREMIUM_LOSS_TYPES,
    DEFAULT_X_COL_REINSURANCE, DEFAULT_SERIES_COL_REINSURANCE, DEFAULT_GROUP_COL_REINSURANCE,
    DEFAULT_INSURER_TABLE, DEFAULT_COMPARE_INSURER_TABLE, DEFAULT_PRIMARY_METRICS_TABLE,
    DEFAULT_PRIMARY_METRICS_TABLE, DEFAULT_SECONDARY_METRICS_TABLE, DEFAULT_X_COL_TABLE,
    DEFAULT_SERIES_COL_TABLE, DEFAULT_GROUP_COL_TABLE, DEFAULT_PREMIUM_LOSS_TYPES_TABLE,
    DEFAULT_PRIMARY_METRICS_INWARD, DEFAULT_SECONDARY_METRICS_INWARD


)
from logging_config import get_logger, custom_profile


import logging
from logging_config import get_logger
logger = get_logger(__name__)

#@custom_profile
def setup_filter_values_callbacks(app):
    @app.callback(
        [Output('x-column', 'value'),
         Output('series-column', 'value'),
         Output('group-column', 'value'),
         Output('main-insurer', 'value'),
         Output('compare-insurers-main', 'value'),
         Output('primary-y-metric', 'value'),
         Output('secondary-y-metric', 'value'),
         Output('premium-loss-checklist', 'value'),



        ],
        [Input('show-reinsurance-chart', 'data'),
         Input('selected-categories-store', 'data'),
         Input('compare-insurers-main', 'value'),
         Input('secondary-y-metric', 'value'),
         Input('x-column', 'value'),
         Input('series-column', 'value'),
         Input('group-column', 'value'),
         Input('premium-loss-checklist', 'value'),



        ],
        [State('x-column', 'value'),
         State('series-column', 'value'),
         State('group-column', 'value'),
         State('main-insurer', 'value'),
         State('compare-insurers-main', 'value'),
         State('primary-y-metric', 'value'),
         State('secondary-y-metric', 'value'),
         State('show-data-table', 'data')



        ]
    )
    @custom_profile
    def update_filter_values(show_reinsurance_chart, selected_linemains, compare_insurers, secondary_y_metric, x_column, series_column, group_column, premium_loss_selection, x_column_state, series_column_state, group_column_state, main_insurer_state, compare_insurers_state, primary_y_metric_state, secondary_y_metric_state, show_data_table):
        """
        Update column values when switching between insurance and reinsurance tabs
        """
        ctx = dash.callback_contex
        if not ctx.triggered:
            raise PreventUpdate

        default_returns = {
            'x_column': dash.no_update,
            'series_column': dash.no_update,
            'group_column': dash.no_update,
            'main_insurer': dash.no_update,
            'compare_insurers': dash.no_update,
            'primary_y_metric': dash.no_update,
            'secondary_y_metric': dash.no_update,
            'premium_loss_selection': dash.no_update,


        }


        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"trigger_id {trigger_id}")

        logger.info(f"group_column_state {group_column_state}")
        chart_columns = [x_column, series_column, group_column]

        if trigger_id in ['compare-insurers-main', 'selected-categories-store', 'secondary-y-metric']:

            if trigger_id == 'compare-insurers-main':
                group_column = 'insurer' if 'insurer' not in chart_columns else dash.no_update
                compare_insurers = compare_insurers
                secondary_y_metric = dash.no_update


            elif trigger_id == 'selected-categories-store':
                compare_insurers = dash.no_update
                secondary_y_metric = dash.no_update

                if len(selected_linemains) > 1:
                    group_column = 'linemain' if 'linemain' not in chart_columns else dash.no_update

                else:
                    raise PreventUpdate


            elif trigger_id == 'secondary-y-metric':
                group_column = 'metric' if 'metric' not in chart_columns else dash.no_update
                #x_column = dash.no_update
                #series_column = dash.no_update
                compare_insurers = dash.no_update
                secondary_y_metric = secondary_y_metric



            default_returns.update({
                'group_column': group_column,
                'series_column': dash.no_update, #group_column_state if group_column_state != group_column else series_column_state,
                'x_column': dash.no_update, #_state if x_column_state != series_column else series_column_state if series_column_state != group_column else group_column_state,
                'compare_insurers': compare_insurers,
                'secondary_y_metric': secondary_y_metric

            })

        elif trigger_id in ['x-column', 'series-column', 'group-column']:

            if trigger_id == 'x-column':
                logger.warning(f"x_column_state {x_column_state}")
                logger.warning(f"x_column {x_column}")

                x_column = x_column
                series_column = series_column_state if series_column_state != x_column else DEFAULT_SERIES_COL_INSURANCE if DEFAULT_SERIES_COL_INSURANCE != x_column else DEFAULT_X_COL_INSURANCE
                group_column = group_column_state if group_column_state != x_column and group_column_state != series_column else DEFAULT_GROUP_COL_INSURANCE if DEFAULT_GROUP_COL_INSURANCE != x_column and DEFAULT_GROUP_COL_INSURANCE != series_column else DEFAULT_X_COL_INSURANCE if DEFAULT_X_COL_INSURANCE != series_column and DEFAULT_X_COL_INSURANCE != x_column else DEFAULT_SERIES_COL_INSURANCE

            if trigger_id == 'series-column':
                series_column = series_column
                x_column = x_column_state if x_column_state != series_column else DEFAULT_X_COL_INSURANCE if DEFAULT_X_COL_INSURANCE != series_column else DEFAULT_SERIES_COL_INSURANCE
                group_column = group_column_state if group_column_state != series_column and group_column_state != x_column else DEFAULT_GROUP_COL_INSURANCE if DEFAULT_GROUP_COL_INSURANCE != series_column and DEFAULT_GROUP_COL_INSURANCE != x_column else DEFAULT_SERIES_COL_INSURANCE if DEFAULT_SERIES_COL_INSURANCE != series_column and DEFAULT_SERIES_COL_INSURANCE != x_column else DEFAULT_X_COL_INSURANCE

            if trigger_id == 'group-column':
                group_column = group_column
                x_column = x_column_state if x_column_state != group_column else DEFAULT_X_COL_INSURANCE if DEFAULT_X_COL_INSURANCE != group_column else DEFAULT_GROUP_COL_INSURANCE
                series_column = series_column_state if series_column_state != group_column and series_column_state != x_column else DEFAULT_SERIES_COL_INSURANCE if DEFAULT_SERIES_COL_INSURANCE != group_column and DEFAULT_SERIES_COL_INSURANCE != x_column else DEFAULT_GROUP_COL_INSURANCE if DEFAULT_GROUP_COL_INSURANCE != x_column and DEFAULT_GROUP_COL_INSURANCE != group_column else DEFAULT_X_COL_INSURANCE

            default_returns.update({
                'x_column':x_column,
                'series_column': series_column,
                'group_column': group_column

            })

        elif trigger_id == 'premium-loss-checklist':
            logger.warning(f"premium_loss_selection {premium_loss_selection}")
            if 'direct' in premium_loss_selection:
                primary_y_metric = DEFAULT_PRIMARY_METRICS
                secondary_y_metric = DEFAULT_SECONDARY_METRICS
            else:
                primary_y_metric = DEFAULT_PRIMARY_METRICS_INWARD
                secondary_y_metric = DEFAULT_SECONDARY_METRICS_INWARD

            default_returns.update({
                'primary_y_metric': primary_y_metric,
                'secondary_y_metric': secondary_y_metric

            })


        elif trigger_id == 'show-reinsurance-chart':

            if show_reinsurance_chart:
                default_returns.update({
                    'x_column': DEFAULT_X_COL_REINSURANCE,
                    'series_column': DEFAULT_SERIES_COL_REINSURANCE,
                    'group_column': DEFAULT_GROUP_COL_REINSURANCE,
                    'main_insurer': DEFAULT_INSURER_REINSURANCE,
                    'compare_insurers': DEFAULT_COMPARE_INSURER_REINSURANCE,
                    'primary_y_metric': DEFAULT_PRIMARY_METRICS_REINSURANCE,
                    'secondary_y_metric': DEFAULT_SECONDARY_METRICS_REINSURANCE,
                    'premium_loss_selection': DEFAULT_PREMIUM_LOSS_TYPES_REINSURANCE

                })
            elif show_data_table:
                default_returns.update({
                    'x_column': DEFAULT_X_COL_TABLE,
                    'series_column': DEFAULT_SERIES_COL_TABLE,
                    'group_column': DEFAULT_GROUP_COL_TABLE,
                    'main_insurer': DEFAULT_INSURER_TABLE,
                    'compare_insurers': DEFAULT_COMPARE_INSURER_TABLE,
                    'primary_y_metric': DEFAULT_PRIMARY_METRICS_TABLE,
                    'secondary_y_metric': DEFAULT_SECONDARY_METRICS_TABLE,
                    'premium_loss_selection': DEFAULT_PREMIUM_LOSS_TYPES_TABLE

                })

            else:
                default_returns.update({
                    'x_column': DEFAULT_X_COL_INSURANCE,
                    'series_column': DEFAULT_SERIES_COL_INSURANCE,
                    'group_column': DEFAULT_GROUP_COL_INSURANCE,
                    'main_insurer': DEFAULT_INSURER,
                    'compare_insurers': DEFAULT_COMPARE_INSURER,
                    'primary_y_metric': DEFAULT_PRIMARY_METRICS,
                    'secondary_y_metric': DEFAULT_SECONDARY_METRICS,
                    'premium_loss_selection': DEFAULT_PREMIUM_LOSS_TYPES

                })




        else:
            raise PreventUpdate


        return list(default_returns.values())