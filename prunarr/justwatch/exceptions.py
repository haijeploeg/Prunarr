"""Custom exceptions for JustWatch API integration."""


class JustWatchAPIError(Exception):
    """Base exception for JustWatch API errors."""

    pass


class JustWatchNotFoundError(JustWatchAPIError):
    """Raised when content is not found on JustWatch."""

    pass


class JustWatchRateLimitError(JustWatchAPIError):
    """Raised when JustWatch API rate limit is exceeded."""

    pass


class JustWatchGraphQLError(JustWatchAPIError):
    """Raised when GraphQL query returns an error."""

    pass
