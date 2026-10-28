# Katkı rehberi / Contributing

Katkıların için teşekkürler. / Thanks for contributing.

## Kurallar

- Gönderdiğin her katkı, projenin [MIT Lisansı](LICENSE) altında yayınlanmayı kabul ettiğin anlamına gelir. Katkının sana ait olduğundan ve bu lisansla paylaşma hakkın olduğundan emin ol.
- **Kabul edilmeyecek değişiklikler:** DRM veya kopya korumasını aşan, ücretli içeriğe izinsiz erişim sağlayan, kullanıcıdan veri toplayan veya telemetri ekleyen kodlar.
- GPL lisanslı Python kütüphaneleri (ör. `mutagen`) uygulama koduna eklenmez; dağıtılan exe MIT kalmalıdır. Yeni bir bağımlılık eklerken lisansını [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) dosyasına yaz.
- `core/` arayüzden bağımsız kalmalı; Qt yalnızca `ui/` içinde kullanılır.

## Geliştirme

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

Hata bildirirken: Windows sürümü, zConverter sürümü, bağlantının platformu (gizli bilgi içeren bağlantıları paylaşma) ve ekranda görünen hata metni.

## Rules (English)

- Contributions are accepted under the project's MIT License.
- Not accepted: code that circumvents DRM or copy protection, accesses paid content without permission, or collects user data / adds telemetry.
- No GPL-licensed Python libraries in the app; document every new dependency's license in THIRD_PARTY_NOTICES.md.
