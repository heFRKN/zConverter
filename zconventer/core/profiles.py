"""Profile picture and banner lookup from public sources only."""

import html
import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse

import requests

from .net import NetError, json_string, meta, session
from .paths import app_dir
from .platforms import PLATFORMS, detect, normalize_url

LOGIN_HINT = "Ayarlar → Tarayıcı oturumu'ndan bu platforma giriş yaptığın tarayıcıyı seçip tekrar dene."


class ProfileError(Exception):
    pass


@dataclass
class Asset:
    kind: str                       # avatar | banner
    urls: list[str]                 # candidates, best first
    data: bytes = b""


@dataclass
class Profile:
    platform: str
    handle: str
    name: str = ""
    avatar: Asset | None = None
    banner: Asset | None = None
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- input parsing

def parse_input(text: str, platform: str) -> tuple[str, str]:
    """Return (platform_key, handle_or_url). URLs override the selected platform."""
    text = text.strip()
    if not text:
        raise ProfileError("Kullanıcı adı ya da profil bağlantısı gir.")
    short_reddit = re.fullmatch(r"/?(r|u|user)/([\w-]+)/?", text)
    if short_reddit:
        kind, name = short_reddit.groups()
        return "reddit", ("r/" if kind == "r" else "u/") + name
    if "/" in text or text.startswith(("http", "www.")):
        url = normalize_url(text)
        p = detect(url)
        if not p or p.key not in ("youtube", "instagram", "twitter", "threads", "reddit", "facebook"):
            raise ProfileError("Bu bağlantı desteklenen bir profil platformuna ait değil.")
        if p.key in ("youtube", "facebook"):
            return p.key, url
        path = [s for s in urlparse(url).path.split("/") if s]
        if p.key == "reddit":
            if len(path) >= 2 and path[0] in ("r", "u", "user"):
                return p.key, ("r/" if path[0] == "r" else "u/") + path[1]
            raise ProfileError("Reddit bağlantısı /r/… ya da /user/… olmalı.")
        if not path:
            raise ProfileError("Bağlantıda kullanıcı adı yok.")
        return p.key, path[0].lstrip("@")
    handle = text.lstrip("@")
    if platform == "reddit" and not handle.startswith(("r/", "u/")):
        handle = "u/" + handle
    return platform, handle


# ---------------------------------------------------------------- platforms

class _SilentLog:
    def debug(self, msg):
        pass

    warning = error = debug


def _youtube(target: str, cookies: str) -> Profile:
    import yt_dlp

    url = target if "://" in target else f"https://www.youtube.com/@{target}"
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": "in_playlist",
            "playlistend": 1, "logger": _SilentLog(), "cachedir": str(app_dir() / "cache")}
    if cookies:
        opts["cookiesfrombrowser"] = (cookies,)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise ProfileError("YouTube kanalı bulunamadı.") from e
    thumbs = info.get("thumbnails") or []
    by_id = {t.get("id"): t["url"] for t in thumbs if t.get("url")}
    avatar = by_id.get("avatar_uncropped")
    banner = by_id.get("banner_uncropped")
    prof = Profile("youtube", info.get("uploader_id") or info.get("channel") or target,
                   info.get("channel") or info.get("uploader") or "")
    if avatar:
        prof.avatar = Asset("avatar", [avatar])
    if banner:
        prof.banner = Asset("banner", [banner])
    return prof


def _twitter(handle: str, cookies: str) -> Profile:
    # FxTwitter is an open-source public API for X profiles (https://github.com/FxEmbed/FxEmbed)
    sess = session()
    user = None
    for _ in range(3):  # its cache sometimes answers 404 to the first request
        r = sess.get(f"https://api.fxtwitter.com/{handle}", timeout=15)
        user = (r.json() if r.ok else {}).get("user")
        if user or r.status_code != 404:
            break
    if not user:
        raise ProfileError("X hesabı bulunamadı ya da askıya alınmış.")
    prof = Profile("twitter", user.get("screen_name") or handle, user.get("name") or "")
    if user.get("avatar_url"):
        small = user["avatar_url"]
        prof.avatar = Asset("avatar", [re.sub(r"_(normal|bigger|mini|200x200|400x400)(?=\.\w+$)", "", small),
                                       small.replace("_normal", "_400x400"), small])
    if user.get("banner_url"):
        prof.banner = Asset("banner", [user["banner_url"] + "/1500x500", user["banner_url"]])
    return prof


