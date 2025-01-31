import plotly.graph_objects as go
import pandas as pd
from dash import dcc
from typing import List, Tuple, Dict, Any, Literal

# Simplified style configuration using nested dict comprehension
STYLE_CONFIG = {
    'colors': {
        'primary': '#8884d8',
        'secondary': '#82ca9d',
        'positive': '#4ade80',
        'negative': '#f87171',
        'grid': 'rgb(226, 232, 240)',
        'text': {'primary': 'rgb(17, 24, 39)', 'secondary': 'rgb(107, 114, 128)'}
    },
    'font': {
        'family': 'Inter',
        'sizes': {'title': 18, 'label': 14}
    }
}

def create_axis_config(tickformat: str = ',.0f') -> Dict[str, Any]:
    """Creates consistent axis configuration"""
    return {
        'gridcolor': STYLE_CONFIG['colors']['grid'],  # Changed from STYLE to STYLE_CONFIG
        'zerolinecolor': STYLE_CONFIG['colors']['grid'],
        'showgrid': True,
        'gridwidth': 1,
        'tickfont': {'size': STYLE_CONFIG['font']['sizes']['label']},
        'tickformat': tickformat
    }

def create_responsive_layout(
    container_width: int,
    title: str = '',
    height: int = 384,
    legend_enabled: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """Creates unified responsive chart layout"""
    font_sizes = get_chart_font_sizes(container_width)
    
    layout = {
        'font_family': STYLE_CONFIG['font']['family'],
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'height': height,
        'margin': {
            'l': min(120, container_width * 0.15),  # Responsive margins
            'r': min(24, container_width * 0.03),
            't': 40,
            'b': 40
        },
        'xaxis': {
            'gridcolor': STYLE_CONFIG['colors']['grid'],
            'zerolinecolor': STYLE_CONFIG['colors']['grid'],
            'showgrid': True,
            'gridwidth': 1,
            'tickfont': {'size': font_sizes['tick_labels']},
            'titlefont': {'size': font_sizes['axis_title']},
            'tickformat': ',.0f'
        },
        'yaxis': {
            'gridcolor': STYLE_CONFIG['colors']['grid'],
            'zerolinecolor': STYLE_CONFIG['colors']['grid'],
            'showgrid': True,
            'gridwidth': 1,
            'tickfont': {'size': font_sizes['tick_labels']},
            'titlefont': {'size': font_sizes['axis_title']},
            'tickformat': ',.0f',
            'autorange': 'reversed'
        },
        'title': {
            'text': title,
            'font': {
                'family': STYLE_CONFIG['font']['family'],
                'size': font_sizes['title'],
                'color': STYLE_CONFIG['colors']['text']['primary']
            },
            'y': 0.98,
            'x': 0,
            'xanchor': 'left'
        },
        **kwargs
    }

    if legend_enabled:
        layout['legend'] = {
            'orientation': 'h',
            'yanchor': 'top',
            'y': -0.12,
            'xanchor': 'center',
            'x': 0.5,
            'font': {
                'family': STYLE_CONFIG['font']['family'],
                'size': font_sizes['legend'],
                'color': STYLE_CONFIG['colors']['text']['secondary']
            }
        }

    return layout




def create_responsive_bar_trace(
    y_data: List[str],
    x_data: List[float],
    name: str = '',
    color: str | List[str] = STYLE_CONFIG['colors']['primary'],
    width: float = 0.35,
    hovertemplate: str = '%{x:.2f}<extra></extra>',
    **kwargs
) -> go.Bar:
    """Creates a standardized horizontal bar trace with responsive sizing"""
    trace_kwargs = {
        'y': y_data,
        'x': x_data,
        'name': name,
        'orientation': 'h',
        'width': width,
        'hovertemplate': hovertemplate,
        'textposition': 'outside',
        'textfont': kwargs.pop('textfont', None)  # Allow custom text font sizing
    }

    if 'marker' in kwargs:
        kwargs['marker']['color'] = color
    else:
        kwargs['marker'] = {'color': color}

    return go.Bar(**{**trace_kwargs, **kwargs})


def get_chart_font_sizes(container_width: int) -> Dict[str, int]:
    """Calculate responsive font sizes for charts based on container width"""
    # Base size calculation
    base_size = max(6, min(16, container_width / 60))
    
    return {
        'title': int(base_size * 1.4),      # Larger for chart titles
        'axis_title': int(base_size * 1.2),  # Slightly larger for axis titles
        'tick_labels': int(base_size),       # Base size for tick labels
        'legend': int(base_size),            # Base size for legend text
        'annotations': int(base_size * 0.9)  # Slightly smaller for annotations
    }



def create_comparison_charts(
    df: pd.DataFrame,
    metric: str,
    periods: List[str],
    container_width: int = 800
) -> List[dcc.Graph]:
    """Creates responsive value and market share comparison charts"""
    font_sizes = get_chart_font_sizes(container_width)
    
    def create_chart(suffix: str, title: str, unit: str) -> dcc.Graph:
        traces = [
            create_responsive_bar_trace(
                df['insurer'],
                df[f"{metric}_{period}{suffix}"],
                period,
                STYLE_CONFIG['colors'][['primary', 'secondary'][i]],
                textfont={'size': font_sizes['tick_labels']},
                hovertemplate=f'%{{x:.2f}}{unit}<extra></extra>'
            )
            for i, period in enumerate(periods)
        ]

        fig = go.Figure(traces)
        fig.update_layout(create_responsive_layout(
            container_width=container_width,
            title=title
        ))
        return dcc.Graph(figure=fig, config={'displayModeBar': False})

    return [
        create_chart('', 'Распределение премий по компаниям', ' млрд ₽'),
        create_chart('_market_share', 'Распределение долей рынка', '%')
    ]

def create_changes_chart(
    companies_data: pd.DataFrame,
    filtered_data: pd.DataFrame,
    metric: str,
    period: str,
    container_width: int = 800
) -> go.Figure:
    """Creates responsive chart showing changes in metric and market share"""
    font_sizes = get_chart_font_sizes(container_width)

    traces = [
        create_responsive_bar_trace(
            companies_data['insurer'],
            companies_data[f"{metric}_{period}_market_share_q_to_q_change"],
            'Изменение доли (п.п.)',
            STYLE_CONFIG['colors']['secondary'],
            textfont={'size': font_sizes['tick_labels']},
            hovertemplate='%{x:.2f} п.п.<extra></extra>'
        ),
        create_responsive_bar_trace(
            filtered_data['insurer'],
            filtered_data[f"{metric}_{period}_q_to_q_change"],
            'Изменение показателя (%)',
            STYLE_CONFIG['colors']['primary'],
            textfont={'size': font_sizes['tick_labels']},
            hovertemplate='%{x:.2f}%<extra></extra>'
        )
    ]
    
    fig = go.Figure(traces)
    fig.update_layout(create_responsive_layout(
        container_width=container_width,
        title='Изменение премий и доли рынка'
    ))
    return fig

def create_growth_comparison_chart(
    df: pd.DataFrame,
    metric: str,
    period: str,
    market_growth: float,
    container_width: int = 800  # Add container width parameter
) -> go.Figure:
    """Creates chart comparing growth rates to market growth"""
    growth_col = f"{metric}_{period}_q_to_q_change"
    df = df.copy()
    df['growth_diff'] = df[growth_col] - market_growth

    font_sizes = get_chart_font_sizes(container_width)

    trace = create_responsive_bar_trace(  # Changed to create_responsive_bar_trace
        df['insurer'],
        df['growth_diff'],
        'Опережение/отставание от рынка (п.п.)',
        width=0.7,
        textfont={'size': font_sizes['tick_labels']},
        hovertemplate='%{x:.2f} п.п. (рост %{customdata:.2f}%)<extra></extra>',
        marker={'color': [
            STYLE_CONFIG['colors']['positive' if val >= 0 else 'negative']  # Changed to STYLE_CONFIG
            for val in df['growth_diff']
        ]},
        customdata=df[growth_col]
    )

    fig = go.Figure([trace])
    fig.update_layout(create_responsive_layout(  # Changed to create_responsive_layout
        container_width=container_width,
        title='Темпы роста относительно рынка',
        legend_enabled=False
    ))
    return fig

def create_contribution_charts(
    df: pd.DataFrame,
    metric: str,
    periods: List[str],
    total_growth: float,
    container_width: int = 800  # Add container width parameter
) -> Tuple[go.Figure, go.Figure]:
    """Creates charts showing contribution to market growth"""
    df = df.copy()
    df['absolute_growth'] = df[f"{metric}_{periods[0]}"] - df[f"{metric}_{periods[1]}"]
    df['growth_contribution'] = df['absolute_growth'] / total_growth * 100
    df = df.sort_values('absolute_growth', key=abs, ascending=False)

    font_sizes = get_chart_font_sizes(container_width)

    # Individual contributions chart
    contribution_trace = create_responsive_bar_trace(  # Changed to create_responsive_bar_trace
        df['insurer'],
        df['absolute_growth'],
        width=0.7,
        textfont={'size': font_sizes['tick_labels']},
        hovertemplate='%{x:.2f} млрд ₽ (%{text})<extra></extra>',
        marker={'color': [
            STYLE_CONFIG['colors']['positive' if val >= 0 else 'negative']  # Changed to STYLE_CONFIG
            for val in df['absolute_growth']
        ]},
        text=[f"{x:.1f}%" for x in df['growth_contribution']],
        textposition='outside'
    )

    fig1 = go.Figure([contribution_trace])
    fig1.update_layout(create_responsive_layout(  # Changed to create_responsive_layout
        container_width=container_width,
        title='Вклад в абсолютный рост рынка',
        legend_enabled=False
    ))

    # Growth structure chart
    positive_sum = df[df['absolute_growth'] > 0]['absolute_growth'].sum()
    negative_sum = df[df['absolute_growth'] < 0]['absolute_growth'].sum()

    structure_traces = [
        create_responsive_bar_trace(  # Changed to create_responsive_bar_trace
            ['Структура роста'],
            [value],
            name,
            STYLE_CONFIG['colors']['positive' if value > 0 else 'negative'],  # Changed to STYLE_CONFIG
            width=0.7,
            textfont={'size': font_sizes['tick_labels']},
            hovertemplate='%{x:.2f} млрд ₽<extra></extra>'
        )
        for name, value in [
            ('Положительный вклад', positive_sum),
            ('Отрицательный вклад', negative_sum)
        ]
    ]

    fig2 = go.Figure(structure_traces)
    fig2.update_layout(create_responsive_layout(  # Changed to create_responsive_layout
        container_width=container_width,
        title='Структура абсолютного роста',
        height=200,
        barmode='relative'
    ))

    return fig1, fig2