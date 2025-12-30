"""Tests for HandoffKit configuration loader."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from handoffkit import HandoffConfig, TriggerConfig
from handoffkit.core.config_loader import (
    ConfigLoader,
    ENV_PREFIX,
    _coerce_value,
    _deep_merge,
    _get_nested_value,
    _set_nested_value,
    load_config,
)
from handoffkit.core.exceptions import ConfigurationError


class TestValueCoercion:
    """Test value type coercion from environment variables."""

    def test_coerce_string(self):
        """Test string coercion (passthrough)."""
        assert _coerce_value("hello", str, "TEST") == "hello"
        assert _coerce_value("", str, "TEST") == ""

    def test_coerce_int_valid(self):
        """Test valid integer coercion."""
        assert _coerce_value("3", int, "TEST") == 3
        assert _coerce_value("0", int, "TEST") == 0
        assert _coerce_value("-5", int, "TEST") == -5

    def test_coerce_int_invalid(self):
        """Test invalid integer raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            _coerce_value("not_an_int", int, "HANDOFFKIT_TEST")

        assert "Invalid integer value" in str(exc_info.value)
        assert "HANDOFFKIT_TEST" in str(exc_info.value)

    def test_coerce_float_valid(self):
        """Test valid float coercion."""
        assert _coerce_value("0.3", float, "TEST") == 0.3
        assert _coerce_value("1.0", float, "TEST") == 1.0
        assert _coerce_value("0", float, "TEST") == 0.0

    def test_coerce_float_invalid(self):
        """Test invalid float raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            _coerce_value("not_a_float", float, "HANDOFFKIT_TEST")

        assert "Invalid float value" in str(exc_info.value)

    def test_coerce_bool_true_values(self):
        """Test boolean coercion for true values."""
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "on", "ON"]:
            assert _coerce_value(value, bool, "TEST") is True

    def test_coerce_bool_false_values(self):
        """Test boolean coercion for false values."""
        for value in ["false", "False", "FALSE", "0", "no", "No", "off", "OFF"]:
            assert _coerce_value(value, bool, "TEST") is False

    def test_coerce_bool_invalid(self):
        """Test invalid boolean raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            _coerce_value("maybe", bool, "HANDOFFKIT_TEST")

        assert "Invalid boolean value" in str(exc_info.value)

    def test_coerce_list_comma_separated(self):
        """Test list coercion from comma-separated string."""
        result = _coerce_value("fraud,emergency,stolen", list, "TEST")
        assert result == ["fraud", "emergency", "stolen"]

    def test_coerce_list_with_spaces(self):
        """Test list coercion strips whitespace."""
        result = _coerce_value("fraud , emergency , stolen", list, "TEST")
        assert result == ["fraud", "emergency", "stolen"]

    def test_coerce_list_empty(self):
        """Test empty string returns empty list."""
        assert _coerce_value("", list, "TEST") == []
        assert _coerce_value("   ", list, "TEST") == []

    def test_coerce_list_single_item(self):
        """Test single item list."""
        result = _coerce_value("fraud", list, "TEST")
        assert result == ["fraud"]


class TestNestedDictOperations:
    """Test nested dictionary helper functions."""

    def test_set_nested_value_simple(self):
        """Test setting a simple nested value."""
        data: dict = {}
        _set_nested_value(data, "triggers.failure_threshold", 5)
        assert data == {"triggers": {"failure_threshold": 5}}

    def test_set_nested_value_deep(self):
        """Test setting a deeply nested value."""
        data: dict = {}
        _set_nested_value(data, "a.b.c.d", "value")
        assert data == {"a": {"b": {"c": {"d": "value"}}}}

    def test_set_nested_value_top_level(self):
        """Test setting a top-level value."""
        data: dict = {}
        _set_nested_value(data, "max_context_messages", 50)
        assert data == {"max_context_messages": 50}

    def test_get_nested_value_exists(self):
        """Test getting an existing nested value."""
        data = {"triggers": {"failure_threshold": 5}}
        assert _get_nested_value(data, "triggers.failure_threshold") == 5

    def test_get_nested_value_missing(self):
        """Test getting a missing nested value returns None."""
        data = {"triggers": {"failure_threshold": 5}}
        assert _get_nested_value(data, "triggers.missing") is None
        assert _get_nested_value(data, "missing.path") is None

    def test_deep_merge_simple(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self):
        """Test nested dictionary merge."""
        base = {"triggers": {"failure_threshold": 3, "sentiment_threshold": 0.3}}
        override = {"triggers": {"failure_threshold": 5}}
        result = _deep_merge(base, override)
        assert result == {
            "triggers": {"failure_threshold": 5, "sentiment_threshold": 0.3}
        }

    def test_deep_merge_preserves_base(self):
        """Test that original dictionaries are not modified."""
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert base == {"a": 1}
        assert override == {"b": 2}


