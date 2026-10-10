# Bölümler: "Oyna → Bölümler" ile sırayla oynanan, sonu belli tırmanışlar. Her zorluğun (Kolay, Orta, Zor,
# Ultra Zor) kendi bölüm listesi var (STAGE_SETS); hepsi baştan açık, her birinin yıldızları ve kilitleri ayrı.
# Her bölümün haritası sabittir (aynı seed = hep aynı harita) ve mevcut parçalardan (chunks.py) yapılır;
# tepesinde bayrak (FINISH_CHUNK) vardır. Kolay ve Orta'nın ilk bölümleri oyundaki şeyleri tek tek tanıtır;
# Zor ve Ultra Zor'da her bölüm bir şeyin (yay, kirpi, lav...) zorlu bir sınavı.
#
# Bölüm sayıları (stage(...) içinde):
#   goal         hedef yükseklik (m = blok); bayrak bunun biraz üstünde olabilir (parçalar tam oturmaz)
#   intro        bölüm başlarken ekranda yazan açıklama
#   max_chunk    en zor parça (1 kolay, 2 orta, 3 zor)
#   features     hangi yapılar olabilir: S yay, M hareketli platform, K kırılan platform
#   focus        bu işaretlerin olduğu parçalar FOCUS_WEIGHT kat sık gelir (yeni tanıtılan şey çok görünsün)
#   walkers      yürüyen düşman türleri ve ağırlıkları (başta, sonda) — boşsa yürüyen düşman yok
#   flyers       uçan düşman türleri — boşsa uçan düşman yok
#   items        altın yerine çıkabilecekler: heart, magnet, shield
#   boost        items'tan biri: o bölümde ITEM_BOOST kat sık çıkar (tanıtılan güçlendirme görünsün)
#   lava         None = lav yok; (bekleme karesi, hız, en yüksek hız)
#   hardness     bölüm boyunca zorluk (0 = kolay, 1 = en zor; settings.DIFFICULTIES'teki sayıların arası)
#   base         sayıların alındığı zorluk modu ("easy" / "normal" / "hard" / "ultra")
#   extra        her platforma ek yürüyen düşman gelme ihtimali (başta, sonda)
#   extra_flyers her boş satıra ek uçan düşman gelme ihtimali (başta, sonda)
# Canlar listenin zorluğundan gelir (settings STAGE_LIVES).
from functools import partial

from chunks import CHUNKS
from settings import (
    DIFFICULTIES,
    DIFFICULTY_NAMES,
    TILE_SIZE,
    STAGE_LIVES,
    ITEM_BOOST,
    MAGNET_CHANCE,
    SHIELD_CHANCE,
    CANNON_FIRE_TIME,
    WALKER_KINDS,
    FLYER_KINDS,
)

STRUCTURES = "SMK"  # parçayı seçerken bakılan yapılar (olmazsa parça çıkılamaz olabilir, silinmez)
STAGE_COUNT = 20  # her zorlukta kaç bölüm (bölüm seçme ekranı buna göre)


def stage(name, goal, intro, *, max_chunk=1, features="", focus="", walkers=None, flyers=None, items="heart",
          boost=None, lava=None, hardness=(0.0, 0.3), base="easy", extra=(0.05, 0.08), extra_flyers=(0.0, 0.0)):
    return {
        "name": name, "goal": goal, "intro": intro, "max_chunk": max_chunk, "features": features, "focus": focus,
        "walkers": walkers or {}, "flyers": flyers or {}, "items": items.split(), "boost": boost, "lava": lava,
        "hardness": hardness, "base": base, "extra": extra, "extra_flyers": extra_flyers,
    }


WALKER = {"walker": (1, 1)}
BAT = {"bat": (1, 1)}
ALL_ITEMS = "heart magnet shield"


