# Bölümler: "Oyna → Bölümler" ile sırayla oynanan, sonu belli tırmanışlar. Her bölümün haritası sabittir
# (aynı seed = hep aynı harita) ve mevcut parçalardan (chunks.py) yapılır; tepesinde bayrak (FINISH_CHUNK)
# vardır. İlk bölümler oyundaki şeyleri tek tek tanıtır (yay, yarasa, kirpi...), sonrakiler zorlaşır.
#
# Bölüm sayıları (stage(...) içinde):
#   goal         hedef yükseklik (m = blok); bayrak bunun biraz üstünde olabilir (parçalar tam oturmaz)
#   intro        bölüm başlarken ekranda yazan "Yeni: ..." açıklaması
#   max_chunk    en zor parça (1 kolay, 2 orta, 3 zor)
#   features     hangi yapılar olabilir: S yay, M hareketli platform, K kırılan platform
#   focus        bu işaretlerin olduğu parçalar FOCUS_WEIGHT kat sık gelir (yeni tanıtılan şey çok görünsün)
#   walkers      yürüyen düşman türleri ve ağırlıkları (başta, sonda) — boşsa yürüyen düşman yok
#   flyers       uçan düşman türleri — boşsa uçan düşman yok
#   items        altın yerine çıkabilecekler: heart, magnet, shield
#   lava         None = lav yok; (bekleme karesi, hız, en yüksek hız)
#   hardness     bölüm boyunca zorluk (0 = kolay, 1 = en zor; settings.DIFFICULTIES'teki sayıların arası)
#   base         sayıların alındığı zorluk modu ("easy" / "normal")
#   extra        her platforma ek yürüyen düşman gelme ihtimali (başta, sonda)
#   extra_flyers her boş satıra ek uçan düşman gelme ihtimali (başta, sonda)
from chunks import CHUNKS
from settings import (
    DIFFICULTIES,
    TILE_SIZE,
    STAGE_LIVES,
    MAGNET_CHANCE,
    SHIELD_CHANCE,
    WALKER_KINDS,
    FLYER_KINDS,
)

STRUCTURES = "SMK"  # parçayı seçerken bakılan yapılar (olmazsa parça çıkılamaz olabilir, silinmez)


def stage(name, goal, intro, *, max_chunk=1, features="", focus="", walkers=None, flyers=None, items="heart",
          lava=None, hardness=(0.0, 0.3), base="easy", extra=(0.05, 0.08), extra_flyers=(0.0, 0.0)):
    return {
        "name": name, "goal": goal, "intro": intro, "max_chunk": max_chunk, "features": features, "focus": focus,
        "walkers": walkers or {}, "flyers": flyers or {}, "items": items.split(), "lava": lava,
        "hardness": hardness, "base": base, "extra": extra, "extra_flyers": extra_flyers,
    }


WALKER = {"walker": (1, 1)}
BAT = {"bat": (1, 1)}

