# checklist_components.py

import dash_bootstrap_components as dbc
from typing import Dict, List
from constants.filter_options import BUSINESS_TYPE_OPTIONS
from config.default_values import DEFAULT_BUSINESS_TYPE
from dash import html

class ChecklistComponent:
    """Factory for creating checklist components with consistent styling"""
    
    @staticmethod
    def create_checklist(
        id: str,
        options: List[Dict],
        value: List = None,
        switch: bool = False,
        inline: bool = False,
        readonly: bool = False
    ) -> dbc.Checklist:
        """Create a checklist component with consistent styling
        
        Args:
            id (str): Component ID
            options (List[Dict]): List of options for the checklist
            value (List, optional): Default selected values. Defaults to None.
            switch (bool, optional): Use switch style. Defaults to False.
            inline (bool, optional): Display inline. Defaults to False.
            readonly (bool, optional): Make component readonly. Defaults to False.
            
        Returns:
            dbc.Checklist: Styled checklist component
        """
        style = {"fontSize": "0.85rem", "margin": 0}
        if readonly:
            style.update({'pointerEvents': 'none', 'opacity': 0.5})

        return dbc.Checklist(
            id=id,
            options=options,
            value=value or [],
            switch=switch,
            inline=inline,
            style=style,
            className="checklist"
        )

def create_business_type_checklist() -> html.Div:
    """Create a business type checklist component with default configuration
    
    Returns:
        html.Div: Wrapped checklist component
    """
    checklist = ChecklistComponent.create_checklist(
        id='business-type-checklist',
        options=BUSINESS_TYPE_OPTIONS,
        value=DEFAULT_BUSINESS_TYPE,
        switch=True,
        inline=True
    )
    
    return html.Div(
        id='business-type-checklist-container',
        children=[checklist]
    )