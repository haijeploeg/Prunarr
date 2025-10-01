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

    def extract_username_from_tags(
        self, tag_ids: List[int], api_client
    ) -> Optional[str]:
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