class TestConfigLoaderEnv:
    """Test loading configuration from environment variables."""

    def test_load_failure_threshold(self):
        """Test loading HANDOFFKIT_FAILURE_THRESHOLD."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_FAILURE_THRESHOLD": "5"}):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["triggers"]["failure_threshold"] == 5

    def test_load_sentiment_threshold(self):
        """Test loading HANDOFFKIT_SENTIMENT_THRESHOLD."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_SENTIMENT_THRESHOLD": "0.5"}):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["triggers"]["sentiment_threshold"] == 0.5

    def test_load_critical_keywords(self):
        """Test loading HANDOFFKIT_CRITICAL_KEYWORDS."""
        with mock.patch.dict(
            os.environ, {"HANDOFFKIT_CRITICAL_KEYWORDS": "fraud,emergency,stolen"}
        ):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["triggers"]["critical_keywords"] == [
                "fraud",
                "emergency",
                "stolen",
            ]

    def test_load_helpdesk_provider(self):
        """Test loading HANDOFFKIT_HELPDESK."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_HELPDESK": "intercom"}):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["integration"]["provider"] == "intercom"

    def test_load_api_key(self):
        """Test loading HANDOFFKIT_API_KEY."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_API_KEY": "secret123"}):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["integration"]["api_key"] == "secret123"

    def test_load_api_url(self):
        """Test loading HANDOFFKIT_API_URL."""
        with mock.patch.dict(
            os.environ, {"HANDOFFKIT_API_URL": "https://api.example.com"}
        ):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["integration"]["api_url"] == "https://api.example.com"

    def test_load_max_context_messages(self):
        """Test loading HANDOFFKIT_MAX_CONTEXT_MESSAGES."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_MAX_CONTEXT_MESSAGES": "50"}):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["max_context_messages"] == 50

    def test_load_routing_strategy(self):
        """Test loading HANDOFFKIT_ROUTING_STRATEGY."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_ROUTING_STRATEGY": "least_busy"}):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["routing"]["strategy"] == "least_busy"

    def test_load_multiple_env_vars(self):
        """Test loading multiple environment variables."""
        env_vars = {
            "HANDOFFKIT_FAILURE_THRESHOLD": "2",
            "HANDOFFKIT_SENTIMENT_THRESHOLD": "0.4",
            "HANDOFFKIT_HELPDESK": "custom",
        }
        with mock.patch.dict(os.environ, env_vars):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            assert env_config["triggers"]["failure_threshold"] == 2
            assert env_config["triggers"]["sentiment_threshold"] == 0.4
            assert env_config["integration"]["provider"] == "custom"

    def test_load_empty_env_returns_empty_dict(self):
        """Test loading with no env vars returns empty dict."""
        with mock.patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            env_config = loader.load_from_env()
            # Should only include values that are actually set
            assert "triggers" not in env_config or env_config.get("triggers") == {}

    def test_invalid_env_var_raises_error(self):
        """Test invalid environment variable value raises ConfigurationError."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_FAILURE_THRESHOLD": "not_int"}):
            loader = ConfigLoader()
            with pytest.raises(ConfigurationError):
                loader.load_from_env()


class TestConfigLoaderFile:
    """Test loading configuration from YAML files."""

    def test_load_from_yaml_file(self):
        """Test loading config from a YAML file."""
        config_content = {
            "triggers": {"failure_threshold": 4, "sentiment_threshold": 0.4},
            "max_context_messages": 75,
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_content, f)
            f.flush()

            try:
                loader = ConfigLoader()
                file_config = loader.load_from_file(f.name)
                assert file_config["triggers"]["failure_threshold"] == 4
                assert file_config["triggers"]["sentiment_threshold"] == 0.4
                assert file_config["max_context_messages"] == 75
            finally:
                os.unlink(f.name)

    def test_load_from_default_config_file(self):
        """Test loading from default config file name."""
        config_content = {"triggers": {"failure_threshold": 2}}

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "handoffkit.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config_content, f)

            loader = ConfigLoader(search_paths=[tmpdir])
            file_config = loader.load_from_file()
            assert file_config["triggers"]["failure_threshold"] == 2

    def test_load_from_yml_extension(self):
        """Test loading from .yml extension."""
        config_content = {"triggers": {"failure_threshold": 3}}

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "handoffkit.yml"
            with open(config_path, "w") as f:
                yaml.dump(config_content, f)

            loader = ConfigLoader(search_paths=[tmpdir])
            file_config = loader.load_from_file()
            assert file_config["triggers"]["failure_threshold"] == 3

    def test_load_from_env_config_file_path(self):
        """Test loading from HANDOFFKIT_CONFIG_FILE env var."""
        config_content = {"triggers": {"failure_threshold": 5}}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_content, f)
            f.flush()

            try:
                with mock.patch.dict(
                    os.environ, {"HANDOFFKIT_CONFIG_FILE": f.name}
                ):
                    loader = ConfigLoader()
                    file_config = loader.load_from_file()
                    assert file_config["triggers"]["failure_threshold"] == 5
            finally:
                os.unlink(f.name)

    def test_missing_file_returns_empty_dict(self):
        """Test missing config file returns empty dict."""
        loader = ConfigLoader(search_paths=["/nonexistent/path"])
        file_config = loader.load_from_file()
        assert file_config == {}

    def test_explicit_missing_file_returns_empty_dict(self):
        """Test explicit missing file path returns empty dict."""
        loader = ConfigLoader()
        file_config = loader.load_from_file("/nonexistent/config.yaml")
        assert file_config == {}

    def test_invalid_yaml_raises_error(self):
        """Test invalid YAML file raises ConfigurationError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            try:
                loader = ConfigLoader()
                with pytest.raises(ConfigurationError) as exc_info:
                    loader.load_from_file(f.name)
                assert "Failed to parse" in str(exc_info.value)
            finally:
                os.unlink(f.name)


