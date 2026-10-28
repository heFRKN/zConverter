import re
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yt_dlp
from yt_dlp.postprocessor.common import PostProcessor
from yt_dlp.utils import DownloadCancelled, DownloadError

from . import accounts, media, spotify
from .net import meta, session
from .paths import app_dir, ffmpeg_exe
from .platforms import detect, normalize_url

VIDEO_QUALITIES = [("best", "En iyi"), ("2160", "2160p"), ("1440", "1440p"), ("1080", "1080p"),
                   ("720", "720p"), ("480", "480p"), ("360", "360p")]
AUDIO_QUALITIES = [("320", "320 kbps"), ("256", "256 kbps"), ("192", "192 kbps"), ("128", "128 kbps")]
VIDEO_FORMATS = ["mp4", "mkv"]
AUDIO_FORMATS = ["mp3", "m4a", "opus", "flac", "wav"]
COVER_FORMATS = {"mp3", "m4a"}  # embeddable with ffmpeg alone

_PP_LABELS = {
    "Merger": "Görüntü ve ses birleştiriliyor",
    "ExtractAudio": "Sese dönüştürülüyor",
    "VideoRemuxer": "Kapsayıcı değiştiriliyor",
    "EmbedThumbnail": "Kapak ekleniyor",
    "Metadata": "Etiketler yazılıyor",
    "ZcFinish": "Kırpılıyor",
}


class Cancelled(Exception):
    pass


@dataclass
class Request:
    url: str
    mode: str = "video"          # video | audio
    quality: str = "best"
    fmt: str = "mp4"
    start: float | None = None
    end: float | None = None
    playlist: bool = False
    cover: bool = True
    output_dir: str = ""
    cookies_browser: str = ""

    @property
    def trimming(self) -> bool:
        return self.start is not None or self.end is not None


_LOGIN_WORDS = ("login", "log in", "sign in", "authentication", "cookies", "private", "confirm your age",
                "cannot parse data", "rate-limit", "not available without")


def _clean(err: BaseException | str) -> str:
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(err)).strip()
    msg = re.sub(r"^ERROR:\s*", "", msg)
    msg = re.sub(r"^\[([\w:]+)\]\s*[\w-]+:\s*", "", msg)
    return msg


def needs_login(err: BaseException | str) -> bool:
    low = _clean(err).lower()
    return any(k in low for k in _LOGIN_WORDS)


def humanize(err: BaseException | str) -> str:
    raw = str(err)
    msg = _clean(err)
    low = msg.lower()
    if "[tiktok]" in raw.lower() or "tiktok" in low and "unexpected response" in low:
        return "TikTok, tarayıcı dışından gelen istekleri engelliyor; bu sürümde TikTok indirmesi çalışmıyor."
    if "unsupported url" in low:
        return "Bu bağlantı desteklenmiyor."
    if "drm" in low:
        return "Bu içerik DRM korumalı, indirilemez."
    if "[reddit]" in raw.lower() and needs_login(err):
        return "Reddit videoları için Reddit hesabıyla giriş gerekiyor."
    if "[facebook]" in raw.lower() and needs_login(err):
        return "Facebook bu videoyu giriş yapmadan göstermiyor."
    if "[instagram]" in raw.lower() and needs_login(err):
        return "Instagram bu gönderiyi giriş yapmadan göstermiyor."
    if needs_login(err):
        return "Bu içerik için giriş gerekiyor."
    if "404" in low or "does not exist" in low:
        return "İçerik bulunamadı. Silinmiş ya da gizli olabilir."
    return msg.split("\n")[0][:220] or "Bilinmeyen hata."


class _Log:
    def __init__(self, owner: "Downloader"):
        self.owner = owner

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        self.owner.errors.append(msg)


class _TrackMeta(PostProcessor):
    """Give a YouTube match the Spotify title, artist, album and cover."""

    def __init__(self, track: spotify.Track):
        super().__init__(None)
        self.track = track

    def run(self, info):
        t = self.track
        info.update(title=f"{t.artist} - {t.title}", track=t.title, artist=t.artist,
                    artists=[t.artist], album=t.album or None)
        if t.cover:
            info["thumbnails"] = [{"url": t.cover, "id": "spotify"}]
        return [], info


