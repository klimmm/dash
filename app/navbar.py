import dash_bootstrap_components as dbc  # type: ignore

from app.style_constants import StyleConstants
from app.components.button import create_button
from config.logging import get_logger

logger = get_logger(__name__)


def create_navbar() -> dbc.Navbar:
    """Create navigation bar component."""
    return dbc.Navbar(
        [
            dbc.Container(
                children=[
                    create_button(
                        "show logs",
                        button_id="debug-collapse-button",
                        className=StyleConstants.BTN["DEBUG"]
                    ),
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    create_button(
                        label="Data Table",
                        button_id='data-table-tab',
                        className=StyleConstants
                        .BTN["TABLE_TAB"],
                        hidden=True
                    ),

              ]
            )
        ],
        color="dark",
        dark=True,
        className=StyleConstants
        .NAV
    )