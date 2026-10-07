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
    LIFE_COLOR,
    LIFE_EMPTY_COLOR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SKY_TOP_COLOR,
    SKY_BOTTOM_COLOR,
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


# --- Arka plan: renk geçişli gökyüzü + yavaş kayan yıldızlar ---
class Background:
    def __init__(self):
        # Üstten alta yumuşak renk geçişi (bir kere hazırlanır)
        self.sky = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / (SCREEN_HEIGHT - 1)
            color = [round(a + (b - a) * t) for a, b in zip(SKY_TOP_COLOR, SKY_BOTTOM_COLOR)]
            pygame.draw.line(self.sky, color, (0, y), (SCREEN_WIDTH, y))
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
        screen.blit(self.sky, (0, 0))
        # Kamera yukarı çıktıkça yıldızlar daha yavaş aşağı kayar; ekrandan çıkan üstten geri gelir
        shift = -camera_top * STAR_PARALLAX
        for x, y, size, color in self.stars:
            screen.fill(color, (x, (y + shift) % SCREEN_HEIGHT, size, size))
