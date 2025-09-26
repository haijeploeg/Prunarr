from __future__ import annotations
import re
from typing import Any, Dict, List
import requests

IMDB_ID_PATTERN = re.compile(r"^imdb:\/\/(tt\d+)")


class TautulliAPI:
    """
    Kleine Tautulli client, gericht op de calls die we nodig hebben:
    - get_history (met paginering)
    - get_metadata
    - imdb-id extractie uit metadata.guids
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(self, cmd: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/api/v2"
        params = params or {}
        params.update({"apikey": self.api_key, "cmd": cmd})
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("response", {})

    def get_watch_history(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        Haal alle history records op via paginering.
        Retourneert de ruwe records zoals Tautulli ze teruggeeft (lijst van dicts).
        """
        all_records: List[Dict[str, Any]] = []
        start = 0
        while True:
            params = {"length": page_size, "start": start}
            resp = self._request("get_history", params=params)
            # Tautulli response structure: { "data": { "data": [ ... ] } }
            page_data = resp.get("data", {}).get("data", [])
            if not page_data:
                break
            all_records.extend(page_data)
            # Als de pagina kleiner is dan page_size, einde
            if len(page_data) < page_size:
                break
            start += page_size
        return all_records

    def get_movie_completed_history(self) -> List[Dict[str, Any]]:
        """
        Filter alleen records die volledig bekeken zijn en media_type == "movie".
        Tautulli gebruikt 'watched_status' == 1 voor volledig bekeken.
        """
        return [
            {
                "title": r.get("title"),
                "rating_key": r.get("rating_key"),
                "user": r.get("friendly_name"),
                "watched_at": r.get("date"),
                "watched_status": r.get("watched_status"),
                "media_type": r.get("media_type"),
            }
            for r in self.get_watch_history()
            if r.get("watched_status") == 1 and r.get("media_type") == "movie"
        ]

    def get_metadata(self, rating_key: str) -> Dict[str, Any]:
        """Haal metadata op van een item via rating_key."""
        resp = self._request("get_metadata", params={"rating_key": rating_key})
        return resp.get("data", {})

    def get_imdb_id_from_rating_key(self, rating_key: str) -> str | None:
        """
        Haal IMDb ID (tt...) uit metadata.guids wanneer beschikbaar.
        Retourneert bijvoorbeeld 'tt1234567' of None.
        """
        metadata = self.get_metadata(rating_key)
        for guid in metadata.get("guids", []) or []:
            m = IMDB_ID_PATTERN.match(guid)
            if m:
                return m.group(1)
        return None
