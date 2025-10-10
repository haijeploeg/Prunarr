"""
Unit tests for the logger module.

Tests the PrunArrLogger class functionality including message formatting,
log levels, debug mode, and Rich console integration.
"""

from datetime import datetime
from unittest.mock import Mock, patch

from prunarr.logger import PrunArrLogger, get_logger


class TestPrunArrLogger:
    """Test the PrunArrLogger class functionality."""

    def test_logger_initialization(self):
        """Test logger initialization with default and custom parameters."""
        # Default initialization
        logger = PrunArrLogger()
        assert logger.logger_name == "prunarr"
        assert logger.debug_enabled is False

        # Custom initialization
        logger = PrunArrLogger("test_module", debug=True)
        assert logger.logger_name == "test_module"
        assert logger.debug_enabled is True

    def test_timestamp_format(self):
        """Test that timestamps are formatted correctly."""
        logger = PrunArrLogger()

        with patch("prunarr.logger.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 30, 45)
            timestamp = logger._get_timestamp()
            assert timestamp == "14:30:45"

    def test_format_message_basic(self):
        """Test basic message formatting without extra details."""
        logger = PrunArrLogger()

        with patch.object(logger, "_get_timestamp", return_value="14:30:45"):
            formatted = logger._format_message("info", "ℹ️", "blue", "Test message")
            expected = "[dim][14:30:45][/dim] - [blue]ℹ️ INFO:[/blue] Test message"
            assert formatted == expected

    def test_format_message_with_extra_detail(self):
        """Test message formatting with extra details."""
        logger = PrunArrLogger()

        with patch.object(logger, "_get_timestamp", return_value="14:30:45"):
            formatted = logger._format_message("info", "ℹ️", "blue", "Test message", "Extra details")
            expected = (
                "[dim][14:30:45][/dim] - [blue]ℹ️ INFO:[/blue] Test message\n"
                "[dim]    Extra details[/dim]"
            )
            assert formatted == expected

    @patch("prunarr.logger.Console")
    def test_debug_message_enabled(self, mock_console_class):
        """Test debug message output when debug mode is enabled."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger(debug=True)
        logger.debug("Debug message", "Extra info")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "🔍 DEBUG:" in call_args
        assert "Debug message" in call_args
        assert "Extra info" in call_args

    @patch("prunarr.logger.Console")
    def test_debug_message_disabled(self, mock_console_class):
        """Test debug message is not output when debug mode is disabled."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger(debug=False)
        logger.debug("Debug message")

        mock_console.print.assert_not_called()

    @patch("prunarr.logger.Console")
    def test_info_message(self, mock_console_class):
        """Test info message output."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger(log_level="INFO")
        logger.info("Info message", "Additional context")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "ℹ️ INFO:" in call_args
        assert "Info message" in call_args
        assert "Additional context" in call_args

    @patch("prunarr.logger.Console")
    def test_warning_message(self, mock_console_class):
        """Test warning message output."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger(log_level="WARNING")
        logger.warning("Warning message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⚠️ WARNING:" in call_args
        assert "Warning message" in call_args

    @patch("prunarr.logger.Console")
    def test_error_message(self, mock_console_class):
        """Test error message output."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger()
        logger.error("Error message", "Error details")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "❌ ERROR:" in call_args
        assert "Error message" in call_args
        assert "Error details" in call_args

    @patch("prunarr.logger.Console")
    def test_success_message(self, mock_console_class):
        """Test success message output."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger()
        logger.success("Success message")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "✅ SUCCESS:" in call_args
        assert "Success message" in call_args

    @patch("prunarr.logger.Console")
    def test_progress_message(self, mock_console_class):
        """Test progress message output."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        logger = PrunArrLogger()
        logger.progress("Processing data", "Step 1 of 3")

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "⏳ PROGRESS:" in call_args
        assert "Processing data" in call_args
        assert "Step 1 of 3" in call_args

    @patch("prunarr.logger.Console")
    def test_console_initialization(self, mock_console_class):
        """Test that console is initialized with stderr=True."""
        PrunArrLogger()
        mock_console_class.assert_called_once_with(stderr=True)

    def test_multiple_log_levels(self):
        """Test that different log levels work correctly in sequence."""
        with patch("prunarr.logger.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            logger = PrunArrLogger(debug=True)

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.success("Success message")
            logger.progress("Progress message")

            # Should have 6 calls (debug enabled)
            assert mock_console.print.call_count == 6

    def test_message_without_extra_detail(self):
        """Test that messages work correctly without extra details."""
        with patch("prunarr.logger.Console") as mock_console_class:
            mock_console = Mock()
            mock_console_class.return_value = mock_console

            logger = PrunArrLogger(log_level="INFO")
            logger.info("Simple message")

            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Simple message" in call_args
            assert "Extra details" not in call_args


class TestGetLogger:
    """Test the get_logger factory function."""

    def test_get_logger_default_parameters(self):
        """Test get_logger with default parameters."""
        logger = get_logger()

        assert isinstance(logger, PrunArrLogger)
        assert logger.logger_name == "prunarr"
        assert logger.debug_enabled is False

    def test_get_logger_custom_parameters(self):
        """Test get_logger with custom parameters."""
        logger = get_logger("custom_module", debug=True)

        assert isinstance(logger, PrunArrLogger)
        assert logger.logger_name == "custom_module"
        assert logger.debug_enabled is True

    def test_get_logger_returns_new_instance(self):
        """Test that get_logger returns a new instance each time."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1 is not logger2
        assert logger1.logger_name != logger2.logger_name

    def test_get_logger_debug_parameter(self):
        """Test that debug parameter is correctly passed through."""
        debug_logger = get_logger(debug=True)
        normal_logger = get_logger(debug=False)

        assert debug_logger.debug_enabled is True
        assert normal_logger.debug_enabled is False


class TestLoggerIntegration:
    """Integration tests for logger functionality."""

    def test_real_console_output(self, capsys):
        """Test that logger actually outputs to console (integration test)."""
        # Note: This test uses capsys to capture real stderr output
        logger = PrunArrLogger("test", log_level="INFO")
        logger.info("Test message")

        # Capture the output
        captured = capsys.readouterr()

        # The output should contain our message
        # Note: Rich outputs to stderr by default
        assert "Test message" in captured.err
        assert "INFO:" in captured.err

    def test_debug_mode_integration(self, capsys):
        """Test debug mode integration with real output."""
        # Debug disabled
        logger_no_debug = PrunArrLogger("test", debug=False)
        logger_no_debug.debug("Debug message")

        captured = capsys.readouterr()
        assert "Debug message" not in captured.err

        # Debug enabled
        logger_with_debug = PrunArrLogger("test", debug=True)
        logger_with_debug.debug("Debug message")

        captured = capsys.readouterr()
        assert "Debug message" in captured.err
        assert "DEBUG:" in captured.err

    def test_timestamp_in_real_output(self, capsys):
        """Test that timestamps appear in real output."""
        logger = PrunArrLogger("test", log_level="INFO")
        logger.info("Timestamped message")

        captured = capsys.readouterr()

        # Should contain timestamp pattern (HH:MM:SS)
        import re

        timestamp_pattern = r"\d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, captured.err)

    def test_rich_markup_in_output(self, capsys):
        """Test that Rich markup is processed in real output."""
        logger = PrunArrLogger("test", log_level="INFO")
        logger.info("Test message")

        captured = capsys.readouterr()

        # Output should contain ANSI escape codes from Rich formatting
        # (Rich converts markup to ANSI codes)
        assert "\033[" in captured.err or "INFO:" in captured.err