class _Finish(PostProcessor):
    """Runs once the file is in its final place: trims it and records the path."""

    def __init__(self, owner: "Downloader"):
        super().__init__(None)
        self.owner = owner

    @classmethod
    def pp_key(cls):
        return "ZcFinish"

    def run(self, info):
        path = info.get("filepath")
        req = self.owner.req
        if path and req.trimming:
            duration = info.get("duration")
            if duration and req.start and req.start >= duration:
                raise DownloadError(f"Başlangıç ({media.format_time(req.start)}) içeriğin süresini aşıyor.")
            media.trim(path, req.start, req.end)
        # cover art goes in last so trimming can't drop it; ffmpeg only, no ffprobe needed
        thumbs = [t["filepath"] for t in info.get("thumbnails") or []
                  if t.get("filepath") and Path(t["filepath"]).exists()]
        if path and thumbs:
            try:
                media.embed_cover(path, thumbs[-1])
            finally:
                for t in thumbs:
                    Path(t).unlink(missing_ok=True)
        if path:
            self.owner.outputs.append(path)
        return [], info


class Downloader:
    def __init__(self, req: Request, emit: Callable[..., None]):
        """emit(kind, *args): ("title", str) ("progress", fraction|None, str) ("status", str)"""
        self.req = req
        self.emit = emit
        self.outputs: list[str] = []
        self.errors: list[str] = []
        self._cancel = threading.Event()
        self._prefix = ""
        self._fixed_title = False
        self._last_title = ""

    def cancel(self):
        self._cancel.set()

    # ------------------------------------------------------------ entry point

    def run(self) -> list[str]:
        Path(self.req.output_dir).mkdir(parents=True, exist_ok=True)
        url = normalize_url(self.req.url)
        platform = detect(url)
        try:
            if platform and platform.key == "spotify":
                self._run_spotify(url)
            else:
                if platform and platform.audio_only and self.req.mode == "video":
                    self.req.mode, self.req.fmt, self.req.quality = "audio", "mp3", "320"
                try:
                    self._download(url)
                except DownloadError as e:
                    if platform and platform.key == "threads" and "unsupported url" in str(e).lower():
                        self._download(self._threads_media(url))
                    else:
                        raise
        except Exception as e:
            if self._cancel.is_set():
                raise Cancelled() from e
            raise
        if self._cancel.is_set():
            raise Cancelled()
        if not self.outputs:
            raise DownloadError(self.errors[-1] if self.errors else "Hiçbir dosya indirilemedi.")
        return self.outputs

    # ------------------------------------------------------------ yt-dlp

    def _template(self, base: str) -> str:
        r = self.req
        if r.trimming:
            a = media.format_time(r.start or 0).replace(":", ".")
            b = media.format_time(r.end).replace(":", ".") if r.end is not None else "son"
            base += f" (kesit {a}-{b})"
        return base + ".%(ext)s"

    def _options(self, outtmpl: str) -> dict:
        r = self.req
        pps = []
        o = {
            "outtmpl": outtmpl,
            "paths": {"home": r.output_dir},
            "ffmpeg_location": ffmpeg_exe(),
            "cachedir": str(app_dir() / "cache"),
            "noplaylist": not r.playlist,
            "ignoreerrors": "only_download" if r.playlist else False,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "logger": _Log(self),
            "progress_hooks": [self._on_progress],
            "postprocessor_hooks": [self._on_pp],
            "js_runtimes": {name: {"path": None} for name in ("deno", "node", "bun")},
            "windowsfilenames": True,
            "concurrent_fragment_downloads": 4,
            "retries": 5,
            "fragment_retries": 5,
        }
        if r.cookies_browser:
            o["cookiesfrombrowser"] = (r.cookies_browser,)

        if r.mode == "video":
            sort = ["res"] if r.quality == "best" else [f"res:{r.quality}"]
            if r.fmt == "mp4":
                sort += ["vcodec:h264", "acodec:aac"]
            o.update(format="bv*+ba/b", format_sort=sort, merge_output_format=r.fmt)
            pps.append({"key": "FFmpegVideoRemuxer", "preferedformat": r.fmt})
        else:
            o["format"] = "ba/b"
            pps.append({"key": "FFmpegExtractAudio", "preferredcodec": r.fmt, "preferredquality": r.quality})
            if r.cover and r.fmt in COVER_FORMATS:
                o["writethumbnail"] = True  # embedded by _Finish
                pps.append({"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"})
            pps.append({"key": "FFmpegMetadata", "add_metadata": True})
        o["postprocessors"] = pps
        return o

    def _download(self, target: str, track: spotify.Track | None = None, outtmpl: str | None = None):
        if outtmpl is None:
            outtmpl = "%(title).90B"
            if self.req.playlist:
                outtmpl = "%(playlist_title,playlist_id|Liste).80B/" + outtmpl
        with yt_dlp.YoutubeDL(self._options(self._template(outtmpl))) as ydl:
            accounts.apply(ydl.cookiejar)
            if track:
                ydl.add_post_processor(_TrackMeta(track), when="pre_process")
            ydl.add_post_processor(_Finish(self), when="after_move")
            ydl.download([target])

    def _run_spotify(self, url: str):
        r = self.req
        r.mode = "audio"
        if r.fmt not in AUDIO_FORMATS:
            r.fmt, r.quality = "mp3", "320"
        self.emit("status", "Spotify bilgileri okunuyor")
        loaders = spotify.resolve(url, session())
        many = len(loaders) > 1
        self._fixed_title = True
        for i, load in enumerate(loaders, 1):
            if self._cancel.is_set():
                raise Cancelled()
            self._prefix = f"{i}/{len(loaders)} · " if many else ""
            track = load()
            if not track:
                continue
            self.emit("title", f"{self._prefix}{track.artist} - {track.title}")
            outtmpl = ("%(album|Spotify).80B/" if many else "") + "%(artist)s - %(track).120B"
            try:
                self._download(track.query, track=track, outtmpl=outtmpl)
            except DownloadError as e:
                if not many or self._cancel.is_set():
                    raise
                self.errors.append(f"{track.title}: {humanize(e)}")

    def _threads_media(self, url: str) -> str:
        self.emit("status", "Threads gönderisi okunuyor")
        page = session(self.req.cookies_browser).get(url, timeout=15).text
        media_url = meta(page, "og:video:secure_url") or meta(page, "og:video")
        if not media_url:
            raise DownloadError("Threads gönderisinde video bulunamadı. Gönderi gizli olabilir; "
                                "giriş yapıp tekrar dene.")
        return media_url

    # ------------------------------------------------------------ hooks

    def _on_progress(self, d):
        if self._cancel.is_set():
            raise DownloadCancelled()
        info = d.get("info_dict") or {}
        prefix = self._prefix
        if info.get("playlist_index") and info.get("n_entries"):
            prefix = f"{info['playlist_index']}/{info['n_entries']} · "
        title = info.get("title")
        if title and not self._fixed_title and prefix + title != self._last_title:
            self._last_title = prefix + title
            self.emit("title", self._last_title)

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            parts = [f"{media.format_size(done)} / {media.format_size(total)}"]
            if d.get("speed"):
                parts.append(f"{media.format_size(d['speed'])}/sn")
            if d.get("eta") is not None:
                parts.append(f"{media.format_time(d['eta'])} kaldı")
            self.emit("progress", done / total if total else None, "  ·  ".join(parts))
        elif d["status"] == "finished":
            self.emit("progress", 1.0, "İşleniyor")

    def _on_pp(self, d):
        if self._cancel.is_set():
            raise DownloadCancelled()
        if d.get("status") == "started":
            key = (d.get("postprocessor") or "").removeprefix("FFmpeg")
            label = _PP_LABELS.get(key)
            if key == "ZcFinish" and not self.req.trimming:
                label = None
            if label:
                self.emit("status", label)
