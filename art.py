# Piksel sanatı: tüm resimler burada harflerle "çizilir" (chunks.py'deki haritalar gibi).
# Her harf bir renk, '.' saydam. Her kare ekranda PIXEL_SCALE x PIXEL_SCALE piksel olur.
# Renkler settings.py'den gelir; açık/koyu tonlar o renklerden otomatik üretilir.
import math
import random

import pygame

from settings import (
    AD_COLOR,
    PIXEL_SCALE,
    LOGO_PIXEL,
    LOGO_OUTLINE_COLOR,
    WHITE,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    TILE_SIZE,
    TILE_COLOR,
    TILE_TOP_COLOR,
    PLATFORM_HEIGHT,
    PLATFORM_COLOR,
    COIN_SIZE,
    COIN_COLOR,
    COIN_EDGE_COLOR,
    ENEMY_WIDTH,
    ENEMY_HEIGHT,
    ENEMY_COLOR,
    ENEMY_EYE_COLOR,
    FLYER_COLOR,
    SLIME_COLOR,
    SPIKY_COLOR,
    CANNON_COLOR,
    FIREBALL_COLOR,
    BEE_COLOR,
    LIFE_COLOR,
    SPRING_COLOR,
    MOVING_PLATFORM_COLOR,
    CRUMBLE_COLOR,
    LIFE_EMPTY_COLOR,
    MAGNET_COLOR,
    SHIELD_COLOR,
    GEM_COLOR,
    FLAG_COLOR,
    STAR_COLOR,
    STAR_EMPTY_COLOR,
    LAVA_COLOR,
    LAVA_TOP_COLOR,
    LAVA_GLOW_COLOR,
    LAVA_WARN_DISTANCE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SKY_THEMES,
    SKY_CHANGE_HEIGHT,
    SKY_BLEND_HEIGHT,
    STAR_COUNT,
    STAR_PARALLAX,
)

EYE_DARK = (25, 25, 40)


def shade(color, amount):
    # Rengi koyulaştır (amount 0-1: 0 = siyah, 1 = aynı renk)
    return tuple(int(c * amount) for c in color)


def tint(color, amount):
    # Rengi açıklaştır (amount 0-1: 0 = aynı renk, 1 = beyaz)
    return tuple(int(c + (255 - c) * amount) for c in color)


def mix(color, other, amount):
    # İki rengin arası (amount 0-1: 0 = ilk renk, 1 = ikinci renk)
    return tuple(round(a + (b - a) * amount) for a, b in zip(color, other))


def render(rows, palette, size=None):
    # Harf haritasından resim yap. size verilirse resim o boyda olur, çizim alta ve ortaya yaslanır.
    width = len(rows[0]) * PIXEL_SCALE
    height = len(rows) * PIXEL_SCALE
    size = size or (width, height)
    image = pygame.Surface(size, pygame.SRCALPHA)
    left = (size[0] - width) // 2
    top = size[1] - height
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell != ".":
                rect = (left + c * PIXEL_SCALE, top + r * PIXEL_SCALE, PIXEL_SCALE, PIXEL_SCALE)
                image.fill(palette[cell], rect)
    # Hiç saydam yeri olmayan resim (blok, platform) saydamlık hesabı yapılmadan çizilsin: tarayıcıda
    # ~5 kat hızlı. convert() ancak ekran açıkken çalışır (check_chunks.py ekransız çalışır)
    opaque = size == (width, height) and not any("." in row for row in rows)
    if opaque and pygame.display.get_surface():
        image = image.convert()
    return image


def facing_pair(image):
    # Sağa bakan resimden sola bakanı üret (aynalama)
    return {1: image, -1: pygame.transform.flip(image, True, False)}


# --- Karakter (sağa bakıyor): gövdesi ve renkleri seçili skinden (skins.py), bacaklar çoğunda bunlar ---
PLAYER_LEGS = {
    "idle": ["..LL..LL..", "..LL..LL.."],
    "walk1": ["..LL..LL..", ".LL....LL."],
    "walk2": ["...LL.LL..", "...LLLL..."],
    "jump": [".LL....LL.", ".........."],
}


