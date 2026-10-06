# Oyuncunun kontrol ettiği karakter.
import pygame

from settings import (
    SCREEN_WIDTH,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_COLOR,
    PLAYER_SPEED,
    GRAVITY,
    JUMP_POWER,
    MAX_FALL_SPEED,
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

    def update(self, tiles):
        keys = pygame.key.get_pressed()

        # --- Yatay hareket ---
        # Sol ok veya A → sola, sağ ok veya D → sağa
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED
        self.rect.x += dx

        # Bir bloğa yandan çarptıysa bloğun kenarında dur
        for tile in pygame.sprite.spritecollide(self, tiles, False):
            if dx > 0:
                self.rect.right = tile.rect.left
            elif dx < 0:
                self.rect.left = tile.rect.right

        # Ekranın dışına çıkmasın
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, SCREEN_WIDTH)

        # --- Dikey hareket ---
        # Zıplama: Boşluk, yukarı ok veya W — sadece yerdeyken
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.velocity_y = -JUMP_POWER

        # Yerçekimi: her karede aşağı doğru biraz daha hızlan
        self.velocity_y = min(self.velocity_y + GRAVITY, MAX_FALL_SPEED)
        self.pos_y += self.velocity_y
        self.rect.bottom = round(self.pos_y)

        # Bloğa üstten düştüyse üstüne otur, alttan kafa attıysa geri düş
        for tile in pygame.sprite.spritecollide(self, tiles, False):
            if self.velocity_y > 0:
                self.rect.bottom = tile.rect.top
            elif self.velocity_y < 0:
                self.rect.top = tile.rect.bottom
            self.velocity_y = 0
        self.pos_y = float(self.rect.bottom)

        # Ayağının hemen altında blok varsa yerdedir
        feet = self.rect.move(0, 1)
        self.on_ground = any(feet.colliderect(tile.rect) for tile in tiles)
