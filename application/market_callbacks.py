import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import html, dcc
from typing import Dict, List, Tuple, Union
from data_process.data_utils import map_insurer
from application.market_cards import create_market_cards, format_value
from application.market_analysis_component import (
    create_comparison_charts,
    create_changes_chart,
    create_growth_comparison_chart,
    create_contribution_charts
)
from data_process.table_data import table_data_pivot

from config.logging_config import get_logger, track_callback, track_callback_end

logger = get_logger(__name__)


# Consolidated style configuration
STYLE_CONFIG = {
    'colors': {
        'negative': '#f87171',
        'text_secondary': 'rgb(107, 114, 128)'
    },
    'card_base': {
        'border-radius': '0.5rem',
        'border': '1px solid rgb(226, 232, 240)',
        'background-color': 'white',
        'box-shadow': '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        'height': '100%'
    },
    'font': {
        'family': 'Inter',
        'sizes': {'title': 18, 'label': 14}
    }
}

def get_chart_font_sizes(container_width: int) -> Dict[str, int]:
    """Calculate responsive font sizes for charts based on container width"""
    # Base size calculation
    base_size = max(6, min(16, container_width / 60))
    
    sizes = {
        'title': int(base_size * 1.4),      
        'axis_title': int(base_size * 1.2),  
        'tick_labels': int(base_size),       
        'legend': int(base_size),            
        'annotations': int(base_size * 0.9)  
    }
    
    logger.debug(f"Calculated font sizes for width {container_width}px: {sizes}")
    return sizes


def get_card_font_sizes(container_id: str, dimensions: Dict) -> Dict[str, int]:
    """Get responsive font sizes for cards based on container dimensions"""
    if not dimensions or container_id not in dimensions:
        return {'title': 18, 'label': 14}  # Default sizes
        
    container_width = dimensions[container_id]['width']
    base_size = max(6, min(16, container_width / 60))
    logger.debug(f"container_id {container_id}, dimensions {dimensions}, base_size {base_size}")
    return {
        'title': int(base_size * 1.4),
        'label': int(base_size * 1)
    }

