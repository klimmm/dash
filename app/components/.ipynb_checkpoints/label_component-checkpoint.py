from dash import html


def create_label(label_text, class_name=None):
    """Create a label component"""
    return html.Label(
        label_text,
        className=class_name
    )