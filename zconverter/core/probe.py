"""Look at a link before downloading: title, duration, thumbnail, and the stream URLs
used to show frames, a waveform and short audio previews for trimming."""

import re
import struct
import subprocess
from dataclasses import dataclass, field

import yt_dlp

from . import accounts, spotify
from .net import session
from .paths import app_dir, ffmpeg_exe
from .platforms import detect, normalize_url

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class _Quiet:
    def __init__(self):
        self.errors = []

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        self.errors.append(msg)


@dataclass
class Stream:
    url: str
    headers: dict = field(default_factory=dict)


@dataclass
class MediaInfo:
    url: str
    platform: str
    title: str = ""
    uploader: str = ""
    duration: float | None = None
    thumbnail: str | None = None
    count: int = 1                  # > 1 for playlists / albums
    video: Stream | None = None     # low-res stream for frame previews
    audio: Stream | None = None     # stream for waveform / listening
    note: str = ""

    @property
    def trimmable(self) -> bool:
        return self.count == 1 and bool(self.duration) and self.duration > 1


def _ydl_opts(cookies: str, playlist: bool) -> dict:
    o = {
        "quiet": True, "no_warnings": True, "skip_download": True, "logger": _Quiet(),
        "noplaylist": not playlist, "extract_flat": "in_playlist",
        "cachedir": str(app_dir() / "cache"),
        "js_runtimes": {name: {"path": None} for name in ("deno", "node", "bun")},
    }
    if cookies:
        o["cookiesfrombrowser"] = (cookies,)
    return o


def _pick(formats: list[dict], video: bool) -> Stream | None:
    def ok(f):
        if not f.get("url") or f.get("protocol") not in ("https", "http", "m3u8", "m3u8_native"):
            return False
        if f.get("format_note") == "watermarked":
            return False
        # a missing codec means "unknown" (e.g. Facebook), not "absent"
        if video:
            return f.get("vcodec") != "none"
        return f.get("acodec") != "none"

    cands = [f for f in formats if ok(f)]
    if not cands:
        return None
    if video:
        # small but not tiny; plain https before HLS (faster seeking)
        cands.sort(key=lambda f: (f.get("protocol", "").startswith("m3u8"),
                                  abs((f.get("height") or 360) - 360)))
    else:
        audio_only = [f for f in cands if f.get("vcodec") in (None, "none")]
        cands = audio_only or cands
        cands.sort(key=lambda f: (f.get("protocol", "").startswith("m3u8"), -(f.get("abr") or 0)))
    f = cands[0]
    return Stream(f["url"], dict(f.get("http_headers") or {}))


def _fill_streams(info: MediaInfo, raw: dict, jar=None):
    formats = raw.get("formats") or ([raw] if raw.get("url") else [])
    info.video = _pick(formats, video=True)
    info.audio = _pick(formats, video=False)
    # some CDNs (e.g. TikTok) only serve the stream together with the cookies set while extracting
    for stream in (info.video, info.audio):
        if stream and jar is not None and (cookie := jar.get_cookie_header(stream.url)):
            stream.headers["Cookie"] = cookie
    if not info.duration and (info.video or info.audio):
        info.duration = _stream_duration(info.video or info.audio)


