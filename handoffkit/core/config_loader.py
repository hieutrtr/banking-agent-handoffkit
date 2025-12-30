"""HandoffKit Configuration Loader.

This module provides utilities for loading HandoffKit configuration from
multiple sources including environment variables and YAML config files.

Configuration precedence (highest to lowest):
1. Explicit config passed to HandoffOrchestrator
2. Environment variables (HANDOFFKIT_*)
3. Config file (handoffkit.yaml or handoffkit.yml)
4. Default values

Example usage:
    >>> from handoffkit.core.config_loader import ConfigLoader
    >>> loader = ConfigLoader()
    >>> config = loader.load()  # Combines env vars and file config

    # Or load specific sources:
    >>> env_config = loader.load_from_env()
    >>> file_config = loader.load_from_file("config.yaml")
"""

import os
from pathlib import Path
from typing import Any, Optional

from handoffkit.core.config import (
    HandoffConfig,
    IntegrationConfig,
    RoutingConfig,
    SentimentConfig,
    TriggerConfig,
)
from handoffkit.core.exceptions import ConfigurationError


# Environment variable prefix
ENV_PREFIX = "HANDOFFKIT_"

# Environment variable to config path mappings
# Format: env_var_suffix -> (nested_path, type)
ENV_VAR_MAPPINGS: dict[str, tuple[str, type]] = {
    "FAILURE_THRESHOLD": ("triggers.failure_threshold", int),
    "SENTIMENT_THRESHOLD": ("triggers.sentiment_threshold", float),
    "CRITICAL_KEYWORDS": ("triggers.critical_keywords", list),
    "DIRECT_REQUEST_ENABLED": ("triggers.direct_request_enabled", bool),
    "CUSTOM_RULES_ENABLED": ("triggers.custom_rules_enabled", bool),
    "HELPDESK": ("integration.provider", str),
    "API_KEY": ("integration.api_key", str),
    "API_URL": ("integration.api_url", str),
    "ROUTING_STRATEGY": ("routing.strategy", str),
    "FALLBACK_QUEUE": ("routing.fallback_queue", str),
    "SENTIMENT_TIER": ("sentiment.tier", str),
    "MAX_CONTEXT_MESSAGES": ("max_context_messages", int),
    "MAX_CONTEXT_SIZE_KB": ("max_context_size_kb", int),
    "SUMMARY_MAX_WORDS": ("summary_max_words", int),
}

# Default config file names to search for
DEFAULT_CONFIG_FILES = ["handoffkit.yaml", "handoffkit.yml"]


def _coerce_value(value: str, target_type: type, var_name: str) -> Any:
    """Coerce a string value to the target type.

    Args:
        value: The string value from environment variable
        target_type: The target Python type
        var_name: The variable name for error messages

    Returns:
        The coerced value

    Raises:
        ConfigurationError: If the value cannot be coerced
    """
    if target_type == str:
        return value

    if target_type == int:
        try:
            return int(value)
        except ValueError:
            raise ConfigurationError(
                f"Invalid integer value for {var_name}: '{value}'. "
                f"Expected a whole number like '3' or '5'."
            )

    if target_type == float:
        try:
            return float(value)
        except ValueError:
            raise ConfigurationError(
                f"Invalid float value for {var_name}: '{value}'. "
                f"Expected a decimal number like '0.3' or '0.5'."
            )

    if target_type == bool:
        lower_value = value.lower().strip()
        if lower_value in ("true", "1", "yes", "on"):
            return True
        if lower_value in ("false", "0", "no", "off"):
            return False
        raise ConfigurationError(
            f"Invalid boolean value for {var_name}: '{value}'. "
            f"Expected 'true', 'false', '1', '0', 'yes', 'no', 'on', or 'off'."
        )

    if target_type == list:
        # Parse comma-separated list
        if not value.strip():
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    # Fallback to string
    return value


