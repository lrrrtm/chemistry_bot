from __future__ import annotations

from os import getenv
from urllib.parse import quote, urlencode, urlparse


def _normalize_domain(domain: str | None) -> str | None:
    if not domain:
        return None

    clean = domain.strip().rstrip("/")
    if not clean:
        return None

    if clean.startswith(("http://", "https://")):
        return clean

    return f"https://{clean}"


def get_tma_base_url() -> str | None:
    domain = _normalize_domain(getenv("DOMAIN"))
    if not domain:
        return None
    return f"{domain}/tma/"


def get_tma_start_url(startapp: str | None = None) -> str | None:
    base_url = get_tma_base_url()
    if not base_url:
        return None

    if not startapp:
        return base_url

    return f"{base_url}?startapp={quote(startapp)}"


def append_query_params(url: str | None, params: dict[str, str | None]) -> str | None:
    if not url:
        return None

    clean_params = {key: value for key, value in params.items() if value}
    if not clean_params:
        return url

    return f"{url}{'&' if '?' in url else '?'}{urlencode(clean_params)}"


def get_tma_invite_url(invite_token: str) -> str | None:
    return append_query_params(get_tma_start_url(), {"invite": invite_token})


def get_tma_share_link(startapp: str | None = None) -> str | None:
    bot_name = (getenv("BOT_NAME") or "").strip().lstrip("@")
    if not bot_name:
        return None

    if not startapp:
        return f"https://t.me/{bot_name}?startapp"

    return f"https://t.me/{bot_name}?startapp={quote(startapp)}"


def is_public_web_app_url(url: str | None) -> bool:
    if not url:
        return False

    hostname = (urlparse(url).hostname or "").lower()
    if not hostname:
        return False

    return hostname not in {"localhost", "127.0.0.1", "0.0.0.0"}
