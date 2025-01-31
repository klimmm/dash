from typing import Dict, List
import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

STYLE_CONFIG = {
    'colors': {
        'primary': '#8884d8',
        'secondary': '#82ca9d',
        'positive': '#4ade80',
        'negative': '#f87171',
        'grid': 'rgb(226, 232, 240)',
        'text': {
            'primary': 'rgb(17, 24, 39)',
            'secondary': 'rgb(107, 114, 128)'
        }
    },
    'card': {
        'base': {
            'border-radius': '0.5rem',
            'border': '1px solid rgb(226, 232, 240)',
            'background-color': 'white',
            'box-shadow': '0 1px 3px 0 rgb(0 0 0 / 0.1)',
            'height': '100%'
        },
        'header': {
            'padding': '1rem 1.5rem 0.5rem',
            'border-bottom': 'none',
            'background-color': 'transparent'
        }
    }
}


def format_value(value: float, is_percent: bool = False, include_sign: bool = True) -> str:
    """Unified formatting function for numbers and percentages"""
    decimals = 2 if is_percent else 3
    formatted = f"{value:,.{decimals}f}".replace(',', ' ')
    return f"+{formatted}" if include_sign and value > 0 else formatted


def get_market_metrics(market_data: pd.DataFrame, metric: str, period: str) -> dict:
    """Extracts key market metrics from market data"""
    total_data = market_data[market_data['insurer'] == 'Весь рынок'].iloc[0]
    return {
        'volume': total_data[f"{metric}_{period}"],
        'growth': total_data[f"{metric}_{period}_q_to_q_change"],
        'concentrations': {
            level: {
                'share': market_data[market_data['insurer'] == f'Топ {level}'].iloc[0][f"{metric}_{period}_market_share"],
                'change': market_data[market_data['insurer'] == f'Топ {level}'].iloc[0][f"{metric}_{period}_market_share_q_to_q_change"]
            }
            for level in [5, 10, 20]
        }
    }


def get_market_leaders(df: pd.DataFrame, metric: str, periods: List[str]) -> dict:
    """Gets market leaders by growth rate and absolute growth"""
    growth_rate_col = f"{metric}_{periods[0]}_q_to_q_change"
    growth_rate_leader = df.nlargest(1, growth_rate_col).iloc[0]

    df = df.copy()
    df['absolute_growth'] = df[f"{metric}_{periods[0]}"] - df[f"{metric}_{periods[1]}"]
    absolute_growth_leader = df.nlargest(1, 'absolute_growth').iloc[0]

    return {
        'growth_rate': {
            'insurer': growth_rate_leader['insurer'],
            'value': growth_rate_leader[growth_rate_col]
        },
        'absolute_growth': {
            'insurer': absolute_growth_leader['insurer'],
            'value': absolute_growth_leader['absolute_growth']
        }
    }


def get_responsive_styles(container_width: int) -> Dict:
    """Calculate responsive styles based on container width"""
    # Base size calculation
    base_size = max(6, min(16, container_width / 60))
    
    return {
        'title': {
            'font-size': f'{base_size}px',
            'font-weight': '700',
            'color': STYLE_CONFIG['colors']['text']['primary']
        },
        'value': {
            'font-size': f'{base_size * 1.5}px',
            'font-weight': '700',
            'color': STYLE_CONFIG['colors']['text']['primary']
        },
        'secondary_value': {
            'font-size': f'{base_size * 1.25}px',
            'font-weight': '700',
            'color': STYLE_CONFIG['colors']['text']['primary']
        },
        'label': {
            'font-size': f'{base_size * 0.875}px',
            'color': STYLE_CONFIG['colors']['text']['secondary']
        }
    }

def create_market_cards(
    companies_data: pd.DataFrame, 
    market_data: pd.DataFrame, 
    metric: str, 
    periods: List[str],
    dimensions: Dict = None
) -> List[dbc.Card]:
    """Creates all market analysis cards with responsive sizing"""
    market_metrics = get_market_metrics(market_data, metric, periods[0])
    leaders = get_market_leaders(companies_data, metric, periods)
    
    # Get responsive styles for each card
    volume_styles = get_responsive_styles(
        dimensions.get('market-volume-card', {}).get('width', 800) if dimensions else 800
    )
    concentration_styles = get_responsive_styles(
        dimensions.get('market-concentration-card', {}).get('width', 800) if dimensions else 800
    )
    leaders_styles = get_responsive_styles(
        dimensions.get('leaders-card', {}).get('width', 800) if dimensions else 800
    )

    return [
        create_market_volume_card(market_metrics, volume_styles),
        create_concentration_card(market_metrics, concentration_styles),
        create_leaders_card(leaders, leaders_styles)
    ]

