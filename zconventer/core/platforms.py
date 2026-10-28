from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Platform:
    key: str
    name: str
    badge: str
    domains: tuple[str, ...]
    audio_only: bool = False


PLATFORMS = {
    p.key: p
    for p in (
        Platform("youtube", "YouTube", "YT", ("youtube.com", "youtu.be")),
        Platform("spotify", "Spotify", "SP", ("spotify.com", "spotify.link"), audio_only=True),
        Platform("soundcloud", "SoundCloud", "SC", ("soundcloud.com",), audio_only=True),
        Platform("instagram", "Instagram", "IG", ("instagram.com", "instagr.am")),
        Platform("tiktok", "TikTok", "TT", ("tiktok.com",)),
        Platform("twitter", "X", "X", ("twitter.com", "x.com")),
        Platform("reddit", "Reddit", "RD", ("reddit.com", "redd.it")),
        Platform("threads", "Threads", "TH", ("threads.net", "threads.com")),
        Platform("facebook", "Facebook", "FB", ("facebook.com", "fb.watch", "fb.com")),
    )
}

PROFILE_PLATFORMS = ("youtube", "instagram", "twitter", "threads", "reddit", "facebook")


def normalize_url(text: str) -> str:
    text = text.strip()
    if text and "://" not in text and "." in text.split("/")[0]:
        text = "https://" + text
    return text


def detect(url: str) -> Platform | None:
    try:
        host = (urlparse(normalize_url(url)).hostname or "").lower()
    except ValueError:
        return None
    for p in PLATFORMS.values():
        if any(host == d or host.endswith("." + d) for d in p.domains):
            return p
    return None
