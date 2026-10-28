# Privacy Policy

Last updated: 28 October 2026 · [Türkçe (KVKK Aydınlatma Metni)](#gizlilik-politikası-ve-kvkk-aydınlatma-metni)

## In short

- No accounts, no servers, no analytics or telemetry, no ads.
- The author **never receives, collects or stores** any personal data about you.
- Everything stays on this computer.

## 1. Data controller

The app runs entirely on your device and sends nothing to the author, so the author is not a data controller or processor for anything processed with it (Turkish KVKK No. 6698, Art. 3; GDPR). If you use the app to save other people's personal data (for example a profile picture), you are responsible for that processing. Purely personal or household activity is outside the scope of KVKK (Art. 28/1-a) and GDPR (Art. 2(2)(c)); sharing or publishing such data may not be.

## 2. What is stored on your computer

| Data | Location | Purpose |
|---|---|---|
| Settings: save folder, language, Firefox session preference, parallel downloads, accepted terms version | `%APPDATA%\zConverter\settings.json` | Remember your preferences |
| Sessions of platforms you signed in to (session cookies, encrypted with Windows DPAPI) | `%APPDATA%\zConverter\sessions` | Download content that requires signing in |
| yt-dlp cache (no personal data) | `%APPDATA%\zConverter\cache` | Faster downloads |
| Files you download | The folder you choose | Your request |

No history, search log or other logs are kept. Delete `%APPDATA%\zConverter` to remove everything.

## 3. Network connections

Connections are made only for actions you start, directly from your device to: the platform you chose (YouTube, Spotify, SoundCloud, Instagram, TikTok, X, Reddit, Threads, Facebook) and its content delivery networks; YouTube search, to match Spotify tracks; and the open-source [FxTwitter](https://github.com/FxEmbed/FxEmbed) API (`api.fxtwitter.com`) for X profile images, which only receives the username you entered. These services process data such as your IP address under their own policies. The app identifies itself as `zConverter/<version>`; only for TikTok links yt-dlp's browser compatibility mode is used.

## 4. Sessions

There is no session until you sign in.

- You sign in on the platform's **own page** inside the app; your password never reaches the app and is never stored.
- Only the resulting session cookies are kept, encrypted with Windows DPAPI so that only your Windows account on this computer can read them.
- Sessions are **never sent** to the author or third parties, only to the platform they belong to, as a browser would.
- If your default browser is Firefox and you turn the option on, its open session is read in memory only and never written to disk.
- Sessions of Chrome, Edge, Brave and similar browsers are never read.
- Remove a session at any time with Settings → Accounts → Sign out.

## 5. Your rights

As the author holds no data about you, requests under KVKK Art. 11 or the GDPR should go to the platforms that process your data. Questions: [GitHub Issues](https://github.com/heFRKN/zConverter/issues).

## 6. Changes

This policy may change; the current version is always in the repository and in the app's Legal section.

<!-- tr -->

---

# Gizlilik Politikası ve KVKK Aydınlatma Metni

Son güncelleme: 28 Ekim 2026 · [English](#privacy-policy)

## Kısaca

- Hesap yok, sunucu yok, analiz/telemetri yok, reklam yok.
- Geliştirici senin hakkında **hiçbir kişisel veriye erişmez, toplamaz, saklamaz.**
- Her şey bu bilgisayarda kalır.

## 1. Veri sorumlusu

6698 sayılı Kişisel Verilerin Korunması Kanunu'nun (KVKK) 3. maddesine göre veri sorumlusu, kişisel verilerin işlenme amaçlarını ve vasıtalarını belirleyen kişidir. zConverter tamamen senin cihazında çalışır ve geliştiriciye hiçbir veri aktarmaz. Bu nedenle geliştirici, Uygulama aracılığıyla işlenen verilerin veri sorumlusu değildir.

Uygulamayı kullanarak başkalarına ait kişisel verileri (ör. profil fotoğrafı) kaydeden kullanıcı, bu işlemden kendisi sorumludur. KVKK m. 28/1-(a) uyarınca, üçüncü kişilere verilmemek ve veri güvenliğine uyulmak kaydıyla gerçek kişilerin tamamen kendileriyle veya aynı konutta yaşayan aile fertleriyle ilgili faaliyetleri kapsamında işlenen veriler Kanun kapsamı dışındadır. Bu verileri paylaşmak veya yaymak bu istisnanın dışında kalabilir.

## 2. Bilgisayarında saklananlar

| Veri | Konum | Amaç |
|---|---|---|
| Ayarlar: kayıt klasörü, dil, Firefox oturumu tercihi, eşzamanlı indirme sayısı, kabul edilen koşul sürümü | `%APPDATA%\zConverter\settings.json` | Tercihlerini hatırlamak |
| Hesap oturumları (yalnızca giriş yaptığın platformlar için oturum çerezleri, DPAPI ile şifreli) | `%APPDATA%\zConverter\sessions` | Giriş isteyen içerikleri indirebilmek |
| yt-dlp önbelleği (kişisel veri içermez, platform çözümleme verileri) | `%APPDATA%\zConverter\cache` | Daha hızlı indirme |
| İndirdiğin dosyalar | Seçtiğin klasör | Senin isteğin |

Uygulama geçmiş, arama kaydı veya log **tutmaz**. Her şeyi silmek için `%APPDATA%\zConverter` klasörünü silmen yeterli.

## 3. Ağ bağlantıları

Uygulama yalnızca senin başlattığın işlemler için ağ bağlantısı kurar. Bağlantılar doğrudan cihazından şu hizmetlere gider:

- İndirmek ya da görüntülemek istediğin platform (YouTube, Spotify, SoundCloud, Instagram, TikTok, X, Reddit, Threads, Facebook) ve bunların içerik dağıtım ağları,
- Spotify parçaları için YouTube araması,
- X profil görselleri için açık kaynaklı [FxTwitter](https://github.com/FxEmbed/FxEmbed) API'si (`api.fxtwitter.com`). Yalnızca girdiğin kullanıcı adı gönderilir.

Bu hizmetler IP adresin gibi verileri kendi gizlilik politikalarına göre işler; geliştiricinin bu işleme üzerinde kontrolü yoktur. Uygulama kendini `zConverter/<sürüm>` kullanıcı aracısıyla tanıtır; yalnızca TikTok bağlantılarında yt-dlp'nin tarayıcı uyumluluk modu kullanılır.

## 4. Hesap oturumları

Giriş varsayılan olarak **yoktur**; yalnızca sen bir platforma giriş yaparsan oluşur.

- Giriş, Uygulama içinde açılan platformun **kendi sayfasında** yapılır; şifren Uygulamaya geçmez ve saklanmaz.
- Girişten sonra oluşan oturum çerezleri, Windows'un kullanıcıya özel şifrelemesiyle (DPAPI) yalnızca bu bilgisayarda saklanır; başka bir Windows kullanıcısı veya başka bir bilgisayar bunları okuyamaz.
- Oturumlar geliştiriciye veya üçüncü bir tarafa **gönderilmez**; yalnızca ait oldukları platforma, tarayıcının da göndereceği şekilde iletilir.
- Varsayılan tarayıcın Firefox ise ve sen açarsan, Firefox'taki açık oturum istek anında bellekte okunur ve diske yazılmaz.
- Uygulama, Chrome / Edge / Brave gibi tarayıcıların koruma altındaki oturumlarını okumaz.
- Ayarlar → Hesaplar'dan "Çıkış yap" ile oturumu istediğin an silebilirsin.

## 5. Hakların

KVKK m. 11 kapsamındaki hakların (bilgi talep etme, silme, düzeltme vb.) için: geliştirici senin hakkında veri tutmadığından bu hakların muhatabı, verilerini işleyen ilgili platformlardır. Sorular için [GitHub Issues](https://github.com/heFRKN/zConverter/issues).

## 6. GDPR (AB)

Aynı ilkeler geçerlidir. Geliştirici GDPR anlamında veri sorumlusu (controller) veya veri işleyen (processor) değildir. Tamamen kişisel veya ev içi faaliyetler GDPR m. 2(2)(c) uyarınca kapsam dışındadır.

## 7. Değişiklikler

Bu metin güncellenebilir; güncel sürüm her zaman depoda ve Uygulamanın "Yasal" bölümünde yer alır.
