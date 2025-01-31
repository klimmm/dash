import dash_bootstrap_components as dbc
from dash import html
from typing import Dict
from application.components.dropdown import (
    create_dynamic_insurer_container_for_layout,
    create_dynamic_primary_metric_container_for_layout,
    create_dynamic_insurance_line_container_for_layout,
    create_end_quarter_dropdown,
    create_secondary_metric_dropdown
)
from application.components.button import (
    create_reporting_form_buttons,
    create_top_insurers_buttons,
    create_period_type_buttons, 
    create_periods_data_table_buttons,
    create_metric_toggles_buttons,
    create_table_split_buttons
)
from application.components.checklist import create_business_type_checklist
from constants.style_constants import StyleConstants

FILTERS = {
    'collapsed': [
        {'label': 'Отчетный квартал:', 'label_width': 6,
         'component': create_end_quarter_dropdown},
        {'label': 'Бизнес:', 'label_width': 3,
         'component': create_business_type_checklist,
         'component_className': 'd-flex justify-content-start'
        },
        {'label': 'Доп. показатель:', 'label_width': 3,
         'component': create_secondary_metric_dropdown}
    ],
    'expanded': [
        {'label': 'Отчетность:', 'label_width': 4,
         'component': create_reporting_form_buttons},
        {'label': 'Период:', 'label_width': 1,
         'component': create_period_type_buttons,
         'component_className': 'd-flex justify-content-center'},
        {'label': 'Страховщик:', 'label_width': 3,
         'component': create_dynamic_insurer_container_for_layout},
        {'label': 'Вид страхования:', 'label_width': 3,
         'component': create_dynamic_insurance_line_container_for_layout},
        {'label': 'Показатель:', 'label_width': 3,
         'component': create_dynamic_primary_metric_container_for_layout},
        {'label': ' ', 'label_width': 12,
         'component': create_top_insurers_buttons,
         'component_className': 'd-flex justify-content-end'
         
        },
        {'label': ' ', 'label_width': 0,
         'component': create_periods_data_table_buttons,
         'component_className': 'd-flex justify-content-center'
        },
        {'label': ' ', 'label_width': 0,
         'component': create_metric_toggles_buttons,
         'component_className': 'd-flex justify-content-center'
        },
        {'label': 'Показать:', 'label_width': 4,
         'component': create_table_split_buttons,
         'component_className': 'd-flex justify-content-center'
        }        

        
    ]
}


def create_filter_component(config: Dict) -> html.Div:
    """Create a filter component with label and component in a row"""
    component = config['component']()
    return dbc.Row([
        dbc.Col(
            html.Label(config['label'], className=StyleConstants.FILTER["LABEL"]),
            xs=config['label_width'], 
            sm=config['label_width'], 
            md=config['label_width']
        ),
        dbc.Col(
            component,
            xs=12-config['label_width'], 
            sm=12-config['label_width'],
            className=config.get('component_className', StyleConstants.FLEX["CENTER"])
        )
    ])


def create_filters() -> html.Div:
    """Create the complete filter interface with responsive rows"""
    # Create filter components
    filters = {
        section: [create_filter_component(config) for config in configs]
        for section, configs in FILTERS.items()
    }

    # Period indicator
    period_indicator = html.Div(
        id="period-type-text",
        className=StyleConstants.UTILS["PERIOD_TYPE"],
        style={"display": "none"}
    )

    row1 = dbc.Row([
        dbc.Col(
            filters['collapsed'][0], 
            xs=6, sm=6, md=6, lg=6,
            className=StyleConstants.FILTER_PANEL["TWO_COL"]
        ),
        dbc.Col(
            filters['collapsed'][1], 
            xs=6, sm=6, md=6, lg=6,
            className=f'{StyleConstants.FILTER_PANEL["TWO_COL"]} {StyleConstants.SPACING["PS_3"]}'
        ),
    ], className=StyleConstants.FILTER_PANEL["ROW"])

    row2 = dbc.Row([
        dbc.Col(
            filters['collapsed'][2], 
            xs=12, sm=12, md=12, lg=12,
            className=StyleConstants.FILTER_PANEL["COL"]
        ),
    ], className=StyleConstants.FILTER_PANEL["ROW"])

    row3 = dbc.Row([
        dbc.Col(
            filters['expanded'][0], 
            xs=5, sm=5, md=5, lg=5,
            className=StyleConstants.FILTER_PANEL["TWO_COL"]
        ),
        dbc.Col(
            filters['expanded'][1], 
            xs=5, sm=5, md=5, lg=5,
            className=StyleConstants.FILTER_PANEL["TWO_COL"]
        ),
        dbc.Col(
            filters['expanded'][6], 
            xs=2, sm=2, md=2, lg=2,
            className=StyleConstants.FILTER_PANEL["THIRD_COL"]
        )

    ], className=StyleConstants.FILTER_PANEL["ROW"])

    row4 = dbc.Row([
        dbc.Col(
            filters['expanded'][3], # line
            xs=12, sm=12, md=12, lg=12, 
            className=StyleConstants.FILTER_PANEL["COL"]
        ),
    ], className=StyleConstants.FILTER_PANEL["ROW_LARGE"])

    row5 = dbc.Row([
        dbc.Col(
            filters['expanded'][4], # metric
            xs=12, sm=12, md=12, lg=12,
            className=StyleConstants.FILTER_PANEL["COL"]
        ),
    ], className=StyleConstants.FILTER_PANEL["ROW"])

    row6 = dbc.Row([
        dbc.Col(
            filters['expanded'][2], # insurer
            xs=12, sm=12, md=12, lg=12,
            className=StyleConstants.FILTER_PANEL["COL"]
        ),
    ], className=StyleConstants.FILTER_PANEL["ROW"])

    row7 = dbc.Row([
        dbc.Col(
            filters['expanded'][8], 
            xs=4, sm=4, md=4, lg=4,
            className=StyleConstants.FILTER_PANEL["THIRD_COL"]
        ),
        
        dbc.Col(
            filters['expanded'][7], 
            xs=4, sm=4, md=4, lg=4,
            className=StyleConstants.FILTER_PANEL["THIRD_COL"]
        ),
        
        dbc.Col(
            filters['expanded'][5], 
            xs=4, sm=4, md=4, lg=4,
            className=StyleConstants.FILTER_PANEL["THIRD_COL"]
        )



        
    ], className=f'{StyleConstants.FILTER_PANEL["ROW"]} {StyleConstants.SPACING["MT_3"]}')

    collapsed_section = html.Div(
        [row1, row2],
        id='sidebar-col',
        className=StyleConstants.SIDEBAR_COLLAPSED
    )


    expanded_section = [period_indicator, row3, row4, row5, row6, row7]

    return html.Div(
        dbc.CardBody([collapsed_section] + expanded_section)
    )