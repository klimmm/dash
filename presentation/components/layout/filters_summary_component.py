

class FiltersSummaryComponent:
    """Manages filters summary display"""

    def __init__(self, formatting_service, context):
        self.fmt = formatting_service
        self.context = context
        self.logger = formatting_service.logger

    def _format_row(self, row_data: list) -> list:
        """Format a row of filter summary data"""
        elements = []
        for key, prefix, suffix, is_list in row_data:
            # Get value directly from context instead of using data_mapping
            value = getattr(self.context, key, None)

            if value is None:
                continue

            if key == "quarters":
                self.logger.debug(f"Formatting quarters: {value}")
                if isinstance(value, list):
                    value = sorted(value)
                    formatted = ", ".join(self.fmt.format_value(
                        value, period_type=self.context.period_type,
                        val_type=self.context.value_types))
            else:
                formatted = (", ".join(self.fmt.format_value(value))
                             if is_list and isinstance(value, list)
                             else self.fmt.format_value(value))

            elements.append(f"{prefix}{formatted}{suffix}")

        return elements