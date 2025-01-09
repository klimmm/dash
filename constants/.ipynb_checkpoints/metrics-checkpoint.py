# constants/metrics.py

from typing import Dic

# Direct Metrics
METRICS_DIRECT: Dict[str, Dict[str, str]] = {
    'direct_premiums': {'label': 'Direct Premiums', 'type': 'value'},
    'direct_losses': {'label': 'Direct Losses', 'type': 'value'},
    'ceded_premiums': {'label': 'Ceded Premiums', 'type': 'value'},
    'ceded_losses': {'label': 'Ceded Losses', 'type': 'value'},
    # ... (rest of METRICS_DIRECT)
}

# Inward Metrics
METRICS_INWARD: Dict[str, Dict[str, str]] = {
    'inward_premiums': {'label': 'Inward Premiums', 'type': 'value'},
    'inward_losses': {'label': 'Inward Losses', 'type': 'value'},
    # ... (rest of METRICS_INWARD)
}

# Reinsurance Metrics
REINSURANCE_METRICS: Dict[str, Dict[str, str]] = {
    'ceded_premiums': {'label': 'Ceded Premiums', 'type': 'value'},
    'ceded_losses': {'label': 'Ceded Losses', 'type': 'value'},
    'inward_premiums': {'label': 'Inward Premiums', 'type': 'value'},
    'inward_losses': {'label': 'Inward Losses', 'type': 'value'},
    # ... (rest of REINSURANCE_METRICS)
}

# Combined Metrics
METRICS: Dict[str, Dict[str, str]] = {
    **METRICS_DIRECT,
    **METRICS_INWARD,
    **REINSURANCE_METRICS,
    # Add other combined metrics if any
}
