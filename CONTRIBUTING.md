# Contributing

Thanks for contributing.

## Rules

- Contributions are accepted under the project's [MIT License](LICENSE). Make sure the work is yours and you may share it under that license.
- **Not accepted:** code that circumvents DRM or copy protection, accesses paid content without permission, or collects user data / adds telemetry.
- No GPL-licensed Python libraries (e.g. `mutagen`) in the app; the distributed exe must stay MIT. Add the license of every new dependency to [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- `core/` stays independent of the UI; Qt is only used in `ui/`.
- Every user-visible string goes through `t("…")` with an English entry in `zconverter/i18n.py`. `python tools/i18n_keys.py` lists missing ones.

## Development

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

When reporting a bug, include your Windows version, the zConverter version, the platform of the link (don't share links with private information) and the error text shown in the app.

---

## Katkı rehberi (Türkçe)

- Katkılar projenin MIT Lisansı altında kabul edilir.
- Kabul edilmeyenler: DRM veya kopya korumasını aşan, ücretli içeriğe izinsiz erişen, kullanıcıdan veri toplayan veya telemetri ekleyen kodlar.
- Uygulamaya GPL lisanslı Python kütüphanesi eklenmez; her yeni bağımlılığın lisansı THIRD_PARTY_NOTICES.md'ye yazılır.
- Arayüzdeki her metin `t("…")` ile yazılır ve `zconverter/i18n.py`'ye İngilizcesi eklenir.