# --- Kolay: her şey yavaş yavaş, tek tek tanıtılır; kısa bölümler, lav sadece sonlarda ve yavaş ---
EASY_STAGES = [
    stage("Merhaba!", 15, "Yürü, zıpla, bayrağa ulaş!", items=""),
    stage("Altın Toplama", 20, "Altınları topla, yıldız kazan", items=""),
    stage("Can Kalbi", 25, "Kalp: +1 can verir", boost="heart"),
    stage("Kırmızı Dost", 25, "Düşmanın üstüne zıpla, yanına değme", walkers=WALKER, extra=(0.03, 0.05)),
    stage("Boing!", 30, "Yay: üstüne bas, yükseğe fırla", features="S", focus="S", walkers=WALKER),
    stage("Çatlak Yol", 30, "Çatlak taş basınca kırılır", features="SK", focus="K", walkers=WALKER),
    stage("Kanatlı Misafir", 35, "Yarasa: onun da üstüne zıpla", features="SK", focus="F", walkers=WALKER,
          flyers=BAT, extra_flyers=(0.02, 0.03)),
    stage("Kayan Tahta", 35, "Mavi platform seni taşır", max_chunk=2, features="SKM", focus="M",
          walkers=WALKER, flyers=BAT),
    stage("Mıknatıs", 40, "Mıknatıs altınları sana çeker", max_chunk=2, features="SKM", walkers=WALKER,
          flyers=BAT, items="heart magnet", boost="magnet"),
    stage("Sümük Zıpzıp", 40, "Sümük zıplar, inince üstüne bas", max_chunk=2, features="SKM", focus="E",
          walkers={"walker": (1, 1), "slime": (3, 3)}, flyers=BAT, items="heart magnet"),
    stage("Kalkan", 45, "Kalkan seni düşmandan korur", max_chunk=2, features="SKM",
          walkers={"walker": (2, 2), "slime": (1, 1)}, flyers=BAT, items=ALL_ITEMS, boost="shield"),
    stage("Dikenli Dost", 45, "Kirpiye BASMA, üstünden atla", max_chunk=2, features="SKM", focus="E",
          walkers={"walker": (2, 2), "spiky": (3, 3)}, flyers=BAT, items=ALL_ITEMS),
    stage("Vızz Vızz", 50, "Arı aşağı yukarı uçar", max_chunk=2, features="SKM", focus="F",
          walkers={"walker": (2, 2), "slime": (1, 1)}, flyers={"bee": (1, 1)}, items=ALL_ITEMS,
          extra_flyers=(0.1, 0.14)),
    stage("Pat Pat", 50, "Topçu ateş atar, üstüne zıpla", max_chunk=2, features="SKM", focus="E",
          walkers={"walker": (1, 1), "cannon": (3, 3)}, flyers=BAT, items=ALL_ITEMS),
    stage("Sıcak Ayaklar", 50, "Lav geliyor ama yavaş", max_chunk=2, features="SKM", walkers=WALKER,
          flyers=BAT, items=ALL_ITEMS, lava=(360, 0.2, 0.25)),
    stage("Karışık Torba", 60, "Hepsi bir arada!", max_chunk=2, features="SKM", focus="SMK",
          walkers=WALKER_KINDS, flyers=FLYER_KINDS, items=ALL_ITEMS, hardness=(0.1, 0.3)),
    stage("Uzun Yol", 70, "Bu sefer biraz uzun", max_chunk=2, features="SKM", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, hardness=(0.1, 0.4), extra_flyers=(0.01, 0.03)),
    stage("Lavlı Tepe", 70, "Lav yine geliyor, acele et", max_chunk=2, features="SKM", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, lava=(300, 0.22, 0.3), hardness=(0.2, 0.4)),
    stage("Yıldızlara Doğru", 80, "Küçük platformlar da var", max_chunk=3, features="SKM", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, hardness=(0.2, 0.5), extra_flyers=(0.01, 0.03)),
    stage("Büyük Tırmanış", 90, "Son bölüm: zirveye çık!", max_chunk=3, features="SKM", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, lava=(300, 0.25, 0.32), hardness=(0.3, 0.6),
          extra_flyers=(0.02, 0.04)),
]

