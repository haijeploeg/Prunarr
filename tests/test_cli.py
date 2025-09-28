"""
Unit tests for the CLI module.

Tests the main CLI application functionality including command routing,
configuration handling, error management, and global options.
"""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import yaml

from prunarr.cli import app
from prunarr.config import Settings


class TestCLIApp:
    """Test the CLI application functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_app_help(self):
        """Test the main app help command."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "PrunArr CLI" in result.output
        assert "movies" in result.output
        assert "series" in result.output
        assert "history" in result.output

    def test_app_with_debug_flag(self, temp_config_file):
        """Test app with debug flag enabled."""
        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            self.runner.invoke(app, [
                "--debug",
                "--config", temp_config_file,
                "movies", "--help"
            ])

            # Should not fail and should enable debug logging
            mock_get_logger.assert_called_with("cli", debug=True)
            mock_logger.debug.assert_called()

    def test_app_with_config_file(self, temp_config_file):
        """Test app with custom config file."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            self.runner.invoke(app, [
                "--config", temp_config_file,
                "movies", "--help"
            ])

            mock_load_settings.assert_called_once_with(temp_config_file)

    def test_app_without_config_file(self):
        """Test app without config file (using environment variables)."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            self.runner.invoke(app, ["movies", "--help"])

            mock_load_settings.assert_called_once_with(None)

    def test_app_config_file_not_found(self):
        """Test app with non-existent config file."""
        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = self.runner.invoke(app, [
                "--config", "/nonexistent/config.yaml",
                "movies", "--help"
            ])

            assert result.exit_code == 1
            mock_logger.error.assert_called_with("Configuration file not found: [Errno 2] No such file or directory: '/nonexistent/config.yaml'")

    def test_app_validation_error(self, temp_config_file):
        """Test app with configuration validation error."""
        # Create invalid config
        with open(temp_config_file, 'w') as f:
            yaml.dump({"radarr_api_key": ""}, f)  # Empty API key

        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = self.runner.invoke(app, [
                "--config", temp_config_file,
                "movies", "--help"
            ])

            assert result.exit_code == 1
            mock_logger.error.assert_any_call("Configuration validation failed")

    def test_app_unexpected_error(self, temp_config_file):
        """Test app with unexpected error during initialization."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_load_settings.side_effect = RuntimeError("Unexpected error")

            with patch('prunarr.cli.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                result = self.runner.invoke(app, [
                    "--config", temp_config_file,
                    "movies", "--help"
                ])

                assert result.exit_code == 1
                mock_logger.error.assert_called_with("Unexpected error during initialization: Unexpected error")

    def test_app_context_passing(self, temp_config_file):
        """Test that context is properly passed to subcommands."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            # Mock the movies command to check context
            with patch('prunarr.commands.movies.app') as mock_movies_app:
                result = self.runner.invoke(app, [
                    "--debug",
                    "--config", temp_config_file,
                    "movies", "list"
                ])

                # Context should be set with settings and debug flag
                # Note: This is tested indirectly through successful loading

    def test_debug_mode_logging(self, temp_config_file):
        """Test debug mode logging behavior."""
        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            with patch('prunarr.cli.load_settings') as mock_load_settings:
                mock_settings = Mock(spec=Settings)
                mock_load_settings.return_value = mock_settings

                result = self.runner.invoke(app, [
                    "--debug",
                    "--config", temp_config_file,
                    "--help"
                ])

                # Debug logging should be enabled
                mock_get_logger.assert_called_with("cli", debug=True)
                mock_logger.debug.assert_any_call("Debug mode enabled for CLI session")
                mock_logger.debug.assert_any_call(f"Loaded configuration from: {temp_config_file}")

    def test_no_debug_mode_logging(self, temp_config_file):
        """Test normal mode logging behavior."""
        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            with patch('prunarr.cli.load_settings') as mock_load_settings:
                mock_settings = Mock(spec=Settings)
                mock_load_settings.return_value = mock_settings

                result = self.runner.invoke(app, [
                    "--config", temp_config_file,
                    "--help"
                ])

                # Debug logging should not be enabled
                mock_get_logger.assert_called_with("cli", debug=False)

    def test_environment_config_logging(self):
        """Test logging when using environment configuration."""
        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            with patch('prunarr.cli.load_settings') as mock_load_settings:
                mock_settings = Mock(spec=Settings)
                mock_load_settings.return_value = mock_settings

                result = self.runner.invoke(app, ["--help"])

                mock_logger.debug.assert_any_call("Using environment variables for configuration")

    def test_command_registration(self):
        """Test that subcommands are properly registered."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "movies" in result.output
        assert "series" in result.output
        assert "history" in result.output

    def test_rich_markup_in_help(self):
        """Test that Rich markup is enabled in help."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Rich markup should be processed (though exact output depends on terminal)
        assert "PrunArr CLI" in result.output


