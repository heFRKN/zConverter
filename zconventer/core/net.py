"""HTTP access. The app always identifies itself honestly and never impersonates
browsers or crawlers. When a site requires login, the user's own browser session
can be used (opt-in, read locally, never stored or sent anywhere else)."""

import html
import json
import re

import requests

from .. import REPO_URL, __version__

USER_AGENT = f"zConventer/{__version__} (+{REPO_URL})"


class NetError(Exception):
    pass


def session(cookies_browser: str = "") -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"})
    if cookies_browser:
        from yt_dlp.cookies import extract_cookies_from_browser

        try:
            s.cookies = extract_cookies_from_browser(cookies_browser)
        except Exception as e:  # browser locked, unsupported encryption, etc.
            raise NetError(f"{cookies_browser} oturumu okunamadı: {e}") from e
    return s


def meta(page: str, prop: str) -> str | None:
    """Read an <meta property|name=... content=...> value regardless of attribute order."""
    for tag in re.findall(r"<meta\b[^>]*>", page, re.I):
        if re.search(rf'(?:property|name)\s*=\s*"{re.escape(prop)}"', tag, re.I):
            m = re.search(r'content\s*=\s*"([^"]*)"', tag, re.I)
            if m:
                return html.unescape(m.group(1))
    return None


def json_string(page: str, key: str) -> str | None:
    """Find "key":"value" inside inline JSON and decode the JSON string escapes."""
    m = re.search(rf'"{re.escape(key)}"\s*:\s*("(?:[^"\\]|\\.)*")', page)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None