# --- Orta: ilk bölümler tanıtır, sonra zorlaşır (bölüm modunun ilk listesi) ---
NORMAL_STAGES = [
    stage("İlk Adımlar", 20, "Platformlara zıpla, bayrağa ulaş!", items=""),
    stage("Kalp Avı", 30, "Kalp: +1 can verir"),
    stage("İlk Düşman", 35, "Düşmanın üstüne zıpla, yanına değme", walkers=WALKER),
    stage("Zıpla Zıpla", 40, "Yay: üstüne bas, yükseğe fırla", features="S", focus="S", walkers=WALKER),
    stage("Lav Geliyor!", 40, "Lav yükseliyor, acele et!", features="S", walkers=WALKER, lava=(240, 0.25, 0.32)),
    stage("Kayan Yollar", 45, "Mavi platform seni taşır", max_chunk=2, features="SM", focus="M", walkers=WALKER),
    stage("Gece Kanatları", 50, "Yarasa: onun da üstüne zıpla", max_chunk=2, features="SM", focus="F",
          walkers=WALKER, flyers=BAT, extra_flyers=(0.02, 0.04)),
    stage("Çatlak Taşlar", 50, "Çatlak taş kırılır, mıknatıs altın çeker", max_chunk=2, features="SMK",
          focus="K", walkers=WALKER, flyers=BAT, items="heart magnet", boost="magnet", lava=(300, 0.25, 0.32),
          extra=(0.08, 0.1)),
    stage("Yapışkan Sümük", 55, "Sümük zıplar, inince üstüne bas", max_chunk=2, features="SMK", focus="E",
          walkers={"walker": (1, 1), "slime": (3, 3)}, flyers=BAT, items="heart magnet"),
    stage("Dikenli Yol", 60, "Kirpiye BASMA! Kalkan seni korur", max_chunk=2, features="SMK", focus="E",
          walkers={"walker": (2, 2), "slime": (1, 1), "spiky": (3, 3)}, flyers=BAT, items=ALL_ITEMS,
          boost="shield", lava=(240, 0.28, 0.36)),
    stage("Arı Kovanı", 65, "Arı aşağı yukarı uçar", max_chunk=2, features="SMK", focus="F",
          walkers={"walker": (2, 2), "slime": (1, 1), "spiky": (1, 1)}, flyers={"bat": (1, 1), "bee": (3, 3)},
          items=ALL_ITEMS, extra_flyers=(0.06, 0.1)),
    stage("Ateş Hattı", 65, "Topçu ateş atar, üstüne zıpla", max_chunk=2, features="SMK", focus="E",
          walkers={"walker": (1, 1), "slime": (1, 1), "spiky": (1, 1), "cannon": (3, 3)},
          flyers={"bat": (1, 1), "bee": (1, 1)}, items=ALL_ITEMS, lava=(240, 0.3, 0.38)),
    stage("Hepsi Bir Arada", 75, "Şimdi her şey bir arada!", max_chunk=2, features="SMK", focus="SMK",
          walkers=WALKER_KINDS, flyers=FLYER_KINDS, items=ALL_ITEMS, hardness=(0.2, 0.6),
          extra=(0.1, 0.14), extra_flyers=(0.03, 0.06)),
    stage("Kızgın Kaçış", 80, "Lav bu sefer daha hızlı!", max_chunk=2, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, lava=(180, 0.35, 0.5), base="normal",
          hardness=(0.0, 0.3), extra=(0.08, 0.12), extra_flyers=(0.02, 0.05)),
    stage("Gök Merdiveni", 90, "Küçük platformlar geliyor", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, base="normal", hardness=(0.2, 0.5),
          extra=(0.08, 0.12), extra_flyers=(0.02, 0.05)),
    stage("Ateş Çemberi", 100, "Lav ve topçular bir arada", max_chunk=3, features="SMK",
          walkers={"walker": (2, 2), "slime": (1, 1), "spiky": (1, 1), "cannon": (3, 3)}, flyers=FLYER_KINDS,
          items=ALL_ITEMS, lava=(180, 0.4, 0.6), base="normal", hardness=(0.3, 0.6),
          extra=(0.08, 0.13), extra_flyers=(0.03, 0.06)),
    stage("Düşman Ordusu", 110, "Her yer düşman dolu!", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, base="normal", hardness=(0.4, 0.7),
          extra=(0.14, 0.2), extra_flyers=(0.05, 0.08)),
    stage("Lav Seli", 120, "Durmak yok!", max_chunk=3, features="SMK", walkers=WALKER_KINDS, flyers=FLYER_KINDS,
          items=ALL_ITEMS, lava=(120, 0.5, 0.75), base="normal", hardness=(0.5, 0.8),
          extra=(0.1, 0.15), extra_flyers=(0.03, 0.07)),
    stage("Son Hazırlık", 130, "Neredeyse zirvedesin", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, base="normal", hardness=(0.6, 0.9),
          extra=(0.12, 0.17), extra_flyers=(0.05, 0.08)),
    stage("Zirve", 150, "Son bölüm: zirveye çık!", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items=ALL_ITEMS, lava=(120, 0.55, 0.85), base="normal",
          hardness=(0.7, 1.0), extra=(0.12, 0.17), extra_flyers=(0.05, 0.08)),
]

