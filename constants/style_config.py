# style_config.py

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
        "GRAPH": "graph-container",
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
        "PERIOD_ACTIVE": "btn-custom btn-period active",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "TAB": "btn-custom btn-tab",
        "TABLE_TAB": "btn-custom btn-table-tab",
        "ADD": "btn-metric-add pr-1",
        "REMOVE": "btn-metric-remove",
        "GROUP_CONTROL": "btn-custom btn-group-control",
        "GROUP_CONTROL_ACTIVE": "btn-custom btn-group-control active",
        "SECONDARY": "btn-custom btn-group-control active"
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
    # Flex utilities
    FLEX = {
        "START": "d-flex justify-content-start",
        "END": "d-flex justify-content-end",
        "CENTER": "d-flex align-items-center"  # Added for the align-items-center class
    }
    # Table styles
    TABLE = {
        "TITLE": "table-title",
        "SUBTITLE": "table-subtitle mb-3",
    }
    # General utilities
    UTILS = {
        "MB_0": "mb-0",
        "PERIOD_TYPE": "period-type__text",
        "W_100": "w-100",  # Added for width 100% utility
        "FLEX_GROW_1": "flex-grow-1",  # Added for flex-grow-1 utility
        "PY_0": "py-0",  # Added for padding-y-0 utility
        "PR_1": "pr-1"   # Added for padding-right-1 utility
    }
    # Dropdown specific styles
    DROPDOWN = {
        "CONTAINER": "dash-dropdown",
        "DYNAMIC_CONTAINER": "dynamic-dropdowns-container"
    }