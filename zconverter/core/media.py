import io
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from ..i18n import t
from .paths import ffmpeg_exe

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov"}
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ---------------------------------------------------------------- time helpers

def parse_time(text: str) -> float | None:
    """'90', '1:30', '01:02:03.5' -> seconds. Empty -> None."""
    text = text.strip().replace(",", ".")
    if not text:
        return None
    parts = text.split(":")
    if len(parts) > 3:
        raise ValueError(text)
    seconds = 0.0
    for part in parts:
        value = float(part)
        if value < 0:
            raise ValueError(text)
        seconds = seconds * 60 + value
    return seconds


def format_time(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def format_precise(seconds: float) -> str:
    """m:ss.d (h:mm:ss.d past an hour)."""
    tenths = int(round(max(0.0, seconds) * 10))
    s, d = divmod(tenths, 10)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}.{d}" if h else f"{m}:{s:02d}.{d}"


def format_size(n: float | None) -> str:
    if not n:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------- audio / video

_AUDIO_CODECS = {
    ".mp3": ["-c:a", "libmp3lame", "-q:a", "0"],
    ".m4a": ["-c:a", "aac", "-b:a", "256k"],
    ".opus": ["-c:a", "libopus", "-b:a", "160k"],
    ".flac": ["-c:a", "flac"],
    ".wav": ["-c:a", "pcm_s16le"],
}


def trim(path: str, start: float | None, end: float | None) -> None:
    """Cut a downloaded file in place. Frame accurate (re-encodes)."""
    src = Path(path)
    tmp = src.with_name(src.stem + ".zc-trim" + src.suffix)
    args = [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error"]
    if start:
        args += ["-ss", f"{start:.3f}"]
    args += ["-i", str(src)]
    if end is not None:
        args += ["-t", f"{end - (start or 0):.3f}"]
    ext = src.suffix.lower()
    if ext in VIDEO_EXTS:
        args += ["-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast",
                 "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"]
        if ext in (".mp4", ".mov"):
            args += ["-movflags", "+faststart"]
    else:
        # keep embedded cover art (an attached picture stream) as-is
        args += ["-map", "0:a:0", "-map", "0:v?", "-c:v", "copy", "-map_metadata", "0"]
        args += _AUDIO_CODECS.get(ext, [])
        if ext == ".mp3":
            args += ["-id3v2_version", "3"]
    args.append(str(tmp))
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=_NO_WINDOW)
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(t("Kırpma başarısız: ") + (proc.stderr.strip().splitlines() or ["ffmpeg hatası"])[-1])
    os.replace(tmp, src)


def embed_cover(path: str, image: str) -> None:
    """Attach a cover picture to an MP3 / M4A file in place."""
    src = Path(path)
    if src.suffix.lower() not in (".mp3", ".m4a"):
        return
    tmp = src.with_name(src.stem + ".zc-cover" + src.suffix)
    args = [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-i", image,
            "-map", "0:a", "-map", "1:0", "-c:a", "copy", "-c:v", "mjpeg", "-map_metadata", "0",
            "-disposition:v:0", "attached_pic"]
    if src.suffix.lower() == ".mp3":
        args += ["-id3v2_version", "3", "-metadata:s:v", "title=Album cover",
                 "-metadata:s:v", "comment=Cover (front)"]
    args.append(str(tmp))
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          creationflags=_NO_WINDOW)
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        return  # a missing cover is not worth failing the download
    os.replace(tmp, src)


# ---------------------------------------------------------------- images

@dataclass
class ImageOptions:
    width: int = 0          # 0 = keep
    height: int = 0
    keep_ratio: bool = True
    fmt: str = "original"   # original | png | jpg | webp
    quality: int = 92
    crop: str = "none"      # none | square | circle | wide
    box: tuple[int, int, int, int] | None = None  # free crop (left, top, right, bottom) in source pixels


def image_info(data: bytes) -> tuple[int, int, str]:
    with Image.open(io.BytesIO(data)) as im:
        return im.width, im.height, _ext(im.format)


def _ext(pil_format: str | None) -> str:
    fmt = (pil_format or "png").lower()
    return {"jpeg": "jpg", "mpo": "jpg"}.get(fmt, fmt)


def _center_crop(im: Image.Image, ratio: float) -> Image.Image:
    w, h = im.size
    if w / h > ratio:
        nw = round(h * ratio)
        left = (w - nw) // 2
        return im.crop((left, 0, left + nw, h))
    nh = round(w / ratio)
    top = (h - nh) // 2
    return im.crop((0, top, w, top + nh))


def target_size(src: tuple[int, int], opts: ImageOptions) -> tuple[int, int]:
    """Final pixel size after crop + resize, used for the live size readout."""
    w, h = src
    if opts.box:
        w, h = opts.box[2] - opts.box[0], opts.box[3] - opts.box[1]
    if opts.crop in ("square", "circle"):
        w = h = min(w, h)
    elif opts.crop == "wide":
        if w / h > 16 / 9:
            w = round(h * 16 / 9)
        else:
            h = round(w * 9 / 16)
    tw, th = opts.width, opts.height
    if not tw and not th:
        return w, h
    if opts.keep_ratio:
        if tw and th:
            scale = min(tw / w, th / h)
        else:
            scale = tw / w if tw else th / h
        return max(1, round(w * scale)), max(1, round(h * scale))
    return tw or w, th or h


def process_image(data: bytes, opts: ImageOptions) -> tuple[bytes, str]:
    im = Image.open(io.BytesIO(data))
    im.load()
    src_ext = _ext(im.format)
    full = (0, 0, im.width, im.height)
    box = opts.box if opts.box and tuple(opts.box) != full else None
    untouched = opts.crop == "none" and not box and target_size(im.size, opts) == im.size
    if untouched and opts.fmt in ("original", src_ext):
        return data, src_ext  # nothing to do: keep the original bytes, no re-encode loss
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.getbands() or im.mode == "P" else "RGB")
    if box:
        im = im.crop(box)

    if opts.crop in ("square", "circle"):
        im = _center_crop(im, 1.0)
    elif opts.crop == "wide":
        im = _center_crop(im, 16 / 9)

    size = target_size(im.size, ImageOptions(opts.width, opts.height, opts.keep_ratio))
    if opts.width and opts.height and not opts.keep_ratio:
        im = _center_crop(im, opts.width / opts.height)  # fill the exact size, never stretch
    if size != im.size:
        im = im.resize(size, Image.Resampling.LANCZOS)

    ext = src_ext if opts.fmt == "original" else opts.fmt
    if ext not in ("png", "jpg", "webp"):
        ext = "png"

    if opts.crop == "circle":
        # 4x supersampled mask for a smooth edge
        big = (im.width * 4, im.height * 4)
        mask = Image.new("L", big, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, big[0] - 1, big[1] - 1), fill=255)
        im = im.convert("RGBA")
        im.putalpha(mask.resize(im.size, Image.Resampling.LANCZOS))
        if ext == "jpg":
            ext = "png"  # jpg has no transparency

    out = io.BytesIO()
    if ext == "jpg":
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.getchannel("A"))
            im = bg
        im.save(out, "JPEG", quality=opts.quality, optimize=True, progressive=True)
    elif ext == "webp":
        im.save(out, "WEBP", quality=opts.quality, method=5)
    else:
        im.save(out, "PNG", optimize=True)
    return out.getvalue(), ext
