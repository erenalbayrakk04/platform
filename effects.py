# Küçük efektler: altın alınca / düşman ölünce etrafa saçılan renkli parçacıklar.
import random

import pygame

from settings import PARTICLE_COUNT, PARTICLE_LIFE, PIXEL_SCALE, GRAVITY


class Particle(pygame.sprite.Sprite):
    def __init__(self, center, color):
        super().__init__()
        self.image = pygame.Surface((PIXEL_SCALE, PIXEL_SCALE))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=center)
        # Rastgele yöne fırlasın, biraz da yukarı
        self.x, self.y = float(self.rect.x), float(self.rect.y)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -1)
        self.life = PARTICLE_LIFE

    def update(self):
        self.vy += GRAVITY * 0.5  # yavaşça düşsün
        self.x += self.vx
        self.y += self.vy
        self.rect.topleft = (round(self.x), round(self.y))
        self.life -= 1
        if self.life <= 0:
            self.kill()  # süresi bitti, gruptan çıkar


def burst(group, center, color, count=PARTICLE_COUNT):
    # center noktasından count tane parçacık saç
    for _ in range(count):
        group.add(Particle(center, color))
