from __future__ import annotations
from typing import Any, Dict, List, Optional
import re
from datetime import datetime, timedelta

from .config import Settings
from .radarr import RadarrAPI
from .tautulli import TautulliAPI

TAG_PATTERN = re.compile(r"^\d+ - (.+)$")


class CleanArr:
    """
    Hoofdlogica die Radarr en Tautulli koppelt.
    Functies zijn zo geschreven dat ze overeenkomen met je originele script.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.radarr = RadarrAPI(settings.radarr_url, settings.radarr_api_key)
        self.tautulli = TautulliAPI(settings.tautulli_url, settings.tautulli_api_key)
        self.days_before_removal = settings.days_before_removal

    def get_user_tags(self, tag_ids: List[int]) -> Optional[str]:
        """
        Haal username uit tags. Verwacht tags in format "userid - username".
        Retourneert de username (gedeelte na ' - ') of None.
        """
        # Vraag per tag_id de tag op en test regex
        for tag_id in tag_ids:
            tag = self.radarr.get_tag(tag_id)
            label = tag.get("label", "")
            m = TAG_PATTERN.match(label)
            if m:
                return m.group(1)
        return None

    @property
    def radarr_movies(self) -> List[Dict[str, Any]]:
        """
        Retourneert alle Radarr films die:
        - een movieFile hebben (dus gedownload)
        - tags bevatten die overeenkomen met het 'userid - username' format
        Per item returnen we id, title, imdb_id en user.
        """
        result: List[Dict[str, Any]] = []
        movies = self.radarr.get_movie()
        for movie in movies:
            movie_file = movie.get("movieFile")
            tag_ids = movie.get("tags", [])
            if not movie_file or not tag_ids:
                continue
            username = self.get_user_tags(tag_ids)
            if username:
                result.append(
                    {
                        "id": movie.get("id"),
                        "title": movie.get("title"),
                        "imdb_id": movie.get("imdbId"),
                        "user": username,
                    }
                )
        return result

    def get_movie_by_imdb_id(self, imdb_id: Optional[str], movies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Zoek in lijst van radarr-movies op imdb_id (tt...)."""
        if not imdb_id:
            return None
        return next((m for m in movies if m.get("imdb_id") == imdb_id), None)

    def get_watch_history(self) -> List[Dict[str, Any]]:
        """
        Combineer Tautulli kijkgeschiedenis met Radarr-requested movies.
        Return een lijst met Radarr-details van films die:
         - door dezelfde gebruiker zijn bekeken als in de tag
         - en waarbij het bekeken-verschil >= days_before_removal
        """
        tautulli_history = self.tautulli.get_movie_completed_history()
        requested_movies = self.radarr_movies

        movies_to_delete: List[Dict[str, Any]] = []
        now = datetime.now()

        for record in tautulli_history:
            watched_by = record.get("user")
            watched_at_ts = record.get("watched_at")
            # watched_at in tautulli is epoch seconds — guard against None
            if not watched_at_ts:
                continue
            watched_at = datetime.fromtimestamp(int(watched_at_ts))
            time_diff = now - watched_at

            rating_key = record.get("rating_key")
            imdb_id = None
            if rating_key is not None:
                imdb_id = self.tautulli.get_imdb_id_from_rating_key(str(rating_key))

            radarr_details = self.get_movie_by_imdb_id(imdb_id, requested_movies)
            if not radarr_details:
                continue

            if watched_by == radarr_details.get("user") and time_diff >= timedelta(days=self.days_before_removal):
                movies_to_delete.append(radarr_details)

        return movies_to_delete