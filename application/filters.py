import dash_bootstrap_components as dbc
from dash import html
from typing import Any, Dict, List
import uuid
from application.button_components import (
    create_reporting_form_buttons,
    create_top_insurers_buttons,
    create_period_type_buttons,
    create_periods_data_table_buttons,
    create_metric_toggles_buttons
)
from application.dropdown_components import (
    create_end_quarter_dropdown,
    create_dynamic_insurer_container_for_layout,
    create_dynamic_insurance_line_container_for_layout,
    create_secondary_metric_dropdown,
    create_dynamic_primary_metric_container_for_layout
)
from application.checklist_components import create_business_type_checklist
from config.logging_config import get_logger
logger = get_logger(__name__)

COMPONENTS = {
    'dropdown': {
        'primary-metric': create_dynamic_primary_metric_container_for_layout,
        'selected-insurers': create_dynamic_insurer_container_for_layout,
        'insurance-line': create_dynamic_insurance_line_container_for_layout,
        'end-quarter': create_end_quarter_dropdown,
        'secondary-y-metric': create_secondary_metric_dropdown
    },
    'checklist': {
        'business-type-checklist': create_business_type_checklist
    },
    'button-group': {
        'reporting-form': create_reporting_form_buttons,
        'top-insurers': create_top_insurers_buttons,
        'period-type': create_period_type_buttons,
        'periods-data-table': create_periods_data_table_buttons,
        'metric-toggles': create_metric_toggles_buttons

    }
}

FILTER_LAYOUT = {
    'collapsed': [
        {
            'id': 'sidebar-col',
            'className': 'sidebar-col collapsed',
            'items': [
                {
                    'type': 'row-container',
                    'className': 'first-row',
                    'widths': {'xs': 6, 'sm': 6, 'md': 4},
                    'components': [
                        {
                            'label': 'Отчетный квартал:',
                            'type': 'dropdown',
                            'component_id': 'end-quarter',
                            'label_width': 8,
                            'component_width': 4,
                            'row_className': 'filter-row mb-0',
                            'wrapper_className': 'd-flex justify-content-center'
                        },
                        {
                            'label': 'Бизнес:',
                            'type': 'checklist',
                            'component_id': 'business-type-checklist',
                            'label_width': 3,
                            'component_width': 9,
                            'row_className': 'filter-row mb-0',
                            'wrapper_className': 'd-flex justify-content-center'
                        }
                    ]
                },
                {
                    'type': 'row-container',
                    'className': 'second-row',
                    'widths': {'xs': 12, 'sm': 12, 'md': 12},
                    'components': [
                        {
                            'label': 'Доп. показатель:',
                            'type': 'dropdown',
                            'component_id': 'secondary-y-metric',
                            'label_width': 4,
                            'component_width': 8,
                            'row_className': 'filter-row mb-0',
                            'wrapper_className': 'd-flex justify-content-center'
                        }
                    ]
                }
            ],
            'col_className': 'main-filter-column'
        }
    ],
    'expanded': [
        {
            'className': 'sidebar-col',
            'items': [
                {
                    'label': 'Отчетность:',
                    'type': 'button-group',
                    'component_id': 'reporting-form',
                    'label_width': 3,
                    'component_width': 9,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-center'
                },
                {
                    'label': 'Период:',
                    'type': 'button-group',
                    'component_id': 'period-type',
                    'label_width': 3,
                    'component_width': 9,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-start'
                },

            ],
            'col_className': 'top-sidebar-row',
            'widths': {'xs': 6, 'sm': 6, 'md': 6}
        },
        {
            'className': 'sidebar-col',
            'items': [
                {
                    'label': 'Страховщик:',
                    'type': 'dropdown',
                    'component_id': 'selected-insurers',
                    'label_width': 3,
                    'component_width': 9,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-center'
                },
                {
                    'label': 'Вид страхования:',
                    'type': 'dropdown',
                    'component_id': 'insurance-line',
                    'label_width': 3,
                    'component_width': 9,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-center'
                },
                {
                    'label': 'Показатель:',
                    'type': 'dropdown',
                    'component_id': 'primary-metric',
                    'label_width': 3,
                    'component_width': 9,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-center'
                }
            ],
            'col_className': 'main-filter-column',
            'widths': {'xs': 12, 'sm': 12, 'md': 12}
        },
        {
            'className': 'button-groups-row',
            'items': [
                {
                    'label': ' ',
                    'type': 'button-group',
                    'component_id': 'top-insurers',
                    'label_width': 0,
                    'component_width': 12,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-start'
                },
                {
                    'label': ' ',
                    'type': 'button-group',
                    'component_id': 'periods-data-table',
                    'label_width': 0,
                    'component_width': 12,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-center'
                },
                {
                    'label': ' ',
                    'type': 'button-group',
                    'component_id': 'metric-toggles',
                    'label_width': 0,
                    'component_width': 12,
                    'row_className': 'filter-row mb-0',
                    'wrapper_className': 'd-flex justify-content-start'
                }
            ],
            'col_className': 'main-filter-column',
            'widths': {'xs': 4, 'sm': 4, 'md': 4}
        }
    ]
}


