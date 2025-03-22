from typing import Any, Optional, Union, List
from datetime import datetime
import re

class FormattingServiceFacade:
    """Maps and formats insurance data with translations and code-to-name mappings."""
    # Templates for base values
    BASE_PERIOD_TEMPLATES = {
        'default': "{q} кв. {yr}",
        'ytd': "{months} мес. {yr}"
    }

    # Templates for change comparisons
    CHANGE_PERIOD_TEMPLATES = {
        'default': "{yr} vs {prev_yr}",
        'qoq': "{q} кв. vs {prev_q} кв."
    }
    DATE_FORMATS = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%m/%d/%Y',
        '%Y%m%d',
        '%b %d, %Y',
        '%d %b %Y',
        '%Y-%m-%d %H:%M:%S'
    ]
    
    def __init__(
        self,
        domain_services, metrics_mapping
    ):
        insurers_service = domain_services.insurers_service
        lines_service = domain_services.lines_service
        metrics_service = domain_services.metrics_service
        self.metrics_mapping = metrics_mapping
        self.logger = insurers_service.logger
        self.config = insurers_service.config
        self.get_insurer_label = insurers_service.get_node_label
        self.get_line_label = lines_service.get_node_label
        self.get_metric_label = metrics_service.get_node_label

    def _get_metric_unit_custom(self, metric: Union[str, List[str]]) -> str:
        """Get unit for metric code(s)."""
        units = self.get_metric_unit(metric)
        if not isinstance(units, list):
            return units
        return "/ ".join(units) if units and len(units) < 3 else "--"

    def get_metric_unit(self, metric: Union[str, List[str]]) -> str:
        """Get unit for metric code(s)."""
        if not isinstance(metric, list):
            return self.metrics_mapping.get(metric, ['', '', ''])[2]

        return [u for m in metric if (u := self.metrics_mapping.get(m, ['', '', ''])[2])]

    def _map_value_type(self, value_type: str, metric_unit: Optional[str] = None) -> str:
        """Maps value type to display string."""
        if value_type == self.config.value_types.BASE:
            return metric_unit or '--'
        return self.config.format_config.VALUE_TYPE_DISPLAYS.get(value_type, value_type)

    def _translate(self, text: str) -> str:
        """_translates text using translations dictionary."""
        return self.config.format_config.TRANSLATIONS.get(text, text)

    def format_period_label(self, value: str) -> str:
        """Convert various date formats to quarter label (YYYYQN)."""
        if hasattr(value, 'month') and hasattr(value, 'year'):
            return f"{value.year}Q{(value.month - 1) // 3 + 1}"

        if isinstance(value, str):
            # Check if already in YYYYQN format
            if re.match(r'^(\d{2,4})Q([1-4])$', value):
                return value

            # Handle Timestamp string representation
            ts_match = re.match(r"Timestamp\('([^']+)'\)", str(value))
            date_str = ts_match.group(1) if ts_match else value

            # Try parsing with multiple formats
            for fmt in self.DATE_FORMATS:
                try:
                    date = datetime.strptime(date_str, fmt)
                    return f"{date.year}Q{(date.month - 1) // 3 + 1}"
                except ValueError:
                    continue

        raise ValueError(f"Could not parse date '{value}'")

    def _format_period(self, value: str, period_type: str = 'qoq', value_type: str = '') -> str:
        """Formats period string based on configuration templates."""
        value = self.format_period_label(value)
        year_part, quarter_part = value.split('Q')

        yr = int(year_part[-2:])  # Extract last 2 digits regardless of year format
        q = int(quarter_part)

        params = {
            'q': q,
            'yr': yr,
            'months': q * 3,
            'prev_q': 4 if q == 1 else q - 1,
            'prev_yr': yr - 1,
            'prev_month': q * 3 - 1
        }

        templates = (self.CHANGE_PERIOD_TEMPLATES
                     if value_type 
                     and self.config.value_types.CHANGE_SUFFIX in value_type
                     else self.BASE_PERIOD_TEMPLATES)

        return templates.get(period_type, templates['default']).format(**params)

    def _get_mapped_string(self, val: Any, period_type: str = None,
                          metric: str = None, val_type: str = None) -> str:
        """Maps value using available mapping functions."""
        mapping_funcs = [
            lambda v: self._format_period(v, period_type, val_type),
            self.get_insurer_label,
            self.get_line_label,
            self.get_metric_label,
            lambda v: self._map_value_type(v, self._get_metric_unit_custom(metric))
        ]

        for func in mapping_funcs:
            try:
                if result := func(val):
                    if str(result) != str(val):
                        return result
            except Exception:
                continue

        return self._translate(str(val))

    def format_value(self, val: Union[Any, List], col: Optional[Union[str, List]] = None,
                     period_type: Optional[str] = None, metric: Optional[str] = None,
                     val_type: Optional[str] = None) -> Union[str, List[str]]:
        """Format single value or list of values using appropriate mapping methods."""
        if col and isinstance(col, list) and isinstance(val, list):
            for c, v in zip(col, val):
                if c == self.config.columns.METRIC and metric is None:
                    metric = v
                elif c == self.config.columns.VALUE_TYPE and val_type is None:
                    val_type = v

        return ([self._get_mapped_string(v, period_type, metric, val_type) for v in val]
                if isinstance(val, list)
                else self._get_mapped_string(val, period_type, metric, val_type))