def player_frames(skin):
    # skin = skins.py'deki bir skin. Resimler: "idle" duruyor, "walk1"/"walk2" yürüyor, "jump" havada; {1: sağa, -1: sola}
    palette = {"W": WHITE, "E": EYE_DARK, **skin["palette"]}
    palette.setdefault("L", palette["K"])  # bacaklar verilmezse dış çizgi renginde
    size = (PLAYER_WIDTH, PLAYER_HEIGHT)
    return {
        name: facing_pair(render(skin["body"] + legs, palette, size))
        for name, legs in (skin["legs"] or PLAYER_LEGS).items()
    }


# --- Düşman (sağa bakıyor): iki resim arasında zıplar gibi kıpırdar ---
ENEMY_ROWS = [
    [
        "..KKKK..",
        ".KRRRRK.",
        "KRhRRRRK",
        "KRWERWEK",
        "KRRRRRRK",
        "KrRRRRrK",
        ".KK..KK.",
    ],
    [
        "........",
        ".KKKKKK.",
        "KRhRRRRK",
        "KRWERWEK",
        "KRRRRRRK",
        "KrrRRrrK",
        "KK.KK.KK",
    ],
]


def enemy_frames():
    palette = {
        "K": shade(ENEMY_COLOR, 0.3),
        "R": ENEMY_COLOR,
        "r": shade(ENEMY_COLOR, 0.7),
        "h": tint(ENEMY_COLOR, 0.5),
        "W": ENEMY_EYE_COLOR,
        "E": EYE_DARK,
    }
    size = (ENEMY_WIDTH, ENEMY_HEIGHT)
    return [facing_pair(render(rows, palette, size)) for rows in ENEMY_ROWS]


# --- Uçan düşman (yarasa, önden): kanatlar yukarıda ve aşağıda ---
FLYER_ROWS = [
    [
        "w........w",
        "ww.K..K.ww",
        "wwwKKKKwww",
        "wwKBBBBKww",
        ".KBYBBYBK.",
        "..KBhBBK..",
        "...KKKK...",
    ],
    [
        "..........",
        "...K..K...",
        "...KKKK...",
        "..KBBBBK..",
        "wKBYBBYBKw",
        "wwKBhBBKww",
        "ww.KKKK.ww",
    ],
]


def flyer_frames():
    palette = {
        "K": shade(FLYER_COLOR, 0.3),
        "B": FLYER_COLOR,
        "h": tint(FLYER_COLOR, 0.4),
        "w": shade(FLYER_COLOR, 0.6),
        "Y": (255, 230, 90),  # parlayan gözler
    }
    return [render(rows, palette) for rows in FLYER_ROWS]


# --- Zıplayan sümük (sağa bakıyor): iki yürüme resmi, zıplamadan önce basık, havada uzamış ---
SLIME_ROWS = {
    "walk1": [
        "..KKKK..",
        ".KGhGGK.",
        "KGhGGGGK",
        "KGWEGWEK",
        "KGGGGGGK",
        "KgGGGGgK",
        ".KKKKKK.",
    ],
    "walk2": [
        "........",
        ".KKKKKK.",
        "KGhGGGGK",
        "KGWEGWEK",
        "KGGGGGGK",
        "KgGGGGgK",
        "KKKKKKKK",
    ],
    "squash": [
        ".KKKKKK.",
        "KGhGGGGK",
        "KGWEGWEK",
        "KgGGGGgK",
        "KKKKKKKK",
    ],
    "jump": [
        "..KKKK..",
        ".KGhGGK.",
        ".KhGGGK.",
        ".KWEWEK.",
        ".KGGGGK.",
        ".KgGGgK.",
        "..KKKK..",
    ],
}


