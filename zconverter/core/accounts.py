"""Sessions from the in-app login window.

Cookies are only ever obtained by the user signing in themselves inside the app. They are
stored per platform, encrypted with Windows DPAPI (readable only by the same Windows user),
and only sent to the site they belong to (normal cookie domain matching)."""

import ctypes
import json
import sys
import time
from ctypes import wintypes
from http.cookiejar import Cookie, CookieJar

from .paths import app_dir

PLATFORMS = {
    # key: (display name, login url, cookie domains, cookie that proves a signed-in session)
    "reddit": ("Reddit", "https://www.reddit.com/login/", ("reddit.com",), "reddit_session"),
    "instagram": ("Instagram", "https://www.instagram.com/accounts/login/", ("instagram.com",), "sessionid"),
    "threads": ("Threads", "https://www.threads.com/login", ("threads.com", "threads.net"), "sessionid"),
    "facebook": ("Facebook", "https://www.facebook.com/login/", ("facebook.com",), "c_user"),
    "twitter": ("X", "https://x.com/i/flow/login", ("x.com", "twitter.com"), "auth_token"),
    "tiktok": ("TikTok", "https://www.tiktok.com/login", ("tiktok.com",), "sessionid"),
    "soundcloud": ("SoundCloud", "https://soundcloud.com/signin", ("soundcloud.com",), "oauth_token"),
    "youtube": ("YouTube", "https://accounts.google.com/ServiceLogin?service=youtube&continue=https://www.youtube.com/",
                ("youtube.com", "google.com"), "SID"),
}


def default_browser() -> str:
    """'firefox', 'brave', 'chrome', 'edge', ... from the Windows https handler."""
    if sys.platform != "win32":
        return ""
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations"
                            r"\UrlAssociations\https\UserChoice") as key:
            prog = winreg.QueryValueEx(key, "ProgId")[0].lower()
    except OSError:
        return ""
    for name, token in (("firefox", "firefox"), ("brave", "brave"), ("edge", "msedge"), ("chrome", "chrome"),
                        ("opera", "opera"), ("vivaldi", "vivaldi")):
        if token in prog:
            return name
    return ""


# ---------------------------------------------------------------- DPAPI

class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(data: bytes, protect: bool) -> bytes:
    if sys.platform != "win32":
        return data
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(data, len(data))
    src = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = _Blob()
    fn = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    if not fn(ctypes.byref(src), None, None, None, None, 0x1, ctypes.byref(out)):  # UI_FORBIDDEN
        raise OSError("DPAPI failed")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(out.pbData)


# ---------------------------------------------------------------- storage

def _file(platform: str):
    folder = app_dir() / "sessions"
    folder.mkdir(exist_ok=True)
    return folder / f"{platform}.bin"


def domain_matches(domain: str, platform: str) -> bool:
    d = domain.lstrip(".").lower()
    return any(d == x or d.endswith("." + x) for x in PLATFORMS[platform][2])


def save(platform: str, cookies: list[dict]) -> None:
    cookies = [c for c in cookies if domain_matches(c["domain"], platform)]
    _file(platform).write_bytes(_dpapi(json.dumps(cookies).encode(), protect=True))


def load(platform: str) -> list[dict]:
    path = _file(platform)
    if not path.exists():
        return []
    try:
        cookies = json.loads(_dpapi(path.read_bytes(), protect=False))
    except (OSError, ValueError):
        return []
    now = time.time()
    return [c for c in cookies if not c.get("expires") or c["expires"] > now]


def signed_in(platform: str) -> bool:
    marker = PLATFORMS[platform][3]
    return any(c["name"] == marker for c in load(platform))


def sign_out(platform: str) -> None:
    _file(platform).unlink(missing_ok=True)


def is_signed_in_cookie(platform: str, name: str) -> bool:
    return name == PLATFORMS[platform][3]


def apply(jar: CookieJar) -> None:
    """Add every saved session to a cookie jar (yt-dlp's or a requests session's)."""
    for platform in PLATFORMS:
        for c in load(platform):
            domain = c["domain"]
            jar.set_cookie(Cookie(
                version=0, name=c["name"], value=c["value"], port=None, port_specified=False,
                domain=domain, domain_specified=True, domain_initial_dot=domain.startswith("."),
                path=c.get("path") or "/", path_specified=True, secure=bool(c.get("secure")),
                expires=int(c["expires"]) if c.get("expires") else None, discard=not c.get("expires"),
                comment=None, comment_url=None, rest={"HttpOnly": ""} if c.get("httponly") else {},
            ))
