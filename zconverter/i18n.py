"""Interface language. Source strings are Turkish; English comes from the table below.

t("Kaydedildi: {names}", names=...) translates and then formats. tools/i18n_keys.py lists any
t() string that has no English entry yet."""

import locale
import sys

_lang = "tr"


def set_language(code: str) -> None:
    global _lang
    _lang = code if code in ("tr", "en") else "en"


def language() -> str:
    return _lang


def system_language() -> str:
    """'tr' when Windows (or the locale) is Turkish, otherwise 'en'."""
    if sys.platform == "win32":
        import ctypes
        try:
            return "tr" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x1F else "en"
        except (AttributeError, OSError):
            pass
    return "tr" if (locale.getlocale()[0] or "").lower().startswith(("tr", "turkish")) else "en"


def t(text: str, **kwargs) -> str:
    if _lang == "en":
        text = EN.get(text, text)
    return text.format(**kwargs) if kwargs else text


def restart_app() -> None:
    """Start a fresh copy of the app and quit this one (used after changing the language)."""
    from PySide6.QtCore import QProcess
    from PySide6.QtWidgets import QApplication

    args = sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv
    QProcess.startDetached(sys.executable, args)
    QApplication.quit()


# strings that reach t() through a variable rather than a literal
EXTRA_KEYS = [
    "En iyi", "Orijinal", "Serbest", "Kare", "Daire", "Özel", "Profil", "Profil HD", "YouTube banner", "X kapak",
    "Facebook kapak", "Instagram gönderi", "Hikâye / Reels", "Video kapağı", "Kullanım koşulları",
    "Gizlilik ve KVKK", "Lisanslar", "Görüntü ve ses birleştiriliyor", "Sese dönüştürülüyor",
    "Kapsayıcı değiştiriliyor", "Kapak ekleniyor", "Etiketler yazılıyor", "Kırpılıyor",
]

