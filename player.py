# Oyuncunun kontrol ettiği karakter.
import pygame

from settings import (
    SCREEN_WIDTH,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_COLOR,
    PLAYER_SPEED,
)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Şimdilik karakter düz renkli bir kare; resmi Aşama 8'de ekleyeceğiz.
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(PLAYER_COLOR)
        # rect = karakterin ekrandaki konumu ve boyutu
        self.rect = self.image.get_rect(midbottom=(x, y))

    def update(self):
        keys = pygame.key.get_pressed()

        # Sol ok veya A → sola, sağ ok veya D → sağa
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED

        # Ekranın dışına çıkmasın
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, SCREEN_WIDTH)
