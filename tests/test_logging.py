"""Tests for HandoffKit structured logging utilities.

This module tests the JSON formatter, logging configuration, PII masking,
and other logging utilities.
"""

import io
import json
import logging
import re
from datetime import datetime

import pytest

from handoffkit.utils.logging import (
    JSONFormatter,
    LogContext,
    TextFormatter,
    get_logger,
    is_logging_configured,
    log_duration,
    log_with_context,
    mask_pii,
    reset_logging,
    setup_logging,
)


class TestJSONFormatter:
    """Test JSONFormatter class."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()

    def test_format_produces_valid_json(self):
        """Test that format() produces valid JSON output."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_output_has_required_fields(self):
        """Test that JSON output contains all required fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="handoffkit.orchestrator",
            level=logging.INFO,
            pathname="orchestrator.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        # Check required fields
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "logger" in parsed
        assert "message" in parsed
        assert "module" in parsed
        assert "function" in parsed

    def test_timestamp_is_iso8601_format(self):
        """Test that timestamp is in ISO 8601 format."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        # ISO 8601 format should be parseable
        timestamp = parsed["timestamp"]
        # Should contain T separator and timezone info
        assert "T" in timestamp
        # Should be parseable as datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_level_is_string(self):
        """Test that level is a string like INFO, DEBUG, etc."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "WARNING"

    def test_custom_fields_appear_in_output(self):
        """Test that custom fields from extra dict appear in JSON output."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add custom fields
        record.handoff_id = "abc123"
        record.user_id = "user456"
        record.confidence = 0.85

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["handoff_id"] == "abc123"
        assert parsed["user_id"] == "user456"
        assert parsed["confidence"] == 0.85

    def test_exception_formatting_in_json(self):
        """Test that exceptions are properly formatted in JSON."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "exception" in parsed
        assert "exception_type" in parsed
        assert parsed["exception_type"] == "ValueError"
        assert "Test error" in parsed["exception"]

    def test_message_with_format_args(self):
        """Test that message with format args is properly formatted."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Processing %s items",
            args=(5,),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "Processing 5 items"


class TestSetupLogging:
    """Test setup_logging function."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()

    def teardown_method(self):
        """Reset logging after each test."""
        reset_logging()

    def test_setup_logging_configures_logger(self):
        """Test that setup_logging configures the handoffkit logger."""
        setup_logging()
        assert is_logging_configured()

    def test_log_level_from_env_variable(self, monkeypatch):
        """Test that LOG_LEVEL environment variable is respected."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        setup_logging()

        logger = logging.getLogger("handoffkit")
        assert logger.level == logging.DEBUG

    def test_handoffkit_log_level_takes_precedence(self, monkeypatch):
        """Test that HANDOFFKIT_LOG_LEVEL takes precedence over LOG_LEVEL."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        monkeypatch.setenv("HANDOFFKIT_LOG_LEVEL", "DEBUG")
        setup_logging()

        logger = logging.getLogger("handoffkit")
        assert logger.level == logging.DEBUG

    def test_log_format_json(self, monkeypatch):
        """Test that LOG_FORMAT=json uses JSONFormatter."""
        monkeypatch.setenv("LOG_FORMAT", "json")
        setup_logging()

        logger = logging.getLogger("handoffkit")
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_log_format_text(self, monkeypatch):
        """Test that LOG_FORMAT=text uses TextFormatter."""
        monkeypatch.setenv("LOG_FORMAT", "text")
        setup_logging()

        logger = logging.getLogger("handoffkit")
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, TextFormatter)

    def test_default_log_format_is_json(self):
        """Test that default log format is JSON."""
        setup_logging()

        logger = logging.getLogger("handoffkit")
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_no_duplicate_handlers(self):
        """Test that repeated setup_logging calls don't add duplicate handlers."""
        setup_logging()
        setup_logging()
        setup_logging()

        logger = logging.getLogger("handoffkit")
        assert len(logger.handlers) == 1

    def test_force_reconfigures(self):
        """Test that force=True allows reconfiguration."""
        setup_logging(level=logging.INFO)
        logger = logging.getLogger("handoffkit")
        assert logger.level == logging.INFO

        setup_logging(level=logging.DEBUG, force=True)
        assert logger.level == logging.DEBUG


