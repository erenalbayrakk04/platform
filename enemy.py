# Düşman: bir platformun üstünde sağa-sola yürür, ucuna gelince geri döner.
import pygame

from settings import ENEMY_WIDTH, ENEMY_HEIGHT, ENEMY_COLOR, ENEMY_EYE_COLOR, ENEMY_SPEED


class Enemy(pygame.sprite.Sprite):
    def __init__(self, center_x, bottom, left, right):
        super().__init__()
        # Şimdilik gözlü kırmızı bir kare; resmi Aşama 8'de ekleyeceğiz
        self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT))
        self.image.fill(ENEMY_COLOR)
        for eye_x in (ENEMY_WIDTH // 3, ENEMY_WIDTH * 2 // 3):
            pygame.draw.rect(self.image, ENEMY_EYE_COLOR, (eye_x - 3, 7, 6, 6))
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
