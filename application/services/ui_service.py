from typing import Optional


class UIService:
    """Service for managing button configurations and processors."""
    config_multi = {
        'index-col': False,
        'pivot-col': True,
        'view-metrics': True,
        'top-insurers': False,
        'period-type': False,
        'reporting-form': False,
        'number-of-periods': False,
        'view-mode': False,
        'selected-insurers': True,
        'end-quarter': False,
        'log_level': True,
        'module': True
    }
    context_attributes = {
        'pivot-col': 'pivot_cols',
        'index-col': 'index_cols',
        'view-metrics': 'view_metrics',
        'top-insurers': 'top_insurers',
        'period-type': 'period_type',
        'reporting-form': 'reporting_form',
        'number-of-periods': 'num_periods',
        'view-mode': 'view_mode',
        'selected-insurers': 'insurers'
    }
    processors = {
        'view-metrics': 'process_view_metrics',
        'top-insurers': 'process_top_insurers',
        'number-of-periods': 'process_number_of_periods',
        'index-col': 'process_index_pivot_split',
        'pivot-col': 'process_index_pivot_split',
        'view-mode': 'process_view_mode',
        'selected-insurers': 'process_selected_insurers'
    }

    def __init__(self, config, selection_facade):
        self.config = config
        self.columns = self.config.columns
        self.value_types = self.config.value_types
        self.view_modes = self.config.view_modes
        self.logger = self.config.logger
        self.special_values = self.config.special_values
        self.selection_facade = selection_facade

    def __getattr__(self, name):
        return getattr(self.selection_facade, name)

    def get_processor(self, key: Optional[str] = None) -> str:
        """"""
        return self.processors.get(key) if key else self.processors

    def calculate_new_values(self, key, input_value, current_values):
        if not self.config_multi.get(key, False):
            return input_value
        else:
            if input_value in current_values:
                return [v for v in current_values if v != input_value]
            else:
                return current_values + [input_value]

    def process_index_pivot_split(self, key, input_value, context, current_values):
        """"""
        df = context.processed_df
        selected_insurers = context.insurers
        additional_pivot = {self.columns.VALUE_TYPE, self.columns.YEAR_QUARTER}
        value_col = {self.columns.VALUE}
        self.logger.debug(f"index cols {context.index_cols}")
        pivot_cols = set(context.pivot_cols) - additional_pivot
        index_cols = {context.index_cols} if isinstance(
            context.index_cols, str) else set(context.index_cols)
        index_cols.discard(
            input_value) if key == "pivot-col" else pivot_cols.discard(input_value)
        key_func = lambda col: (df[col].nunique(), col)
        index_cols = sorted(index_cols, key=key_func)
        pivot_cols = sorted(pivot_cols, key=key_func) + list(additional_pivot)
        split_cols = list(
            set(df.columns) - set(index_cols) - set(pivot_cols) - value_col)
        if selected_insurers[0].startswith('top-') and len(index_cols) > 0:
            pivot_cols.extend([v for v in index_cols if v != index_cols[0]])
            index_cols = [index_cols[0]]
        context.update_state(
            split_cols=split_cols, index_cols=index_cols, pivot_cols=pivot_cols)

    def process_view_metrics(self, key, input_value, context, current_values):
        """"""
        vm, vt = self.view_modes, self.value_types
        filtered_value_types = [vt.BASE]

        vm_to_vt_map = {
            vm.MARKET_SHARE: vt.MARKET_SHARE,
            vm.RANK: vt.RANK,
        }
        for mode, value_type in vm_to_vt_map.items():
            if mode in current_values:
                filtered_value_types.append(value_type)

        if vm.CHANGE in current_values:
            filtered_value_types.append(
                vt.BASE + vt.CHANGE_SUFFIX)
            for mode in [vm.MARKET_SHARE, vm.RANK]:
                if mode in current_values:
                    filtered_value_types.append(
                        vm_to_vt_map[mode] + vt.CHANGE_SUFFIX)
        context.update_state(value_types=filtered_value_types)

    def process_view_mode(self, key, input_value, context, current_values):
        """"""
        if 'combined' in current_values:
            view_mode = ['table', 'chart']
        else:
            view_mode = [current_values]
        context.update_state(view_mode=view_mode)

    def process_top_insurers(self, key, input_value, context, current_values):
        """"""
        if input_value != self.special_values.TOTAL_INSURER:
            new_values = [f"top-{int(input_value)}"]
        else:
            new_values = [self.special_values.TOTAL_INSURER]
        context.update_state(insurers=new_values)

    def process_number_of_periods(self, key, input_value, context, current_values):
        """"""

    def process_selected_insurers(self, key, input_value, context, current_values):
        """"""
        insurers = ([v for v in current_values
                     if not v.startswith(('top-', 'total'))])
        context.update_state(insurers=insurers)

    def process_input(self, key, input_value, context):
        """"""
        processor_name = self.get_processor(key)

        if key in self.context_attributes:
            attr_name = self.context_attributes[key]
            current_values = getattr(context, attr_name)
            new_values = self.calculate_new_values(key, input_value, current_values)
            update_kwargs = {attr_name: new_values}
            context.update_state(**update_kwargs)

        if processor_name and hasattr(self, processor_name):
            processor_method = getattr(self, processor_name)
            processor_method(key, input_value, context, new_values)