# --- Zor: her şeyi biliyorsun; her bölüm bir şeyin sınavı (çok yay, çok kirpi, hızlı lav...) ---
hard = partial(
    stage, base="hard", max_chunk=2, features="SMK", walkers=WALKER_KINDS, flyers=FLYER_KINDS, items=ALL_ITEMS,
    hardness=(0.1, 0.4), extra=(0.11, 0.16), extra_flyers=(0.035, 0.06),
)
HARD_STAGES = [
    hard("Isınma Turu", 50, "Zor bölümler başlıyor!", hardness=(0.0, 0.2)),
    hard("Yay Kulesi", 60, "Yaylarla göğe fırla", max_chunk=3, focus="S"),
    hard("Kırık Köprüler", 60, "Çatlak taşlarda durma!", max_chunk=3, focus="K"),
    hard("Yarasa Mağarası", 65, "Gökyüzü yarasa dolu", focus="F", flyers=BAT, extra_flyers=(0.08, 0.12)),
    hard("Lav Kovalıyor", 60, "Lav hemen peşinde!", lava=(120, 0.5, 0.6)),
    hard("Sümük Bataklığı", 70, "Her yerde zıplayan sümük", focus="E",
         walkers={"walker": (1, 1), "slime": (5, 5)}, extra=(0.14, 0.18)),
    hard("Kayan Kule", 70, "Hareketli platformlar", max_chunk=3, focus="M"),
    hard("Diken Tarlası", 75, "Kirpilere dikkat!", focus="E", walkers={"walker": (1, 1), "spiky": (5, 5)},
         extra=(0.14, 0.18)),
    hard("Arı Fırtınası", 75, "Arılar her yerde", focus="F", flyers={"bee": (1, 1)}, extra_flyers=(0.16, 0.2)),
    hard("Topçu Kalesi", 80, "Ateş toplarından kaç", focus="E", walkers={"walker": (1, 1), "cannon": (5, 5)},
         lava=(180, 0.5, 0.65)),
    hard("Gece Avı", 85, "Uçanlar ve yürüyenler", hardness=(0.3, 0.5), extra_flyers=(0.06, 0.09)),
    hard("Sıcak Takip", 90, "Lav daha da hızlı!", lava=(90, 0.6, 0.75), hardness=(0.3, 0.5)),
    hard("Kırık Merdiven", 90, "Çatlak taş ve lav", max_chunk=3, focus="K", lava=(120, 0.55, 0.7)),
    hard("Kalabalık", 100, "Düşman ordusu!", max_chunk=3, hardness=(0.4, 0.6), extra=(0.16, 0.22),
         extra_flyers=(0.06, 0.09)),
    hard("Yaylı Kaçış", 100, "Yaylara bas, lavdan kaç", max_chunk=3, focus="S", lava=(90, 0.6, 0.8)),
    hard("Karanlık Gök", 110, "Küçük platformlar, çok düşman", max_chunk=3, hardness=(0.5, 0.7)),
    hard("Dikenli Kale", 120, "Kirpiler ve topçular", max_chunk=3, focus="E",
         walkers={"walker": (1, 1), "spiky": (3, 3), "cannon": (3, 3)}, hardness=(0.5, 0.8), extra=(0.14, 0.2)),
    hard("Lav Nehri", 130, "Durursan yanarsın!", max_chunk=3, lava=(60, 0.7, 0.9), hardness=(0.6, 0.8)),
    hard("Son Sınav", 150, "Neredeyse bitti", max_chunk=3, hardness=(0.7, 0.9), extra=(0.15, 0.2),
         extra_flyers=(0.07, 0.09)),
    hard("Dev Zirve", 180, "Son bölüm: en yükseğe!", max_chunk=3, lava=(60, 0.7, 1.0), hardness=(0.8, 1.0),
         extra=(0.15, 0.2), extra_flyers=(0.07, 0.09)),
]