def create_filter_row(item: Dict[str, Any]) -> html.Div:
    """Create a filter row with label and component"""
    if item['type'] == 'row-container':
        row_items = []
        for component in item['components']:
            try:
                comp = COMPONENTS[component['type']][component['component_id']]()
            except Exception as e:
                logger.error(f"Failed to create component {component['component_id']}: {str(e)}")
                return html.Div("Error creating component")

            row_items.append(dbc.Row([
                dbc.Col(
                    html.Label(component['label'], className='filter-label'),
                    width=component['label_width']
                ),
                dbc.Col(
                    comp,
                    width=component['component_width'],
                    className=component.get('wrapper_className')
                )
            ], className=component.get('row_className')))

        return dbc.Col(
            html.Div(row_items),
            **item.get('widths', {'xs': 12, 'sm': 12, 'md': 12}),
            className=item.get('className')
        )

    # Handle regular items (non row-container)
    if not item.get('label'):
        component = COMPONENTS[item['type']][item['component_id']]()
        return component

    try:
        component = COMPONENTS[item['type']][item['component_id']]()
    except Exception as e:
        logger.error(f"Failed to create component {item['component_id']}: {str(e)}")
        return html.Div("Error creating component")

    return dbc.Row([
        dbc.Col(
            html.Label(item['label'], className='filter-label'),
            width=item['label_width']
        ),
        dbc.Col(
            component,
            width=item['component_width'],
            className=item.get('wrapper_className')
        )
    ], className=item.get('row_className'))


def create_filter_section(config: List[Dict]) -> List[html.Div]:
    """Create a section of filter components"""
    trace_id = str(uuid.uuid4())[:8]
    rows = []

    for section_idx, section in enumerate(config):
        logger.debug(f"[{trace_id}] Processing section {section_idx}")

        columns = []
        for item in section['items']:
            filtered_row = create_filter_row(item)
            if item.get('type') == 'row-container':
                columns.append(filtered_row)
            else:
                columns.append(dbc.Col(
                    filtered_row,
                    **section.get('widths', {'xs': 12, 'sm': 12, 'md': 12}),
                    className=section.get('col_className')
                ))

        row_props = {
            'children': columns,
            'className': section.get('className')
        }

        if section_id := section.get('id'):
            row_props['id'] = section_id
        if section_style := section.get('style'):
            row_props['style'] = section_style

        rows.append(dbc.Row(**row_props))

    return rows


def create_filters() -> html.Div:
    """Create the complete filter interface

    Returns:
        html.Div: Complete filter interface component

    @API_STABILITY: BACKWARDS_COMPATIBLE
    """
    # Create collapsed and expanded sections
    collapsed = create_filter_section(FILTER_LAYOUT['collapsed'])
    expanded = create_filter_section(FILTER_LAYOUT['expanded'])

    # Period type indicator
    period_type = html.Div(
        id="period-type-text",
        className="period-type__text",
        style={"display": "none"}
    )

    # Combine all components
    all_components = (
        collapsed[:1] +
        [period_type] +
        collapsed[1:] +
        expanded
    )

    return html.Div(dbc.CardBody(all_components))