def get_rgba_color(outer_idx: int, inner_idx: int, num_groups: int, num_series: int, outer_loop: str, x_column: str, config: ChartConfig, chart_type: str) -> str:
    logger.info(f"outer_idx: {outer_idx}")
    logger.info(f"inner_idx: {inner_idx}")
    logger.info(f"num_groups: {num_groups}")
    logger.info(f" num_series: {num_series}")

    logger.info(f"outer_loop: {outer_loop}")
    logger.info(f"x_column: {x_column}")

    if outer_loop == 'series':
        #if x_column == 'year':
        #    decrement = 1 / (num_groups + 1)
        #
        #    color = get_color(outer_idx, num_groups, config)
        #    opacity = max(0, 1 - (decrement * inner_idx))

        if num_series > 1:
            decrement = 1 / (num_groups)
            opacity = min(1, 0.1 + decrement * (inner_idx + 1))
            color = get_color(outer_idx, num_groups, config)
            # opacity = max(0.1, 1 - (decrement * inner_idx))
        else:
            decrement = 1 / (num_groups)

            color = get_color(outer_idx, num_series, config)
            logger.info(f"outer_idx: {outer_idx}")

            opacity = 1

    elif outer_loop == 'group':
        #if x_column == 'year':
        #       decrement = 1 / (num_series)
        #        color = get_color(outer_idx, num_groups, config)
        #        opacity = min(1, 0.1 + decrement * (outer_idx + 1))
        #
        #if x_column != 'year_quarter':
        #    if num_groups == 1:
        #        decrement = 1 / (num_groups)
        #        color = get_color(inner_idx, num_series, config)

        #        opacity = min(1, 0.1 + decrement * (outer_idx + 1))

        decrement = 1 / (num_series)
        color = get_color(outer_idx, num_series, config)

        opacity = max(0, 1 - (decrement / 7 * 6 * inner_idx))

        #opacity = min(1, 0.1 + decrement * (inner_idx + 1))
        #else:
        #    color = get_color(inner_idx, num_series, config)
        #    opacity = 1

    # Adjust opacity for area charts
    if chart_type == 'area':
        opacity = 0.8  # Lower opacity for better visibility

    hex_color = color.lstrip('#')
    logger.info(f"hex_color: {hex_color}")

    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    return f'rgba({r}, {g}, {b}, {opacity})'



def log_callback_inputs(**kwargs):
    """Log the inputs to a callback function for debugging purposes."""
    logger.debug("Callback inputs:")
    for key, value in kwargs.items():
        logger.debug(f"{key}: {value}")


dbc.Row([
    create_dropdown_component(id='aggregation-type-dropdown', xs=12, sm=6, md=4),
], className="g-0 mb-2"),