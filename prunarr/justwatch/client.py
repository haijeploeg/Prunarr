"""JustWatch API client with caching support."""

import json
from typing import Any, Dict, List, Optional

import requests

from prunarr.justwatch.exceptions import (
    JustWatchAPIError,
    JustWatchGraphQLError,
    JustWatchNotFoundError,
    JustWatchRateLimitError,
)
from prunarr.justwatch.models import AvailabilityResult, Offer, Provider, SearchResult
from prunarr.justwatch.queries import OFFERS_QUERY, PROVIDERS_QUERY, SEARCH_QUERY
from prunarr.logger import PrunArrLogger


class JustWatchClient:
    """Client for interacting with JustWatch GraphQL API."""

    GRAPHQL_URL = "https://apis.justwatch.com/graphql"
    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        locale: str = "en_US",
        logger: Optional[PrunArrLogger] = None,
        cache_manager: Optional[Any] = None,
    ):
        """
        Initialize JustWatch client.

        Args:
            locale: Locale in format "language_COUNTRY" (e.g., "en_US", "en_GB")
            logger: Logger instance for debug output
            cache_manager: Cache manager for caching API responses
        """
        self.locale = locale
        self.logger = logger
        self.cache_manager = cache_manager

        # Parse locale into country and language
        parts = locale.split("_")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid locale format: {locale}. Expected format: language_COUNTRY (e.g., en_US)"
            )

        self.language = parts[0].lower()
        self.country = parts[1].upper()

        if self.logger:
            self.logger.debug(
                f"Initialized JustWatch client with locale={locale}, country={self.country}, language={self.language}"
            )

    def _make_request(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a GraphQL request to JustWatch API.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            GraphQL response data

        Raises:
            JustWatchAPIError: On API errors
            JustWatchRateLimitError: On rate limiting
            JustWatchGraphQLError: On GraphQL errors
        """
        payload = {"query": query, "variables": variables}

        if self.logger:
            self.logger.debug(f"JustWatch GraphQL request: {json.dumps(variables)}")

        # Headers required by JustWatch API to prevent 403
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": f"{self.language}-{self.country},{self.language};q=0.9,en;q=0.8",
            "Origin": "https://www.justwatch.com",
            "Referer": "https://www.justwatch.com/",
        }

        try:
            response = requests.post(
                self.GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
            )

            if response.status_code == 429:
                raise JustWatchRateLimitError("JustWatch API rate limit exceeded")

            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                if self.logger:
                    self.logger.error(f"GraphQL errors: {data['errors']}")
                raise JustWatchGraphQLError(f"GraphQL error: {error_msg}")

            if self.logger:
                self.logger.debug("JustWatch GraphQL request successful")

            return data.get("data", {})

        except requests.exceptions.Timeout:
            raise JustWatchAPIError("JustWatch API request timed out")
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            # Try to get response body for debugging 422 errors
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_body = e.response.text
                    if self.logger and e.response.status_code == 422:
                        self.logger.error(f"422 Response body: {error_body}")
                except:
                    pass
            raise JustWatchAPIError(f"JustWatch API request failed: {error_detail}")
        except json.JSONDecodeError:
            raise JustWatchAPIError("Failed to decode JustWatch API response")

    def search_title(
        self, title: str, release_year: Optional[int] = None, content_type: str = "MOVIE"
    ) -> List[SearchResult]:
        """
        Search for content by title.

        Args:
            title: Content title to search for
            release_year: Optional release year to filter results
            content_type: Type of content (MOVIE or SHOW)

        Returns:
            List of search results

        Raises:
            JustWatchAPIError: On API errors
        """
        cache_key = None
        if self.cache_manager and self.cache_manager.is_enabled():
            cache_key = (
                f"justwatch_search_{content_type}_{title}_{release_year or 'any'}_{self.locale}"
            )
            cached = self.cache_manager.get(cache_key)
            if cached:
                if self.logger:
                    self.logger.debug(f"Cache hit for JustWatch search: {title}")
                return [SearchResult(**item) for item in cached]

        variables = {
            "country": self.country,
            "language": self.language,
            "first": 5,
            "sortBy": "POPULAR",
            "searchTitlesFilter": {
                "searchQuery": title,
                "objectTypes": [content_type],
            },
        }

        if release_year:
            # JustWatch expects an IntFilter object, not just an integer
            variables["searchTitlesFilter"]["releaseYear"] = {
                "min": release_year,
                "max": release_year,
            }

        data = self._make_request(SEARCH_QUERY, variables)

        results = []
        edges = data.get("popularTitles", {}).get("edges", [])

        for edge in edges:
            node = edge.get("node", {})
            content = node.get("content", {})
            external_ids = content.get("externalIds", {})

            result = SearchResult(
                id=node.get("id", ""),
                object_type=node.get("objectType", content_type),
                title=content.get("title", ""),
                release_year=content.get("originalReleaseYear"),
                imdb_id=external_ids.get("imdbId"),
                tmdb_id=external_ids.get("tmdbId"),
            )
            results.append(result)

        # Cache the results
        if cache_key and self.cache_manager and self.cache_manager.is_enabled():
            cache_data = [r.model_dump() for r in results]
            self.cache_manager.set(cache_key, cache_data)
            if self.logger:
                self.logger.debug(f"Cached JustWatch search results for: {title}")

        return results

    def get_offers(self, justwatch_id: str, providers: Optional[List[str]] = None) -> List[Offer]:
        """
        Get streaming offers for content.

        Args:
            justwatch_id: JustWatch content ID
            providers: Optional list of provider technical names to filter by

        Returns:
            List of streaming offers

        Raises:
            JustWatchAPIError: On API errors
        """
        cache_key = None
        if self.cache_manager and self.cache_manager.is_enabled():
            providers_str = "_".join(sorted(providers)) if providers else "all"
            cache_key = f"justwatch_offers_{justwatch_id}_{providers_str}_{self.locale}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                if self.logger:
                    self.logger.debug(f"Cache hit for JustWatch offers: {justwatch_id}")
                return [Offer(**item) for item in cached]

        variables = {
            "nodeId": justwatch_id,
            "country": self.country,
            "filterBuy": {"monetizationTypes": ["BUY"]},
            "filterFlatrate": {"monetizationTypes": ["FLATRATE"]},
            "filterRent": {"monetizationTypes": ["RENT"]},
            "filterFree": {"monetizationTypes": ["FREE", "ADS"]},
        }

        data = self._make_request(OFFERS_QUERY, variables)

        node = data.get("node", {})
        if not node:
            raise JustWatchNotFoundError(f"Content not found: {justwatch_id}")

        offers = []
        all_offers = node.get("offers", [])

        if self.logger:
            self.logger.debug(f"Found {len(all_offers)} total offers for {justwatch_id}")

        for offer_data in all_offers:
            package = offer_data.get("package", {})
            technical_name = package.get("technicalName", "")
            monetization_type = offer_data.get("monetizationType", "")

            if self.logger and len(all_offers) < 20:  # Only log details for small lists
                self.logger.debug(f"  Offer: {technical_name} ({monetization_type})")

            # Filter by providers if specified
            if providers and technical_name not in providers:
                continue

            # Only include FLATRATE (subscription) offers
            if monetization_type != "FLATRATE":
                continue

            offer = Offer(
                provider_id=package.get("packageId", 0),
                provider_short_name=package.get("shortName", ""),
                monetization_type=monetization_type,
                presentation_type=offer_data.get("presentationType", "SD"),
            )
            offers.append(offer)

        # Cache the results
        if cache_key and self.cache_manager and self.cache_manager.is_enabled():
            cache_data = [o.model_dump() for o in offers]
            self.cache_manager.set(cache_key, cache_data)
            if self.logger:
                self.logger.debug(f"Cached JustWatch offers for: {justwatch_id}")

        return offers

    def check_availability(
        self,
        title: str,
        providers: List[str],
        release_year: Optional[int] = None,
        content_type: str = "MOVIE",
        imdb_id: Optional[str] = None,
    ) -> AvailabilityResult:
        """
        Check if content is available on specified providers.

        Args:
            title: Content title
            providers: List of provider technical names to check
            release_year: Optional release year for better matching
            content_type: Type of content (MOVIE or SHOW)
            imdb_id: Optional IMDB ID for caching

        Returns:
            Availability result with provider information

        Raises:
            JustWatchAPIError: On API errors
        """
        # Check cache first using IMDB ID if available
        cache_key = None
        if self.cache_manager and self.cache_manager.is_enabled() and imdb_id:
            cache_key = f"justwatch_availability_{content_type}_{imdb_id}_{self.locale}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                if self.logger:
                    self.logger.debug(f"Cache hit for availability check: {title} ({imdb_id})")
                return AvailabilityResult.from_cache_dict(cached)

        # Search for the content
        search_results = self.search_title(title, release_year, content_type)

        if not search_results:
            result = AvailabilityResult(
                title=title,
                available=False,
                providers=[],
                locale=self.locale,
            )
            # Cache negative result
            if cache_key and self.cache_manager and self.cache_manager.is_enabled():
                self.cache_manager.set(cache_key, result.to_cache_dict())
            return result

        # Use the first (most popular) result
        best_match = search_results[0]

        # Get offers for this content
        offers = self.get_offers(best_match.id, providers)

        # Determine which providers have this content
        found_providers = list(set(offer.provider_short_name for offer in offers))

        # Check if any of the configured providers have this content
        available = len(found_providers) > 0

        result = AvailabilityResult(
            title=title,
            available=available,
            providers=found_providers,
            offers=offers,
            locale=self.locale,
            justwatch_id=best_match.id,
        )

        # Cache the result
        if cache_key and self.cache_manager and self.cache_manager.is_enabled():
            self.cache_manager.set(cache_key, result.to_cache_dict())
            if self.logger:
                self.logger.debug(f"Cached availability result for: {title} ({imdb_id})")

        return result

    def get_providers(self) -> List[Provider]:
        """
        Get all available streaming providers for the configured locale.

        Returns:
            List of available providers

        Raises:
            JustWatchAPIError: On API errors
        """
        cache_key = None
        if self.cache_manager and self.cache_manager.is_enabled():
            cache_key = f"justwatch_providers_{self.locale}"
            cached = self.cache_manager.get(cache_key)
            if cached:
                if self.logger:
                    self.logger.debug(f"Cache hit for providers list: {self.locale}")
                return [Provider(**item) for item in cached]

        variables = {"country": self.country}

        data = self._make_request(PROVIDERS_QUERY, variables)

        packages = data.get("packages", [])
        providers = []

        for package in packages:
            provider = Provider(
                id=package.get("packageId", 0),
                technical_name=package.get("technicalName", ""),
                short_name=package.get("shortName", ""),
                clear_name=package.get("clearName", ""),
                monetization_types=package.get("monetizationTypes", []),
            )
            providers.append(provider)

        # Cache the results
        if cache_key and self.cache_manager and self.cache_manager.is_enabled():
            cache_data = [p.model_dump() for p in providers]
            self.cache_manager.set(cache_key, cache_data)
            if self.logger:
                self.logger.debug(f"Cached providers list for: {self.locale}")

        return providers
