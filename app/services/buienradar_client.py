from collections.abc import Mapping
from typing import Any

import httpx

from app.core.config import get_settings


class BuienradarClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_latest(self) -> Mapping[str, Any]:
        response = httpx.get(
            self.settings.buienradar_url,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Unexpected payload type from Buienradar")
        return payload
