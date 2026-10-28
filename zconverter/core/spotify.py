"""Spotify streams are DRM protected and are never downloaded. We only read the public
track metadata (title, artist, album, cover) and look the song up on YouTube."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from ..i18n import t
from .net import meta

MAX_TRACKS = 200
_URL = re.compile(r"open\.spotify\.com/(?:intl-[\w-]+/)?(track|album|playlist)/([A-Za-z0-9]+)")


@dataclass
class Track:
    title: str
    artist: str
    album: str = ""
    cover: str = ""

    @property
    def query(self) -> str:
        return f"ytsearch1:{self.artist} - {self.title}"


def _track_from_page(page: str) -> Track | None:
    title = meta(page, "og:title")
    if not title:
        return None
    # "Artist · Album · Song · 1987"
    desc = [p.strip() for p in (meta(page, "og:description") or "").split("·")]
    artist = desc[0] if desc and desc[0] else ""
    album = desc[1] if len(desc) > 2 else ""
    return Track(title=title, artist=artist, album=album, cover=meta(page, "og:image") or "")


def resolve(url: str, sess) -> list[Callable[[], Track | None]]:
    """Return lazy loaders so a long playlist starts downloading right away."""
    if "spotify.link" in url:
        url = sess.get(url, timeout=15, allow_redirects=True).url
    m = _URL.search(url)
    if not m:
        raise ValueError(t("Spotify bağlantısı tanınmadı (track / album / playlist olmalı)."))
    kind, sid = m.groups()
    page = sess.get(f"https://open.spotify.com/{kind}/{sid}", timeout=15).text
    if kind == "track":
        track = _track_from_page(page)
        if not track:
            raise ValueError(t("Spotify parça bilgisi okunamadı."))
        return [lambda: track]

    song_urls = []
    for tag in re.findall(r'<meta\b[^>]*name="music:song"[^>]*>', page):
        m2 = re.search(r'content="([^"]+)"', tag)
        if m2 and m2.group(1) not in song_urls:
            song_urls.append(m2.group(1))
    if not song_urls:
        raise ValueError(t("Listedeki parçalar okunamadı. Liste gizli olabilir."))
    return [lambda u=u: _track_from_page(sess.get(u, timeout=15).text) for u in song_urls[:MAX_TRACKS]]