def slime_frames():
    palette = {
        "K": shade(SLIME_COLOR, 0.3),
        "G": SLIME_COLOR,
        "g": shade(SLIME_COLOR, 0.75),
        "h": tint(SLIME_COLOR, 0.6),
        "W": WHITE,
        "E": EYE_DARK,
    }
    size = (ENEMY_WIDTH, ENEMY_HEIGHT)
    return {name: facing_pair(render(rows, palette, size)) for name, rows in SLIME_ROWS.items()}


# --- Dikenli kirpi (sağa bakıyor): sırtında açık renkli dikenler, iki yürüme resmi ---
SPIKY_BODY = [
    ".s.s.s..",
    "sKsKsKF.",
    "KSSSSFEF",
    "sSSSSFFN",
    "KSSSSFF.",
    "sKSSSKK.",
]
SPIKY_LEGS = [".K...K..", "..K.K..."]


def spiky_frames():
    palette = {
        "s": tint(SPIKY_COLOR, 0.8),  # diken uçları
        "S": SPIKY_COLOR,
        "K": shade(SPIKY_COLOR, 0.45),
        "F": (240, 205, 160),  # yüz
        "E": EYE_DARK,
        "N": EYE_DARK,  # burun
    }
    size = (ENEMY_WIDTH, ENEMY_HEIGHT)
    return [facing_pair(render(SPIKY_BODY + [legs], palette, size)) for legs in SPIKY_LEGS]


# --- Topçu (sağa bakıyor): gözü olan yuvarlak top. Ateş etmeden önce namlunun ağzı kızarır ---
CANNON_ROWS = [
    "..KKK...",
    ".KGhGK..",
    "KGWEGKKK",
    "KGGGGGGM",
    "KGGGGGGM",
    "KGGGGKKK",
    ".KwwK...",
]
CANNON_MUZZLE_Y = 4 * PIXEL_SCALE  # namlu (M) 3. ve 4. satırda; ortası tepeden bu kadar aşağıda (ateş topu çıkar)


def cannon_frames():
    # [normal, kızarmış] — her biri {1: sağa, -1: sola}
    images = []
    for glow in (False, True):
        palette = {
            "K": shade(CANNON_COLOR, 0.35),
            "G": tint(CANNON_COLOR, 0.25) if glow else CANNON_COLOR,
            "h": tint(CANNON_COLOR, 0.55),
            "M": FIREBALL_COLOR if glow else EYE_DARK,  # namlunun ağzı
            "W": (255, 220, 120) if glow else WHITE,
            "E": EYE_DARK,
            "w": (60, 60, 70),  # tekerlekler
        }
        images.append(facing_pair(render(CANNON_ROWS, palette, (ENEMY_WIDTH, ENEMY_HEIGHT))))
    return images


# --- Ateş topu: iki resim arasında titreşir ---
FIREBALL_ROWS = [
    [".OO.", "OYYO", "OYYO", ".OO."],
    [".RO.", "OYYR", "RYYO", ".OR."],
]


def fireball_frames():
    palette = {
        "Y": tint(FIREBALL_COLOR, 0.7),  # parlak orta
        "O": FIREBALL_COLOR,
        "R": shade(FIREBALL_COLOR, 0.75),
    }
    return [render(rows, palette) for rows in FIREBALL_ROWS]


# --- Arı (yandan, sağa bakıyor): çizgili gövde, arkada iğne, kanat çırpar ---
BEE_BODY = [
    "..KKKKKK.",
    ".KYKYKYYK",
    "SKYKYKYEK",
    ".KYKYKYYK",
    "..KKKKKK.",
]
BEE_WINGS = [
    ["...ww.ww.", "..wwwwww."],
    [".........", "...wwwww."],
]


def bee_frames():
    palette = {
        "Y": BEE_COLOR,
        "K": (40, 30, 20),
        "S": (40, 30, 20),  # iğne
        "E": WHITE,
        "w": (225, 240, 255),  # saydamımsı kanatlar
    }
    return [facing_pair(render(wings + BEE_BODY, palette)) for wings in BEE_WINGS]


