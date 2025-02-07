class StyleConstants:
    """
    Centralized storage for all style constants used in the application.
    All classNames should be defined here and referenced from this class.
    """
    # Top-level navigation and layout
    NAV = "main-nav"
    LAYOUT = "layout-wrapper"
    SIDEBAR = "sidebar-col"
    SIDEBAR_COLLAPSED = "sidebar-col collapsed"
    CHECKLIST = "checklist"
    DROPDOWN = "dd-control"
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
        "PERIOD": "btn-custom btn-period",
        "PERIOD_ACTIVE": "btn-custom btn-period active",
        "SIDEBAR_SHOW": "btn-custom btn-sidebar-toggle-show",
        "SIDEBAR_HIDE": "btn-custom btn-sidebar-toggle-hide",
        "TABLE_TAB": "btn-custom btn-table-tab",
        "GROUP_CONTROL": "btn-custom btn-group-control",
        "GROUP_CONTROL_ACTIVE": "btn-custom btn-group-control active",
        "DEBUG": "btn-custom btn-debug-toggle",
        "BUTTON_GROUP_ROW": "mb-0",
        "MARKET_SHARE": "btn-custom btn-group-control",
        "MARKET_SHARE_ACTIVE": "btn-custom btn-group-control active",
        "TOP_N": "btn-custom btn-group-control",
        "TOP_N_ACTIVE": "btn-custom btn-group-control active",
        "PERIOD_TYPE": "btn-custom btn-period",
        "PERIOD_TYPE_ACTIVE": "btn-custom btn-period active",
        "REPORTING_FORM": "btn-custom btn-period",
        "REPORTING_FORM_ACTIVE": "btn-custom btn-period active",
        "NUM_PERIODS": "btn-custom btn-group-control",
        "NUM_PERIODS_ACTIVE": "btn-custom btn-group-control active",
        "DEFAULT": "btn-custom btn-group-control",
        "DEFAULT_ACTIVE": "btn-custom btn-group-control active",
        "TABLE_SPLIT": "btn-custom btn-group-control",
        "TABLE_SPLIT_ACTIVE": "btn-custom btn-group-control active",
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
        "CENTER": "d-flex align-items-center"
    }

    # General utilities
    UTILS = {
        "MB_0": "mb-0",
        "PERIOD_TYPE": "period-type__text"
    }

    # Spacing utilities
    SPACING = {
        "PS_3": "ps-3",
        "MT_3": "mt-3"
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
        "INSURANCE_LINE_LABEL": "insurance-line-label",
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
