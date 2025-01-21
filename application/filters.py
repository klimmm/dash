# application.filters

import dash_bootstrap_components as dbc
from dash import html
from application.style_config import StyleConstants
from application.create_component import FilterComponents

def create_filters() -> html.Div:
    """Create the complete filter interface with optimized structure"""
    components = FilterComponents()
    
    # Define filter configurations for cleaner creation
    filter_configs = {
        'sidebar_collapsed': [
            {
                'columns': [
                    {
                        'label': 'Отчетный квартал:',
                        'component_type': 'dropdown',
                        'component_id': 'end-quarter',
                        'label_width': 8,
                        'component_width': 4
                    },

                    
                    {
                        'label': 'Top-',
                        'component_type': 'button-group',
                        'component_id': 'top-insurers',
                        'label_width': 2,
                        'component_width': 10
                    },
                    {
                        'label': 'Кол-во периодов:',
                        'component_type': 'button-group',
                        'component_id': 'periods-data-table',
                        'label_width': 9,
                        'component_width': 3
                    },
                    {
                        'label': 'Показать',
                        'component_type': 'button-group',
                        'component_id': 'metric-toggles',
                        'label_width': 4,
                        'component_width': 8
                    },


                    {
                        'label': 'Бизнес:',
                        'component_type': 'checklist',
                        'component_id': 'premium-loss-checklist',
                        'container_id': 'premium-loss-checklist-container',
                        'label_width': 3,
                        'component_width': 9
                    },
                    {
                        'label': 'Доп. показатель:',
                        'component_type': 'dropdown',
                        'component_id': 'secondary-y-metric',
                        'label_width': 4,
                        'component_width': 8
                    }
                    
                    
                ], 'id': 'sidebar-col',                    
                'column_widths': {'xs': 6, 'sm': 6, 'md': 4}
                
            },
            {
                'columns': [],
                'id': 'sidebar-col-2'
            }
        ],


        
        'sidebar': [
            # First row with reporting controls
            {
                'columns': [

                ],
                'column_widths': {'xs': 4, 'sm': 4, 'md': 4}
            },
            # Second row with metric controls
            {
                'columns': [
                    {
                        'label': 'Отчетность:',
                        'component_type': 'button-group',
                        'component_id': 'reporting-form',
                        'label_width': 5,
                        'component_width': 7
                    },                    
                    {
                        'label': 'Тип данных:',
                        'component_type': 'button-group',
                        'component_id': 'period-type',
                        'label_width': 5,
                        'component_width': 7
                    },


                    
                ],
                'column_widths': {'xs': 6, 'sm': 6, 'md': 4}
                
            },
            # Insurer/Line switch row
            {
                'columns': [
                    {
                        'label': 'Insurer/Line',
                        'component_type': 'radioitems',
                        'component_id': 'insurer-line-switch',
                        'label_width': 2,
                        'component_width': 10
                    }
                ],
                'style': {'display': 'none'}
            },
            # Main filters row
            {
                'columns': [
                    {
                        'label': 'Страховщик:',
                        'component_type': 'dropdown',
                        'component_id': 'selected-insurers',
                        'label_width': 4,
                        'component_width': 8
                    },
                    {
                        'label': 'Вид страхования:',
                        'component_type': 'dropdown',
                        'component_id': 'insurance-line-dropdown',
                        'label_width': 4,
                        'component_width': 8
                    },
                    {
                        'label': 'Показатель:',
                        'component_type': 'dropdown',
                        'component_id': 'primary-y-metric',
                        'label_width': 4,
                        'component_width': 8
                    },

                ]
            }
        ]
    }

    def create_filter_columns(config, col_class=None):
        """Helper function to create filter columns based on configuration"""
        columns = []
        column_widths = config.get('column_widths', {'xs': 12, 'sm': 6, 'md': 6})
        
        for col_data in config['columns']:
            component = components.create_component(
                col_data['component_type'],
                col_data['component_id']
            )
            
            filter_row = components.create_filter_row(
                label_text=col_data['label'],
                component=component,
                label_width=col_data['label_width'],
                component_width=col_data['component_width'],
                component_id=col_data['component_id'],
                container_id=col_data.get('container_id')
            )
            
            column = dbc.Col(
                filter_row,
                **column_widths,
                className=col_class or StyleConstants.FILTER["MAIN"]
            )
            columns.append(column)
        
        return columns

    # Build the layout
    rows = []
    
    # Add collapsed sidebar rows
    for config in filter_configs['sidebar_collapsed']:
        row = dbc.Row(
            create_filter_columns(config),
            className=StyleConstants.SIDEBAR_COLLAPSED,
            id=config.get('id')
        )
        rows.append(row)
    
    # Add sidebar rows
    for config in filter_configs['sidebar']:
        columns = create_filter_columns(config, StyleConstants.FILTER["MAIN"])
        if 'style' in config:
            row = dbc.Row([dbc.Col(columns, xs=12, sm=6, md=6, style=config['style'])])
        else:
            row = dbc.Row(columns)
        row.className = StyleConstants.SIDEBAR
        rows.append(row)
    
    # Add period type text div
    period_type_div = html.Div(
        id="period-type-text",
        className=StyleConstants.UTILS["PERIOD_TYPE"],
        style={"display": "none"}
    )
    rows.insert(1, period_type_div)

    return html.Div(dbc.CardBody(rows))