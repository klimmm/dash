from typing import List, Optional, Union
from dash import html, dash_table


def create_visual_section(
        table: Optional[dash_table.DataTable] = None,
        charts: Optional[List[html.Div]] = None,
        filter_buttons: Optional[html.Div] = None
        ) -> html.Div:

        """Create a visual section with table and/or charts.
        Args:
            table: Optional DataTable component
            charts: Optional list of chart components
            filter_buttons: Optional filter buttons component
        Returns:
            html.Div containing the visual components
        """
        if all(component is None for component in [table, charts, filter_buttons]):
            return html.Div(
                "No data available for the selected filters",
                className="data-section empty-section"
            )
        content: List[html.Div] = []
        if table is not None:
            content.append(html.Div(table, className="table-container"))
        if charts or filter_buttons:
            chart_elements: List[Union[html.Div, None]] = [
                filter_buttons] if filter_buttons else []
            if charts:
                chart_elements.extend(charts)
            content.append(html.Div(chart_elements, className="chart-container"))
        return html.Div(content, className="viz-section")