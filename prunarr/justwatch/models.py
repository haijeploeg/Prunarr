"""Data models for JustWatch API responses."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Provider(BaseModel):
    """Streaming provider information."""

    id: int = Field(description="Provider ID")
    technical_name: str = Field(description="Technical name (e.g., 'nfx', 'amp')")
    short_name: str = Field(description="Short display name")
    clear_name: str = Field(description="Full provider name")
    monetization_types: List[str] = Field(
        default_factory=list, description="Types of offers (FLATRATE, RENT, BUY, etc.)"
    )


class Offer(BaseModel):
    """Streaming offer information."""

    provider_id: int = Field(description="Provider offering this content")
    provider_short_name: str = Field(description="Provider short name")
    monetization_type: str = Field(description="Type of offer (FLATRATE, RENT, BUY, ADS, FREE)")
    presentation_type: str = Field(default="SD", description="Quality (SD, HD, 4K, etc.)")
    url: Optional[str] = Field(default=None, description="Direct URL to content")


class SearchResult(BaseModel):
    """Search result from JustWatch."""

    id: str = Field(description="JustWatch content ID")
    object_type: str = Field(description="Type: MOVIE or SHOW")
    title: str = Field(description="Content title")
    release_year: Optional[int] = Field(default=None, description="Release year")
    imdb_id: Optional[str] = Field(default=None, description="IMDB ID if available")
    tmdb_id: Optional[int] = Field(default=None, description="TMDB ID if available")


class AvailabilityResult(BaseModel):
    """Result of streaming availability check."""

    title: str = Field(description="Content title")
    available: bool = Field(description="Whether content is available on any configured provider")
    providers: List[str] = Field(
        default_factory=list, description="List of provider short names where available"
    )
    offers: List[Offer] = Field(default_factory=list, description="All streaming offers found")
    checked_at: datetime = Field(
        default_factory=datetime.now, description="When this check was performed"
    )
    locale: str = Field(description="Locale used for check")
    justwatch_id: Optional[str] = Field(default=None, description="JustWatch internal ID")

    def to_cache_dict(self) -> Dict:
        """Convert to dictionary suitable for caching."""
        return {
            "title": self.title,
            "available": self.available,
            "providers": self.providers,
            "checked_at": self.checked_at.isoformat(),
            "locale": self.locale,
            "justwatch_id": self.justwatch_id,
        }

    @classmethod
    def from_cache_dict(cls, data: Dict) -> "AvailabilityResult":
        """Create from cached dictionary."""
        return cls(
            title=data["title"],
            available=data["available"],
            providers=data.get("providers", []),
            checked_at=datetime.fromisoformat(data["checked_at"]),
            locale=data["locale"],
            justwatch_id=data.get("justwatch_id"),
        )
