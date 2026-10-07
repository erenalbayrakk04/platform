# Puan: tırmanılan yükseklik + altınlar + yenilen düşmanlar. Ekranın sol üstünde, kameradan
# bağımsız çizilir. Canlar (kalpler) sağ üstte.
import pygame

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
    LIFE_SIZE,
    LIFE_COLOR,
    LIFE_EMPTY_COLOR,
)


class Score:
    def __init__(self, start_y):
        # Karakterin ayaklarının başladığı yükseklik — yükseklik buna göre ölçülür
        self.start_y = start_y
        self.height = 0  # üstüne basılan en yüksek yer (blok sayısı)
        self.coins = 0  # toplanan altın sayısı
        self.enemies = 0  # üstüne basılıp yenilen düşman sayısı
        # None = pygame'in kendi yazı tipi
        self.font = pygame.font.Font(None, SCORE_FONT_SIZE)
        self.small_font = pygame.font.Font(None, SCORE_SMALL_FONT_SIZE)

    @property
    def total(self):
        return (
            self.height * HEIGHT_POINTS
            + self.coins * COIN_POINTS
            + self.enemies * ENEMY_POINTS
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

    def draw_text(self, screen, font, text, pos):
        # Önce 2 piksel kaydırılmış gölge, sonra asıl yazı — her zeminde okunsun
        shadow = font.render(text, True, SCORE_SHADOW_COLOR)
        screen.blit(shadow, (pos[0] + 2, pos[1] + 2))
        screen.blit(font.render(text, True, SCORE_COLOR), pos)

    def draw(self, screen):
        self.draw_text(screen, self.font, f"Puan: {self.total}", (12, 10))
        self.draw_text(
            screen, self.small_font, f"Yükseklik: {self.height}   Altın: {self.coins}", (12, 44)
        )


def make_heart(color):
    # Kalp: yan yana iki daire + altında aşağı bakan üçgen
    size = LIFE_SIZE
    r = size // 4
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(image, color, (r, r + 1), r + 1)
    pygame.draw.circle(image, color, (size - r - 1, r + 1), r + 1)
    pygame.draw.polygon(image, color, [(0, r + 2), (size - 1, r + 2), (size // 2, size - 1)])
    return image


HEART_IMAGES = {}


def draw_lives(screen, lives):
    # Sağ üstte PLAYER_LIVES kadar kalp: kalan canlar dolu, kaybedilenler gri
    if not HEART_IMAGES:  # ilk çizimde bir kere hazırla
        HEART_IMAGES["full"] = make_heart(LIFE_COLOR)
        HEART_IMAGES["empty"] = make_heart(LIFE_EMPTY_COLOR)
    for i in range(PLAYER_LIVES):
        image = HEART_IMAGES["full" if i < lives else "empty"]
        x = SCREEN_WIDTH - 12 - (PLAYER_LIVES - i) * (LIFE_SIZE + 6)
        screen.blit(image, (x, 14))