EN = {
    # navigation / common
    "İndir": "Download",
    "Profil görselleri": "Profile images",
    "Ayarlar": "Settings",
    "Yasal": "Legal",
    "Sürüm {version}": "Version {version}",
    "Kaydet": "Save",
    "Klasörü aç": "Open folder",
    "Video": "Video",
    "Ses": "Audio",
    "Tür": "Type",
    "Kalite": "Quality",
    "Biçim": "Format",
    "En iyi": "Best",
    "Orijinal": "Original",
    "Giriş yap": "Sign in",
    "Giriş yap ve tekrar dene": "Sign in and try again",
    "Önizleme yok": "No preview",

    # download page
    "Bağlantıyı yapıştır. Önizleme gelince biçimi seç, istersen kırp.":
        "Paste a link. When the preview appears, pick a format and trim if you like.",
    "Bağlantıyı buraya yapıştır": "Paste a link here",
    "Yapıştır": "Paste",
    "Bu bağlantı desteklenen platformlardan birine ait değil.": "This link is not from a supported platform.",
    "Bilgiler alınıyor": "Getting details",
    "Başlıksız": "Untitled",
    "{n} öğe": "{n} items",
    "Önizleme alınamadı": "Couldn't load a preview",
    "Kayıt yeri: {path}": "Saving to: {path}",
    "Kapak ve etiketler": "Cover and tags",
    "Tüm listeyi indir": "Download the whole list",
    "Kırp": "Trim",
    "Tutamakları sürükle ya da zamanı yaz. Seçili aralık indirilir.":
        "Drag the handles or type the times. Only the selected range is downloaded.",
    "Kuyruk": "Queue",
    "Bitenleri temizle": "Clear finished",
    "Henüz bir şey yok. İndirdiklerin burada görünecek.": "Nothing here yet. Your downloads will show up here.",
    "Kapak gömme yalnızca MP3 ve M4A için.": "Cover art can only be embedded in MP3 and M4A.",
    "Sırada": "Queued",
    "Klasörde göster": "Show in folder",
    "Tekrar dene": "Try again",
    "İptal et": "Cancel",
    "Listeden kaldır": "Remove from list",
    "İptal edildi": "Cancelled",
    "Tamamlandı": "Done",
    "Tamamlandı · {n} dosya": "Done · {n} files",
    "son": "end",

    # trim editor
    "Başlangıç": "Start",
    "Bitiş": "End",
    "Dinle": "Listen",
    "Durdur": "Stop",
    "Hazırlanıyor": "Preparing",
    "Örnek: 1:30 ya da 1:30.5": "e.g. 1:30 or 1:30.5",
    "Tamamını al": "Use all",
    "Tamamı": "All",
    "Seçim": "Selection",
    "Yükleniyor": "Loading",
    "Kare alınamadı": "Couldn't get frame",
    "Dalga formu hazırlanıyor": "Preparing waveform",
    "Dalga formu alınamadı": "Couldn't load waveform",
    "Ses önizlemesi alınamadı": "Couldn't load audio preview",

    # profile page
    "Profil fotoğrafını ve kapak görselini en yüksek çözünürlükte al, istersen boyutlandır.":
        "Get profile pictures and banners at the highest resolution and resize them if you like.",
    "Getir": "Fetch",
    "Profil fotoğrafı": "Profile picture",
    "Kapak": "Banner",
    "Düzenle": "Edit",
    "Hazır boyut": "Preset",
    "Boyut": "Size",
    "Kırpma": "Crop",
    "Oranı koru (kapalıyken tam bu boyuta kırpılır)": "Keep aspect ratio (when off, the image is cropped to exactly this size)",
    "Orijinal boyuta dön": "Back to original size",
    "Kırpmayı ve boyutu sıfırla": "Reset crop and size",
    "Çerçeveyi sürükle, köşelerinden boyutlandır ya da resmin üstünde yeni bir alan çiz.":
        "Drag the frame, resize it from its corners, or draw a new area on the image.",
    "Kırpma oranı": "Crop ratio",
    "Çıktı boyutu": "Output size",
    "Serbest": "Free",
    "Yok": "None",
    "Kare": "Square",
    "Daire": "Circle",
    "Özel": "Custom",
    "Profil": "Profile",
    "Profil HD": "Profile HD",
    "YouTube banner": "YouTube banner",
    "X kapak": "X header",
    "Facebook kapak": "Facebook cover",
    "Instagram gönderi": "Instagram post",
    "Hikâye / Reels": "Story / Reels",
    "Video kapağı": "Video thumbnail",
    "@kanal ya da kanal bağlantısı": "@channel or channel link",
    "u/kullanıcı ya da r/topluluk": "u/user or r/community",
    "@kullanıcıadı ya da profil bağlantısı": "@username or profile link",
    "Aranıyor": "Searching",
    "Bu hesapta kapak görseli yok.": "This account has no banner.",
    "Profil fotoğrafı bulunamadı.": "No profile picture found.",
    "Kaynak bundan küçük; büyütülen görsel bulanık olabilir.": "The source is smaller than this; the enlarged image may look blurry.",
    "Kaydedilecek görsel seçilmedi.": "Nothing selected to save.",
    "Profiller": "Profiles",
    "profil": "profile",
    "kapak": "banner",
    "Kaydedildi: {names}": "Saved: {names}",
    "Kaydedilemedi: {error}": "Couldn't save: {error}",

    # settings
    "Her şey bu bilgisayarda kalır. Uygulama hiçbir veriyi bize göndermez.":
        "Everything stays on this computer. The app sends no data to us.",
    "Dil": "Dil",
    "Yeniden başlat": "Restart",
    "Kayıt yeri": "Save location",
    "Değiştir": "Change",
    "Aç": "Open",
    "Hesaplar": "Accounts",
    "Gizli, yaş sınırlı ya da giriş isteyen içerikler (Reddit videoları gibi) için hesabına giriş yap. "
    "Giriş, platformun kendi sayfasında uygulamanın içinde yapılır; şifren uygulamaya geçmez. "
    "Oturum bu bilgisayarda Windows şifrelemesiyle saklanır ve sadece o platforma gönderilir. "
    "Sadece kendi hesabını kullan.":
        "Sign in for private, age-restricted or sign-in-only content (such as Reddit videos). You sign in on the "
        "platform's own page inside the app; your password never reaches the app. The session is stored on this "
        "computer with Windows encryption and only sent to that platform. Use only your own account.",
    "Bağlı": "Connected",
    "Bağlı değil": "Not connected",
    "Çıkış yap": "Sign out",
    "Firefox'taki açık oturumu kullan": "Use my open Firefox session",
    "Aynı anda indirme": "Parallel downloads",
    "Bileşenler": "Components",
    "dahili": "built in",
    "JavaScript çalışma ortamı": "JavaScript runtime",
    "{name} bulundu": "{name} found",
    "Bulunamadı. YouTube'da bazı kaliteler eksik kalabilir. Kurmak için terminalde: ":
        "Not found. Some YouTube qualities may be missing. To install, run in a terminal: ",
    "Hakkında": "About",
    "zConverter {version} · MIT Lisansı · © 2026 {author}": "zConverter {version} · MIT License · © 2026 {author}",
    "Bağımsız, açık kaynaklı bir projedir. Adı geçen platformların hiçbiriyle bağlantılı değildir, "
    "onlar tarafından desteklenmez veya onaylanmaz.":
        "An independent open-source project. It is not affiliated with, endorsed or approved by any of the "
        "platforms named.",
    "GitHub'da aç": "Open on GitHub",

    # legal / consent
    "Kısaca: kişisel kullanım için. İndirdiğin içerikten ve nasıl kullandığından sen sorumlusun.":
        "In short: for personal use. You are responsible for what you download and how you use it.",
    "Kullanım koşulları": "Terms of use",
    "Gizlilik ve KVKK": "Privacy",
    "Lisanslar": "Licenses",
    "{name} bulunamadı.": "{name} not found.",
    "Başlamadan önce": "Before you start",
    "zConverter yalnızca hakkın olan ya da kişisel kullanımına izin verilen içerikler içindir. Lütfen koşulları oku.":
        "zConverter is only for content you own or are allowed to save for personal use. Please read the terms.",
    "Okudum, anladım ve kabul ediyorum": "I have read, understood and accept",
    "Çık": "Quit",
    "Devam et": "Continue",

    # sign-in window
    "{name} girişi": "{name} sign-in",
    "{name} hesabına giriş": "Sign in to {name}",
    "Giriş doğrudan {site} sayfasında yapılır; şifren uygulamaya geçmez. Oturum bu bilgisayarda şifreli saklanır.":
        "You sign in directly on {site}; your password never reaches the app. The session is stored encrypted on "
        "this computer.",
    "Giriş yapınca pencere kendiliğinden kapanır.": "This window closes by itself once you're signed in.",
    "Giriş yapıldı": "Signed in",
    "Vazgeç": "Cancel",
    "Bitti": "Done",

    # download engine
    "Görüntü ve ses birleştiriliyor": "Merging video and audio",
    "Sese dönüştürülüyor": "Converting to audio",
    "Kapsayıcı değiştiriliyor": "Changing container",
    "Kapak ekleniyor": "Adding cover",
    "Etiketler yazılıyor": "Writing tags",
    "Kırpılıyor": "Trimming",
    "İşleniyor": "Processing",
    "{time} kaldı": "{time} left",
    "{size}/sn": "{size}/s",
    "kesit": "clip",
    "Liste": "List",
    "Spotify bilgileri okunuyor": "Reading Spotify details",
    "Threads gönderisi okunuyor": "Reading Threads post",
    "Başlangıç ({time}) içeriğin süresini aşıyor.": "The start ({time}) is past the end of the content.",
    "Hiçbir dosya indirilemedi.": "No file could be downloaded.",
    "Threads gönderisinde video bulunamadı. Gönderi gizli olabilir; giriş yapıp tekrar dene.":
        "No video found in this Threads post. It may be private; sign in and try again.",
    "TikTok isteği geri çevirdi. Biraz bekleyip tekrar dene.": "TikTok refused the request. Wait a little and try again.",
    "Bu bağlantı desteklenmiyor.": "This link isn't supported.",
    "Bu içerik DRM korumalı, indirilemez.": "This content is DRM protected and can't be downloaded.",
    "Reddit videoları için Reddit hesabıyla giriş gerekiyor.": "Reddit videos require signing in with a Reddit account.",
    "Facebook bu videoyu giriş yapmadan göstermiyor.": "Facebook doesn't show this video without signing in.",
    "Instagram bu gönderiyi giriş yapmadan göstermiyor.": "Instagram doesn't show this post without signing in.",
    "Bu içerik için giriş gerekiyor.": "This content requires signing in.",
    "İçerik bulunamadı. Silinmiş ya da gizli olabilir.": "Content not found. It may be deleted or private.",
    "Bilinmeyen hata.": "Unknown error.",
    "Kırpma başarısız: ": "Trimming failed: ",
    "{n} parça": "{n} tracks",
    "Her parça YouTube'da eşleştirilip ayrı ayrı indirilecek.": "Each track will be matched on YouTube and downloaded separately.",
    "YouTube eşleşmesi: {title}": "YouTube match: {title}",

    # profiles
    "Giriş yapıp tekrar dene.": "Sign in and try again.",
    "Kullanıcı adı ya da profil bağlantısı gir.": "Enter a username or profile link.",
    "Bu bağlantı desteklenen bir profil platformuna ait değil.": "This link isn't from a supported profile platform.",
    "Reddit bağlantısı /r/… ya da /user/… olmalı.": "A Reddit link must be /r/… or /user/….",
    "Bağlantıda kullanıcı adı yok.": "The link has no username.",
    "YouTube kanalı bulunamadı.": "YouTube channel not found.",
    "X hesabı bulunamadı ya da askıya alınmış.": "X account not found or suspended.",
    "Instagram hesabı bulunamadı.": "Instagram account not found.",
    "Instagram profili okunamadı.": "Couldn't read the Instagram profile.",
    "Instagram giriş yapmadan sadece küçük boyut (100 px) veriyor. Tam boyut için:":
        "Without signing in Instagram only gives a small (100 px) picture. For full size:",
    "Threads profil fotoğrafı bağlı Instagram hesabından alındı. Threads'te kapak görseli yok.":
        "The Threads picture comes from the linked Instagram account. Threads has no banners.",
    "Reddit giriş yapmadan erişime izin vermiyor.": "Reddit doesn't allow access without signing in.",
    "Reddit hesabı ya da topluluğu bulunamadı.": "Reddit user or community not found.",
    "Facebook sayfası bulunamadı.": "Facebook page not found.",
    "Facebook profili okunamadı.": "Couldn't read the Facebook profile.",
    "Facebook kapak görseli herkese açık sayfada yer almıyor.": "Facebook doesn't show the cover photo on the public page.",
    "{name} bağlantı hatası: {error}": "{name} connection error: {error}",
    "Görsel bulunamadı.": "No image found.",
    "Spotify bağlantısı tanınmadı (track / album / playlist olmalı).":
        "Spotify link not recognised (must be a track, album or playlist).",
    "Spotify parça bilgisi okunamadı.": "Couldn't read the Spotify track details.",
    "Listedeki parçalar okunamadı. Liste gizli olabilir.": "Couldn't read the tracks. The list may be private.",
}
