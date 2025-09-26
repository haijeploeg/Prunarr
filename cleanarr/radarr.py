from __future__ import annotations
from typing import Any, Dict, List
from pyarr import RadarrAPI as PyarrRadarrAPI


class RadarrAPI:
    """
    Lichte wrapper rond pyarr.RadarrAPI zodat de rest van de code
    niet direct aan pyarr gebonden is (eenvoudige facade).
    """

    def __init__(self, url: str, api_key: str) -> None:
        # pyarr RadarrAPI initialisatie: RadarrAPI(base_url, api_key)
        self._api = PyarrRadarrAPI(url.rstrip("/"), api_key)

    def get_movie(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Return list van movies. We gebruiken pyarr's get_movie() interface.
        Extra kwargs worden direct doorgegeven (indien nodig).
        """
        # pyarr may already provide pagination internally; keep signature compatible.
        return self._api.get_movie(**kwargs)

    def get_tag(self, tag_id: int) -> Dict[str, Any]:
        """Haalt een tag op via tag_id."""
        return self._api.get_tag(tag_id)