class TestGetLogger:
    """Test get_logger function."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()

    def teardown_method(self):
        """Reset logging after each test."""
        reset_logging()

    def test_get_logger_returns_child_logger(self):
        """Test that get_logger returns a child logger."""
        logger = get_logger("orchestrator")
        assert logger.name == "handoffkit.orchestrator"

    def test_get_logger_without_name_returns_root(self):
        """Test that get_logger without name returns root logger."""
        logger = get_logger()
        assert logger.name == "handoffkit"

    def test_get_logger_auto_initializes(self):
        """Test that get_logger auto-initializes logging if not configured."""
        assert not is_logging_configured()
        logger = get_logger("test")
        assert is_logging_configured()
        assert logger.name == "handoffkit.test"


class TestLogContext:
    """Test LogContext context manager."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()
        LogContext._context = {}

    def test_log_context_adds_fields(self):
        """Test that LogContext adds fields to context."""
        with LogContext(handoff_id="abc123"):
            context = LogContext.get_context()
            assert context["handoff_id"] == "abc123"

    def test_log_context_restores_previous(self):
        """Test that LogContext restores previous context on exit."""
        with LogContext(handoff_id="abc123"):
            assert LogContext.get_context()["handoff_id"] == "abc123"

        assert "handoff_id" not in LogContext.get_context()

    def test_nested_log_context(self):
        """Test nested LogContext managers."""
        with LogContext(handoff_id="abc123"):
            assert LogContext.get_context()["handoff_id"] == "abc123"

            with LogContext(user_id="user456"):
                context = LogContext.get_context()
                assert context["handoff_id"] == "abc123"
                assert context["user_id"] == "user456"

            # user_id should be gone
            context = LogContext.get_context()
            assert context["handoff_id"] == "abc123"
            assert "user_id" not in context


class TestLogWithContext:
    """Test log_with_context function."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()
        LogContext._context = {}

    def test_log_with_context_includes_extra_fields(self):
        """Test that log_with_context includes extra fields."""
        setup_logging(level=logging.DEBUG, log_format="json")
        logger = get_logger("test")

        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        log_with_context(logger, logging.INFO, "Test message", handoff_id="abc123")

        output = stream.getvalue()
        parsed = json.loads(output)
        assert parsed["handoff_id"] == "abc123"

    def test_log_with_context_includes_context_fields(self):
        """Test that log_with_context includes LogContext fields."""
        setup_logging(level=logging.DEBUG, log_format="json")
        logger = get_logger("test")

        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

        with LogContext(user_id="user456"):
            log_with_context(logger, logging.INFO, "Test message", handoff_id="abc123")

        output = stream.getvalue()
        parsed = json.loads(output)
        assert parsed["handoff_id"] == "abc123"
        assert parsed["user_id"] == "user456"


class TestLogDuration:
    """Test log_duration context manager."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()

    def test_log_duration_logs_start_and_end(self):
        """Test that log_duration logs start and end messages."""
        setup_logging(level=logging.DEBUG, log_format="json")
        logger = get_logger("test")

        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        with log_duration(logger, "test_operation"):
            pass

        output = stream.getvalue()
        lines = [line for line in output.strip().split("\n") if line]

        assert len(lines) == 2
        start_log = json.loads(lines[0])
        end_log = json.loads(lines[1])

        assert "started" in start_log["message"]
        assert "completed" in end_log["message"]
        assert "duration_ms" in end_log

    def test_log_duration_includes_extra_fields(self):
        """Test that log_duration includes extra fields."""
        setup_logging(level=logging.DEBUG, log_format="json")
        logger = get_logger("test")

        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        with log_duration(logger, "trigger_evaluation", trigger_type="sentiment"):
            pass

        output = stream.getvalue()
        lines = [line for line in output.strip().split("\n") if line]

        for line in lines:
            parsed = json.loads(line)
            assert parsed["trigger_type"] == "sentiment"