# --- Ultra Zor: tek can, hızlı düşmanlar, beklemeyen lav; bölümler kısa ama acımasız ---
ultra = partial(
    stage, base="ultra", max_chunk=3, features="SMK", walkers=WALKER_KINDS, flyers=FLYER_KINDS, items=ALL_ITEMS,
    hardness=(0.3, 0.6), extra=(0.15, 0.2), extra_flyers=(0.08, 0.1),
)
ULTRA_STAGES = [
    ultra("Tek Can", 40, "Tek canın var, dikkat!", hardness=(0.2, 0.4)),
    ultra("Hızlı Lav", 45, "Lav beklemiyor!", lava=(30, 0.8, 0.9)),
    ultra("Yay Çılgınlığı", 50, "Yaylarla uç", focus="S"),
    ultra("Çökük Yol", 50, "Basınca kırılan taşlar", focus="K", lava=(60, 0.8, 0.9)),
    ultra("Gece Sürüsü", 55, "Yarasa sürüsü", focus="F", flyers=BAT, extra_flyers=(0.1, 0.14)),
    ultra("Topçu Hattı", 55, "Ateş topları ve lav", focus="E", walkers={"walker": (1, 1), "cannon": (5, 5)},
          lava=(60, 0.8, 0.9)),
    ultra("Sümük Yağmuru", 60, "Sümükler zıplıyor", focus="E", walkers={"walker": (1, 1), "slime": (5, 5)},
          extra=(0.18, 0.22)),
    ultra("Diken Duvarı", 60, "Kirpi dolu platformlar", focus="E", walkers={"walker": (1, 1), "spiky": (5, 5)},
          lava=(60, 0.8, 0.95), extra=(0.18, 0.22)),
    ultra("Arı Sürüsü", 65, "Arılar yolunu kesiyor", focus="F", flyers={"bee": (1, 1)}, extra_flyers=(0.18, 0.22)),
    ultra("Kayan Tuzak", 70, "Hareketli platform ve lav", focus="M", lava=(30, 0.85, 0.95)),
    ultra("Kaos", 75, "Her yer düşman!", hardness=(0.5, 0.7), extra=(0.2, 0.25), extra_flyers=(0.1, 0.13)),
    ultra("Ateş Yağmuru", 80, "Topçular ve hızlı lav", focus="E",
          walkers={"walker": (1, 1), "slime": (1, 1), "cannon": (4, 4)}, lava=(0, 0.9, 1.0)),
    ultra("Kırık Kule", 85, "Kırılan taşlar, beklemeyen lav", focus="K", lava=(0, 0.9, 1.0)),
    ultra("Uçan Ordu", 90, "Gökyüzü düşman dolu", focus="F", hardness=(0.5, 0.8), extra_flyers=(0.12, 0.16)),
    ultra("Durma!", 95, "Lav çok hızlı!", lava=(0, 1.0, 1.1), hardness=(0.5, 0.7)),
    ultra("Kâbus", 100, "Her şey bir arada", focus="SMK", hardness=(0.6, 0.8), lava=(30, 0.9, 1.05)),
    ultra("Çılgın Tırmanış", 110, "Hızlı ve uzun", hardness=(0.7, 0.9), extra=(0.18, 0.22)),
    ultra("Lav Okyanusu", 120, "Lav seni yutmak istiyor", lava=(0, 1.05, 1.15), hardness=(0.7, 0.9)),
    ultra("Efsane", 140, "Sadece efsaneler geçer", hardness=(0.8, 1.0), extra=(0.2, 0.25),
          extra_flyers=(0.1, 0.13)),
    ultra("Ultra Zirve", 160, "Son bölüm: başarabilir misin?", lava=(0, 1.0, 1.2), hardness=(0.9, 1.0),
          extra=(0.2, 0.25), extra_flyers=(0.1, 0.13)),
]

# Zorluk → bölüm listesi. Her bölüme zorluğu ve sabit seed'i yazılır (harita beğenilmezse seed değiştirilebilir;
# Orta 1000'den başlar — ilk listenin haritaları değişmesin diye)
STAGE_SETS = {"easy": EASY_STAGES, "normal": NORMAL_STAGES, "hard": HARD_STAGES, "ultra": ULTRA_STAGES}
SEED_BASE = {"normal": 1000, "easy": 2000, "hard": 3000, "ultra": 4000}
for _mode, _stages in STAGE_SETS.items():
    for _index, _stage in enumerate(_stages):
        _stage["seed"] = SEED_BASE[_mode] + _index
        _stage["difficulty"] = _mode