# --- Altın: dönüyormuş gibi daralıp genişler ---
COIN_ROWS = [
    [".KKK.", "KYhYK", "KYYYK", "KYyYK", ".KKK."],
    ["..K..", ".KhK.", ".KYK.", ".KyK.", "..K.."],
    ["..K..", "..K..", "..K..", "..K..", "..K.."],
]


def coin_frames():
    palette = {
        "K": COIN_EDGE_COLOR,
        "Y": COIN_COLOR,
        "y": shade(COIN_COLOR, 0.85),
        "h": tint(COIN_COLOR, 0.7),
    }
    full, half, thin = (render(rows, palette, (COIN_SIZE, COIN_SIZE)) for rows in COIN_ROWS)
    return [full, half, thin, half]


# --- Yay: normal ve basık hali ---
SPRING_ROWS = [
    ["hGGGGh", ".k..k.", "..kk..", "KKKKKK"],
    ["hGGGGh", "KKKKKK"],
]
SPRING_SIZE = (24, 16)


def spring_frames():
    palette = {
        "G": SPRING_COLOR,
        "h": tint(SPRING_COLOR, 0.5),
        "k": (170, 170, 190),
        "K": (90, 90, 110),
    }
    return [render(rows, palette, SPRING_SIZE) for rows in SPRING_ROWS]


# --- Blok: üstü çimen, altı toprak ---
TILE_ROWS = [
    "GGGGGGGGGG",
    "GGgGGGGgGG",
    "gDgDDgDDgD",
    "DDDDDDDDDD",
    "DDdDDDDsDD",
    "DDDDDDDDDD",
    "DsDDDdDDDD",
    "DDDDDDDDdD",
    "DDdDDDsDDD",
    "dddddddddd",
]


def tile_image():
    palette = {
        "G": TILE_TOP_COLOR,
        "g": shade(TILE_TOP_COLOR, 0.7),
        "D": TILE_COLOR,
        "d": shade(TILE_COLOR, 0.7),
        "s": tint(TILE_COLOR, 0.25),
    }
    return render(TILE_ROWS, palette, (TILE_SIZE, TILE_SIZE))


# --- İnce platform: tahta ---
PLATFORM_ROWS = ["hhhhhhhhhh", "WWWwWWWWWk", "kkkkkkkkkk"]


def platform_image():
    palette = {
        "h": tint(PLATFORM_COLOR, 0.3),
        "W": PLATFORM_COLOR,
        "w": shade(PLATFORM_COLOR, 0.8),
        "k": shade(PLATFORM_COLOR, 0.5),
    }
    return render(PLATFORM_ROWS, palette, (TILE_SIZE, PLATFORM_HEIGHT))


# --- Uçan adacık (giriş ekranı): üstü çimen, altı sivrilen toprak (renkleri blokla aynı) ---
ISLAND_ROWS = [
    "GGGGGGGGGGGGGGGGGGGGGGGG",
    "GGgGGGGGgGGGGGGgGGGGGgGG",
    "gDgDDgDDgDDgDgDDgDDgDDgD",
    "DDDDDDsDDDDDDDDDDDDdDDDD",
    ".DdDDDDDDDDDdDDDsDDDDDD.",
    ".DDDDsDDDDDDDDDDDDDDdDD.",
    "..dDDDDDDDdDDDDDsDDDDd..",
    "...DDDDsDDDDDDDDDDDDD...",
    ".....dDDDDDDDDdDDDd.....",
    ".......ddDDsDDDdd.......",
    ".........dddddd.........",
    "...........dd...........",
]


def island_image():
    palette = {
        "G": TILE_TOP_COLOR,
        "g": shade(TILE_TOP_COLOR, 0.7),
        "D": TILE_COLOR,
        "d": shade(TILE_COLOR, 0.7),
        "s": tint(TILE_COLOR, 0.25),
    }
    return render(ISLAND_ROWS, palette)