class TestMaskPii:
    """Test mask_pii function."""

    def test_mask_account_numbers(self):
        """Test that account numbers are masked."""
        result = mask_pii("Account number is 12345678")
        assert "12345678" not in result
        assert "****5678" in result

    def test_mask_long_account_numbers(self):
        """Test that longer account numbers are masked."""
        result = mask_pii("Card number is 1234567890123456")
        assert "1234567890123456" not in result
        assert "****3456" in result

    def test_mask_email_addresses(self):
        """Test that email addresses are masked."""
        result = mask_pii("Email is user@example.com")
        assert "user@example.com" not in result
        assert "u***@example.com" in result

    def test_mask_phone_numbers(self):
        """Test that phone numbers are masked."""
        result = mask_pii("Phone is 555-123-4567")
        assert "555-123-4567" not in result
        assert "***-***-****" in result

    def test_mask_phone_with_parens(self):
        """Test that phone numbers with parentheses are masked."""
        result = mask_pii("Phone is (555) 123-4567")
        assert "(555) 123-4567" not in result
        assert "***-***-****" in result

    def test_mask_ssn(self):
        """Test that SSNs are masked."""
        result = mask_pii("SSN is 123-45-6789")
        assert "123-45-6789" not in result
        assert "***-**-****" in result

    def test_mask_multiple_pii(self):
        """Test that multiple PII items are masked."""
        result = mask_pii(
            "Account 12345678 for user@example.com, phone 555-123-4567"
        )
        assert "12345678" not in result
        assert "user@example.com" not in result
        assert "555-123-4567" not in result

    def test_preserves_non_pii_text(self):
        """Test that non-PII text is preserved."""
        result = mask_pii("Hello, this is a normal message without PII")
        assert result == "Hello, this is a normal message without PII"


class TestResetLogging:
    """Test reset_logging function."""

    def test_reset_clears_handlers(self):
        """Test that reset_logging clears handlers."""
        setup_logging()
        logger = logging.getLogger("handoffkit")
        assert len(logger.handlers) > 0

        reset_logging()
        assert len(logger.handlers) == 0

    def test_reset_clears_configured_flag(self):
        """Test that reset_logging clears the configured flag."""
        setup_logging()
        assert is_logging_configured()

        reset_logging()
        assert not is_logging_configured()


class TestTextFormatter:
    """Test TextFormatter class."""

    def test_text_formatter_output(self):
        """Test that TextFormatter produces human-readable output."""
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="handoffkit.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)

        # Should contain key parts
        assert "handoffkit.test" in output
        assert "INFO" in output
        assert "Test message" in output


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def setup_method(self):
        """Reset logging before each test."""
        reset_logging()

    def teardown_method(self):
        """Reset logging after each test."""
        reset_logging()

    def test_full_logging_workflow(self):
        """Test complete logging workflow."""
        setup_logging(level=logging.DEBUG, log_format="json")
        logger = get_logger("integration")

        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        # Log with context using log_with_context helper
        with LogContext(session_id="sess123"):
            log_with_context(
                logger, logging.INFO, "Starting process", handoff_id="abc123"
            )

            with log_duration(logger, "process_step"):
                pass

        output = stream.getvalue()
        lines = [line for line in output.strip().split("\n") if line]

        # Should have 3 log entries: start, duration start, duration end
        assert len(lines) == 3

        # First log should have both context and extra
        first_log = json.loads(lines[0])
        assert first_log["handoff_id"] == "abc123"
        assert first_log["session_id"] == "sess123"
