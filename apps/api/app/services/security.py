from __future__ import annotations

from fastapi import Header, HTTPException

from app.core.config import settings


def require_auth(authorization: str | None = Header(default=None)) -> None:
    """Bearer-token gate for the API.

    When API_AUTH_TOKEN is unset (the local/dev default) the API is open. When set,
    every request must send ``Authorization: Bearer <token>``. The token is only ever
    read from settings/environment and never logged (never print secrets).
    """
    token = settings.api_auth_token
    if not token:
        return
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
