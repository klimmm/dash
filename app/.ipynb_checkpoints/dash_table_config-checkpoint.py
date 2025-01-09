import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union

def generate_dash_table_config(df: pd.DataFrame, columns_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Generate Dash table configuration.

    Args:
        df (pd.DataFrame): Input DataFrame.
        columns_config (Optional[Dict[str, str]]): Configuration for columns to display.

    Returns:
        Dict[str, Any]: Dash table configuration.
    """
    from styles import (
        format_table_columns, create_conditional_style, get_data_table_styles,
        is_monetary_column, is_percentage_column, is_growth_column, COLOR_PALETTE
    )

    table_columns = [{"name": col, "id": col} for col in df.columns]
    table_data = df.to_dict('records')

    if columns_config:
        table_columns = [col for col in table_columns if col['id'] in columns_config]
        for col in table_columns:
            col['name'] = columns_config.get(col['id'], col['name'])

    table_columns = format_table_columns(table_columns, table_data)
    table_conditional_styles = create_conditional_style(df)
    table_styles = get_data_table_styles()

    style_cell_conditional = []
    style_header_conditional = []
    style_data_conditional = table_conditional_styles

    for col in table_columns:
        col_id = col['id']
        if is_monetary_column(col_id):
            style_cell_conditional.append({
                'if': {'column_id': col_id},
                'textAlign': 'right',
                'width': '120px',
            })
        elif is_percentage_column(col_id):
            style_cell_conditional.append({
                'if': {'column_id': col_id},
                'textAlign': 'center',
                'width': '100px',
            })
        elif is_growth_column(col_id) or col_id.startswith('q_to_q_change_'):
            style_cell_conditional.append({
                'if': {'column_id': col_id},
                'textAlign': 'center',
                'width': '100px',
                'backgroundColor': 'lightskyblue',
            })
            style_header_conditional.append({
                'if': {'column_id': col_id},
                'backgroundColor': COLOR_PALETTE['secondary'],
                'color': 'black',
            })
            style_data_conditional.extend([
                {
                    'if': {
                        'column_id': col_id,
                        'filter_query': f'{{{col_id}}} > 0'
                    },
                    'color': COLOR_PALETTE['success'],
                },
                {
                    'if': {
                        'column_id': col_id,
                        'filter_query': f'{{{col_id}}} < 0'
                    },
                    'color': COLOR_PALETTE['danger'],
                }
            ])
        elif col_id == 'insurer':
            style_cell_conditional.append({
                'if': {'column_id': col_id},
                'textAlign': 'left',
                'width': '200px',
            })
        elif col_id == 'N':
            style_cell_conditional.append({
                'if': {'column_id': col_id},
                'textAlign': 'center',
                'width': '60px',
            })

    return {
        'columns': table_columns,
        'data': table_data,
        'style_table': table_styles['style_table'],
        'style_cell': table_styles['style_cell'],
        'style_header': table_styles['style_header'],
        'style_data': table_styles['style_data'],
        'style_cell_conditional': style_cell_conditional,
        'style_header_conditional': style_header_conditional,
        'style_data_conditional': style_data_conditional,
        'sort_action': 'native',
        'sort_mode': 'multi',
        'filter_action': 'none',
    }

__all__ = ['generate_dash_table_config']