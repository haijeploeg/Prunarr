"""
JustWatch API integration for streaming availability checking.

This module provides functionality to query JustWatch's GraphQL API
to determine streaming availability for movies and TV shows across
different providers and locales.
"""

from prunarr.justwatch.client import JustWatchClient
from prunarr.justwatch.exceptions import (
    JustWatchAPIError,
    JustWatchNotFoundError,
    JustWatchRateLimitError,
)
from prunarr.justwatch.models import (
    AvailabilityResult,
    Offer,
    Provider,
    SearchResult,
)

__all__ = [
    "JustWatchClient",
    "JustWatchAPIError",
    "JustWatchNotFoundError",
    "JustWatchRateLimitError",
    "AvailabilityResult",
    "Offer",
    "Provider",
    "SearchResult",
]
