import functools
import inspect
from typing import Dict, Callable


class ProcessorProxyFacade:
    """Facade for data processing services.

    This facade provides a unified interface to access data processing functionality
    without exposing the individual processors. It dynamically dispatches method calls
    to the appropriate processor and injects only the common dependencies that each
    method can accept.
    """

    def __init__(self, logger=None, config=None, **processors):
        """
        Initialize the facade with common dependencies and processor instances.

        Args:
            logger: A logger instance to be injected into processor methods that accept it.
            config: A configuration object to be injected into processor methods that accept it.
            **processors: Keyword arguments where each key is a processor name 
                          (e.g., 'metrics', 'period') and value is the processor instance.
        """
        self._common_dependencies = {}
        if logger is not None:
            self._common_dependencies['logger'] = logger
        if config is not None:
            self._common_dependencies['config'] = config

        self._processors = processors
        self._method_map = self._build_method_map()

    def _build_method_map(self) -> Dict[str, Callable]:
        """
        Build a mapping of method names to processor methods with injected dependencies.

        Returns:
            Dict mapping method names to processor method callables with injected dependencies.
        """
        method_map = {}

        # For each processor
        for processor_name, processor in self._processors.items():
            # Get all public methods from the processor
            for method_name in dir(processor):
                if not method_name.startswith('_'):  # Only consider public methods
                    method = getattr(processor, method_name)
                    if callable(method):
                        # Wrap the method to inject common dependencies
                        wrapped_method = self._wrap_method_with_dependencies(method)
                        # Register the wrapped method with the facade
                        method_map[method_name] = wrapped_method

        return method_map

    def _wrap_method_with_dependencies(self, method: Callable) -> Callable:
        """
        Wrap a processor method to inject only the common dependencies it can accept.

        Uses function signature inspection to determine which dependencies can be injected.

        Args:
            method: The original processor method.

        Returns:
            A wrapped method that injects only the accepted common dependencies.
        """
        # Get the method signature
        sig = inspect.signature(method)
        param_names = set(sig.parameters.keys())

        # Check for **kwargs parameter
        has_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            # Create a dictionary of dependencies that this method can accept
            injectable_deps = {}

            if has_kwargs:
                # If the method accepts **kwargs, we can inject all dependencies
                injectable_deps = self._common_dependencies.copy()
            else:
                # Otherwise, only inject dependencies that match parameter names
                for dep_name, dep_value in self._common_dependencies.items():
                    if dep_name in param_names:
                        injectable_deps[dep_name] = dep_value

            # Add dependencies to kwargs without overwriting existing values
            for dep_name, dep_value in injectable_deps.items():
                if dep_name not in kwargs:
                    kwargs[dep_name] = dep_value

            return method(*args, **kwargs)

        return wrapper

    def __getattr__(self, name: str) -> Callable:
        """
        Dynamically dispatch method calls to the appropriate processor.

        Args:
            name: The name of the method being called.

        Returns:
            The processor method implementation with injected dependencies.

        Raises:
            AttributeError: If no processor implements the requested method.
        """
        if name in self._method_map:
            return self._method_map[name]

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")