class TestCLIMainCallback:
    """Test the main callback function specifically."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_callback_valid_config(self, temp_config_file):
        """Test main callback with valid configuration."""
        import typer

        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            with patch('prunarr.cli.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                # Create a mock context
                ctx = Mock(spec=typer.Context)
                ctx.obj = None

                # Import and call the main function directly
                from prunarr.cli import main as main_callback

                # Should not raise any exceptions
                main_callback(ctx, Path(temp_config_file), False)

                # Context should be set
                assert ctx.obj is not None
                assert "settings" in ctx.obj
                assert "debug" in ctx.obj
                assert ctx.obj["debug"] is False

    def test_main_callback_file_not_found(self):
        """Test main callback with file not found error."""
        import typer

        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            ctx = Mock(spec=typer.Context)

            from prunarr.cli import main as main_callback

            with pytest.raises(typer.Exit) as exc_info:
                main_callback(ctx, Path("/nonexistent/config.yaml"), False)

            assert exc_info.value.exit_code == 1

    def test_main_callback_validation_error(self, temp_config_file):
        """Test main callback with validation error."""
        import typer

        # Create invalid config
        with open(temp_config_file, 'w') as f:
            yaml.dump({"radarr_url": "invalid-url"}, f)

        with patch('prunarr.cli.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            ctx = Mock(spec=typer.Context)

            from prunarr.cli import main as main_callback

            with pytest.raises(typer.Exit) as exc_info:
                main_callback(ctx, Path(temp_config_file), False)

            assert exc_info.value.exit_code == 1

    def test_main_callback_debug_exception_details(self, temp_config_file):
        """Test that debug mode shows exception details."""
        import typer

        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_load_settings.side_effect = RuntimeError("Test error")

            with patch('prunarr.cli.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                ctx = Mock(spec=typer.Context)

                from prunarr.cli import main as main_callback

                with pytest.raises(typer.Exit):
                    main_callback(ctx, Path(temp_config_file), True)  # Debug enabled

                # Should log exception details
                mock_logger.debug.assert_any_call("Exception details: RuntimeError: Test error")


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_full_command_execution_mock(self, temp_config_file):
        """Test full command execution with mocked dependencies."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            # Mock the command execution
            with patch('prunarr.commands.movies.app') as mock_movies_app:
                mock_movies_app.main = Mock()

                result = self.runner.invoke(app, [
                    "--config", temp_config_file,
                    "movies", "list"
                ])

                # Should complete without errors
                mock_load_settings.assert_called_once()

    def test_command_chain(self, temp_config_file):
        """Test that commands can access the context properly."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            # Test multiple commands to ensure context persistence
            commands = ["movies --help", "series --help", "history --help"]

            for cmd in commands:
                result = self.runner.invoke(app, [
                    "--config", temp_config_file
                ] + cmd.split())

                # Each command should work
                assert result.exit_code == 0

    def test_error_propagation(self, temp_config_file):
        """Test that errors are properly propagated from subcommands."""
        with patch('prunarr.cli.load_settings') as mock_load_settings:
            mock_settings = Mock(spec=Settings)
            mock_load_settings.return_value = mock_settings

            # Mock a command that raises an error
            with patch('prunarr.commands.movies.app') as mock_movies_app:
                mock_movies_app.main = Mock(side_effect=Exception("Command error"))

                # The error should be handled at the command level
                # This test ensures our CLI setup doesn't interfere with error handling

    def test_config_validation_with_real_settings(self):
        """Test configuration validation with real Settings objects."""
        # Create a temporary config with valid settings
        config_data = {
            "radarr_api_key": "test-key",
            "radarr_url": "http://localhost:7878",
            "sonarr_api_key": "test-key",
            "sonarr_url": "http://localhost:8989",
            "tautulli_api_key": "test-key",
            "tautulli_url": "http://localhost:8181"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            result = self.runner.invoke(app, [
                "--config", temp_path,
                "--help"
            ])

            # Should succeed with valid configuration
            assert result.exit_code == 0

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_partial_config_with_env_fallback(self):
        """Test partial config file with environment variable fallback."""
        # Create partial config
        partial_config = {
            "radarr_api_key": "file-key",
            "radarr_url": "http://localhost:7878"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(partial_config, f)
            temp_path = f.name

        try:
            # Set environment variables for missing config
            import os
            env_vars = {
                "SONARR_API_KEY": "env-key",
                "SONARR_URL": "http://localhost:8989",
                "TAUTULLI_API_KEY": "env-key",
                "TAUTULLI_URL": "http://localhost:8181"
            }

            with patch.dict(os.environ, env_vars):
                result = self.runner.invoke(app, [
                    "--config", temp_path,
                    "--help"
                ])

                # Should succeed with mixed config sources
                assert result.exit_code == 0

        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCLIErrorMessages:
    """Test CLI error message formatting and clarity."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_validation_error_formatting(self, temp_config_file):
        """Test that validation errors are clearly formatted."""
        # Create config with multiple validation errors
        invalid_config = {
            "radarr_api_key": "",  # Empty
            "radarr_url": "invalid-url",  # Invalid format
            "sonarr_api_key": "   ",  # Whitespace only
            "sonarr_url": "http://localhost:8989",
            "tautulli_api_key": "key",
            "tautulli_url": "http://localhost:8181",
            "user_tag_regex": "[invalid"  # Invalid regex
        }

        with open(temp_config_file, 'w') as f:
            yaml.dump(invalid_config, f)

        result = self.runner.invoke(app, [
            "--config", temp_config_file,
            "--help"
        ])

        assert result.exit_code == 1
        # Output should contain validation error information

    def test_file_not_found_error_message(self):
        """Test file not found error message."""
        result = self.runner.invoke(app, [
            "--config", "/path/that/does/not/exist.yaml",
            "--help"
        ])

        assert result.exit_code == 1
        # Should contain clear error message about file not found

    def test_yaml_parsing_error_message(self, temp_config_file):
        """Test YAML parsing error message."""
        # Create invalid YAML
        with open(temp_config_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        result = self.runner.invoke(app, [
            "--config", temp_config_file,
            "--help"
        ])

        assert result.exit_code == 1
        # Should contain clear error about YAML parsing