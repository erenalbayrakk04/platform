# Kalıcı kayıtlar: rekorlar (her zorluk modunun ayrı), istatistikler, seçenekler (ses, zorluk), bölüm yıldızları.
# Bilgisayarda oyun klasöründeki dosyalarda; tarayıcıda dosyaya yazılan şey sayfa kapanınca kaybolduğu için
# tarayıcının kendi hafızasında (localStorage) saklanır. pygbag, tarayıcıya platform.window ile eriştirir.
import json
import os

from settings import (
    WEB,
    HIGHSCORE_FILE,
    HIGHSCORE_KEY,
    BEST_HEIGHT_FILE,
    BEST_HEIGHT_KEY,
    STATS_FILE,
    STATS_KEY,
    OPTIONS_FILE,
    OPTIONS_KEY,
    STAGES_FILE,
    STAGES_KEY,
    DEFAULT_DIFFICULTY,
)

# Kayıt türleri: (bilgisayardaki dosya, tarayıcı hafızasındaki ad)
STORES = {
    "height": (BEST_HEIGHT_FILE, BEST_HEIGHT_KEY),  # en yüksek tırmanış (blok)
    "score": (HIGHSCORE_FILE, HIGHSCORE_KEY),  # en yüksek puan
    "stats": (STATS_FILE, STATS_KEY),  # toplamlar (oynanan oyun, altın...)
    "options": (OPTIONS_FILE, OPTIONS_KEY),  # ses kapalı mı, zorluk
    "stages": (STAGES_FILE, STAGES_KEY),  # her bölümün en iyi yıldızı (her zorluğun ayrı)
}


def names(kind, mode=None):
    # (dosya adı, tarayıcı hafızasındaki ad). Rekorlar her zorluk modunun ayrı: Orta eski adları kullanır
    # (ilk rekorlar o moddaydı), diğer modlarda adın sonuna mod eklenir (ör. bestheight-ultra.txt)
    file, key = STORES[kind]
    if mode and mode != DEFAULT_DIFFICULTY:
        stem, ext = os.path.splitext(file)
        return f"{stem}-{mode}{ext}", f"{key}-{mode}"
    return file, key


def path(kind, mode=None):
    # Dosya, oyunun klasöründe dursun (oyun nereden çalıştırılırsa çalıştırılsın)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), names(kind, mode)[0])


def load_text(kind, mode=None):
    # Kayıt yoksa veya okunamazsa None
    try:
        if WEB:
            from platform import window

            return window.localStorage.getItem(names(kind, mode)[1])
        with open(path(kind, mode), encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def save_text(kind, text, mode=None):
    try:
        if WEB:
            from platform import window

            window.localStorage.setItem(names(kind, mode)[1], text)
            return
        with open(path(kind, mode), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass  # kaydedilemese de oyun çalışmaya devam etsin


def load_record(kind, mode=None):
    # Sayı olarak kayıt (mode = hangi zorluk modunun rekoru); yoksa veya bozuksa 0
    try:
        return int(str(load_text(kind, mode)).strip())
    except Exception:
        return 0


def save_record(kind, value, mode=None):
    save_text(kind, str(value), mode)


def load_dict(kind, defaults, mode=None):
    # Sözlük olarak kayıt (JSON). Eksik veya bozuk değerler yerine defaults kullanılır.
    # mode = zorluk modu (bölüm yıldızları gibi her modun ayrı olan kayıtlar için)
    data = dict(defaults)
    try:
        saved = json.loads(load_text(kind, mode))
        for key, value in saved.items():
            if key in defaults and type(value) is type(defaults[key]):
                data[key] = value
    except Exception:
        pass
    return data


def save_dict(kind, data, mode=None):
    save_text(kind, json.dumps(data), mode)
