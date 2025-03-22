import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from application.config import (
    AppConfig, Columns, ValueTypes, SpecialValues,
    DefaultValues, ViewModes, FormatConfig,
    METRICS_FOR_MARKET_SHARE
)
from infrastructure.repositories import InsuranceRepository
from infrastructure.logger import (
    setup_logging, logger, dash_callback,
    configure_callback_logger, pipe_with_logging
)
from domain import METRICS_MAPPING, MetricsFormulas
from application.core.service_factory import ServiceFactory


@dataclass
class ServiceBundle:
    metrics_service: Any
    lines_service: Any
    processor_orchestrator: Any
    formatting_facade: Any
    button_service: Any
    dropdown_service: Any


@dataclass
class AppConfiguration:
    # App config
    app_config: Any
    columns: Any
    value_types: Any
    special_values: Any
    default_values: Any
    view_modes: Any
    format_config: Any

    # Domain config
    metrics_mapping: Dict
    metrics_formulas: Any
    metrics_for_market_share: List

    # Technical services
    debug_handler: Any
    logger: Any
    dash_callback: Any
    pipe_with_logging: Any


def initialize_application():
    """Initialize all application components and services"""
    # Set up logging
    debug_handler = setup_logging(
        console_level=logging.DEBUG,
        file_level=logging.DEBUG,
        log_file='app.log'
    )
    configure_callback_logger()

    # Create consolidated configuration
    config = AppConfiguration(
        # App config
        app_config=AppConfig,
        columns=Columns,
        value_types=ValueTypes,
        special_values=SpecialValues,
        default_values=DefaultValues,
        view_modes=ViewModes,
        format_config=FormatConfig,

        # Domain config
        metrics_mapping=METRICS_MAPPING,
        metrics_formulas=MetricsFormulas,
        metrics_for_market_share=METRICS_FOR_MARKET_SHARE,

        # Technical services
        debug_handler=debug_handler,
        logger=logger,
        dash_callback=dash_callback,
        pipe_with_logging=pipe_with_logging
    )

    # Load data
    repo = InsuranceRepository(config)
    df_158, df_162 = repo.load_dataframes()

    # Create service factory and initialize all services
    factory = ServiceFactory(config)
    service_bundle = factory.create_all_services(df_158, df_162)

    return service_bundle, config