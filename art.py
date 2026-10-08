# Piksel sanatı: tüm resimler burada harflerle "çizilir" (chunks.py'deki haritalar gibi).
# Her harf bir renk, '.' saydam. Her kare ekranda PIXEL_SCALE x PIXEL_SCALE piksel olur.
# Renkler settings.py'den gelir; açık/koyu tonlar o renklerden otomatik üretilir.
import random

import pygame

from settings import (
    PIXEL_SCALE,
    WHITE,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_COLOR,
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
    LIFE_COLOR,
    SPRING_COLOR,
    MOVING_PLATFORM_COLOR,
    CRUMBLE_COLOR,
    LIFE_EMPTY_COLOR,
    MAGNET_COLOR,
    SHIELD_COLOR,
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


# --- Karakter (sağa bakıyor) ---
PLAYER_BODY = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhhBBBK.",
    "KBhBBBBBBK",
    "KBBBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBBBBBK",
    "KbBBBBBBbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]
PLAYER_LEGS = {
    "idle": ["..KK..KK..", "..KK..KK.."],
    "walk1": ["..KK..KK..", ".KK....KK."],
    "walk2": ["...KK.KK..", "...KKKK..."],
    "jump": [".KK....KK.", ".........."],
}


def player_frames():
    palette = {
        "K": shade(PLAYER_COLOR, 0.3),
        "B": PLAYER_COLOR,
        "b": shade(PLAYER_COLOR, 0.75),
        "h": tint(PLAYER_COLOR, 0.5),
        "W": WHITE,
        "E": EYE_DARK,
    }
    size = (PLAYER_WIDTH, PLAYER_HEIGHT)
    return {
        name: facing_pair(render(PLAYER_BODY + legs, palette, size))
        for name, legs in PLAYER_LEGS.items()
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


def shield_bubble(radius):
    # Kalkan sürerken karakterin etrafındaki yarı saydam baloncuk
    image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    center = (radius, radius)
    pygame.draw.circle(image, (*SHIELD_COLOR, 50), center, radius)
    pygame.draw.circle(image, (*SHIELD_COLOR, 170), center, radius, 3)
    # Sol üstte küçük bir parlama
    pygame.draw.circle(image, (*WHITE, 150), (radius * 2 // 3, radius * 2 // 3), PIXEL_SCALE)
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
