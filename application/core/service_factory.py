from typing import Dict, Any
from dataclasses import dataclass
import pandas as pd

from application.config import (
     TreeServiceConfig,
     UIComponentConfigManager,
     SIDEBAR_CONFIG,
     FiltersSummaryConfig
)
from application.processors import (
     MetricsProcessor, PeriodProcessor, GrowthProcessor,
     MarketShareProcessor, RankProcessor, AggregationProcessor,
     ProcessorProxyFacade
)
from application.visualization import (
    BarChartService,
    DataTableService,
    PivotService,
    DimensionalDataService
)
from application.services import (
     UIService,
     TreeUIService,
     SelectionServiceFacade,
     FormattingServiceFacade
)
from domain import DataStructure, InsurersService, PeriodService, MetricsService, LinesService
from application.core.process_orchestrator import ProcessOrchestrator
from application.core.context import ProcessingContext


@dataclass
class ServiceContainer:
    """Container for domain services."""
    insurers_service: Any
    metrics_service: Any
    lines_service: Any
    period_service: Any


@dataclass
class ServiceBundle:
    """Bundle of core services needed for external use."""
    tree_services: Any
    processor_orchestrator: Any
    formatting_facade: Any
    ui_service: Any
    context: Any
    selection_facade: Any
    ui_configs: Any


class ServiceFactory:
    """Factory for creating and managing application services."""

    def __init__(self, config):
        self.config = config
        self._services: Dict[str, Any] = {}

    def create_all_services(self, df_158: pd.DataFrame, df_162: pd.DataFrame
                            ) -> ServiceBundle:
        """Create and initialize all application services."""

        # Get all configurations
        tree_config = TreeServiceConfig()

        base_services = {}
        ui_services = {}  # Will contain only 'metric' and 'line'

        # Initialize all services
        for component_id, config in tree_config.get_all_configs().items():
            # Create base TreeService for all components
            base_service = DataStructure(self.config, structure_config=config)
            base_services[component_id] = base_service

            if component_id in ['metric', 'line']:
                ui_services[component_id] = TreeUIService(base_service, tree_config=config)

        domain_services = ServiceContainer(
            metrics_service=MetricsService(ui_services['metric']),
            lines_service=LinesService(ui_services['line']),
            insurers_service=InsurersService(base_services['insurer']),
            period_service=PeriodService(self.config)
        )

        # Create facades
        facades = {
            'selection_facade': SelectionServiceFacade(domain_services),
            'formatting_facade': FormattingServiceFacade(domain_services, self.config.metrics_mapping)
        }

        ui_service = UIService(self.config, facades['selection_facade'])

        processing_context = ProcessingContext(self.config)
        processing_context.set_dataframes(df_158, df_162)
        # Create processors
        processors = {
            'metrics_processor': MetricsProcessor(
                self.config.metrics_formulas.get_default_formulas()),
            'period_processor': PeriodProcessor(),
            'market_share_processor': MarketShareProcessor(
                self.config.metrics_for_market_share),
            'rank_processor': RankProcessor(),
            'aggregation_processor': AggregationProcessor(),
            'growth_processor': GrowthProcessor()
        }

        # Create visualization services
        viz_services = {
            'pivot_service': PivotService(),
            'data_table_service': DataTableService(facades['formatting_facade']),
            'bar_chart_service': BarChartService(facades['formatting_facade']),
            'dimensional_data_service': DimensionalDataService(
                facades['selection_facade'])
        }

        # Create orchestrator
        orchestrator = ProcessOrchestrator(
            self.config,
            data_processing=ProcessorProxyFacade(
                self.config.logger, self.config, **processors),
            visualization=ProcessorProxyFacade(
                self.config.logger, self.config, **viz_services),
            selection_facade=facades['selection_facade'],
            context=processing_context
        )

        facades['selection_facade'].setup_period_options(df_158, df_162)

        controls_config = UIComponentConfigManager()
        sidebar_config = SIDEBAR_CONFIG
        filters_summary_config = FiltersSummaryConfig()
        ui_configs = {
            'controls_config': controls_config,
            'tree_config': tree_config,
            'sidebar_config': sidebar_config,
            'filters_summary_config': filters_summary_config
        }

        return ServiceBundle(
            tree_services=ui_services,
            processor_orchestrator=orchestrator,
            formatting_facade=facades['formatting_facade'],
            ui_service=ui_service,
            context=processing_context,
            ui_configs=ui_configs,
            selection_facade=facades['selection_facade']
        )