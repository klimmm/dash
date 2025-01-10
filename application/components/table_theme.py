# table_theme.py

from dataclasses import dataclass, field
from typing import Dict, Any, TypedDict, Literal

class ColorConfig(TypedDict):
    header_bg: str
    header_text: str
    cell_bg: str
    cell_text: str
    border: str
    highlight: str
    success: str
    danger: str
    success_bg: str
    qtoq_bg: str
    insurer_bg: str

class TypographyConfig(TypedDict):
    font_family: str
    font_size: str
    header_weight: str

class DimensionsConfig(TypedDict):
    cell_height: str
    header_height: str
    place_col_width: str      # Changed from number_col_width
    insurer_col_width: str
    data_col_width: str

def default_dimensions() -> DimensionsConfig:
    return DimensionsConfig(
        cell_height='var(--table-cell-height)',
        header_height='var(--table-header-height)',
        place_col_width='var(--table-place-col-width)',    # Changed from number_col_width
        insurer_col_width='var(--table-insurer-col-width)',
        data_col_width='var(--table-data-col-width)'
    )

# Update Literal type in get_dimension method
def get_dimension(self, key: Literal['cell_height', 'header_height', 
                                   'place_col_width', 'insurer_col_width', 
                                   'data_col_width']) -> str:
    """
    Get a dimension value from the theme.
    
    Args:
        key: The dimension key to retrieve
        
    Returns:
        The corresponding CSS variable
    """
    return self.dimensions[key]

class SpacingConfig(TypedDict):
    cell_padding: str
    header_padding: str

def default_colors() -> ColorConfig:
    return ColorConfig(
        header_bg='var(--table-header-bg)',
        header_text='var(--table-header-text)',
        cell_bg='var(--table-cell-bg)',
        cell_text='var(--table-cell-text)',
        border='var(--table-border)',
        highlight='var(--table-highlight-bg)',
        success='var(--table-success-text)',
        danger='var(--table-danger-text)',
        success_bg='var(--table-success-bg)',
        qtoq_bg='var(--table-qtoq-bg)',
        insurer_bg='var(--table-insurer-bg)'
    )

def default_typography() -> TypographyConfig:
    return TypographyConfig(
        font_family='var(--font-family-base)',
        font_size='var(--table-font-size)',
        header_weight='var(--table-header-font-weight)'
    )

def default_dimensions() -> DimensionsConfig:
    return DimensionsConfig(
        cell_height='var(--table-cell-height)',
        header_height='var(--table-header-height)',
        number_col_width='var(--table-number-col-width)',
        insurer_col_width='var(--table-insurer-col-width)',
        data_col_width='var(--table-data-col-width)'
    )

def default_spacing() -> SpacingConfig:
    return SpacingConfig(
        cell_padding='var(--table-cell-padding)',
        header_padding='var(--table-header-padding)'
    )

@dataclass(frozen=True)
class TableTheme:
    """
    Centralized theme configuration for table styling.
    Uses CSS variables for consistent styling across the application.
    """
    colors: ColorConfig = field(default_factory=default_colors)
    typography: TypographyConfig = field(default_factory=default_typography)
    dimensions: DimensionsConfig = field(default_factory=default_dimensions)
    spacing: SpacingConfig = field(default_factory=default_spacing)

    def get_color(self, key: Literal['header_bg', 'header_text', 'cell_bg', 'cell_text', 
                                   'border', 'highlight', 'success', 'danger', 
                                   'success_bg', 'qtoq_bg', 'insurer_bg']) -> str:
        """
        Get a color value from the theme.
        
        Args:
            key: The color key to retrieve
            
        Returns:
            The corresponding CSS variable
        """
        return self.colors[key]

    def get_typography(self, key: Literal['font_family', 'font_size', 'header_weight']) -> str:
        """
        Get a typography value from the theme.
        
        Args:
            key: The typography key to retrieve
            
        Returns:
            The corresponding CSS variable
        """
        return self.typography[key]

    def get_dimension(self, key: Literal['cell_height', 'header_height', 
                                       'number_col_width', 'insurer_col_width', 
                                       'data_col_width']) -> str:
        """
        Get a dimension value from the theme.
        
        Args:
            key: The dimension key to retrieve
            
        Returns:
            The corresponding CSS variable
        """
        return self.dimensions[key]

    def get_spacing(self, key: Literal['cell_padding', 'header_padding']) -> str:
        """
        Get a spacing value from the theme.
        
        Args:
            key: The spacing key to retrieve
            
        Returns:
            The corresponding CSS variable
        """
        return self.spacing[key]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the theme to a dictionary format.
        Useful for debugging or serialization.
        
        Returns:
            Dict containing all theme values
        """
        return {
            'colors': dict(self.colors),
            'typography': dict(self.typography),
            'dimensions': dict(self.dimensions),
            'spacing': dict(self.spacing)
        }


def create_default_theme() -> TableTheme:
    """
    Create a default theme instance with all standard values.
    
    Returns:
        TableTheme instance with default configuration
    """
    return TableTheme()


def create_custom_theme(
    colors: Dict[str, str] = None,
    typography: Dict[str, str] = None,
    dimensions: Dict[str, str] = None,
    spacing: Dict[str, str] = None
) -> TableTheme:
    """
    Create a custom theme by overriding specific values.
    
    Args:
        colors: Optional color overrides
        typography: Optional typography overrides
        dimensions: Optional dimension overrides
        spacing: Optional spacing overrides
        
    Returns:
        CustomTableTheme instance
    """
    default_theme = create_default_theme()
    
    new_colors = ColorConfig(**(dict(default_theme.colors) | (colors or {})))
    new_typography = TypographyConfig(**(dict(default_theme.typography) | (typography or {})))
    new_dimensions = DimensionsConfig(**(dict(default_theme.dimensions) | (dimensions or {})))
    new_spacing = SpacingConfig(**(dict(default_theme.spacing) | (spacing or {})))
    
    return TableTheme(
        colors=new_colors,
        typography=new_typography,
        dimensions=new_dimensions,
        spacing=new_spacing
    )