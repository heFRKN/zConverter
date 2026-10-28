<p align="center">
  <img src="assets/icon.png" width="88" alt="zConverter">
</p>

<h1 align="center">zConverter</h1>

<p align="center">
  Download video, music and profile images in one place. Trim, resize and convert while you download.<br>
  A simple Windows app. No accounts, no ads, no telemetry.
</p>

<p align="center">
  <a href="LICENSE">MIT License</a> ·
  <a href="TERMS.md">Terms of use</a> ·
  <a href="PRIVACY.md">Privacy</a> ·
  <a href="#türkçe">Türkçe</a>
</p>

<p align="center"><img src="docs/download.png" width="860" alt="Download screen"></p>

## Features

- **Video and audio downloads** from YouTube, Spotify, SoundCloud, Instagram, TikTok, X, Reddit, Threads and Facebook
- **Formats:** MP4 / MKV video (360p up to 4K), MP3 / M4A / OPUS / FLAC / WAV audio (128 to 320 kbps)
- **Visual trimming:** paste a link and a preview appears; see the frames at both cut points, drag the handles on a filmstrip (or a waveform for audio) and listen to each cut. Cuts are frame accurate
- **Cover and tags:** title, artist, album and cover art are added to MP3 / M4A files
- **Playlists:** download a whole list in one go
- **Profile images:** profile pictures and banners from YouTube, Instagram, X, Threads, Reddit and Facebook at the highest resolution available
- **Image editing:** presets (profile, YouTube banner, X header, Facebook cover, Instagram post, story…), exact pixel sizes (cropped to fill, never stretched), square / circle / 16:9 crop, PNG / JPG / WEBP export with quality control, live preview
- **Sign-in when needed:** sign in on the platform's own page inside the app; the session is stored encrypted with Windows DPAPI and your password never reaches the app
- **Turkish and English interface**, following your Windows language by default
- **Queue:** 1 to 4 parallel downloads, cancel and retry; drag a link onto the window or paste with one click

<p align="center"><img src="docs/profile.png" width="860" alt="Profile images screen"></p>

## Platform support

| Platform | Video | Audio | Profile picture | Banner |
|---|:---:|:---:|:---:|:---:|
| YouTube | ✓ | ✓ | ✓ | ✓ |
| Spotify | – | ✓ ¹ | – | – |
| SoundCloud | – | ✓ | – | – |
| Instagram | ✓ | ✓ | ✓ ² | not on platform |
| TikTok | ✓ ³ | ✓ ³ | – | – |
| X (Twitter) | ✓ | ✓ | ✓ | ✓ |
| Reddit | ✓ ⁴ | ✓ ⁴ | ✓ ⁴ | ✓ ⁴ |
| Threads | ✓ ⁵ | ✓ ⁵ | ✓ | not on platform |
| Facebook | ✓ | ✓ | ✓ | ✓ ⁴ |

1. Spotify is DRM protected; no audio is ever downloaded from Spotify. The public track details are read and the same song is found on YouTube. Tags and album art match Spotify.
2. Without signing in Instagram only gives a 100 px picture; sign in for full size.
3. Downloads without watermark. TikTok rejects non-browser connections, so yt-dlp's browser compatibility mode is used. This may conflict with TikTok's terms of service; use it at your own risk.
4. The platform requires signing in; the app shows a **Sign in** button when needed.
5. Limited: works for public posts.

## Install

