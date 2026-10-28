import json
from dataclasses import asdict, dataclass, fields

from .paths import app_dir, default_output_dir, legacy_output_dir


@dataclass
class Settings:
    output_dir: str = str(default_output_dir())
    cookies_browser: str = ""  # "" = off, otherwise a yt-dlp browser name
    parallel: int = 2
    accepted_terms: int = 0
    language: str = ""  # "" = follow Windows

    @property
    def _file(self):
        return app_dir() / "settings.json"

    @classmethod
    def load(cls) -> "Settings":
        s = cls()
        try:
            data = json.loads(s._file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return s
        known = {f.name for f in fields(cls)}
        for key, value in data.items():
            if key in known:
                setattr(s, key, value)
        if s.output_dir == str(legacy_output_dir()):
            s.output_dir = str(default_output_dir())  # old default → plain Downloads
        if s.cookies_browser not in ("", "firefox"):
            s.cookies_browser = ""  # Chromium sessions can't be read any more; in-app sign-in replaced it
        return s

    def save(self) -> None:
        self._file.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