def process_dataframe(df: pd.DataFrame, metric: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process and split dataframe into companies and market data
    Returns: (companies_df, market_df)
    """
    # Convert market share columns to percentages
    share_cols = [col for col in df.columns if 'market_share' in col or 'q_to_q_change' in col]
    df[share_cols] = df[share_cols].apply(lambda x: x.map(lambda y: '-' if y in (0, '-') else y * 100))
    
    df['insurer'] = df['insurer'].apply(map_insurer)
    
    # Split market and company data
    market_mask = df['insurer'].str.startswith('Топ') | (df['insurer'] == 'Весь рынок')
    return df[~market_mask], df[market_mask]

def detect_outliers(df: pd.DataFrame, column: str, threshold: float = 3) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect statistical outliers using IQR method
    Returns: (normal_data, outliers)
    """
    Q1, Q3 = df[column].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    bounds = (Q1 - threshold * IQR, Q3 + threshold * IQR)
    mask = df[column].between(*bounds)
    return df[mask], df[~mask]

def create_annotation(text: str, style: Dict = None) -> html.Div:
    """Create standardized annotation with red asterisk"""
    base_style = {
        'color': STYLE_CONFIG['colors']['text_secondary'], 
        'font-size': '0.875rem'
    }
    if style:
        base_style.update(style)
        
    return html.Div([
        html.Span("*", style={'color': STYLE_CONFIG['colors']['negative'], 
                            'font-weight': 'bold', 
                            'font-size': '0.875rem'}),
        html.Span(text, style=base_style)
    ])


def create_changes_content(
    companies_data, 
    metric, 
    periods,
    container_width: int = 800
):
    logger.debug(f"Creating changes content - Width: {container_width}px, Metric: {metric}")

    metric_change_col = f"{metric}_{periods[0]}_q_to_q_change"
    filtered_data, outliers = detect_outliers(companies_data, metric_change_col)

    logger.debug(f"Filtered data shape: {filtered_data.shape}, Outliers found: {len(outliers)}")

    fig = create_changes_chart(
        companies_data, 
        filtered_data, 
        metric, 
        periods[0],
        container_width
    )
    content = [dcc.Graph(figure=fig, config={'displayModeBar': False})]

    if not outliers.empty:
        logger.debug(f"Processing {len(outliers)} outliers for changes chart")
        outlier_text = ", ".join(
            f"{row['insurer']} ({row[metric_change_col]:+.2f}%)"
            for _, row in outliers.iterrows()
        )
        font_sizes = get_chart_font_sizes(container_width)
        logger.debug(f"Annotation font size: {font_sizes['annotations']}px")
        content.append(create_annotation(
            f"Изменение показателя для следующих компаний не отображается на графике для сохранения масштаба: {outlier_text}",
            style={'font-size': f"{font_sizes['annotations']}px"}
        ))

    return content

def create_growth_content(
    companies_data, 
    market_data, 
    metric, 
    periods,
    container_width: int = 800
):
    logger.debug(f"Creating growth content - Width: {container_width}px, Metric: {metric}")
    
    market_growth = market_data.loc[
        market_data['insurer'] == 'Весь рынок',
        f'{metric}_{periods[0]}_q_to_q_change'
    ].iloc[0]
    logger.debug(f"Market growth: {market_growth:+.2f}%")
    
    companies_data['growth_diff'] = (
        companies_data[f"{metric}_{periods[0]}_q_to_q_change"] - market_growth
    )
    filtered_data, outliers = detect_outliers(companies_data, 'growth_diff')
    logger.debug(f"Filtered data shape: {filtered_data.shape}, Outliers found: {len(outliers)}")
    
    fig = create_growth_comparison_chart(
        filtered_data, 
        metric, 
        periods[0], 
        market_growth,
        container_width
    )
    content = [dcc.Graph(figure=fig, config={'displayModeBar': False})]
    
    if not outliers.empty:
        logger.debug(f"Processing {len(outliers)} outliers for growth chart")
        growth_col = f"{metric}_{periods[0]}_q_to_q_change"
        outlier_text = ", ".join(
            f"{row['insurer']} (рост {row[growth_col]:+.2f}%, "
            f"опережение/отставание {row['growth_diff']:+.2f} п.п.)"
            for _, row in outliers.iterrows()
        )
        font_sizes = get_chart_font_sizes(container_width)
        logger.debug(f"Annotation font size: {font_sizes['annotations']}px")
        content.append(create_annotation(
            f"Следующие компании не отображаются на графике для сохранения масштаба: {outlier_text}",
            style={'font-size': f"{font_sizes['annotations']}px"}
        ))
    
    return content

def create_contribution_content(
    companies_data, 
    market_data, 
    metric, 
    periods,
    container_width: int = 800
):
    logger.debug(f"Creating contribution content - Width: {container_width}px, Metric: {metric}")
    
    total_growth = (
        market_data.loc[market_data['insurer'] == 'Весь рынок', f'{metric}_{periods[0]}'].iloc[0] -
        market_data.loc[market_data['insurer'] == 'Весь рынок', f'{metric}_{periods[1]}'].iloc[0]
    )
    logger.debug(f"Total market growth: {total_growth:+.2f} млрд ₽")
    
    logger.debug("Creating contribution charts")
    fig1, fig2 = create_contribution_charts(
        companies_data, 
        metric, 
        periods, 
        total_growth,
        container_width
    )
    
    font_sizes = get_chart_font_sizes(container_width)
    logger.debug(f"Annotation font size: {font_sizes['annotations']}px")
    annotation_style = {'font-size': f"{font_sizes['annotations']}px"}
    
    content = [
        dcc.Graph(figure=fig1, config={'displayModeBar': False}),
        dcc.Graph(figure=fig2, config={'displayModeBar': False}),
        create_annotation(
            f"Общий рост рынка: {format_value(total_growth)} млрд ₽", 
            style=annotation_style
        )
    ]
    
    return content




def setup_market_analysis_callbacks(app: dash.Dash) -> None:
    """Setup responsive chart callbacks and container monitoring"""
    
    # Add container dimension store
    app.layout.children.append(dcc.Store(id='chart-dimensions-store'))
    
    # Add resize trigger div
    app.layout.children.append(html.Div(id='resize-trigger', style={'display': 'none'}))
    
    # Clientside callback to monitor container dimensions
    app.clientside_callback(
        """
        function(trigger) {
            let dimensions = {};
            const containers = [
                "market-volume-card",
                "market-concentration-card",
                "leaders-card",
                "market-analysis-tab-content"
            ];
            
            // Function to measure dimensions
            function measureDimensions() {
                containers.forEach(id => {
                    const container = document.getElementById(id);
                    if (container) {
                        dimensions[id] = {
                            width: container.offsetWidth,
                            height: container.offsetHeight
                        };
                    }
                });
                return {...dimensions}; // Return a new object to ensure Dash detects the change
            }
            
            // Initial measurement
            dimensions = measureDimensions();
            
            // Setup ResizeObserver for continuous monitoring
            const observer = new ResizeObserver(() => {
                const newDimensions = measureDimensions();
                // Update the store through the regular Dash callback chain
                if (JSON.stringify(dimensions) !== JSON.stringify(newDimensions)) {
                    dimensions = newDimensions;
                    document.getElementById('resize-trigger').click();
                }
            });
            
            // Observe all containers
            containers.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    observer.observe(element);
                }
            });
            
            return dimensions;
        }
        """,
        Output('chart-dimensions-store', 'data'),
        Input('resize-trigger', 'children')
    )
    
    # Simplified window resize handler
    app.clientside_callback(
        """
        function(trigger) {
            let resizeTimeout;
            
            function handleResize() {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    document.getElementById('resize-trigger').click();
                }, 150);
            }
            
            window.removeEventListener('resize', handleResize);
            window.addEventListener('resize', handleResize);
            
            return (trigger || 0) + 1;
        }
        """,
        Output('resize-trigger', 'children'),
        Input('resize-trigger', 'children')
    )
    
    # Rest of the callback code remains the same...
    @app.callback(
        [Output("market-volume-card", "children"),
         Output("market-concentration-card", "children"),
         Output("leaders-card", "children"),
         Output("market-analysis-tab-content", "children")],
        [Input("market-analysis-tabs", "value"),
         Input('processed-data-store', 'data'),
         Input('chart-dimensions-store', 'data'),
         State('filter-state-store', 'data')]
    )
    def update_market_analysis(tab, processed_data, dimensions, filter_state, periods=['2024Q3', '2023Q3']):
        logger.debug(f"Market analysis callback triggered with tab: {tab}")
        logger.debug(f"Received dimensions data: {dimensions}")
        
        if not all([processed_data, filter_state, dimensions]):
            logger.debug("Missing required data:", {
                "processed_data": bool(processed_data),
                "filter_state": bool(filter_state),
                "dimensions": bool(dimensions)
            })
            return [dash.no_update] * 3 + [
                html.Div("Waiting for data...", className="text-center p-4")
            ]
                
        try:
            # Process data
            logger.debug("Processing dataframe")
            df = pd.DataFrame.from_records(processed_data['df'])
            df['year_quarter'] = pd.to_datetime(df['year_quarter'])
            
            df_pivoted = table_data_pivot(df, filter_state['selected_metrics'])
            companies_data, market_data = process_dataframe(
                df_pivoted,
                filter_state['selected_metrics'][0]
            )
            
            metric = filter_state['selected_metrics'][0]
            logger.debug(f"Using metric: {metric}")
            
            # Get container width for charts
            container_width = dimensions.get('market-analysis-tab-content', {}).get('width', 800)
            logger.debug(f"Container width: {container_width}")
            
            # Update STYLE configuration with responsive sizes
            tab_content_sizes = get_card_font_sizes('market-analysis-tab-content', dimensions)
            STYLE_CONFIG['font']['sizes'] = tab_content_sizes
            logger.debug(f"Updated font sizes: {tab_content_sizes}")
            
            # Generate content based on selected tab
            logger.debug(f"Generating content for tab: {tab}")
            if tab == "overview":
                content = create_comparison_charts(companies_data, metric, periods, container_width)
            elif tab == "changes":
                content = create_changes_content(companies_data, metric, periods, container_width)
            elif tab == "growth":
                content = create_growth_content(companies_data, market_data, metric, periods, container_width)
            elif tab == "contribution":
                content = create_contribution_content(companies_data, market_data, metric, periods, container_width)
            else:
                logger.error(f"Invalid tab selection: {tab}")
                content = html.Div("Invalid tab selection", className="text-center p-4")
            
            # Create cards
            logger.debug("Creating market cards")
            cards = create_market_cards(
                companies_data,
                market_data,
                metric,
                periods,
                get_card_font_sizes('market-volume-card', dimensions)
            )
            
            tab_content = dbc.Card(
                dbc.CardBody(content),
                style=STYLE_CONFIG['card_base']
            )
            
            logger.debug("Successfully generated all content")
            return [*cards, tab_content]
                
        except Exception as e:
            logger.error(f"Error in update_market_analysis: {str(e)}", exc_info=True)
            error_div = html.Div([
                html.P("An error occurred while rendering the content."),
                html.Pre(str(e))
            ], className="text-center p-4 text-danger")
            return [html.Div("Error loading data")] * 3 + [error_div]