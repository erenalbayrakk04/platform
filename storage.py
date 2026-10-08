# Kalıcı kayıtlar: rekorlar, istatistikler, seçenekler (ses, zorluk).
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
)

# Kayıt türleri: (bilgisayardaki dosya, tarayıcı hafızasındaki ad)
STORES = {
    "height": (BEST_HEIGHT_FILE, BEST_HEIGHT_KEY),  # en yüksek tırmanış (blok)
    "score": (HIGHSCORE_FILE, HIGHSCORE_KEY),  # en yüksek puan
    "stats": (STATS_FILE, STATS_KEY),  # toplamlar (oynanan oyun, altın...)
    "options": (OPTIONS_FILE, OPTIONS_KEY),  # ses kapalı mı, zorluk
}


def path(kind):
    # Dosya, oyunun klasöründe dursun (oyun nereden çalıştırılırsa çalıştırılsın)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), STORES[kind][0])


def load_text(kind):
    # Kayıt yoksa veya okunamazsa None
    try:
        if WEB:
            from platform import window

            return window.localStorage.getItem(STORES[kind][1])
        with open(path(kind), encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def save_text(kind, text):
    try:
        if WEB:
            from platform import window

            window.localStorage.setItem(STORES[kind][1], text)
            return
        with open(path(kind), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass  # kaydedilemese de oyun çalışmaya devam etsin


def load_record(kind):
    # Sayı olarak kayıt; yoksa veya bozuksa 0
    try:
        return int(str(load_text(kind)).strip())
    except Exception:
        return 0


def save_record(kind, value):
    save_text(kind, str(value))


def load_dict(kind, defaults):
    # Sözlük olarak kayıt (JSON). Eksik veya bozuk değerler yerine defaults kullanılır
    data = dict(defaults)
    try:
        saved = json.loads(load_text(kind))
        for key, value in saved.items():
            if key in defaults and type(value) is type(defaults[key]):
                data[key] = value
    except Exception:
        pass
    return data


def save_dict(kind, data):
    save_text(kind, json.dumps(data))
