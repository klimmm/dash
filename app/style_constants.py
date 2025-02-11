class StyleConstants:
    """
    Centralized storage for all style constants used in the application.
    All classNames should be defined here and referenced from this class.
    """
    # Top-level navigation and layout
    NAV = "main-nav"
    LAYOUT = "layout-wrapper"
    SIDEBAR = "sidebar"
    SIDEBAR_COLLAPSED = "sidebar collapsed"
    CHECKLIST = "checklist"
    DROPDOWN = "dd-control"
    FILTER_ROW = "filter-row"
    FILTER_LABEL = "filter-label"
    TABLES_CONTAINER = 'datatable-container'
    # Container styles
    CONTAINER = {
        "CHART": "chart-container",
        "CHART_COLLAPSED": "chart-container collapsed",
        "DATA_TABLE": "datatable-container"
    }

    # Form controls
    FORM = {
        "DD": "dd-control"
    }

    # Button styles
    BTN = {

        "TOP_N": "btn-custom btn-group-control",
        "TOP_N_ACTIVE": "btn-custom btn-group-control active",
        "REPORTING_FORM": "btn-custom btn-group-control",
        "REPORTING_FORM_ACTIVE": "btn-custom btn-group-control active",
        "TABLE_SPLIT": "btn-custom btn-group-control",
        "TABLE_SPLIT_ACTIVE": "btn-custom btn-group-control active",


        "VIEW_METRICS": "btn-custom btn-period",
        "VIEW_METRICS_ACTIVE": "btn-custom btn-period active",
        "NUM_PERIODS": "btn-custom btn-period",
        "NUM_PERIODS_ACTIVE": "btn-custom btn-period active",
        "PERIOD_TYPE": "btn-custom btn-period",
        "PERIOD_TYPE_ACTIVE": "btn-custom btn-period active",

        "DEFAULT": "btn-custom",
        "DEFAULT_ACTIVE": "btn-custom active",
        "TABLE_TAB": "btn-custom btn-table-tab",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "BUTTON_GROUP_ROW": "mb-0",

        "DEBUG": "btn-custom btn-debug-toggle",
    }

    # Filter styles
    FILTER = {
        "LABEL": "filter-label",
        "DROPDOWN": "d-flex justify-content-start",
        "BUTTONS_CENTER": "d-flex justify-content-center",
        "BUTTONS_END": "d-flex justify-content-end",
        "BUTTONS_START": "d-flex justify-content-start",
    }

    # Filter Panel Layout
    FILTER_PANEL = {
        "COL": "sidebar-col",
        "TWO_COL": "sidebar-two-col",
        "THIRD_COL": "sidebar-third-col",
        "ROW": "fltr-row"
    }

    # Flex utilities
    FLEX = {
        "CENTER": "d-flex align-items-center",
        "WRAP": "flex-wrap"
    }

    # General utilities
    UTILS = {
        "MB_0": "mb-0",
        "PERIOD_TYPE": "period-type__text"
    }

    # Spacing utilities
    SPACING = {
        "PS_3": "ps-3",
        "MT_3": "mt-3",
        "MB_5": "mb-5",
        "MB_3": "mb-3",
        "MT_2": "mt-2",
        "MT_1": "mt-1",
        "MT_0": "mt-0",
    }

    # Debug-related styles
    DEBUG = {
        "DEBUG_TITLE": "debug-title",
        "DEBUG_OUTPUT": "debug-output"
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
        "TREE_DROPDOWN_CONTAINER": "tree-dropdown-container"
    }