class TestConfigLoaderPrecedence:
    """Test configuration precedence rules."""

    def test_env_overrides_file(self):
        """Test environment variables override file config."""
        file_config = {"triggers": {"failure_threshold": 2}}
        env_vars = {"HANDOFFKIT_FAILURE_THRESHOLD": "5"}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(file_config, f)
            f.flush()

            try:
                with mock.patch.dict(os.environ, env_vars):
                    loader = ConfigLoader(config_file=f.name)
                    config = loader.load()
                    # Env var should win
                    assert config.triggers.failure_threshold == 5
            finally:
                os.unlink(f.name)

    def test_file_provides_defaults_for_missing_env(self):
        """Test file provides values when env vars not set."""
        file_config = {
            "triggers": {"failure_threshold": 2, "sentiment_threshold": 0.4}
        }
        env_vars = {"HANDOFFKIT_FAILURE_THRESHOLD": "5"}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(file_config, f)
            f.flush()

            try:
                with mock.patch.dict(os.environ, env_vars, clear=False):
                    loader = ConfigLoader(config_file=f.name)
                    config = loader.load()
                    # Env var wins for failure_threshold
                    assert config.triggers.failure_threshold == 5
                    # File provides sentiment_threshold
                    assert config.triggers.sentiment_threshold == 0.4
            finally:
                os.unlink(f.name)


class TestConfigLoaderIntegration:
    """Test full ConfigLoader integration."""

    def test_load_returns_handoff_config(self):
        """Test load() returns a HandoffConfig instance."""
        loader = ConfigLoader()
        config = loader.load()
        assert isinstance(config, HandoffConfig)

    def test_load_with_env_vars(self):
        """Test load() with environment variables."""
        env_vars = {
            "HANDOFFKIT_FAILURE_THRESHOLD": "4",
            "HANDOFFKIT_SENTIMENT_THRESHOLD": "0.5",
        }
        with mock.patch.dict(os.environ, env_vars):
            loader = ConfigLoader()
            config = loader.load()
            assert config.triggers.failure_threshold == 4
            assert config.triggers.sentiment_threshold == 0.5

    def test_load_preserves_defaults(self):
        """Test load() preserves defaults for unset values."""
        loader = ConfigLoader()
        config = loader.load()
        # Should have default values
        assert config.triggers.failure_threshold == 3
        assert config.triggers.sentiment_threshold == 0.3
        assert config.max_context_messages == 100

    def test_load_config_convenience_function(self):
        """Test load_config() convenience function."""
        config = load_config()
        assert isinstance(config, HandoffConfig)

    def test_load_config_with_file_only(self):
        """Test load_config with use_env=False."""
        env_vars = {"HANDOFFKIT_FAILURE_THRESHOLD": "5"}
        with mock.patch.dict(os.environ, env_vars):
            config = load_config(use_env=False)
            # Should NOT pick up env var
            assert config.triggers.failure_threshold == 3  # default

    def test_load_config_with_env_only(self):
        """Test load_config with use_file=False."""
        env_vars = {"HANDOFFKIT_FAILURE_THRESHOLD": "5"}
        with mock.patch.dict(os.environ, env_vars):
            config = load_config(use_file=False)
            assert config.triggers.failure_threshold == 5


class TestConfigLoaderValidation:
    """Test configuration validation."""

    def test_invalid_failure_threshold_range(self):
        """Test invalid failure_threshold (out of range) raises error."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_FAILURE_THRESHOLD": "10"}):
            loader = ConfigLoader()
            with pytest.raises(ConfigurationError):
                loader.load()

    def test_invalid_sentiment_threshold_range(self):
        """Test invalid sentiment_threshold (out of range) raises error."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_SENTIMENT_THRESHOLD": "2.0"}):
            loader = ConfigLoader()
            with pytest.raises(ConfigurationError):
                loader.load()

    def test_invalid_routing_strategy(self):
        """Test invalid routing strategy raises error."""
        with mock.patch.dict(os.environ, {"HANDOFFKIT_ROUTING_STRATEGY": "invalid"}):
            loader = ConfigLoader()
            with pytest.raises(ConfigurationError):
                loader.load()
