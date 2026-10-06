# Oyuncunun kontrol ettiği karakter.
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_COLOR,
    PLAYER_SPEED,
    GRAVITY,
    JUMP_POWER,
    MAX_FALL_SPEED,
    GROUND_HEIGHT,
)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Şimdilik karakter düz renkli bir kare; resmi Aşama 8'de ekleyeceğiz.
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(PLAYER_COLOR)
        # rect = karakterin ekrandaki konumu ve boyutu
        self.rect = self.image.get_rect(midbottom=(x, y))

        # Dikey hareket: eksi = yukarı, artı = aşağı
        self.velocity_y = 0.0
        # Konumu ondalıklı tutuyoruz ki küçük hızlar kaybolmasın
        self.pos_y = float(self.rect.bottom)
        self.on_ground = False

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

        # Zıplama: Boşluk, yukarı ok veya W — sadece yerdeyken
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.velocity_y = -JUMP_POWER
            self.on_ground = False

        # Yerçekimi: her karede aşağı doğru biraz daha hızlan
        self.velocity_y = min(self.velocity_y + GRAVITY, MAX_FALL_SPEED)
        self.pos_y += self.velocity_y

        # Zemine değince dur
        ground_top = SCREEN_HEIGHT - GROUND_HEIGHT
        if self.pos_y >= ground_top:
            self.pos_y = ground_top
            self.velocity_y = 0
            self.on_ground = True

        self.rect.bottom = round(self.pos_y)
