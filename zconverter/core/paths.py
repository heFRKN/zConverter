import os
import shutil
import sys
from functools import lru_cache
from pathlib import Path

from .. import APP_NAME


def app_dir() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    return Path.home() / "Downloads" / APP_NAME


def resource(rel: str) -> Path:
    """Path to a bundled file, both from source and from a PyInstaller build."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / rel


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


@lru_cache(maxsize=1)
def js_runtime() -> str | None:
    """yt-dlp needs a JS runtime for full YouTube support. Report which one is installed."""
    for name in ("deno", "node", "bun"):
        if shutil.which(name):
            return name
    return None