# --- Kırılan platform: çatlak taş; ikinci resim kırılmak üzereyken (çatlaklar büyür), üçüncüsü silik ---
CRUMBLE_ROWS = [
    ["hhhhhhhhhh", "WWkWWWWkWW", "kkWkkkkWkk"],
    ["hhkhhhhkhh", "WkkWWWkkWW", "kkWkk.kWk."],
]


def crumble_frames():
    palette = {
        "h": tint(CRUMBLE_COLOR, 0.35),
        "W": CRUMBLE_COLOR,
        "k": shade(CRUMBLE_COLOR, 0.45),
    }
    whole, cracked = (render(rows, palette, (TILE_SIZE, PLATFORM_HEIGHT)) for rows in CRUMBLE_ROWS)
    ghost = whole.copy()  # geri gelmeden az önce görünen silik hali
    ghost.set_alpha(70)
    return [whole, cracked, ghost]


# --- Hareketli platform: perçinli mavi metal, kaç kare genişse o kadar tekrar edilir ---
MOVING_PLATFORM_ROWS = ["hhhhhhhhhh", "WkWWWWWWkW", "kkkkkkkkkk"]


def moving_platform_image(cells):
    palette = {
        "h": tint(MOVING_PLATFORM_COLOR, 0.4),
        "W": MOVING_PLATFORM_COLOR,
        "k": shade(MOVING_PLATFORM_COLOR, 0.5),
    }
    rows = [row * cells for row in MOVING_PLATFORM_ROWS]
    return render(rows, palette, (TILE_SIZE * cells, PLATFORM_HEIGHT))


# --- Kalp (can göstergesi) ---
HEART_ROWS = [
    ".HH.HH.",
    "HhHHHHH",
    "HHHHHHH",
    ".HHHHH.",
    "..HHH..",
    "...H...",
]


def heart_image(color):
    return render(HEART_ROWS, {"H": color, "h": tint(color, 0.6)})


def heart_images():
    return {"full": heart_image(LIFE_COLOR), "empty": heart_image(LIFE_EMPTY_COLOR)}


# --- Güçlendirmeler ---
MAGNET_ROWS = [
    "WW...WW",
    "ww...ww",
    "Rh...hR",
    "RR...RR",
    "RRr.rRR",
    ".RRRRr.",
    "..rrr..",
]


def magnet_image():
    palette = {
        "W": (230, 230, 240),  # gümüş uçlar
        "w": (160, 160, 180),
        "R": MAGNET_COLOR,
        "r": shade(MAGNET_COLOR, 0.65),
        "h": tint(MAGNET_COLOR, 0.5),
    }
    return render(MAGNET_ROWS, palette)


SHIELD_ROWS = [
    ".KKKKK.",
    "KhhSSSK",
    "KhSSSSK",
    "KSSWSSK",
    "KSSSSSK",
    ".KSSSK.",
    "..KSK..",
    "...K...",
]


def shield_image():
    palette = {
        "K": shade(SHIELD_COLOR, 0.35),
        "S": SHIELD_COLOR,
        "h": tint(SHIELD_COLOR, 0.5),
        "W": WHITE,
    }
    return render(SHIELD_ROWS, palette)


# --- Elmas (skin parası): ışıltısı iki resim arasında kayar ---
GEM_ROWS = [
    [
        ".KKKKK.",
        "KWhhBbK",
        "KhBBBbK",
        ".KBBbK.",
        "..KbK..",
        "...K...",
    ],
    [
        ".KKKKK.",
        "KhBhWbK",
        "KBBhBbK",
        ".KBhbK.",
        "..KbK..",
        "...K...",
    ],
]


def gem_frames():
    palette = {
        "K": shade(GEM_COLOR, 0.4),
        "B": GEM_COLOR,
        "b": shade(GEM_COLOR, 0.75),
        "h": tint(GEM_COLOR, 0.55),
        "W": WHITE,
    }
    return [render(rows, palette) for rows in GEM_ROWS]