def stage_mode(stage):
    # Level ve Lava'nın kullandığı sayılar: zorluk modunun (base) sayıları + bölümün kendi sayıları
    mode = dict(DIFFICULTIES[stage["base"]])
    items = stage["items"]
    walker_chance = stage["extra"] if stage["walkers"] else (0, 0)
    flyer_chance = stage["extra_flyers"] if stage["flyers"] else (0, 0)
    lives, max_lives = STAGE_LIVES[stage["difficulty"]]
    mode.update(
        lives=lives,
        max_lives=max_lives,
        hard_height=stage["goal"] * TILE_SIZE,  # bölümün sonunda "hardness"ın ikinci sayısına ulaşır
        map_head_start=0,
        hardness=stage["hardness"],
        walker_kinds=stage["walkers"],
        flyer_kinds=stage["flyers"],
        extra_enemy_chance=walker_chance[0],
        extra_enemy_chance_max=walker_chance[1],
        extra_flyer_chance=flyer_chance[0],
        extra_flyer_chance_max=flyer_chance[1],
        heart_chance=mode["heart_chance"] if "heart" in items else 0,
        heart_chance_min=mode["heart_chance_min"] if "heart" in items else 0,
        magnet_chance=MAGNET_CHANCE if "magnet" in items else 0,
        shield_chance=SHIELD_CHANCE if "shield" in items else 0,
        cannon_fire_time=CANNON_FIRE_TIME,  # Ultra Zor'un sonsuz oyundaki sık ateşi bölümlere geçmesin
        lava=stage["lava"] is not None,
    )
    boost = stage["boost"]
    if boost == "heart":
        mode["heart_chance"] *= ITEM_BOOST
        mode["heart_chance_min"] *= ITEM_BOOST
    elif boost:
        mode[f"{boost}_chance"] *= ITEM_BOOST
    if stage["lava"]:
        mode["lava_delay"], mode["lava_speed"], mode["lava_speed_max"] = stage["lava"]
    return mode


def structures(chunk):
    # Parçadaki yapılar (yay, hareketli, kırılan) — parça seçerken bakılır
    return set("".join(chunk["rows"])) & set(STRUCTURES)


def allowed_chunks(stage, entry):
    # Bu bölümde girişi entry tarafında olan, kullanılabilecek parçalar
    return [
        chunk
        for chunk in CHUNKS
        if chunk["entry"] == entry
        and chunk["difficulty"] <= stage["max_chunk"]
        and structures(chunk) <= set(stage["features"])
    ]


def focused(stage, chunk):
    # Bölümün tanıttığı şey bu parçada var mı (varsa daha sık gelir)
    return any(mark in row for mark in stage["focus"] for row in chunk["rows"])


def check_stages():
    # Yanlış ayarlanmış bölümde oyun açılırken hata ver
    if set(STAGE_SETS) != set(DIFFICULTY_NAMES):
        raise ValueError("Her zorluk modunun bir bölüm listesi olmalı (STAGE_SETS)")
    for mode, stages in STAGE_SETS.items():
        if len(stages) != STAGE_COUNT:
            raise ValueError(f"{DIFFICULTY_NAMES[mode]} zorlukta {STAGE_COUNT} bölüm olmalı ({len(stages)} var)")
        for number, stage in enumerate(stages, 1):
            where = f"{DIFFICULTY_NAMES[mode]} {number}. bölüm"
            for side in "LR":
                if not allowed_chunks(stage, side):
                    raise ValueError(f"{where}: girişi '{side}' olan uygun parça yok")
            for kinds, known in ((stage["walkers"], WALKER_KINDS), (stage["flyers"], FLYER_KINDS)):
                if any(kind not in known for kind in kinds):
                    raise ValueError(f"{where}: bilinmeyen düşman türü: {list(kinds)}")
            if stage["boost"] and stage["boost"] not in stage["items"]:
                raise ValueError(f"{where}: boost '{stage['boost']}' items içinde değil")


check_stages()
