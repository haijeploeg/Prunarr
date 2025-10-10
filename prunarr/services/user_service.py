"""
User service for managing user tag parsing and validation.

This service encapsulates all logic related to extracting and validating
user associations from Radarr/Sonarr tags.
"""

import re
from typing import List, Optional


class UserService:
    """
    Service for managing user tag extraction and validation.

    This service handles the parsing of user information from media tags
    based on configurable regex patterns, enabling flexible user identification
    schemes across different Radarr/Sonarr setups.

    Attributes:
        tag_pattern: Compiled regex pattern for user tag extraction
    """

    def __init__(self, user_tag_regex: str):
        """
        Initialize UserService with tag pattern.

        Args:
            user_tag_regex: Regex pattern for extracting username from tags
                          (default: r'^\\d+ - (.+)$' for format "123 - username")
        """
        self.tag_pattern = re.compile(user_tag_regex)

    def extract_username_from_tags(self, tag_ids: List[int], api_client) -> Optional[str]:
        """
        Extract username from media tags using configured regex pattern.

        Args:
            tag_ids: List of tag IDs to examine
            api_client: API client instance (Radarr or Sonarr) for tag retrieval

        Returns:
            Username string if a matching tag is found, None otherwise

        Examples:
            For tag format "123 - john_doe":
            >>> user_service = UserService(r'^\\d+ - (.+)$')
            >>> username = user_service.extract_username_from_tags([5, 10], radarr_client)
            >>> print(username)  # "john_doe"
        """
        for tag_id in tag_ids:
            try:
                tag = api_client.get_tag(tag_id)
                label = tag.get("label", "")
                match = self.tag_pattern.match(label)
                if match:
                    return match.group(1)
            except Exception:
                # Continue processing remaining tags if one fails
                continue
        return None

    def validate_tag_format(self, tag_label: str) -> bool:
        """
        Validate if a tag label matches the configured pattern.

        Args:
            tag_label: Tag label string to validate

        Returns:
            True if tag matches pattern, False otherwise
        """
        return bool(self.tag_pattern.match(tag_label))

    def extract_username_from_label(self, tag_label: str) -> Optional[str]:
        """
        Extract username directly from tag label string.

        Args:
            tag_label: Tag label string

        Returns:
            Username if pattern matches, None otherwise
        """
        match = self.tag_pattern.match(tag_label)
        return match.group(1) if match else None

    def is_user_tag(self, tag_label: str) -> bool:
        """
        Check if a tag label is a user tag (matches user tag pattern).

        Args:
            tag_label: Tag label string to check

        Returns:
            True if tag is a user tag, False otherwise
        """
        return self.validate_tag_format(tag_label)

    def get_all_tag_labels(self, tag_ids: List[int], api_client) -> List[str]:
        """
        Get all tag labels for given tag IDs.

        Args:
            tag_ids: List of tag IDs to retrieve
            api_client: API client instance (Radarr or Sonarr) for tag retrieval

        Returns:
            List of tag label strings

        Examples:
            >>> labels = user_service.get_all_tag_labels([1, 2, 3], radarr_client)
            >>> print(labels)  # ["4K", "Action", "123 - john_doe"]
        """
        labels = []
        for tag_id in tag_ids:
            try:
                tag = api_client.get_tag(tag_id)
                label = tag.get("label", "")
                if label:
                    labels.append(label)
            except Exception:
                # Skip failed tag retrievals
                continue
        return labels

    def get_non_user_tag_labels(self, tag_ids: List[int], api_client) -> List[str]:
        """
        Get all non-user tag labels (tags that don't match user tag pattern).

        This is useful for displaying organizational tags separately from user associations.

        Args:
            tag_ids: List of tag IDs to examine
            api_client: API client instance (Radarr or Sonarr) for tag retrieval

        Returns:
            List of non-user tag label strings

        Examples:
            >>> tags = user_service.get_non_user_tag_labels([1, 2, 3], radarr_client)
            >>> print(tags)  # ["4K", "Action"] (excludes "123 - john_doe")
        """
        all_labels = self.get_all_tag_labels(tag_ids, api_client)
        return [label for label in all_labels if not self.is_user_tag(label)]
