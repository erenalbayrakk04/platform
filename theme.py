# Görünüş teması (kullanıcı kararı: NSS gibi iki görünüş): "retro" = Nostalji (piksel sanatı, oyunun ilk görünüşü,
# varsayılan), "modern" = yumuşak kenarlı, renk geçişli, parlak çizim (modern.py). Ayarlar ekranındaki "Tema"
# düğmesiyle değişir ve kaydedilir. Sadece görünüş: resimlerin boyları ve oyun aynı.
# Resimleri bir kere hazırlayıp saklayan her yer temayı da anahtara katar (cached): tema değişince yeni temanın
# resimleri hazırlanır, eskileriyle karışmaz.
from lang import mark

THEMES = {"retro": mark("Nostalji"), "modern": mark("Modern")}  # ayarlar ekranında bu sırayla değişir
DEFAULT_THEME = "retro"
_current = [DEFAULT_THEME]


def set_theme(name):
    _current[0] = name if name in THEMES else DEFAULT_THEME


def current():
    return _current[0]


def modern():
    return _current[0] == "modern"


def cached(store, key, make):
    # store'da bu temanın key'i yoksa make() ile bir kere hazırla
    key = (_current[0], key)
    if key not in store:
        store[key] = make()
    return store[key]
