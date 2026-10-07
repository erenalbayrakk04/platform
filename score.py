# Puan: tırmanılan yükseklik + altınlar + yenilen düşmanlar. Ekranın sol üstünde, kameradan
# bağımsız çizilir. Canlar (kalpler) sağ üstte. En yüksek skor bir dosyada saklanır.
import os

import pygame

from art import heart_images, magnet_image, shield_image
from settings import (
    TILE_SIZE,
    COIN_POINTS,
    ENEMY_POINTS,
    HEIGHT_POINTS,
    SCORE_COLOR,
    SCORE_SHADOW_COLOR,
    SCORE_FONT_SIZE,
    SCORE_SMALL_FONT_SIZE,
    SCREEN_WIDTH,
    PLAYER_LIVES,
    HIGHSCORE_FILE,
    HIGHSCORE_KEY,
    WEB,
    POWERUP_WARN_TIME,
)


class Score:
    def __init__(self, start_y):
        # Karakterin ayaklarının başladığı yükseklik — yükseklik buna göre ölçülür
        self.start_y = start_y
        self.height = 0  # üstüne basılan en yüksek yer (blok sayısı)
        self.coins = 0  # toplanan altın sayısı
        self.enemies = 0  # üstüne basılıp yenilen düşman sayısı
        self.bonus = 0  # diğer puanlar (ör. canın doluyken alınan kalp)
        # None = pygame'in kendi yazı tipi
        self.font = pygame.font.Font(None, SCORE_FONT_SIZE)
        self.small_font = pygame.font.Font(None, SCORE_SMALL_FONT_SIZE)

    @property
    def total(self):
        return (
            self.height * HEIGHT_POINTS
            + self.coins * COIN_POINTS
            + self.enemies * ENEMY_POINTS
            + self.bonus
        )

    def update(self, player):
        # Sadece üstüne bastığı yer sayılır (havada zıplamak puan vermesin);
        # aşağı düşünce puan azalmaz, en yükseği hatırlanır
        if player.on_ground:
            climbed = (self.start_y - player.rect.bottom) // TILE_SIZE
            self.height = max(self.height, climbed)

    def add_coin(self):
        self.coins += 1

    def add_enemy(self):
        self.enemies += 1

    def add_bonus(self, points):
        self.bonus += points

    def draw(self, screen):
        draw_text(screen, self.font, f"Puan: {self.total}", topleft=(12, 10))
        draw_text(
            screen, self.small_font, f"Yükseklik: {self.height}   Altın: {self.coins}", topleft=(12, 44)
        )


def draw_text(screen, font, text, color=SCORE_COLOR, **position):
    # Gölgeli yazı: önce 2 piksel kaydırılmış gölge, sonra asıl yazı — her zeminde okunsun.
    # Konum rect gibi verilir: topleft=(x, y) veya center=(x, y) vb.
    image = font.render(text, True, color)
    rect = image.get_rect(**position)
    screen.blit(font.render(text, True, SCORE_SHADOW_COLOR), rect.move(2, 2))
    screen.blit(image, rect)


def high_score_path():
    # Dosya, oyunun klasöründe dursun (oyun nereden çalıştırılırsa çalıştırılsın)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), HIGHSCORE_FILE)


# Tarayıcıda dosyaya yazılan şey sayfa kapanınca kaybolur; orada rekor tarayıcının kendi
# hafızasında (localStorage) saklanır. pygbag, tarayıcıya platform.window ile eriştirir.


def load_high_score():
    # Kayıt yoksa veya bozuksa en yüksek skor 0
    try:
        if WEB:
            from platform import window

            return int(window.localStorage.getItem(HIGHSCORE_KEY) or 0)
        with open(high_score_path(), encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_high_score(value):
    try:
        if WEB:
            from platform import window

            window.localStorage.setItem(HIGHSCORE_KEY, str(value))
            return
        with open(high_score_path(), "w", encoding="utf-8") as f:
            f.write(str(value))
    except Exception:
        pass  # kaydedilemese de oyun çalışmaya devam etsin


HEART_IMAGES = {}


def draw_lives(screen, lives):
    # Sağ üstte PLAYER_LIVES kadar kalp: kalan canlar dolu, kaybedilenler gri
    if not HEART_IMAGES:  # ilk çizimde bir kere hazırla
        HEART_IMAGES.update(heart_images())
    width = HEART_IMAGES["full"].get_width() + 6
    for i in range(PLAYER_LIVES):
        image = HEART_IMAGES["full" if i < lives else "empty"]
        screen.blit(image, (SCREEN_WIDTH - 12 - (PLAYER_LIVES - i) * width, 14))


POWER_ICONS = {}


def draw_powers(screen, player):
    # Kalplerin altında süren güçlendirmeler: simge + altında kalan süre çubuğu (sağdan sola dizilir).
    # Bitmesine az kalınca simge yanıp söner
    if not POWER_ICONS:
        POWER_ICONS.update(magnet=magnet_image(), shield=shield_image())
    right = SCREEN_WIDTH - 12
    for kind, left in player.powers.items():
        if not left:
            continue
        icon = POWER_ICONS[kind]
        rect = icon.get_rect(bottomright=(right, 80))  # simgeler alta hizalı, çubuklar aynı hizada
        if left > POWERUP_WARN_TIME or (left // 8) % 2 == 0:
            screen.blit(icon, rect)
        bar = pygame.Rect(rect.left, rect.bottom + 4, rect.width, 4)
        screen.fill(SCORE_SHADOW_COLOR, bar)  # boş çubuk
        bar.width = round(bar.width * player.power_fraction(kind))
        screen.fill(SCORE_COLOR, bar)
        right = rect.left - 10