def _instagram(handle: str, cookies: str, platform: str = "instagram") -> Profile:
    r = session(cookies).get(f"https://www.instagram.com/{handle}/", timeout=15)
    if r.status_code == 404:
        raise ProfileError("Instagram hesabı bulunamadı.")
    page = r.text
    hd = json_string(page, "profile_pic_url_hd")
    og = meta(page, "og:image")
    if not hd and not og:
        raise ProfileError("Instagram profili okunamadı. " + LOGIN_HINT)
    title = meta(page, "og:title") or ""
    prof = Profile(platform, handle, re.sub(r"\s*\(@.*$", "", title))
    prof.avatar = Asset("avatar", [u for u in (hd, og) if u])
    if not hd and not cookies:
        prof.notes.append("Instagram oturum açmadan küçük boyut veriyor. Tam çözünürlük için: " + LOGIN_HINT)
    return prof


def _threads(handle: str, cookies: str) -> Profile:
    # A Threads profile is an Instagram account; its picture is the same image.
    prof = _instagram(handle, cookies, platform="threads")
    prof.notes.insert(0, "Threads profil fotoğrafı bağlı Instagram hesabından alındı. Threads'te kapak görseli yok.")
    return prof


def _reddit(handle: str, cookies: str) -> Profile:
    kind, name = handle.split("/", 1)
    path = f"r/{name}" if kind == "r" else f"user/{name}"
    r = session(cookies).get(f"https://www.reddit.com/{path}/about.json", timeout=15)
    if r.status_code in (401, 403, 429) or "json" not in r.headers.get("content-type", ""):
        raise ProfileError("Reddit oturum açmadan erişime izin vermiyor. " + LOGIN_HINT)
    if r.status_code == 404:
        raise ProfileError("Reddit hesabı ya da topluluğu bulunamadı.")
    data = r.json().get("data") or {}

    def clean(u):
        u = html.unescape(u or "")
        return u if u.startswith("http") else ""

    def candidates(*urls):
        out = []
        for u in filter(None, map(clean, urls)):
            out += [u.split("?")[0], u]  # without resize params first = original size
        return list(dict.fromkeys(out))

    if kind == "r":
        prof = Profile("reddit", f"r/{name}", data.get("title") or "")
        avatar = candidates(data.get("community_icon"), data.get("icon_img"))
        banner = candidates(data.get("banner_background_image"), data.get("mobile_banner_image"),
                            data.get("banner_img"))
    else:
        sub = data.get("subreddit") or {}
        prof = Profile("reddit", f"u/{name}", sub.get("title") or data.get("name") or "")
        avatar = candidates(data.get("icon_img"), data.get("snoovatar_img"))
        banner = candidates(sub.get("banner_img"))
    if avatar:
        prof.avatar = Asset("avatar", avatar)
    if banner:
        prof.banner = Asset("banner", banner)
    return prof


def _facebook(target: str, cookies: str) -> Profile:
    url = target if "://" in target else f"https://www.facebook.com/{target}"
    r = session(cookies).get(url, timeout=15)
    if r.status_code == 404:
        raise ProfileError("Facebook sayfası bulunamadı.")
    page = r.text
    avatar = meta(page, "og:image")
    if not avatar:
        raise ProfileError("Facebook profili okunamadı. " + LOGIN_HINT)
    q = parse_qs(urlparse(url).query)
    handle = q.get("id", [None])[0] or [s for s in urlparse(url).path.split("/") if s][0]
    prof = Profile("facebook", handle, meta(page, "og:title") or "")
    prof.avatar = Asset("avatar", [avatar])
    cover = None
    m = re.search(r'"cover_photo".{0,400}?"uri"\s*:\s*("(?:[^"\\]|\\.)*")', page)
    if m:
        cover = json_string('{"uri":' + m.group(1) + "}", "uri")
    if cover:
        prof.banner = Asset("banner", [cover])
    else:
        prof.notes.append("Facebook kapak görseli herkese açık sayfada yer almıyor. " + LOGIN_HINT)
    return prof


_FETCHERS = {"youtube": _youtube, "twitter": _twitter, "instagram": _instagram,
             "threads": _threads, "reddit": _reddit, "facebook": _facebook}


def _download(asset: Asset) -> None:
    sess = session()
    for url in asset.urls:
        try:
            r = sess.get(url, timeout=20)
        except requests.RequestException:
            continue
        if r.ok and r.headers.get("content-type", "").startswith("image/") and r.content:
            asset.data = r.content
            return


def fetch(text: str, platform: str, cookies_browser: str = "") -> Profile:
    key, target = parse_input(text, platform)
    try:
        prof = _FETCHERS[key](target, cookies_browser)
    except NetError as e:
        raise ProfileError(str(e)) from e
    except requests.RequestException as e:
        raise ProfileError(f"{PLATFORMS[key].name} bağlantı hatası: {e.__class__.__name__}") from e
    for asset in (prof.avatar, prof.banner):
        if asset:
            _download(asset)
    if prof.avatar and not prof.avatar.data:
        prof.avatar = None
    if prof.banner and not prof.banner.data:
        prof.banner = None
    if not prof.avatar and not prof.banner:
        raise ProfileError("Görsel bulunamadı.")
    return prof
