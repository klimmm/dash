# Consolidated style configurations
STYLE_BASE = "btn-custom"
BUTTON_STYLES = {
    "DEFAULT": STYLE_BASE,
    "PERIOD": f"{STYLE_BASE} btn-period",
    "GROUP_CONTROL": f"{STYLE_BASE} btn-group-control",
    "TABLE_TAB": f"{STYLE_BASE} btn-table-tab",
    "SIDEBAR": "sidebar-button",
    "DEBUG": f"{STYLE_BASE} btn-debug-toggle",
    "BUTTON_GROUP_ROW": "mb-0"
}

STYLE_MAPPING = {
    'view-metrics': "PERIOD",
    'top-insurers': "GROUP_CONTROL",
    'period-type': "PERIOD",
    'reporting-form': "PERIOD",
    'number-of-periods': "PERIOD",
    'index-col': "PERIOD",
    'pivot-col': "PERIOD",
    'view-mode': "PERIOD"
}






class StyleConstants:
    DROPDOWN = "dd-control"
    CHECKLIST = "checklist"

    SIDEBAR = "sidebar"
    SIDEBAR_COLLAPSED = "sidebar collapsed"

    FILTER_PANEL = "filter-panel"
    FILTER_LABEL = "filter-label"

    # Collapsible sections
    FILTER_SECTION = "filter-section"
    FILTER_SECTION_HEADER = "filter-header"
    FILTER_SECTION_TITLE = "filter-section-title"
    FILTER_SECTION_CONTENT = "filter-section-content"

    # Icons
    SIDEBAR_ICON = "fas fa-chevron-left"
    COLLAPSE_ICON_UP = "fas fa-chevron-up ms-auto"
    COLLAPSE_ICON_DOWN = "fas fa-chevron-down ms-auto"

    # Metrics
    METRIC_GROUP_BTN_ICON = "fas fa-chevron-down"
    METRIC_GROUP_BTN = "metric-group-button"
    METRIC_CHECKLIST = "metric-checklist"
    METRIC_GROUP_CARD = "metric-group-card"
    METRICS_CONTAINER = "metrics-container"

    # Layout
    APP_ROW = "app-row"
    APP_CONTAINER = "app-container"
    NAV = "main-nav"
    CONTENT = "content"
    MAIN_CONTENT = "main-content"
    FILTERS_SUMMARY = "filters-summary"
    FILTERS_SUMMARY_SECOND_ROW = "filters-summary-second-row"

    BTN_GROUP = "mb-0"
    BTN = {
        "BUTTON_GROUP_ROW": "mb-0",
        "TOP_INSURERS": "btn-custom btn-group-control",
        "REPORTING_FORM": "btn-custom btn-period",
        "TABLE_SPLIT": "btn-custom btn-period",
        "PIVOT_COL": "btn-custom btn-period",
        "INDEX_COL": "btn-custom btn-period",
        "VIEW_METRICS": "btn-custom btn-period",
        "NUMBER_OF_PERIODS": "btn-custom btn-period",
        "PERIOD_TYPE": "btn-custom btn-period",
        "DEFAULT": "btn-custom",
        "TABLE_TAB": "btn-custom btn-table-tab",
        "SIDEBAR_SHOW": "sidebar-button",
        "SIDEBAR_HIDE": "sidebar-button",
        "DEBUG": "btn-custom btn-debug-toggle"
    }

    TREE = {
        "EXPAND_BUTTON": "expand-button",
        "EXPAND_BUTTON_PLACEHOLDER": "expand-button-placeholder",
        "NODE_CHECKBOX": "node-checkbox",
        "PARENT_OF_SELECTED": "parent-of-selected",
        "SELECTED": "selected",
        "TREE_ITEM_LABEL": "insurance-line-label",
        "TREE_ITEM": "tree-item",
        "LEVEL_PREFIX": "level-",
        "HAS_SELECTED": "has-selected",
        "TREE_CHILDREN": "tree-children",
        "D_FLEX_ALIGN_ITEMS_CENTER": "d-flex align-items-center",
        "SELECTED_TAG": "selected-tag",
        "SELECTED_TAG_LABEL": "selected-tag-label",
        "SELECTED_TAG_REMOVE": "selected-tag-remove",
        "DROPDOWN_PLACEHOLDER": "dropdown-placeholder",
        "DROPDOWN_TAGS_CONTAINER": "dropdown-tags-container",
        "DROPDOWN_ARROW": "dropdown-arrow",
        "TREE_DROPDOWN_HEADER": "tree-dropdown-header",
        "TREE_DROPDOWN_CONTENT": "tree-dropdown-content",
        "TREE_DROPDOWN_CONTAINER": "tree-dropdown-container",


        # New entries for custom top-level nodes
        "TREE_CONTAINER": "custom-tree-container",
        "TOP_LEVEL_NODE": "top-level-node",
        "TOP_LEVEL_LABEL": "top-level-label",
        "TOP_LEVEL_EXPAND_BUTTON": "top-level-expand-button",
        "EXPAND_ICON_PREFIX": "fas",
        "EXPAND_ICON_DOWN": "fa-chevron-down",
        "EXPAND_ICON_RIGHT": "fa-chevron-right"

    }