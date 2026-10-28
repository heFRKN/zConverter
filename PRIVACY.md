# Gizlilik Politikası ve KVKK Aydınlatma Metni

Son güncelleme: 28 Ekim 2026

## Kısaca

- Hesap yok, sunucu yok, analiz/telemetri yok, reklam yok.
- Geliştirici senin hakkında **hiçbir kişisel veriye erişmez, toplamaz, saklamaz.**
- Her şey bu bilgisayarda kalır.

## 1. Veri sorumlusu

6698 sayılı Kişisel Verilerin Korunması Kanunu'nun (KVKK) 3. maddesine göre veri sorumlusu, kişisel verilerin işlenme amaçlarını ve vasıtalarını belirleyen kişidir. zConventer tamamen senin cihazında çalışır ve geliştiriciye hiçbir veri aktarmaz. Bu nedenle geliştirici, Uygulama aracılığıyla işlenen verilerin veri sorumlusu değildir.

Uygulamayı kullanarak başkalarına ait kişisel verileri (ör. profil fotoğrafı) kaydeden kullanıcı, bu işlemden kendisi sorumludur. KVKK m. 28/1-(a) uyarınca, üçüncü kişilere verilmemek ve veri güvenliğine uyulmak kaydıyla gerçek kişilerin tamamen kendileriyle veya aynı konutta yaşayan aile fertleriyle ilgili faaliyetleri kapsamında işlenen veriler Kanun kapsamı dışındadır. Bu verileri paylaşmak veya yaymak bu istisnanın dışında kalabilir.

## 2. Bilgisayarında saklananlar

| Veri | Konum | Amaç |
|---|---|---|
| Ayarlar: kayıt klasörü, tarayıcı oturumu seçimi (yalnızca tarayıcının adı), eşzamanlı indirme sayısı, kabul edilen koşul sürümü | `%APPDATA%\zConventer\settings.json` | Tercihlerini hatırlamak |
| yt-dlp önbelleği (kişisel veri içermez, platform çözümleme verileri) | `%APPDATA%\zConventer\cache` | Daha hızlı indirme |
| İndirdiğin dosyalar | Seçtiğin klasör | Senin isteğin |

Uygulama geçmiş, arama kaydı veya log **tutmaz**. Her şeyi silmek için `%APPDATA%\zConventer` klasörünü silmen yeterli.

## 3. Ağ bağlantıları

Uygulama yalnızca senin başlattığın işlemler için ağ bağlantısı kurar. Bağlantılar doğrudan cihazından şu hizmetlere gider:

- İndirmek ya da görüntülemek istediğin platform (YouTube, Spotify, SoundCloud, Instagram, TikTok, X, Reddit, Threads, Facebook) ve bunların içerik dağıtım ağları,
- Spotify parçaları için YouTube araması,
- X profil görselleri için açık kaynaklı [FxTwitter](https://github.com/FxEmbed/FxEmbed) API'si (`api.fxtwitter.com`). Yalnızca girdiğin kullanıcı adı gönderilir.

Bu hizmetler IP adresin gibi verileri kendi gizlilik politikalarına göre işler; geliştiricinin bu işleme üzerinde kontrolü yoktur. Uygulama kendini `zConventer/<sürüm>` kullanıcı aracısıyla tanıtır.

## 4. Tarayıcı çerezleri

"Tarayıcı oturumu" varsayılan olarak **kapalıdır**. Açarsan:

- Çerezler yalnızca istek anında bellekte okunur, **diske yazılmaz**,
- Geliştiriciye veya üçüncü bir tarafa **gönderilmez**,
- Yalnızca ait oldukları platforma, tarayıcının da göndereceği şekilde iletilir.

## 5. Hakların

KVKK m. 11 kapsamındaki hakların (bilgi talep etme, silme, düzeltme vb.) için: geliştirici senin hakkında veri tutmadığından bu hakların muhatabı, verilerini işleyen ilgili platformlardır. Sorular için [GitHub Issues](https://github.com/heFRKN/zConventer/issues).

## 6. GDPR (AB)

Aynı ilkeler geçerlidir. Geliştirici GDPR anlamında veri sorumlusu (controller) veya veri işleyen (processor) değildir. Tamamen kişisel veya ev içi faaliyetler GDPR m. 2(2)(c) uyarınca kapsam dışındadır.

## 7. Değişiklikler

Bu metin güncellenebilir; güncel sürüm her zaman depoda ve Uygulamanın "Yasal" bölümünde yer alır.

---

# Privacy Policy (English)

- **No accounts, no servers, no analytics or telemetry, no ads.** The author never receives, collects or stores any personal data.
- **Stored locally:** settings (`%APPDATA%\zConventer\settings.json`), a yt-dlp cache with no personal data (`%APPDATA%\zConventer\cache`) and the files you download. No history or logs are kept.
- **Network:** connections are made only when you start an action, directly from your device to the platform you chose, YouTube search (for Spotify matching) and the open-source FxTwitter API (for X profile images; only the username is sent). Those services process data such as your IP address under their own policies.
- **Cookies:** the optional browser session feature is off by default. When enabled, cookies are read in memory only, never written to disk, never sent to the author or third parties, and only sent to the platform they belong to.
- **Controller:** the app runs entirely on your device, so the author is not a data controller or processor under KVKK or GDPR. Purely personal or household activity is outside the scope of KVKK (Art. 28/1-a) and GDPR (Art. 2(2)(c)).
