"""
Async API client for cmhair-api.
Supports both per-user tokens (from /login) and optional env-based fallback.
"""

import asyncio
import logging
from typing import Any

import httpx
from config import API_BASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD

log = logging.getLogger(__name__)

ADMIN_ROLES = {"engineer_admin"}

# ── Global fallback token (env-based) ─────────────────────────────────────────
_global_token: str | None = None
_lock = asyncio.Lock()


# ── Auth ───────────────────────────────────────────────────────────────────────

async def login_user(email: str, password: str) -> dict:
    """
    Login with email/password. Returns dict with token, roles, name.
    Raises ValueError if credentials are wrong or user is not admin.
    """
    # Use a longer timeout (60s) and specifically extend the connect timeout
    timeout = httpx.Timeout(60.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{API_BASE_URL}/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()
        body = resp.json()
        inner = body.get("data") or body
        token = inner.get("access_token") or body.get("access_token")
        if not token:
            raise ValueError("No access_token in response")
        user = inner.get("user", {})
        roles: list[str] = user.get("roles", [])
        name = (user.get("profile") or {}).get("full_name") or email
        return {"token": token, "roles": roles, "name": name}


async def _global_login() -> str:
    """Fallback: login using env credentials (used by /status command)."""
    result = await login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
    return result["token"]


async def _get_global_token() -> str:
    global _global_token
    async with _lock:
        if not _global_token:
            _global_token = await _global_login()
    return _global_token


async def ensure_logged_in() -> bool:
    global _global_token
    try:
        _global_token = await _global_login()
        return True
    except Exception as exc:
        log.error("Login failed: %s", exc)
        return False


# ── HTTP helper ────────────────────────────────────────────────────────────────

def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _request(method: str, path: str, token: str, **kwargs) -> Any:
    """Authenticated request. Raises on HTTP error with detail."""
    timeout = httpx.Timeout(60.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, f"{API_BASE_URL}{path}", headers=_headers(token), **kwargs)
        if resp.status_code >= 400:
            try:
                err = resp.json()
                detail = err.get("detail") or err.get("error") or resp.text
            except:
                detail = resp.text
            raise Exception(detail)
        return resp.json()


# ── Products ───────────────────────────────────────────────────────────────────

async def get_categories(token: str) -> list[dict]:
    return await _request("GET", "/products/categories", token)


async def create_product(data: dict, token: str) -> dict:
    return await _request("POST", "/products/", token, json=data)


async def create_category(data: dict, token: str) -> dict:
    return await _request("POST", "/products/categories", token, json=data)


# ── Uploads ────────────────────────────────────────────────────────────────────

async def upload_image(file_bytes: bytes, token: str, filename: str = "image.jpg") -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{API_BASE_URL}/upload/image",
            headers=_headers(token),
            files={"file": (filename, bytes(file_bytes), "image/jpeg")},
        )
        resp.raise_for_status()
        return resp.json()["url"]
