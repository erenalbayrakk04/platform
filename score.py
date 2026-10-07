# Puan: tırmanılan yükseklik + toplanan altınlar. Ekranın sol üstünde, kameradan bağımsız çizilir.
import pygame

from settings import (
    TILE_SIZE,
    COIN_POINTS,
    HEIGHT_POINTS,
    SCORE_COLOR,
    SCORE_SHADOW_COLOR,
    SCORE_FONT_SIZE,
    SCORE_SMALL_FONT_SIZE,
)


class Score:
    def __init__(self, start_y):
        # Karakterin ayaklarının başladığı yükseklik — yükseklik buna göre ölçülür
        self.start_y = start_y
        self.height = 0  # üstüne basılan en yüksek yer (blok sayısı)
        self.coins = 0  # toplanan altın sayısı
        # None = pygame'in kendi yazı tipi
        self.font = pygame.font.Font(None, SCORE_FONT_SIZE)
        self.small_font = pygame.font.Font(None, SCORE_SMALL_FONT_SIZE)

    @property
    def total(self):
        return self.height * HEIGHT_POINTS + self.coins * COIN_POINTS

    def update(self, player):
        # Sadece üstüne bastığı yer sayılır (havada zıplamak puan vermesin);
        # aşağı düşünce puan azalmaz, en yükseği hatırlanır
        if player.on_ground:
            climbed = (self.start_y - player.rect.bottom) // TILE_SIZE
            self.height = max(self.height, climbed)

    def add_coin(self):
        self.coins += 1

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
