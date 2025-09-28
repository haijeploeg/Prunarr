"""
Logging module for PrunArr CLI application.

This module provides a custom logging implementation using Rich console styling
for enhanced output formatting. The logger supports multiple log levels with
color-coded messages, timestamps, and optional debug mode functionality.

The logging system is designed to provide:
- Consistent Rich-styled output across all components
- Timestamped messages for debugging and monitoring
- Multiple log levels with appropriate visual indicators
- Debug mode toggle for detailed troubleshooting
- Centralized logging configuration for the entire application
"""

from datetime import datetime
from typing import Optional

from rich.console import Console


class PrunArrLogger:
    """
    Enhanced logger implementation with Rich console styling and comprehensive log level support.

    This logger provides a unified logging interface for the PrunArr application,
    featuring Rich markup styling, timestamp formatting, and configurable debug output.
    All log messages are consistently formatted with appropriate visual indicators
    and color coding for different log levels.

    Attributes:
        console: Rich console instance for styled output
        debug_enabled: Flag controlling debug message visibility
        logger_name: Identifier for this logger instance
    """

    def __init__(self, name: str = "prunarr", debug: bool = False) -> None:
        """
        Initialize the PrunArr logger with configuration options.

        Args:
            name: Logger identifier for tracking message sources
            debug: Enable debug message output and detailed logging

        Examples:
            Basic logger:
            >>> logger = PrunArrLogger("movies")
            >>> logger.info("Processing movies")

            Debug logger:
            >>> debug_logger = PrunArrLogger("series", debug=True)
            >>> debug_logger.debug("Detailed processing information")
        """
        self.console = Console(stderr=True)
        self.debug_enabled = debug
        self.logger_name = name

    def _get_timestamp(self) -> str:
        """
        Generate formatted timestamp string for log messages.

        Returns:
            Formatted timestamp in HH:MM:SS format

        Examples:
            >>> logger._get_timestamp()
            '14:30:45'
        """
        return datetime.now().strftime("%H:%M:%S")

    def _format_message(
        self, level: str, icon: str, color: str, message: str, extra_detail: Optional[str] = None
    ) -> str:
        """
        Format log message with consistent styling and optional details.

        Args:
            level: Log level name (DEBUG, INFO, etc.)
            icon: Unicode icon for the log level
            color: Rich color name for styling
            message: Primary log message
            extra_detail: Optional additional information

        Returns:
            Formatted message string with Rich markup
        """
        timestamp = self._get_timestamp()
        styled_msg = (
            f"[dim][{timestamp}][/dim] - [{color}]{icon} {level.upper()}:[/{color}] {message}"
        )

        if extra_detail:
            styled_msg += f"\n[dim]    {extra_detail}[/dim]"

        return styled_msg

    def debug(self, message: str, extra_detail: Optional[str] = None) -> None:
        """
        Log debug message with detailed information (only when debug mode is enabled).

        Debug messages are only displayed when the logger is initialized with debug=True.
        These messages are useful for troubleshooting and development but should not
        appear in normal operation.

        Args:
            message: Primary debug message
            extra_detail: Optional additional debug information

        Examples:
            >>> logger.debug("Processing series data", "Found 42 episodes")
            >>> logger.debug("API call completed successfully")
        """
        if not self.debug_enabled:
            return

        formatted_msg = self._format_message("debug", "🔍", "cyan", message, extra_detail)
        self.console.print(formatted_msg)

    def info(self, message: str, extra_detail: Optional[str] = None) -> None:
        """
        Log informational message for normal operation status.

        Info messages provide general information about application progress
        and are suitable for normal user feedback.

        Args:
            message: Primary informational message
            extra_detail: Optional additional context

        Examples:
            >>> logger.info("Retrieving movie list from Radarr")
            >>> logger.info("Configuration loaded successfully", "Using config.yaml")
        """
        formatted_msg = self._format_message("info", "ℹ️", "blue", message, extra_detail)
        self.console.print(formatted_msg)

    def warning(self, message: str, extra_detail: Optional[str] = None) -> None:
        """
        Log warning message for potential issues or important notices.

        Warning messages indicate situations that may require attention but
        do not prevent the application from continuing operation.

        Args:
            message: Primary warning message
            extra_detail: Optional additional warning details

        Examples:
            >>> logger.warning("No movies found matching criteria")
            >>> logger.warning("API rate limit approaching", "Consider reducing request frequency")
        """
        formatted_msg = self._format_message("warning", "⚠️", "yellow", message, extra_detail)
        self.console.print(formatted_msg)

    def error(self, message: str, extra_detail: Optional[str] = None) -> None:
        """
        Log error message for failures and critical issues.

        Error messages indicate problems that prevent normal operation or
        cause functionality to fail. These require user attention.

        Args:
            message: Primary error message
            extra_detail: Optional additional error details

        Examples:
            >>> logger.error("Failed to connect to Radarr API")
            >>> logger.error("Configuration validation failed", "Missing required API key")
        """
        formatted_msg = self._format_message("error", "❌", "red", message, extra_detail)
        self.console.print(formatted_msg)

    def success(self, message: str, extra_detail: Optional[str] = None) -> None:
        """
        Log success message for completed operations and achievements.

        Success messages indicate that operations completed successfully
        and provide positive feedback to users.

        Args:
            message: Primary success message
            extra_detail: Optional additional success details

        Examples:
            >>> logger.success("Movie removal completed")
            >>> logger.success("Found 25 movies", "Ready for processing")
        """
        formatted_msg = self._format_message("success", "✅", "green", message, extra_detail)
        self.console.print(formatted_msg)

    def progress(self, message: str, extra_detail: Optional[str] = None) -> None:
        """
        Log progress message for ongoing operations and status updates.

        Progress messages keep users informed about long-running operations
        and provide status updates during processing.

        Args:
            message: Primary progress message
            extra_detail: Optional additional progress information

        Examples:
            >>> logger.progress("Processing movie library")
            >>> logger.progress("Analyzing watch history", "Step 2 of 4")
        """
        formatted_msg = self._format_message("progress", "⏳", "magenta", message, extra_detail)
        self.console.print(formatted_msg)


def get_logger(name: str = "prunarr", debug: bool = False) -> PrunArrLogger:
    """
    Factory function to create and configure PrunArr logger instances.

    This function provides a centralized way to create logger instances with
    consistent configuration across the application. It ensures all loggers
    follow the same styling and behavior patterns.

    Args:
        name: Logger identifier for tracking message sources across modules
        debug: Enable debug logging for detailed troubleshooting output

    Returns:
        Configured PrunArrLogger instance ready for use

    Examples:
        Standard logger for a module:
        >>> logger = get_logger("movies")
        >>> logger.info("Starting movie processing")

        Debug logger for troubleshooting:
        >>> debug_logger = get_logger("series", debug=True)
        >>> debug_logger.debug("Detailed API response analysis")

        Component-specific logger:
        >>> api_logger = get_logger("radarr_api", debug=True)
        >>> api_logger.debug("Making API call to /api/v3/movie")
    """
    return PrunArrLogger(name, debug)
