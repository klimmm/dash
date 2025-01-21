# style_config.py

STYLE_CONFIG = {
    'colors': {
        'primary': '#8884d8',
        'secondary': '#82ca9d',
        'positive': '#4ade80',
        'negative': '#f87171',
        'grid': 'rgb(226, 232, 240)',
        'text': {
            'primary': 'rgb(17, 24, 39)',
            'secondary': 'rgb(107, 114, 128)',
            'muted': 'rgb(156, 163, 175)'
        },
        'border': 'rgb(226, 232, 240)'
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


class StyleConstants:

    NAV = "main-nav"
    LAYOUT = "layout-wrapper"
    SIDEBAR = "sidebar-col"
    SIDEBAR_COLLAPSED = "sidebar-col collapsed"
    TREE = "tree"

    # Layout containers
    CONTAINER = {
        "CHART": "chart-container",
        "CHART_COLLAPSED": "chart-container collapsed",
        "TREE": "tree-container",
        "DATA_TABLE": "datatable-container",
        "TITLES": "titles-container",
        "TITLES_CHART": "titles-container-chart",
        "CARD": "card-container",
        "TABS": "tabs-container",
        "GRAPH": "graph-container"
    }

    # Market analysis
    MARKET = {
        "TITLE": "market-analysis-title",
        "CONTENT": "market-analysis-content"
    }

    # Form elements
    FORM = {
        "DD": "dd-control",
        "CHECKLIST": "checklist",
        "INPUT": "form-control input-short"
    }

    # Buttons
    BTN = {
        "PERIOD": "btn-custom btn-period",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "TAB": "btn-custom btn-tab",
        "TABLE_TAB": "btn-custom btn-table-tab"
    }

    # Filters
    FILTER = {
        "LABEL": "filter-label",
        "CONTENT": "filter-content w-100",
        "ROW": "filter-row",
        "ROW_VERTICAL": "filter-row filter-row--vertical",
        "ROW_NO_MARGIN": "filter-row mb-0",
        "COLUMN": "filter-column",
        "MAIN": "main-filter-column"
    }

    # Tabs
    TAB = {
        "DEFAULT": "tab",
        "SELECTED": "tab-selected"
    }

    # Utilities
    FLEX = {
        "START": "d-flex justify-content-start",
        "END": "d-flex justify-content-end"
    }

    TABLE = {
        "TITLE": "table-title",
        "SUBTITLE": "table-subtitle mb-3",
    }

    UTILS = {
        "MB_0": "mb-0",
        "PERIOD_TYPE": "period-type__text"
    }
