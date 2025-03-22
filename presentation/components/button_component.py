# presentation/components/button_component.py
import dash_bootstrap_components as dbc


class ButtonComponent:
    """Handles creation of button UI components."""
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

    @classmethod
    def get_style_for_group(cls, group_id):
        """Get the appropriate style for a group_id."""
        style_key = cls.STYLE_MAPPING.get(group_id)
        return cls.BUTTON_STYLES.get(
            style_key or "DEFAULT", cls.BUTTON_STYLES["DEFAULT"])

    @classmethod
    def create_button(
        cls,
        label=None,
        button_id=None,
        className=None,
        disabled=False,
        title="Description",
        is_active=False,
        hidden=False,
        group_id=None,
        **kwargs
    ):
        """Create a button with consistent styling."""
        # If no className is provided, determine it from group_id
        if className is None and group_id is not None:
            className = cls.get_style_for_group(group_id)
        elif className is None:
            className = cls.BUTTON_STYLES["DEFAULT"]

        if is_active:
            className += " active"
        elif disabled:
            className += " disabled"

        style = {'display': 'none'} if hidden else {}

        return dbc.Button(
            kwargs.get('content', label),
            id=button_id,
            className=className,
            title=title,
            outline=kwargs.get('outline', False),
            n_clicks=kwargs.get('n_clicks', 0),
            style=style,
            disabled=disabled
        )

    @classmethod
    def create_button_group(cls, buttons, className=None):
        """Create a button group with uniform styling."""
        if className is None:
            className = cls.BUTTON_STYLES["BUTTON_GROUP_ROW"]
        return dbc.ButtonGroup(buttons, className=className)