def create_market_volume_card(market_metrics: Dict, styles: Dict) -> dbc.Card:
    """Creates the market volume card with responsive styling"""
    return dbc.Card([
        dbc.CardHeader(
            html.H6("Объем рынка", className="card-title", style=styles['title']), 
            style=STYLE_CONFIG['card']['header']
        ),
        dbc.CardBody([
            html.Div(
                f"{format_value(market_metrics['volume'], False, False)} млрд ₽",
                style=styles['value']
            ),
            html.Div([
                html.I(
                    className=f"fas {'fa-arrow-up' if market_metrics['growth'] >= 0 else 'fa-arrow-down'}", 
                    style={'margin-right': '0.5rem'}
                ),
                html.Span(f"{format_value(market_metrics['growth'], True)}%")
            ], style={
                'color': STYLE_CONFIG['colors']['positive'] if market_metrics['growth'] >= 0 
                        else STYLE_CONFIG['colors']['negative'],
                'display': 'flex',
                'align-items': 'center',
                **styles['secondary_value']
            })
        ])
    ], style=STYLE_CONFIG['card']['base'])

def create_concentration_card(market_metrics: Dict, styles: Dict) -> dbc.Card:
    """Creates the market concentration card with responsive styling"""
    concentration_items = []
    for level in [5, 10, 20]:
        metrics = market_metrics['concentrations'][level]
        concentration_items.append(html.Div([
            html.Div(
                f"Топ-{level}: {format_value(metrics['share'], True, False)}%",
                style=styles['secondary_value']
            ),
            html.Div([
                html.I(
                    className=f"fas {'fa-arrow-up' if metrics['change'] >= 0 else 'fa-arrow-down'}", 
                    style={'margin-right': '0.5rem'}
                ),
                html.Span(f"{format_value(metrics['change'], True)} п.п.")
            ], style={
                'color': STYLE_CONFIG['colors']['positive'] if metrics['change'] >= 0 
                        else STYLE_CONFIG['colors']['negative'],
                'display': 'flex',
                'align-items': 'center',
                **styles['label']
            })
        ], style={'margin-bottom': '1rem'} if level != 20 else {}))

    return dbc.Card([
        dbc.CardHeader(
            html.H6("Концентрация рынка", className="card-title", style=styles['title']), 
            style=STYLE_CONFIG['card']['header']
        ),
        dbc.CardBody(concentration_items)
    ], style=STYLE_CONFIG['card']['base'])

def create_leaders_card(leaders: Dict, styles: Dict) -> dbc.Card:
    """Creates the market leaders card with responsive styling"""
    return dbc.Card([
        dbc.CardHeader(
            html.H6("Лидеры роста", className="card-title", style=styles['title']), 
            style=STYLE_CONFIG['card']['header']
        ),
        dbc.CardBody([
            # Growth Rate Leader
            html.Div([
                html.Div("По темпу роста", style=styles['label']),
                html.Div(
                    leaders['growth_rate']['insurer'],
                    style=styles['secondary_value']
                ),
                html.Div([
                    html.I(
                        className="fas fa-arrow-up",
                        style={'margin-right': '0.5rem'}
                    ),
                    html.Span(f"{format_value(leaders['growth_rate']['value'], True)}%")
                ], style={
                    'color': STYLE_CONFIG['colors']['positive'],
                    'display': 'flex',
                    'align-items': 'center',
                    **styles['label']
                })
            ], style={'margin-bottom': '1rem'}),

            # Absolute Growth Leader
            html.Div([
                html.Div("По абсолютному росту", style=styles['label']),
                html.Div(
                    leaders['absolute_growth']['insurer'],
                    style=styles['secondary_value']
                ),
                html.Div([
                    html.I(
                        className="fas fa-arrow-up",
                        style={'margin-right': '0.5rem'}
                    ),
                    html.Span(f"{format_value(leaders['absolute_growth']['value'])} млрд ₽")
                ], style={
                    'color': STYLE_CONFIG['colors']['positive'],
                    'display': 'flex',
                    'align-items': 'center',
                    **styles['label']
                })
            ])
        ])
    ], style=STYLE_CONFIG['card']['base'])