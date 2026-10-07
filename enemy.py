# Düşman: bir platformun üstünde sağa-sola yürür, ucuna gelince geri döner.
import pygame

from settings import ENEMY_WIDTH, ENEMY_SPEED, ANIMATION_SPEED
from art import enemy_frames

# Tüm düşmanlar aynı resimleri kullanır; ilk düşman yaratılınca bir kere hazırlanır
FRAMES = []


class Enemy(pygame.sprite.Sprite):
    def __init__(self, center_x, bottom, left, right):
        super().__init__()
        if not FRAMES:
            FRAMES.extend(enemy_frames())
        self.image = FRAMES[0][1]
        self.anim_time = 0
        self.rect = self.image.get_rect(midbottom=(center_x, bottom))
        # Yürüyebileceği sınırlar (platformun sol ve sağ kenarı, piksel)
        self.left = left
        self.right = right
        self.direction = 1  # 1 = sağa, -1 = sola
        # Konumu ondalıklı tutuyoruz ki yavaş hızlar da çalışsın
        self.pos_x = float(self.rect.x)

    def update(self):
        self.pos_x += ENEMY_SPEED * self.direction
        # Platformun ucuna geldiyse geri dön
        if self.pos_x + ENEMY_WIDTH >= self.right:
            self.pos_x = self.right - ENEMY_WIDTH
            self.direction = -1
        elif self.pos_x <= self.left:
            self.pos_x = self.left
            self.direction = 1
        self.rect.x = round(self.pos_x)
        # İki resim arasında kıpırdasın, yürüdüğü yöne baksın
        self.anim_time += 1
        frame = FRAMES[(self.anim_time // (ANIMATION_SPEED * 2)) % 2]
        self.image = frame[self.direction]
