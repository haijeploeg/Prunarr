import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    radarr_api_key: str = Field(..., description="API key voor Radarr")
    radarr_url: str = Field(..., description="URL van Radarr (bijv. http://localhost:7878)")
    tautulli_api_key: str = Field(..., description="API key voor Tautulli")
    tautulli_url: str = Field(..., description="URL van Tautulli (bijv. http://localhost:8181)")
    days_before_removal: int = Field(
        default=60,
        description="Aantal dagen voordat bekeken films worden verwijderd",
    )

    # Validatie om te voorkomen dat lege strings worden ingeladen
    @field_validator("radarr_api_key", "radarr_url", "tautulli_api_key", "tautulli_url")
    def must_not_be_empty(cls, v: str, info):
        if not v or not v.strip():
            raise ValueError("mag niet leeg zijn")
        return v.strip()


def load_settings(config_file: str | None = None) -> Settings:
    """
    Laad instellingen uit YAML configbestand of omgevingsvariabelen.
    """
    data: dict = {}

    if config_file:
        p = Path(config_file)
        if not p.exists():
            raise FileNotFoundError(f"Configbestand niet gevonden: {config_file}")
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    return Settings(
        radarr_api_key=data.get("radarr_api_key") or os.getenv("RADARR_API_KEY", ""),
        radarr_url=data.get("radarr_url") or os.getenv("RADARR_URL", ""),
        tautulli_api_key=data.get("tautulli_api_key") or os.getenv("TAUTULLI_API_KEY", ""),
        tautulli_url=data.get("tautulli_url") or os.getenv("TAUTULLI_URL", ""),
        days_before_removal=data.get("days_before_removal")
        or int(os.getenv("DAYS_BEFORE_REMOVAL", "60")),
    )