STAGES = [
    stage("İlk Adımlar", 20, "Platformlara zıpla, bayrağa ulaş!", items=""),
    stage("Kalp Avı", 30, "Kalp: +1 can verir"),
    stage("İlk Düşman", 35, "Düşmanın üstüne zıpla, yanına değme", walkers=WALKER),
    stage("Zıpla Zıpla", 40, "Yay: üstüne bas, yükseğe fırla", features="S", focus="S", walkers=WALKER),
    stage("Lav Geliyor!", 40, "Lav yükseliyor, acele et!", features="S", walkers=WALKER, lava=(240, 0.25, 0.32)),
    stage("Kayan Yollar", 45, "Mavi platform seni taşır", max_chunk=2, features="SM", focus="M", walkers=WALKER),
    stage("Gece Kanatları", 50, "Yarasa: onun da üstüne zıpla", max_chunk=2, features="SM", focus="F",
          walkers=WALKER, flyers=BAT, extra_flyers=(0.02, 0.04)),
    stage("Çatlak Taşlar", 50, "Çatlak taş kırılır, mıknatıs altın çeker", max_chunk=2, features="SMK",
          focus="K", walkers=WALKER, flyers=BAT, items="heart magnet", lava=(300, 0.25, 0.32), extra=(0.08, 0.1)),
    stage("Yapışkan Sümük", 55, "Sümük zıplar, inince üstüne bas", max_chunk=2, features="SMK", focus="E",
          walkers={"walker": (1, 1), "slime": (3, 3)}, flyers=BAT, items="heart magnet"),
    stage("Dikenli Yol", 60, "Kirpiye BASMA! Kalkan seni korur", max_chunk=2, features="SMK", focus="E",
          walkers={"walker": (2, 2), "slime": (1, 1), "spiky": (3, 3)}, flyers=BAT, items="heart magnet shield",
          lava=(240, 0.28, 0.36)),
    stage("Arı Kovanı", 65, "Arı aşağı yukarı uçar", max_chunk=2, features="SMK", focus="F",
          walkers={"walker": (2, 2), "slime": (1, 1), "spiky": (1, 1)}, flyers={"bat": (1, 1), "bee": (3, 3)},
          items="heart magnet shield", extra_flyers=(0.06, 0.1)),
    stage("Ateş Hattı", 65, "Topçu ateş atar, üstüne zıpla", max_chunk=2, features="SMK", focus="E",
          walkers={"walker": (1, 1), "slime": (1, 1), "spiky": (1, 1), "cannon": (3, 3)},
          flyers={"bat": (1, 1), "bee": (1, 1)}, items="heart magnet shield", lava=(240, 0.3, 0.38)),
    stage("Hepsi Bir Arada", 75, "Şimdi her şey bir arada!", max_chunk=2, features="SMK", focus="SMK",
          walkers=WALKER_KINDS, flyers=FLYER_KINDS, items="heart magnet shield", hardness=(0.2, 0.6),
          extra=(0.1, 0.14), extra_flyers=(0.03, 0.06)),
    stage("Kızgın Kaçış", 80, "Lav bu sefer daha hızlı!", max_chunk=2, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items="heart magnet shield", lava=(180, 0.35, 0.5), base="normal",
          hardness=(0.0, 0.3), extra=(0.08, 0.12), extra_flyers=(0.02, 0.05)),
    stage("Gök Merdiveni", 90, "Küçük platformlar geliyor", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items="heart magnet shield", base="normal", hardness=(0.2, 0.5),
          extra=(0.08, 0.12), extra_flyers=(0.02, 0.05)),
    stage("Ateş Çemberi", 100, "Lav ve topçular bir arada", max_chunk=3, features="SMK",
          walkers={"walker": (2, 2), "slime": (1, 1), "spiky": (1, 1), "cannon": (3, 3)}, flyers=FLYER_KINDS,
          items="heart magnet shield", lava=(180, 0.4, 0.6), base="normal", hardness=(0.3, 0.6),
          extra=(0.08, 0.13), extra_flyers=(0.03, 0.06)),
    stage("Düşman Ordusu", 110, "Her yer düşman dolu!", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items="heart magnet shield", base="normal", hardness=(0.4, 0.7),
          extra=(0.14, 0.2), extra_flyers=(0.05, 0.08)),
    stage("Lav Seli", 120, "Durmak yok!", max_chunk=3, features="SMK", walkers=WALKER_KINDS, flyers=FLYER_KINDS,
          items="heart magnet shield", lava=(120, 0.5, 0.75), base="normal", hardness=(0.5, 0.8),
          extra=(0.1, 0.15), extra_flyers=(0.03, 0.07)),
    stage("Son Hazırlık", 130, "Neredeyse zirvedesin", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items="heart magnet shield", base="normal", hardness=(0.6, 0.9),
          extra=(0.12, 0.17), extra_flyers=(0.05, 0.08)),
    stage("Zirve", 150, "Son bölüm: zirveye çık!", max_chunk=3, features="SMK", walkers=WALKER_KINDS,
          flyers=FLYER_KINDS, items="heart magnet shield", lava=(120, 0.55, 0.85), base="normal",
          hardness=(0.7, 1.0), extra=(0.12, 0.17), extra_flyers=(0.05, 0.08)),
]
# Her bölümün haritası sabit: seed bölümün sırasından gelir (harita beğenilmezse buradan değiştirilebilir)
for _index, _stage in enumerate(STAGES):
    _stage["seed"] = 1000 + _index


def stage_mode(stage):
    # Level ve Lava'nın kullandığı sayılar: zorluk modunun (base) sayıları + bölümün kendi sayıları
    mode = dict(DIFFICULTIES[stage["base"]])
    items = stage["items"]
    walker_chance = stage["extra"] if stage["walkers"] else (0, 0)
    flyer_chance = stage["extra_flyers"] if stage["flyers"] else (0, 0)
    mode.update(
        lives=STAGE_LIVES,
        max_lives=STAGE_LIVES,
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
        lava=stage["lava"] is not None,
    )
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
    for number, stage in enumerate(STAGES, 1):
        for side in "LR":
            if not allowed_chunks(stage, side):
                raise ValueError(f"{number}. bölümde girişi '{side}' olan uygun parça yok")
        for kinds, known in ((stage["walkers"], WALKER_KINDS), (stage["flyers"], FLYER_KINDS)):
            if any(kind not in known for kind in kinds):
                raise ValueError(f"{number}. bölümde bilinmeyen düşman türü: {list(kinds)}")


check_stages()
