"""Thin async client for Orion's token-authed machine API.

Endpoints (see docs/home-assistant.md in the Orion repo):
  GET  /api/machine/summary  -> up-next / airing-today / airing-week / releasing feed
  POST /api/machine/watched  -> {"kind": "episode"|"movie"|"game", "id": int, "watched": bool}
  POST /api/machine/follow   -> {"kind": "show"|"movie"|"game", "id": int, "followed"?: bool, "archived"?: bool}
  POST /api/machine/sync     -> manual catalog refresh + notification check
"""

from __future__ import annotations

from typing import Any

import aiohttp


class OrionApiError(Exception):
    """Raised for any non-2xx response or transport failure talking to Orion."""


class OrionAuthError(OrionApiError):
    """Raised specifically for a 401 (bad or missing token)."""


class OrionClient:
    """Minimal REST client for a single Orion instance + API token."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def get_summary(self) -> dict[str, Any]:
        """Fetch the consolidated /api/machine/summary feed."""
        return await self._request("GET", "/api/machine/summary")

    async def mark_watched(self, kind: str, item_id: int, watched: bool) -> None:
        await self._request(
            "POST",
            "/api/machine/watched",
            json={"kind": kind, "id": item_id, "watched": watched},
        )

    async def set_followed(
        self,
        kind: str,
        item_id: int,
        *,
        followed: bool | None = None,
        archived: bool | None = None,
    ) -> None:
        body: dict[str, Any] = {"kind": kind, "id": item_id}
        if followed is not None:
            body["followed"] = followed
        if archived is not None:
            body["archived"] = archived
        await self._request("POST", "/api/machine/follow", json=body)

    async def trigger_sync(self) -> dict[str, Any]:
        return await self._request("POST", "/api/machine/sync")

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(method, url, headers=self._headers, **kwargs) as resp:
                if resp.status == 401:
                    raise OrionAuthError("Orion rejected the API token")
                if resp.status >= 400:
                    text = await resp.text()
                    raise OrionApiError(f"Orion returned {resp.status}: {text}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise OrionApiError(f"Could not reach Orion at {url}: {err}") from err
