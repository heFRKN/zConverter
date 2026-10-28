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


def downloads_dir() -> Path:
    """The user's Downloads folder, wherever Windows has it (it can be moved to another drive)."""
    if sys.platform == "win32":
        import ctypes
        import uuid
        from ctypes import wintypes

        guid = uuid.UUID("374DE290-123F-4565-9164-39C4925E467B")  # FOLDERID_Downloads
        buf = (ctypes.c_byte * 16).from_buffer_copy(guid.bytes_le)
        path = wintypes.LPWSTR()
        try:
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(buf), 0, None, ctypes.byref(path)) == 0:
                try:
                    return Path(path.value)
                finally:
                    ctypes.windll.ole32.CoTaskMemFree(path)
        except (AttributeError, OSError):
            pass
    return Path.home() / "Downloads"


def default_output_dir() -> Path:
    return downloads_dir()


def legacy_output_dir() -> Path:
    """Default of versions before 1.3 (a zConverter folder inside Downloads)."""
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
