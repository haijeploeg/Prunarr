"""Service for checking streaming availability via JustWatch."""

from typing import Any, Dict, Optional

from prunarr.justwatch import AvailabilityResult, JustWatchClient
from prunarr.logger import PrunArrLogger


class StreamingChecker:
    """
    Service to check streaming availability for movies and TV shows.

    Integrates with JustWatch API to determine if content is available
    on configured streaming providers. Results are cached to minimize
    API calls and improve performance.
    """

    def __init__(
        self,
        locale: str,
        providers: list[str],
        cache_manager: Optional[Any] = None,
        logger: Optional[PrunArrLogger] = None,
    ):
        """
        Initialize streaming checker.

        Args:
            locale: Locale for JustWatch queries (e.g., "en_US")
            providers: List of provider technical names to check
            cache_manager: Optional cache manager for caching results
            logger: Optional logger for debug output
        """
        self.locale = locale
        self.providers = providers
        self.cache_manager = cache_manager
        self.logger = logger

        self.client = JustWatchClient(locale=locale, logger=logger, cache_manager=cache_manager)

        if self.logger:
            self.logger.debug(
                f"Initialized StreamingChecker with locale={locale}, providers={providers}"
            )

    def check_movie_availability(
        self, title: str, year: Optional[int] = None, imdb_id: Optional[str] = None
    ) -> AvailabilityResult:
        """
        Check if a movie is available on configured streaming providers.

        Args:
            title: Movie title
            year: Optional release year for better matching
            imdb_id: Optional IMDB ID for caching

        Returns:
            Availability result with provider information
        """
        if self.logger:
            self.logger.debug(f"Checking movie availability: {title} ({year}), IMDB: {imdb_id}")

        result = self.client.check_availability(
            title=title,
            providers=self.providers,
            release_year=year,
            content_type="MOVIE",
            imdb_id=imdb_id,
        )

        if self.logger:
            status = "available" if result.available else "not available"
            providers_str = ", ".join(result.providers) if result.providers else "none"
            self.logger.debug(f"Movie {title}: {status} on providers: {providers_str}")

        return result

    def check_series_availability(
        self, title: str, tvdb_id: Optional[int] = None
    ) -> AvailabilityResult:
        """
        Check if a TV series is available on configured streaming providers.

        Args:
            title: Series title
            tvdb_id: Optional TVDB ID for caching

        Returns:
            Availability result with provider information
        """
        if self.logger:
            self.logger.debug(f"Checking series availability: {title}, TVDB: {tvdb_id}")

        # Convert TVDB ID to string for cache key if provided
        cache_id = f"tvdb{tvdb_id}" if tvdb_id else None

        result = self.client.check_availability(
            title=title,
            providers=self.providers,
            content_type="SHOW",
            imdb_id=cache_id,
        )

        if self.logger:
            status = "available" if result.available else "not available"
            providers_str = ", ".join(result.providers) if result.providers else "none"
            self.logger.debug(f"Series {title}: {status} on providers: {providers_str}")

        return result

    def is_on_streaming(self, media_type: str, title: str, **kwargs) -> bool:
        """
        Quick check if content is available on any configured streaming provider.

        Args:
            media_type: Type of media ("movie" or "series")
            title: Content title
            **kwargs: Additional arguments (year, imdb_id, tvdb_id)

        Returns:
            True if available on any configured provider, False otherwise
        """
        if media_type.lower() == "movie":
            result = self.check_movie_availability(
                title=title,
                year=kwargs.get("year"),
                imdb_id=kwargs.get("imdb_id"),
            )
        elif media_type.lower() in ("series", "show", "tv"):
            result = self.check_series_availability(
                title=title,
                tvdb_id=kwargs.get("tvdb_id"),
            )
        else:
            if self.logger:
                self.logger.warning(f"Unknown media type: {media_type}")
            return False

        return result.available

    def get_available_providers(self) -> list[Dict[str, Any]]:
        """
        Get list of all available providers for the configured locale.

        Returns:
            List of provider dictionaries with name and technical name
        """
        providers = self.client.get_providers()

        # Filter to only FLATRATE (subscription) providers if needed
        result = []
        for provider in providers:
            # Only include providers with FLATRATE monetization
            if "FLATRATE" in provider.monetization_types:
                result.append(
                    {
                        "technical_name": provider.technical_name,
                        "short_name": provider.short_name,
                        "clear_name": provider.clear_name,
                    }
                )

        return result
