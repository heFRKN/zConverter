"""Capture README screenshots: python tools/screenshot.py <out_dir>"""

import sys
from pathlib import Path

from PySide6.QtCore import QTimer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zconverter.i18n import set_language  # noqa: E402

set_language(sys.argv[2] if len(sys.argv) > 2 else "en")  # before any UI module builds its text

from zconverter.core import profiles  # noqa: E402
from zconverter.core.downloader import Request  # noqa: E402
from zconverter.core.settings import Settings  # noqa: E402
from zconverter.main import build_app  # noqa: E402
from zconverter.ui.jobs import Job  # noqa: E402
from zconverter.ui.window import MainWindow  # noqa: E402

DEMO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs")
    out.mkdir(parents=True, exist_ok=True)
    app = build_app(sys.argv)
    win = MainWindow(Settings())
    win.resize(1200, 900)
    win.show()

    page = win.download_page
    demo = [
        ("https://open.spotify.com/track/x", "audio", "mp3", "Rick Astley - Never Gonna Give You Up", "done"),
        ("https://x.com/NASA/status/1", "video", "mp4", "NASA - Liftoff", 0.62),
    ]
    for url, mode, fmt, title, state in demo:
        job = Job(Request(url, mode=mode, fmt=fmt))
        page._add_row(job)
        job.title.emit(title)
        if state == "done":
            job.state = "done"
            job.done.emit([f"C:/Downloads/{title}.{fmt}"])
        else:
            job.progress.emit(state, "18.4 MB / 29.6 MB  ·  6.2 MB/sn  ·  0:02 kaldı")
    page.set_url(DEMO_URL)

    def select_range():
        ed = page.editor
        ed.timeline.set_range(4.0, 12.5)
        ed._sync()
        ed._load_cut("start")
        ed._load_cut("end")
        QTimer.singleShot(6000, shot_download)

    def shot_download():
        win.grab().save(str(out / "download.png"))
        win.group.button(1).setChecked(True)
        win._go(1)
        prof_page = win.stack.currentWidget()
        prof_page.handle.setText("NASA")
        prof_page._fetched(profiles.fetch("NASA", "youtube"))
        prof_page.target.set_index(1)
        prof_page.ratio_seg.set_index(4)  # banner cropped to 3:1
        prof_page.target.set_index(0)
        prof_page.ratio_seg.set_index(2)  # circle profile picture
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

    QTimer.singleShot(7000, select_range)
    app.exec()


if __name__ == "__main__":
    main()