def shield_bubble(radius):
    # Kalkan sürerken karakterin etrafındaki yarı saydam baloncuk
    image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    center = (radius, radius)
    pygame.draw.circle(image, (*SHIELD_COLOR, 50), center, radius)
    pygame.draw.circle(image, (*SHIELD_COLOR, 170), center, radius, 3)
    # Sol üstte küçük bir parlama
    pygame.draw.circle(image, (*WHITE, 150), (radius * 2 // 3, radius * 2 // 3), PIXEL_SCALE)
    return image


# --- Bölüm modu: bitiş bayrağı, yıldız, kilit ---
FLAG_SIZE = (10, 20)  # bayrağın resmi (kare): direk + bez
FLAG_CLOTH = 6  # bezin yüksekliği (kare)


def flag_frames(count=4):
    # Direğin tepesinde altın top, yeşil-beyaz damalı bez dalgalanır (count resim); dipte taş ayak
    palette = {
        "Y": COIN_COLOR, "y": COIN_EDGE_COLOR, "P": (225, 225, 235), "B": (90, 90, 110),
        "G": FLAG_COLOR, "g": shade(FLAG_COLOR, 0.7), "W": WHITE, "w": (190, 190, 205),
    }
    width, height = FLAG_SIZE
    frames = []
    for frame in range(count):
        grid = [["."] * width for _ in range(height)]
        grid[0][1] = "Y"
        grid[1][0:3] = ["Y", "Y", "y"]
        for r in range(2, height):
            grid[r][1] = "P"
        grid[height - 1][0:3] = ["B", "B", "B"]
        for c in range(2, width):
            # Dalga direkten uzaklaştıkça başlar; geriye doğru kıvrılan yer biraz koyu
            wave = math.sin((c - 2) / 2.2 - frame * math.pi / 2)
            offset = round(wave) if c > 3 else 0
            for k in range(FLAG_CLOTH):
                letter = "G" if ((c - 2) // 2 + k // 2) % 2 else "W"
                grid[2 + offset + k][c] = letter.lower() if wave < -0.3 else letter
        frames.append(render(["".join(row) for row in grid], palette))
    return frames


STAR_ROWS = [
    "....S....",
    "...ShS...",
    "...ShS...",
    "SSSShSSSS",
    ".SSSSSSS.",
    "..SSSSS..",
    "..SSSSS..",
    ".SSS.SSS.",
    ".SS...SS.",
]


def star_image(filled=True, size=None):
    # Kazanılan (sarı) ya da kazanılmayan (gri) yıldız; size verilirse o boya küçültülür (piksel)
    color = STAR_COLOR if filled else STAR_EMPTY_COLOR
    image = render(STAR_ROWS, {"S": color, "h": tint(color, 0.5)})
    if size:
        image = pygame.transform.scale(image, (size, size))
    return image


LOCK_ROWS = [
    "..kkk..",
    ".k...k.",
    ".k...k.",
    "LLLLLLL",
    "LLLdLLL",
    "LLLdLLL",
    "lllllll",
]


def lock_image():
    # Kilitli bölümün üstündeki asma kilit
    body = (170, 170, 190)
    return render(LOCK_ROWS, {"k": (210, 210, 225), "L": body, "l": shade(body, 0.7), "d": EYE_DARK})


AD_ROWS = [
    ".YYYYYY.",
    "YYdYYYYY",
    "YYddYYYY",
    "YYdddYYY",
    "YYddYYYY",
    "YYdYYYYY",
    ".yyyyyy.",
]


def ad_image():
    # Reklam düğmelerindeki ▶ (video) işareti: oyuncu düğmenin reklam açtığını bilsin
    return render(AD_ROWS, {"Y": AD_COLOR, "y": shade(AD_COLOR, 0.7), "d": EYE_DARK})


LAVA_WAVE_ROWS = 8  # dalga şeridinin yüksekliği (piksel sanatı karesi)
LAVA_WAVE_LENGTH = 25  # bir dalganın genişliği (kare)


def lava_frames(count=8):
    # Lavın üst kenarı: yana kayan dalgalar. Her resimde dalga biraz ilerler; sırayla gösterilince akar.
    # Tepeler 0-3. satır arasında oynar; altı düz lav rengi (main.py'de altı ayrıca doldurulur)
    palette = {"Y": LAVA_TOP_COLOR, "y": tint(LAVA_COLOR, 0.45), "O": LAVA_COLOR}
    cols = SCREEN_WIDTH // PIXEL_SCALE
    frames = []
    for f in range(count):
        phase = 2 * math.pi * f / count
        crests = [round(1.5 + 1.5 * math.sin(2 * math.pi * c / LAVA_WAVE_LENGTH + phase)) for c in range(cols)]
        rows = []
        for r in range(LAVA_WAVE_ROWS):
            row = ""
            for crest in crests:
                row += "." if r < crest else "Y" if r == crest else "y" if r == crest + 1 else "O"
            rows.append(row)
        frames.append(render(rows, palette))
    return frames


def lava_glow():
    # Lav ekranın hemen altındayken ekranın dibinde beliren kızıllık (aşağıya doğru koyulaşır)
    image = pygame.Surface((SCREEN_WIDTH, LAVA_WARN_DISTANCE // 3), pygame.SRCALPHA)
    height = image.get_height()
    for y in range(height):
        alpha = round(140 * (y / (height - 1)) ** 2)
        pygame.draw.line(image, (*LAVA_GLOW_COLOR, alpha), (0, y), (SCREEN_WIDTH, y))
    return image


def sky_image(top_color, bottom_color):
    # Üstten alta yumuşak renk geçişi
    sky = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for y in range(SCREEN_HEIGHT):
        t = y / (SCREEN_HEIGHT - 1)
        color = [round(a + (b - a) * t) for a, b in zip(top_color, bottom_color)]
        pygame.draw.line(sky, color, (0, y), (SCREEN_WIDTH, y))
    return sky


# --- Arka plan: yükseldikçe rengi değişen gökyüzü + yavaş kayan yıldızlar ---
class Background:
    def __init__(self):
        # Her renk teması için gökyüzü bir kere hazırlanır
        self.skies = [sky_image(top, bottom) for top, bottom in SKY_THEMES]
        # Yıldızlar: hep aynı yerlerde olsun diye sabit sayıyla rastgele
        rng = random.Random(7)
        self.stars = [
            (
                rng.randrange(SCREEN_WIDTH),
                rng.randrange(SCREEN_HEIGHT),
                rng.choice((1, 2, 2, 3)),  # boyu
                rng.choice(((120, 120, 160), (180, 180, 220), (255, 255, 255))),
            )
            for _ in range(STAR_COUNT)
        ]

    def draw(self, screen, camera_top):
        # Ne kadar yükseldik → hangi gökyüzü; geçiş bölgesinde sıradaki gökyüzü yavaşça belirir
        height = max(0, -camera_top)
        index = int(height // SKY_CHANGE_HEIGHT)
        into = height % SKY_CHANGE_HEIGHT
        blend = (into - (SKY_CHANGE_HEIGHT - SKY_BLEND_HEIGHT)) / SKY_BLEND_HEIGHT
        screen.blit(self.skies[index % len(self.skies)], (0, 0))
        if blend > 0:
            next_sky = self.skies[(index + 1) % len(self.skies)]
            next_sky.set_alpha(round(blend * 255))  # 0 = görünmez, 255 = tam
            screen.blit(next_sky, (0, 0))
            next_sky.set_alpha(None)
        # Kamera yukarı çıktıkça yıldızlar daha yavaş aşağı kayar; ekrandan çıkan üstten geri gelir
        shift = -camera_top * STAR_PARALLAX
        for x, y, size, color in self.stars:
            screen.fill(color, (x, (y + shift) % SCREEN_HEIGHT, size, size))


# --- Oyunun adı (giriş ekranı ve ana menüdeki logo): kalın piksel harfler ---
# Her harfin çizgisi 2 kare kalın. Oyunun adı (settings.TITLE) değişirse eksik harfler buraya eklenmeli
LOGO_FONT = {
    "A": [".####.", "######", "##..##", "##..##", "######", "######", "##..##", "##..##"],
    "F": ["######", "######", "##....", "#####.", "#####.", "##....", "##....", "##...."],
    "L": ["##....", "##....", "##....", "##....", "##....", "##....", "######", "######"],
    "M": ["##...##", "###.###", "#######", "##.#.##", "##...##", "##...##", "##...##", "##...##"],
    "N": ["##...##", "###..##", "####.##", "##.####", "##..###", "##...##", "##...##", "##...##"],
    "O": [".####.", "######", "##..##", "##..##", "##..##", "##..##", "######", ".####."],
    "P": ["#####.", "######", "##..##", "##..##", "######", "#####.", "##....", "##...."],
    "R": ["#####.", "######", "##..##", "##..##", "#####.", "####..", "##.##.", "##..##"],
    "T": ["######", "######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
    "U": ["##..##", "##..##", "##..##", "##..##", "##..##", "##..##", "######", ".####."],
    "Y": ["##..##", "##..##", "##..##", "######", ".####.", "..##..", "..##..", "..##.."],
}
LOGO_DEPTH = 2  # harflerin altındaki kalınlık (3B görünüm), ince kare
LOGO_SPACING = 2  # harfler arası boşluk, ince kare (harflerin koyu kenarları tam birbirine değer)


def logo_letters(text, top_color, bottom_color):
    # Yazının her harfi ayrı resim (ekranda tek tek dalgalanabilsinler). Harf haritasındaki her kare 2x2
    # "ince kareye" bölünür (her ince kare LOGO_PIXEL piksel): koyu kenar çizgisi ve alttaki kalınlık harften
    # ince olur. İçi yukarıdan aşağı top_color'dan bottom_color'a geçer, çizgilerin üst kenarı parlak.
    # Döner: [(resim, parıltı, x)] — parıltı = harfin içi beyaz ve yarı saydam (üstünden ışık geçerken),
    # x = harfin yazıdaki yeri (piksel)
    size = LOGO_PIXEL
    depth_color = shade(bottom_color, 0.5)
    letters = []
    x = 0
    for char in text:
        if char not in LOGO_FONT:
            raise ValueError(f"Logo yazı tipinde '{char}' harfi yok (art.py, LOGO_FONT)")
        fine = ["".join(cell * 2 for cell in row) for row in LOGO_FONT[char] for _ in range(2)]
        height = len(fine)
        # Harfin kareleri (kenar çizgisine yer kalsın diye 1 kare içeriden), altındaki kalınlık, çevresindeki kenar
        fill = {(r + 1, c + 1) for r, row in enumerate(fine) for c, cell in enumerate(row) if cell == "#"}
        depth = {(r + d, c) for r, c in fill for d in range(1, LOGO_DEPTH + 1)} - fill
        body = fill | depth
        outline = {(r + dr, c + dc) for r, c in body for dr in (-1, 0, 1) for dc in (-1, 0, 1)} - body
        image_size = ((len(fine[0]) + 2) * size, (height + 2 + LOGO_DEPTH) * size)
        image = pygame.Surface(image_size, pygame.SRCALPHA)
        shine = pygame.Surface(image_size, pygame.SRCALPHA)
        for cells, color in ((outline, LOGO_OUTLINE_COLOR), (depth, depth_color)):
            for r, c in cells:
                image.fill(color, (c * size, r * size, size, size))
        for r, c in fill:
            color = mix(top_color, bottom_color, (r - 1) / (height - 1))
            if (r - 1, c) not in fill:  # çizginin üst kenarı
                color = tint(color, 0.5)
            image.fill(color, (c * size, r * size, size, size))
            shine.fill((*WHITE, 150), (c * size, r * size, size, size))
        letters.append((image, shine, x))
        x += (len(fine[0]) + LOGO_SPACING) * size
    return letters
