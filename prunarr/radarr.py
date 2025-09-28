"""
Radarr API client module for PrunArr CLI application.

This module provides a comprehensive interface to the Radarr API for movie management
operations. It wraps the pyarr library to provide a consistent, application-specific
API while maintaining flexibility and error handling capabilities.

The RadarrAPI class serves as a facade over the pyarr.RadarrAPI, providing:
- Simplified movie retrieval and management
- Tag-based movie organization and filtering
- Safe movie deletion with file management options
- Comprehensive error handling and logging
- Consistent data formatting across the application
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pyarr import RadarrAPI as PyarrRadarrAPI


class RadarrAPI:
    """
    Enhanced Radarr API client with comprehensive movie management capabilities.

    This class provides a clean, application-specific interface to Radarr's REST API
    through the pyarr library. It handles movie retrieval, tag management, and deletion
    operations while providing consistent error handling and data formatting.

    The API client is designed to:
    - Abstract pyarr implementation details from the rest of the application
    - Provide type-safe interfaces with comprehensive documentation
    - Handle errors gracefully without exposing internal exceptions
    - Support all necessary movie management operations for PrunArr

    Attributes:
        _api: Internal pyarr RadarrAPI instance for actual API communication
        base_url: Radarr server base URL (normalized)
        api_key: Radarr API key for authentication
    """

    def __init__(self, url: str, api_key: str) -> None:
        """
        Initialize the Radarr API client with server connection details.

        Args:
            url: Base URL of the Radarr server (e.g., "http://localhost:7878")
            api_key: Radarr API key for authentication

        Examples:
            >>> radarr = RadarrAPI("http://localhost:7878", "your-api-key")
            >>> movies = radarr.get_movie()
        """
        self.base_url = url.rstrip("/")
        self.api_key = api_key
        self._api = PyarrRadarrAPI(self.base_url, api_key)

    def get_movie(self, movie_id: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve movies from Radarr with optional filtering and pagination.

        This method provides access to Radarr's movie collection with support for
        various filtering options. It can retrieve all movies or specific movies
        based on provided criteria.

        Args:
            movie_id: Optional specific movie ID to retrieve
            **kwargs: Additional query parameters passed to the Radarr API

        Returns:
            List of movie dictionaries containing complete movie metadata

        Examples:
            Get all movies:
            >>> movies = radarr.get_movie()

            Get specific movie:
            >>> movie = radarr.get_movie(movie_id=123)

            Get movies with custom parameters:
            >>> movies = radarr.get_movie(monitored=True)

        Raises:
            Exception: If API communication fails or authentication is invalid
        """
        if movie_id is not None:
            return self._api.get_movie(movie_id, **kwargs)
        return self._api.get_movie(**kwargs)

    def get_tag(self, tag_id: int) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific Radarr tag.

        Tags in Radarr are used to organize and categorize movies. This method
        retrieves the complete tag information including label and associated metadata.

        Args:
            tag_id: Unique identifier of the tag to retrieve

        Returns:
            Dictionary containing tag information with keys like 'id', 'label'

        Examples:
            >>> tag = radarr.get_tag(5)
            >>> print(tag['label'])  # "user123 - john_doe"

        Raises:
            Exception: If tag doesn't exist or API communication fails
        """
        return self._api.get_tag(tag_id)

    def delete_movie(self, movie_id: int, delete_files: bool = True, add_exclusion: bool = False) -> bool:
        """
        Delete a movie from Radarr with comprehensive options.

        This method safely removes a movie from Radarr's database and optionally
        deletes the associated files from disk. It provides fine-grained control
        over the deletion process with proper error handling.

        Args:
            movie_id: Unique Radarr movie ID to delete
            delete_files: Whether to delete movie files from disk (default: True)
            add_exclusion: Whether to add movie to exclusion list (default: False)

        Returns:
            True if deletion was successful, False if it failed

        Examples:
            Delete movie and files:
            >>> success = radarr.delete_movie(123)

            Delete from Radarr but keep files:
            >>> success = radarr.delete_movie(123, delete_files=False)

            Delete and exclude from future imports:
            >>> success = radarr.delete_movie(123, add_exclusion=True)

        Note:
            This operation is irreversible when delete_files=True. Use with caution.
        """
        try:
            return self._api.del_movie(
                movie_id,
                delete_files=delete_files,
                add_exclusion=add_exclusion
            )
        except Exception:
            # Log the exception in production code, but return False for now
            return False

    def get_movie_by_tmdb_id(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a movie by its TMDB (The Movie Database) ID.

        This method searches Radarr's movie collection for a movie with the specified
        TMDB ID, which is useful for cross-referencing with external services.

        Args:
            tmdb_id: The Movie Database ID to search for

        Returns:
            Movie dictionary if found, None if no movie matches the TMDB ID

        Examples:
            >>> movie = radarr.get_movie_by_tmdb_id(550)  # Fight Club
            >>> if movie:
            ...     print(movie['title'])

        Note:
            This method may be slower than direct ID lookup as it searches
            through the movie collection for matching TMDB IDs.
        """
        try:
            movies = self.get_movie()
            for movie in movies:
                if movie.get('tmdbId') == tmdb_id:
                    return movie
            return None
        except Exception:
            return None

    def get_movies_by_tag(self, tag_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all movies associated with a specific tag.

        This method filters the movie collection to return only movies that have
        been tagged with the specified tag ID. Useful for user-based filtering
        and organization.

        Args:
            tag_id: Tag ID to filter movies by

        Returns:
            List of movie dictionaries that have the specified tag

        Examples:
            >>> user_movies = radarr.get_movies_by_tag(5)
            >>> print(f"Found {len(user_movies)} movies for this user")

        Note:
            Movies can have multiple tags, so this returns movies that include
            the specified tag among their tags, not exclusively.
        """
        try:
            movies = self.get_movie()
            return [
                movie for movie in movies
                if tag_id in movie.get('tags', [])
            ]
        except Exception:
            return []

    def get_movie_file_info(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve file information for a specific movie.

        This method gets detailed file information including size, quality,
        and file path for a downloaded movie.

        Args:
            movie_id: Radarr movie ID to get file info for

        Returns:
            Dictionary with file information or None if no file exists

        Examples:
            >>> file_info = radarr.get_movie_file_info(123)
            >>> if file_info:
            ...     print(f"File size: {file_info.get('size', 0)} bytes")
        """
        try:
            movie = self.get_movie(movie_id)
            if movie and isinstance(movie, list) and len(movie) > 0:
                movie_data = movie[0]
                return movie_data.get('movieFile')
            return None
        except Exception:
            return None
