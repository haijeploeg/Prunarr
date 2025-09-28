"""
Unit tests for the configuration module.

Tests configuration loading, validation, and error handling for both
YAML file and environment variable configuration methods.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from pydantic import ValidationError

from prunarr.config import Settings, load_settings


class TestSettings:
    """Test the Settings model validation and behavior."""

    def test_valid_settings_creation(self):
        """Test creating Settings with all valid values."""
        settings = Settings(
            radarr_api_key="test-radarr-key",
            radarr_url="http://localhost:7878",
            sonarr_api_key="test-sonarr-key",
            sonarr_url="http://localhost:8989",
            tautulli_api_key="test-tautulli-key",
            tautulli_url="http://localhost:8181",
            user_tag_regex=r"^\d+ - (.+)$"
        )

        assert settings.radarr_api_key == "test-radarr-key"
        assert settings.radarr_url == "http://localhost:7878"
        assert settings.sonarr_api_key == "test-sonarr-key"
        assert settings.sonarr_url == "http://localhost:8989"
        assert settings.tautulli_api_key == "test-tautulli-key"
        assert settings.tautulli_url == "http://localhost:8181"
        assert settings.user_tag_regex == r"^\d+ - (.+)$"

    def test_url_normalization(self):
        """Test that URLs are properly normalized (trailing slashes removed)."""
        settings = Settings(
            radarr_api_key="key",
            radarr_url="http://localhost:7878/",
            sonarr_api_key="key",
            sonarr_url="http://localhost:8989/",
            tautulli_api_key="key",
            tautulli_url="http://localhost:8181/",
        )

        assert settings.radarr_url == "http://localhost:7878"
        assert settings.sonarr_url == "http://localhost:8989"
        assert settings.tautulli_url == "http://localhost:8181"

    def test_empty_api_key_validation(self):
        """Test that empty API keys are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                radarr_api_key="",
                radarr_url="http://localhost:7878",
                sonarr_api_key="key",
                sonarr_url="http://localhost:8989",
                tautulli_api_key="key",
                tautulli_url="http://localhost:8181",
            )

        errors = exc_info.value.errors()
        assert any("cannot be empty" in str(error) for error in errors)

    def test_whitespace_api_key_validation(self):
        """Test that whitespace-only API keys are rejected."""
        with pytest.raises(ValidationError):
            Settings(
                radarr_api_key="   ",
                radarr_url="http://localhost:7878",
                sonarr_api_key="key",
                sonarr_url="http://localhost:8989",
                tautulli_api_key="key",
                tautulli_url="http://localhost:8181",
            )

    def test_invalid_url_format(self):
        """Test that URLs without http/https protocol are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                radarr_api_key="key",
                radarr_url="localhost:7878",
                sonarr_api_key="key",
                sonarr_url="http://localhost:8989",
                tautulli_api_key="key",
                tautulli_url="http://localhost:8181",
            )

        errors = exc_info.value.errors()
        assert any("must start with http://" in str(error) for error in errors)

    def test_invalid_regex_pattern(self):
        """Test that invalid regex patterns are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                radarr_api_key="key",
                radarr_url="http://localhost:7878",
                sonarr_api_key="key",
                sonarr_url="http://localhost:8989",
                tautulli_api_key="key",
                tautulli_url="http://localhost:8181",
                user_tag_regex="[invalid regex"
            )

        errors = exc_info.value.errors()
        assert any("invalid regex pattern" in str(error) for error in errors)

    def test_default_user_tag_regex(self):
        """Test that the default user tag regex is applied when not specified."""
        settings = Settings(
            radarr_api_key="key",
            radarr_url="http://localhost:7878",
            sonarr_api_key="key",
            sonarr_url="http://localhost:8989",
            tautulli_api_key="key",
            tautulli_url="http://localhost:8181",
        )

        assert settings.user_tag_regex == r"^\d+ - (.+)$"


