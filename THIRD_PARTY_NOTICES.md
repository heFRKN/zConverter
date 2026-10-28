# Üçüncü Taraf Bileşenler / Third-Party Notices

zConverter'ın kendi kaynak kodu MIT Lisansı ile dağıtılır. Derlenmiş sürümler (exe) aşağıdaki bileşenleri içerir; her biri kendi lisansına tabidir.

zConverter's own source code is MIT licensed. Binary releases bundle the components below, each under its own license.

| Bileşen | Lisans | Kaynak |
|---|---|---|
| FFmpeg 7.1 (gyan.dev "essentials" build) | GPL-3.0-or-later | [ffmpeg.org](https://ffmpeg.org/download.html) · [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) |
| Qt 6 / PySide6 / Shiboken6 | LGPL-3.0 | [code.qt.io](https://code.qt.io/cgit/pyside/pyside-setup.git/) |
| yt-dlp | Unlicense | [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| yt-dlp-ejs | Unlicense, MIT, ISC | [github.com/yt-dlp/ejs](https://github.com/yt-dlp/ejs) |
| imageio-ffmpeg | BSD-2-Clause | [github.com/imageio/imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) |
| Pillow | MIT-CMU (HPND) | [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| Requests | Apache-2.0 | [github.com/psf/requests](https://github.com/psf/requests) |
| urllib3 | MIT | [github.com/urllib3/urllib3](https://github.com/urllib3/urllib3) |
| certifi | MPL-2.0 | [github.com/certifi/python-certifi](https://github.com/certifi/python-certifi) |
| idna | BSD-3-Clause | [github.com/kjd/idna](https://github.com/kjd/idna) |
| charset-normalizer | MIT | [github.com/jawah/charset_normalizer](https://github.com/jawah/charset_normalizer) |
| Python 3.12 | PSF License | [python.org](https://www.python.org/) |
| PyInstaller bootloader | GPL-2.0 with bootloader exception | [pyinstaller.org](https://pyinstaller.org/) |

## FFmpeg (GPL)

FFmpeg, uygulamanın içinde **ayrı bir program** (`ffmpeg-*.exe`) olarak bulunur ve yalnızca komut satırı üzerinden çağrılır; zConverter koduyla birleştirilmez. Kullanılan derleme GPL bileşenleri (ör. libx264) içerdiği için GPL-3.0 kapsamındadır. Lisans metni `licenses/GPL-3.0.txt` dosyasındadır. Kaynak kodu ffmpeg.org'dan, derleme betikleri ve kaynak arşivi gyan.dev'den edinilebilir; istenirse bu sürüme ait kaynak kodu proje sahibince de sağlanır.

FFmpeg is shipped as a **separate executable** and only invoked from the command line; it is not linked with zConverter. This build includes GPL components and is therefore licensed under GPL-3.0 (see `licenses/GPL-3.0.txt`). Source code is available from ffmpeg.org and gyan.dev, and on request from the project owner.

## Qt / PySide6 (LGPL)

Qt ve PySide6 kütüphaneleri, uygulama klasöründe ayrı DLL / PYD dosyaları olarak bulunur. LGPL-3.0 gereği bunları kendi derlediğin uyumlu sürümlerle değiştirebilirsin. Lisans metni `licenses/LGPL-3.0.txt` (ve onun atıf yaptığı `licenses/GPL-3.0.txt`) dosyasındadır.

Qt and PySide6 are shipped as separate, replaceable shared libraries in the application folder, as required by the LGPL-3.0 (see `licenses/LGPL-3.0.txt`).

## Ticari markalar / Trademarks

Platform adları sahiplerinin ticari markalarıdır. zConverter hiçbir platformun logosunu içermez ve hiçbiriyle bağlantılı değildir.

Platform names are trademarks of their respective owners. zConverter contains none of their logos and is not affiliated with any of them.
