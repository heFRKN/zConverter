"""Capture README screenshots: python tools/screenshot.py <out_dir>"""

import sys
from pathlib import Path

from PySide6.QtCore import QTimer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zconventer.core import profiles  # noqa: E402
from zconventer.core.downloader import Request  # noqa: E402
from zconventer.core.settings import Settings  # noqa: E402
from zconventer.main import build_app  # noqa: E402
from zconventer.ui.jobs import Job  # noqa: E402
from zconventer.ui.window import MainWindow  # noqa: E402


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs")
    out.mkdir(parents=True, exist_ok=True)
    app = build_app(sys.argv)
    win = MainWindow(Settings())
    win.show()

    page = win.download_page
    page.url.setText("https://www.youtube.com/watch?v=jNQXAC9IVRw")
    page.trim.setChecked(True)
    page.start_at.setText("0:05")
    page.end_at.setText("0:15")
    demo = [
        ("https://open.spotify.com/track/x", "audio", "mp3", "Rick Astley - Never Gonna Give You Up", 1.0, "done"),
        ("https://www.tiktok.com/@x/video/1", "video", "mp4", "Sunset timelapse", 0.62,
         "18.4 MB / 29.6 MB  ·  6.2 MB/sn  ·  0:02 kaldı"),
        ("https://soundcloud.com/x/y", "audio", "mp3", "Late night mix", None, "Sese dönüştürülüyor"),
    ]
    for url, mode, fmt, title, value, status in demo:
        job = Job(Request(url, mode=mode, fmt=fmt))
        page._add_row(job)
        job.title.emit(title)
        if status == "done":
            job.state = "done"
            job.done.emit([f"C:/Downloads/{title}.{fmt}"])
        elif value is None:
            job.status.emit(status)
        else:
            job.progress.emit(value, status)

    def shot_download():
        win.grab().save(str(out / "download.png"))
        win.group.button(1).setChecked(True)
        win._go(1)
        prof_page = win.stack.currentWidget()
        prof_page.handle.setText("NASA")
        prof_page._fetched(profiles.fetch("NASA", "youtube"))
        prof_page.opts["avatar"].crop = "circle"
        prof_page.opts["avatar"].fmt = "png"
        prof_page._select("avatar")
        prof_page._changed()
        QTimer.singleShot(2500, shot_profile)

    def shot_profile():
        win.grab().save(str(out / "profile.png"))
        win.group.button(2).setChecked(True)
        win._go(2)
        QTimer.singleShot(600, shot_rest)

    def shot_rest():
        win.grab().save(str(out / "settings.png"))
        win.group.button(3).setChecked(True)
        win._go(3)
        QTimer.singleShot(600, lambda: (win.grab().save(str(out / "legal.png")), app.quit()))

    QTimer.singleShot(1200, shot_download)
    app.exec()


if __name__ == "__main__":
    main()