class TestLoadSettings:
    """Test the load_settings function behavior."""

    def test_load_from_yaml_file(self, temp_config_file):
        """Test loading configuration from a YAML file."""
        settings = load_settings(temp_config_file)

        assert settings.radarr_api_key == "test-radarr-key"
        assert settings.radarr_url == "http://localhost:7878"
        assert settings.sonarr_api_key == "test-sonarr-key"
        assert settings.sonarr_url == "http://localhost:8989"
        assert settings.tautulli_api_key == "test-tautulli-key"
        assert settings.tautulli_url == "http://localhost:8181"

    def test_load_from_environment_variables(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "RADARR_API_KEY": "env-radarr-key",
            "RADARR_URL": "http://env:7878",
            "SONARR_API_KEY": "env-sonarr-key",
            "SONARR_URL": "http://env:8989",
            "TAUTULLI_API_KEY": "env-tautulli-key",
            "TAUTULLI_URL": "http://env:8181",
            "USER_TAG_REGEX": r"^\d+ - (.+)$"
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = load_settings()

            assert settings.radarr_api_key == "env-radarr-key"
            assert settings.radarr_url == "http://env:7878"
            assert settings.sonarr_api_key == "env-sonarr-key"
            assert settings.sonarr_url == "http://env:8989"
            assert settings.tautulli_api_key == "env-tautulli-key"
            assert settings.tautulli_url == "http://env:8181"

    def test_yaml_overrides_environment(self, temp_config_file):
        """Test that YAML values take precedence over environment variables."""
        env_vars = {
            "RADARR_API_KEY": "env-radarr-key",
            "RADARR_URL": "http://env:7878",
            "SONARR_API_KEY": "env-sonarr-key",
            "SONARR_URL": "http://env:8989",
            "TAUTULLI_API_KEY": "env-tautulli-key",
            "TAUTULLI_URL": "http://env:8181",
        }

        with patch.dict(os.environ, env_vars):
            settings = load_settings(temp_config_file)

            # YAML values should override environment
            assert settings.radarr_api_key == "test-radarr-key"
            assert settings.radarr_url == "http://localhost:7878"

    def test_missing_config_file(self):
        """Test that FileNotFoundError is raised for missing config files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_settings("/nonexistent/config.yaml")

        assert "Configuration file not found" in str(exc_info.value)

    def test_invalid_yaml_file(self):
        """Test that malformed YAML files raise appropriate errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_settings(temp_path)

            assert "Invalid YAML configuration file" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_empty_yaml_file(self):
        """Test that empty YAML files are handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            env_vars = {
                "RADARR_API_KEY": "env-key",
                "RADARR_URL": "http://localhost:7878",
                "SONARR_API_KEY": "env-key",
                "SONARR_URL": "http://localhost:8989",
                "TAUTULLI_API_KEY": "env-key",
                "TAUTULLI_URL": "http://localhost:8181",
            }

            with patch.dict(os.environ, env_vars):
                settings = load_settings(temp_path)
                assert settings.radarr_api_key == "env-key"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_partial_yaml_with_environment_fallback(self):
        """Test that missing YAML values fall back to environment variables."""
        partial_config = {
            "radarr_api_key": "yaml-radarr-key",
            "radarr_url": "http://localhost:7878",
            # Missing sonarr and tautulli config
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(partial_config, f)
            temp_path = f.name

        try:
            env_vars = {
                "SONARR_API_KEY": "env-sonarr-key",
                "SONARR_URL": "http://localhost:8989",
                "TAUTULLI_API_KEY": "env-tautulli-key",
                "TAUTULLI_URL": "http://localhost:8181",
            }

            with patch.dict(os.environ, env_vars):
                settings = load_settings(temp_path)

                # YAML values
                assert settings.radarr_api_key == "yaml-radarr-key"
                assert settings.radarr_url == "http://localhost:7878"

                # Environment fallback values
                assert settings.sonarr_api_key == "env-sonarr-key"
                assert settings.sonarr_url == "http://localhost:8989"
                assert settings.tautulli_api_key == "env-tautulli-key"
                assert settings.tautulli_url == "http://localhost:8181"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_missing_required_settings(self):
        """Test that missing required settings raise ValidationError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                load_settings()

            errors = exc_info.value.errors()
            required_fields = [
                "radarr_api_key", "radarr_url", "sonarr_api_key",
                "sonarr_url", "tautulli_api_key", "tautulli_url"
            ]

            error_fields = [error["loc"][0] for error in errors]
            for field in required_fields:
                assert field in error_fields