def _stream_duration(stream: Stream) -> float | None:
    try:
        proc = subprocess.run([ffmpeg_exe(), "-hide_banner", *_input_args(stream), "-i", stream.url],
                              capture_output=True, timeout=30, creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return None
    m = re.search(rb"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        return None
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def probe(url: str, cookies: str = "", playlist: bool = False) -> MediaInfo:
    url = normalize_url(url)
    p = detect(url)
    key = p.key if p else "?"
    if key == "spotify":
        return _probe_spotify(url, cookies)
    opts = _ydl_opts(cookies, playlist)
    with yt_dlp.YoutubeDL(opts) as ydl:
        accounts.apply(ydl.cookiejar)
        raw = ydl.extract_info(url, download=False)
    info = MediaInfo(url, key)
    if raw.get("_type") == "playlist" or raw.get("entries") is not None:
        entries = list(raw.get("entries") or [])
        info.title = raw.get("title") or "Liste"
        info.uploader = raw.get("uploader") or raw.get("channel") or ""
        info.count = len(entries)
        info.thumbnail = _thumb(raw) or (entries and _thumb(entries[0])) or None
        return info
    info.title = raw.get("title") or ""
    info.uploader = raw.get("uploader") or raw.get("channel") or raw.get("creator") or ""
    info.duration = raw.get("duration")
    info.thumbnail = _thumb(raw)
    _fill_streams(info, raw, ydl.cookiejar)
    return info


def _thumb(raw: dict) -> str | None:
    if raw.get("thumbnail"):
        return raw["thumbnail"]
    thumbs = [t for t in raw.get("thumbnails") or [] if t.get("url")]
    return thumbs[-1]["url"] if thumbs else None


def _probe_spotify(url: str, cookies: str) -> MediaInfo:
    loaders = spotify.resolve(url, session())
    info = MediaInfo(url, "spotify")
    if len(loaders) > 1:
        info.count = len(loaders)
        info.title = f"{len(loaders)} parça"
        info.note = "Her parça YouTube'da eşleştirilip ayrı ayrı indirilecek."
        return info
    track = loaders[0]()
    with yt_dlp.YoutubeDL(_ydl_opts(cookies, False) | {"extract_flat": False}) as ydl:
        accounts.apply(ydl.cookiejar)
        raw = ydl.extract_info(track.query, download=False)
    entry = (raw.get("entries") or [raw])[0]
    info.title = f"{track.artist} - {track.title}"
    info.uploader = track.album or track.artist
    info.thumbnail = track.cover or _thumb(entry)
    info.duration = entry.get("duration")
    info.note = f"YouTube eşleşmesi: {entry.get('title', '')}"
    _fill_streams(info, entry, ydl.cookiejar)
    return info


# ---------------------------------------------------------------- ffmpeg helpers

def _input_args(stream: Stream) -> list[str]:
    args = []
    headers = dict(stream.headers)
    ua = headers.pop("User-Agent", None)
    if ua:
        args += ["-user_agent", ua]
    if headers:
        args += ["-headers", "".join(f"{k}: {v}\r\n" for k, v in headers.items())]
    return args


def _run(args: list[str], timeout: float) -> bytes:
    proc = subprocess.run([ffmpeg_exe(), "-hide_banner", "-loglevel", "error", *args],
                          capture_output=True, timeout=timeout, creationflags=_NO_WINDOW)
    if proc.returncode != 0 or not proc.stdout:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip()[-200:] or "ffmpeg hatası")
    return proc.stdout


def frame(stream: Stream, t: float, width: int = 480) -> bytes:
    """JPEG of the frame at second t."""
    return _run(["-ss", f"{max(0.0, t):.2f}", *_input_args(stream), "-i", stream.url,
                 "-frames:v", "1", "-vf", f"scale={width}:-2", "-f", "image2pipe", "-c:v", "mjpeg",
                 "-q:v", "4", "pipe:1"], timeout=30)


def waveform(stream: Stream, points: int = 400) -> list[float]:
    """Peak levels (0..1) across the whole track. Reads the audio at a very low rate."""
    rate = 400
    raw = _run([*_input_args(stream), "-i", stream.url, "-vn", "-ac", "1", "-ar", str(rate),
                "-f", "s16le", "pipe:1"], timeout=180)
    samples = struct.unpack(f"<{len(raw) // 2}h", raw[: len(raw) // 2 * 2])
    if not samples:
        return []
    step = max(1, len(samples) // points)
    peaks = [max(abs(s) for s in samples[i:i + step]) for i in range(0, len(samples), step)]
    top = max(peaks) or 1
    return [p / top for p in peaks[:points]]


def clip(stream: Stream, start: float, length: float, path: str) -> str:
    """Write a short WAV preview of [start, start + length] to path (a real file, so the
    header carries the length and Windows can play it)."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, start):.2f}",
         *_input_args(stream), "-i", stream.url, "-t", f"{length:.2f}", "-vn", "-ac", "2", "-ar", "44100",
         path],
        capture_output=True, timeout=60, creationflags=_NO_WINDOW)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip()[-200:] or "ffmpeg hatası")
    return path