def _set_nested_value(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation path.

    Args:
        data: The dictionary to modify
        path: Dot-separated path like 'triggers.failure_threshold'
        value: The value to set
    """
    parts = path.split(".")
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def _get_nested_value(data: dict[str, Any], path: str) -> Optional[Any]:
    """Get a value from a nested dictionary using dot notation path.

    Args:
        data: The dictionary to read from
        path: Dot-separated path like 'triggers.failure_threshold'

    Returns:
        The value if found, None otherwise
    """
    parts = path.split(".")
    current = data

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]

    return current


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: The base dictionary
        override: The dictionary with overriding values

    Returns:
        A new dictionary with merged values
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


class ConfigLoader:
    """Loads HandoffKit configuration from multiple sources.

    This class provides methods to load configuration from environment
    variables, YAML files, or a combination of both with proper precedence.

    Configuration precedence (highest to lowest):
    1. Environment variables (HANDOFFKIT_*)
    2. Config file (handoffkit.yaml or handoffkit.yml)
    3. Default values

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load()

        >>> # With custom config file
        >>> loader = ConfigLoader(config_file="/path/to/config.yaml")
        >>> config = loader.load()
    """

    def __init__(
        self,
        config_file: Optional[str] = None,
        search_paths: Optional[list[str]] = None,
    ) -> None:
        """Initialize the config loader.

        Args:
            config_file: Optional path to a specific config file to load.
                        If not provided, searches for default config files.
            search_paths: Optional list of directories to search for config files.
                         Defaults to current working directory.
        """
        self._config_file = config_file
        self._search_paths = search_paths or ["."]

    def load_from_env(self) -> dict[str, Any]:
        """Load configuration from environment variables.

        Reads all HANDOFFKIT_* environment variables and converts them
        to a nested dictionary structure matching HandoffConfig.

        Returns:
            A dictionary with configuration values from environment variables.
            Only includes keys for variables that are actually set.

        Raises:
            ConfigurationError: If a value cannot be parsed to the expected type.

        Example:
            >>> import os
            >>> os.environ["HANDOFFKIT_FAILURE_THRESHOLD"] = "5"
            >>> loader = ConfigLoader()
            >>> env_config = loader.load_from_env()
            >>> env_config["triggers"]["failure_threshold"]
            5
        """
        config_data: dict[str, Any] = {}

        for suffix, (path, target_type) in ENV_VAR_MAPPINGS.items():
            env_var = f"{ENV_PREFIX}{suffix}"
            value = os.environ.get(env_var)

            if value is not None:
                coerced_value = _coerce_value(value, target_type, env_var)
                _set_nested_value(config_data, path, coerced_value)

        return config_data

    def load_from_file(self, file_path: Optional[str] = None) -> dict[str, Any]:
        """Load configuration from a YAML file.

        Args:
            file_path: Path to the config file. If not provided, searches
                      for default config files in the search paths.

        Returns:
            A dictionary with configuration values from the file.
            Returns empty dict if no config file is found.

        Raises:
            ConfigurationError: If the file exists but cannot be parsed.

        Example:
            >>> loader = ConfigLoader()
            >>> file_config = loader.load_from_file("handoffkit.yaml")
        """
        # Try to import yaml
        try:
            import yaml
        except ImportError:
            # PyYAML not installed, return empty config
            return {}

        # Determine file path
        path_to_load: Optional[Path] = None

        if file_path:
            path_to_load = Path(file_path)
        else:
            # Check for HANDOFFKIT_CONFIG_FILE env var
            env_config_file = os.environ.get(f"{ENV_PREFIX}CONFIG_FILE")
            if env_config_file:
                path_to_load = Path(env_config_file)
            else:
                # Search for default config files
                for search_path in self._search_paths:
                    for config_name in DEFAULT_CONFIG_FILES:
                        candidate = Path(search_path) / config_name
                        if candidate.exists():
                            path_to_load = candidate
                            break
                    if path_to_load:
                        break

        if path_to_load is None or not path_to_load.exists():
            return {}

        try:
            with open(path_to_load, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse config file '{path_to_load}': {e}"
            )
        except OSError as e:
            raise ConfigurationError(
                f"Failed to read config file '{path_to_load}': {e}"
            )

    def load(self) -> HandoffConfig:
        """Load configuration from all sources with proper precedence.

        Combines configuration from environment variables and config files,
        with environment variables taking precedence over file configuration.

        Returns:
            A HandoffConfig instance with merged configuration.

        Raises:
            ConfigurationError: If configuration values are invalid.

        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.load()
            >>> config.triggers.failure_threshold
            3
        """
        # Load from file first (lowest precedence)
        file_config = self.load_from_file(self._config_file)

        # Load from environment (higher precedence)
        env_config = self.load_from_env()

        # Merge configs (env overrides file)
        merged = _deep_merge(file_config, env_config)

        # Build config objects from merged data
        return self._build_config(merged)

    def _build_config(self, data: dict[str, Any]) -> HandoffConfig:
        """Build a HandoffConfig from a dictionary.

        Args:
            data: Dictionary with configuration values

        Returns:
            A HandoffConfig instance

        Raises:
            ConfigurationError: If values are invalid
        """
        try:
            # Build nested configs
            triggers_data = data.get("triggers", {})
            sentiment_data = data.get("sentiment", {})
            routing_data = data.get("routing", {})
            integration_data = data.get("integration", {})

            # Create nested config objects
            triggers = TriggerConfig(**triggers_data) if triggers_data else TriggerConfig()
            sentiment = SentimentConfig(**sentiment_data) if sentiment_data else SentimentConfig()
            routing = RoutingConfig(**routing_data) if routing_data else RoutingConfig()
            integration = IntegrationConfig(**integration_data) if integration_data else IntegrationConfig()

            # Build main config with top-level fields
            main_config_data: dict[str, Any] = {
                "triggers": triggers,
                "sentiment": sentiment,
                "routing": routing,
                "integration": integration,
            }

            # Add top-level fields if present
            for field in ["max_context_messages", "max_context_size_kb", "summary_max_words"]:
                if field in data:
                    main_config_data[field] = data[field]

            return HandoffConfig(**main_config_data)

        except Exception as e:
            raise ConfigurationError(
                f"Failed to build configuration: {e}. "
                f"Check that all values match expected types and ranges."
            )


def load_config(
    config_file: Optional[str] = None,
    use_env: bool = True,
    use_file: bool = True,
) -> HandoffConfig:
    """Convenience function to load HandoffKit configuration.

    This is the recommended way to load configuration from external sources.

    Args:
        config_file: Optional path to a specific config file
        use_env: Whether to load from environment variables (default: True)
        use_file: Whether to load from config files (default: True)

    Returns:
        A HandoffConfig instance

    Example:
        >>> from handoffkit import load_config
        >>> config = load_config()
        >>> config.triggers.failure_threshold
        3
    """
    loader = ConfigLoader(config_file=config_file)

    if use_env and use_file:
        return loader.load()

    if use_env:
        env_data = loader.load_from_env()
        return loader._build_config(env_data)

    if use_file:
        file_data = loader.load_from_file(config_file)
        return loader._build_config(file_data)

    # Neither source, return defaults
    return HandoffConfig()
