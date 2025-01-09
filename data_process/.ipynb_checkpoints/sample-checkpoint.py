import plotly.graph_objects as go
import numpy as np
import pandas as pd

def create_grouped_stacked_chart(df, x_col, group_col, stack_col, value_col):
    """
    Create a grouped and stacked bar char

    Parameters:
    df: DataFrame with the data
    x_col: Column to use for x-axis grouping (e.g., 'Year')
    group_col: Column to use for bar grouping (e.g., 'Region')
    stack_col: Column to use for stacking (e.g., 'Product')
    value_col: Column containing the values to plo
    """
    # Get unique values from each dimension
    x_values = sorted(df[x_col].unique())
    group_values = sorted(df[group_col].unique())
    stack_values = sorted(df[stack_col].unique())

    # Create color palettes
    num_colors = len(group_values) * len(stack_values)
    colors = [
        f'hsl({h},70%,50%)'
        for h in np.linspace(0, 360, num_colors, endpoint=False)
    ]

    color_map = {
        (group, stack): colors[i * len(stack_values) + j]
        for i, group in enumerate(group_values)
        for j, stack in enumerate(stack_values)
    }

    fig = go.Figure()

    # Add traces
    for i, group in enumerate(group_values):
        base = np.zeros(len(x_values))

        for j, stack in enumerate(stack_values):
            # Get values for this combination
            values = []
            for x in x_values:
                # Correct boolean operations with parentheses
                mask = (df[x_col] == x) & (df[group_col] == group) & (df[stack_col] == stack)
                val = df.loc[mask, value_col].iloc[0] if len(df.loc[mask]) > 0 else 0
                values.append(val)

            fig.add_trace(go.Bar(
                name=f'{group} - {stack}',
                x=x_values,
                y=values,
                base=base,
                offsetgroup=str(i),
                legendgroup=group,
                legendgrouptitle_text=group,
                marker_color=color_map[(group, stack)],
                text=values,
                textposition='inside',
                hovertemplate=(
                    f"{x_col}: %{{x}}<br>"
                    f"{group_col}: {group}<br>"
                    f"{stack_col}: {stack}<br>"
                    f"{value_col}: %{{y:,.0f}}<br>"
                    "<extra></extra>"
                )
            ))

            base += np.array(values)

    fig.update_layout(
        title={
            'text': f'{value_col} by {group_col} and {stack_col}',
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis={
            'title': x_col,
            'title_font': {'size': 16},
            'tickfont': {'size': 14},
            'tickangle': 0,
            'type': 'category'
        },
        yaxis={
            'title': value_col,
            'title_font': {'size': 16},
            'tickfont': {'size': 14},
            'gridcolor': 'lightgray'
        },
        bargap=0.15,
        bargroupgap=0.1,
        height=700,
        legend={
            'x': 1.05,
            'y': 1,
            'groupclick': 'toggleitem',
            'tracegroupgap': 10,
            'title': {'text': f'{group_col} - {stack_col}'},
            'font': {'size': 12}
        },
        margin={'l': 60, 'r': 150, 't': 100, 'b': 60},
        template='plotly_white',
        hoverlabel=dict(
            bgcolor='white',
            font_size=14,
            bordercolor='gray'
        )
    )

    return fig

# Example usage
def example_usage():
    # Create sample data
    data = []
    years = ['2020', '2021', '2022', '2023']
    regions = ['North', 'South', 'East', 'West']
    products = ['Electronics', 'Clothing', 'Food']

    for year in years:
        for region in regions:
            for product in products:
                data.append({
                    'Year': year,
                    'Region': region,
                    'Product': product,
                    'Sales': np.random.randint(100, 250)
                })

    df = pd.DataFrame(data)

    # Create char
    fig = create_grouped_stacked_chart(
        df=df,
        x_col='Year',
        group_col='Region',
        stack_col='Product',
        value_col='Sales'
    )

    return fig

# Create and show figure
if __name__ == "__main__":
    fig = example_usage()
    fig.show()