1. Download `zConverter-x.y.z-windows-x64.zip` from [Releases](https://github.com/heFRKN/zConverter/releases).
2. Extract it and run `zConverter.exe`.
3. If Windows SmartScreen warns about an unrecognised app: **More info → Run anyway**. The app is not code-signed; all of its source code is in this repository.

**Optional:** a JavaScript runtime gives YouTube its full list of qualities:

```powershell
winget install DenoLand.Deno
```

FFmpeg is included; nothing else to install.

## Run from source / build

Python 3.12+ is required.

```powershell
git clone https://github.com/heFRKN/zConverter.git
cd zConverter
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

Build the exe and the release zip:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Output: `dist\zConverter\zConverter.exe` and `dist\zConverter-x.y.z-windows-x64.zip`. `zConverter.exe --selftest` checks that the bundled parts work and writes `%APPDATA%\zConverter\selftest.txt`.

## Project layout

```
zconverter/
  core/        download engine, previews, Spotify matching, profile images, media processing (no UI)
  ui/          PySide6 interface: theme, widgets, pages, trim editor, sign-in window
  i18n.py      interface language (Turkish source strings, English table)
tools/         icon renderer, screenshots, missing-translation check
```

Adding a string to the UI: wrap it in `t("…")` and add the English text to `zconverter/i18n.py`; `python tools/i18n_keys.py` lists anything missing.

## Legal

zConverter is only for content **you own or are allowed to save for personal use**. You are responsible for what you download and how you use it; copyright law (e.g. DMCA, Turkish FSEK), data protection law (GDPR, KVKK) and each platform's terms apply. The app does not circumvent DRM, hosts no content and collects no data.

- [Terms of use](TERMS.md)
- [Privacy policy](PRIVACY.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

YouTube, Spotify, SoundCloud, Instagram, TikTok, X, Reddit, Threads and Facebook are trademarks of their respective owners. zConverter is not affiliated with, endorsed or sponsored by any of them.

## License

[MIT](LICENSE) © 2026 heFRKN. Third-party components in binary releases (FFmpeg: GPL-3.0, Qt: LGPL-3.0 and others) keep their own licenses.

---

<a id="türkçe"></a>

## Türkçe

**zConverter**; YouTube, Spotify, SoundCloud, Instagram, TikTok, X, Reddit, Threads ve Facebook'tan video ve müzik indirmeni, YouTube, Instagram, X, Threads, Reddit ve Facebook hesaplarının profil fotoğrafı ve kapak görsellerini almanı sağlayan sade bir Windows uygulaması. İndirmeden önce ses ve videoyu görerek kırpabilir, görselleri boyutlandırıp dönüştürebilirsin.

- MP4 / MKV video (4K'ya kadar), etiket ve kapaklı MP3 / M4A / OPUS / FLAC / WAV ses
- Görsel kırpma: kesim noktalarının kareleri, zaman şeridi ya da dalga formu, kesimleri dinleme
- Profil görselleri: hazır boyutlar, tam piksel boyut (esnetmeden kırparak), kare / daire / 16:9, PNG / JPG / WEBP
- Giriş isteyen içerikler için uygulama içi giriş; oturum Windows şifrelemesiyle saklanır, şifren uygulamaya geçmez
- Türkçe ve İngilizce arayüz (Ayarlar → Dil)
- Spotify'dan hiçbir zaman ses indirilmez; parça bilgisi okunur ve şarkı YouTube'da bulunur
- TikTok filigransız iner; TikTok tarayıcı dışı bağlantıları kabul etmediği için yt-dlp'nin tarayıcı uyumluluk modu kullanılır. Bu TikTok'un koşullarına aykırı olabilir, risk kullanıcıya aittir
- Hesap yok, telemetri yok, sunucu yok

**Kurulum:** [Releases](https://github.com/heFRKN/zConverter/releases) sayfasından zip'i indir, çıkar, `zConverter.exe`'yi çalıştır. SmartScreen uyarısında **Ek bilgi → Yine de çalıştır**.

**Yasal:** Yalnızca hakkın olan ya da kişisel kullanımına izin verilen içerikler için. İndirdiğin içerikten ve kullanımından sen sorumlusun. Ayrıntılar: [Kullanım koşulları](TERMS.md#kullanım-koşulları-ve-yasal-uyarı) · [Gizlilik ve KVKK](PRIVACY.md#gizlilik-politikası-ve-kvkk-aydınlatma-metni) · [Lisanslar](THIRD_PARTY_NOTICES.md)

**Lisans:** [MIT](LICENSE) © 2026 heFRKN.
