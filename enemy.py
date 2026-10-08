# Düşmanlar: yürüyen düşman bir platformun üstünde, uçan düşman havada sağa-sola gider,
# ucuna gelince geri döner.
import math

import pygame

from settings import (
    ENEMY_COLOR,
    FLYER_COLOR,
    ANIMATION_SPEED,
    FLYER_BOB,
    FLYER_BOB_SPEED,
    FLYER_FLAP_SPEED,
)
from art import enemy_frames, flyer_frames

# Aynı türdeki düşmanlar aynı resimleri kullanır; ilk düşman yaratılınca bir kere hazırlanır
FRAMES = []
FLYER_FRAMES = []


class Patrol(pygame.sprite.Sprite):
    # İki düşmanın ortak yanı: left-right piksel arasında gidip gelir
    def __init__(self, image, left, right, speed, **position):
        super().__init__()
        self.image = image
        self.rect = image.get_rect(**position)
        # Gidebileceği sınırlar (piksel)
        self.left = left
        self.right = right
        self.direction = 1  # 1 = sağa, -1 = sola
        self.speed = speed  # her karede kaç piksel; zorluk moduna ve yüksekliğe göre (level.py)
        # Konumu ondalıklı tutuyoruz ki yavaş hızlar da çalışsın
        self.pos_x = float(self.rect.x)
        # Önceki karedeki üst kenarı — karakter üstüne mi bastı anlamak için (main.py)
        self.old_top = self.rect.top
        self.anim_time = 0

    def patrol(self):
        self.old_top = self.rect.top
        self.pos_x += self.speed * self.direction
        # Ucuna geldiyse geri dön
        if self.pos_x + self.rect.width >= self.right:
            self.pos_x = self.right - self.rect.width
            self.direction = -1
        elif self.pos_x <= self.left:
            self.pos_x = self.left
            self.direction = 1
        self.rect.x = round(self.pos_x)
        self.anim_time += 1


class Enemy(Patrol):
    # Yürüyen düşman: platformun kenarları arasında yürür
    color = ENEMY_COLOR  # ölünce saçılan parçacıkların rengi

    def __init__(self, center_x, bottom, left, right, speed):
        if not FRAMES:
            FRAMES.extend(enemy_frames())
        super().__init__(FRAMES[0][1], left, right, speed, midbottom=(center_x, bottom))

    def update(self):
        self.patrol()
        # İki resim arasında kıpırdasın, yürüdüğü yöne baksın
        frame = FRAMES[(self.anim_time // (ANIMATION_SPEED * 2)) % 2]
        self.image = frame[self.direction]


class FlyingEnemy(Patrol):
    # Uçan düşman (yarasa): havada uçar, bir yandan hafifçe aşağı-yukarı süzülür
    color = FLYER_COLOR

    def __init__(self, center_x, center_y, left, right, speed):
        if not FLYER_FRAMES:
            FLYER_FRAMES.extend(flyer_frames())
        super().__init__(FLYER_FRAMES[0], left, right, speed, center=(center_x, center_y))
        self.center_y = center_y
        self.anim_time = center_x % 60  # hepsi aynı anda kanat çırpmasın

    def update(self):
        self.patrol()
        bob = FLYER_BOB * math.sin(self.anim_time / FLYER_BOB_SPEED)
        self.rect.centery = self.center_y + round(bob)
        self.image = FLYER_FRAMES[(self.anim_time // FLYER_FLAP_SPEED) % 2]
