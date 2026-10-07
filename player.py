# Oyuncunun kontrol ettiği karakter.
import pygame

from settings import (
    PLAYER_SPEED,
    GRAVITY,
    JUMP_POWER,
    MAX_FALL_SPEED,
    PLAYER_LIVES,
    INVINCIBLE_TIME,
    HURT_BOUNCE,
    ANIMATION_SPEED,
)
from art import player_frames


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, level_width):
        super().__init__()
        # Resimler (art.py): "idle" duruyor, "walk1"/"walk2" yürüyor, "jump" havada; her biri sağa/sola
        self.frames = player_frames()
        self.facing = 1  # 1 = sağa bakıyor, -1 = sola
        self.walk_time = 0  # yürüme animasyonu sayacı
        self.image = self.frames["idle"][self.facing]
        # rect = karakterin bölümdeki konumu ve boyutu
        self.rect = self.image.get_rect()
        # En son güvenle üstünde durduğu yer — düşünce buradan devam eder
        self.safe_pos = (x, y)
        self.level_width = level_width
        self.lives = PLAYER_LIVES
        self.invincible = 0  # dokunulmazlığın bitmesine kaç kare kaldı (0 = dokunulabilir)
        self.respawn()

    def respawn(self):
        # Karakteri en son durduğu güvenli yere geri koy
        self.rect.midbottom = self.safe_pos
        # Dikey hareket: eksi = yukarı, artı = aşağı
        self.velocity_y = 0.0
        # Konumu ondalıklı tutuyoruz ki küçük hızlar kaybolmasın
        self.pos_y = float(self.rect.bottom)
        self.on_ground = False
        self.jumped = False
        # Önceki karedeki ayak hizası — düşmana yukarıdan mı düştü anlamak için
        self.old_bottom = self.rect.bottom

    def hurt(self):
        # Bir can kaybet ve kısa süre dokunulmaz ol (yanıp söner)
        self.lives -= 1
        self.invincible = INVINCIBLE_TIME
        self.velocity_y = -HURT_BOUNCE

    def bounce(self, power):
        # Yukarı sıçra (ör. düşmanın üstüne basınca)
        self.velocity_y = -power
        self.on_ground = False

    @property
    def visible(self):
        # Dokunulmazken birkaç karede bir görünmez olur → yanıp söner
        return self.invincible == 0 or (self.invincible // 5) % 2 == 0

    def update(self, tiles, controls):
        # controls: sola / sağa / zıpla basılıyor mu (klavye veya ekran butonları, controls.py)
        self.old_bottom = self.rect.bottom
        if self.invincible > 0:
            self.invincible -= 1

        # --- Yatay hareket ---
        dx = 0
        if controls.left:
            dx -= PLAYER_SPEED
        if controls.right:
            dx += PLAYER_SPEED
        self.rect.x += dx

        # Bir bloğa yandan çarptıysa bloğun kenarında dur
        for tile in pygame.sprite.spritecollide(self, tiles, False):
            if dx > 0:
                self.rect.right = tile.rect.left
            elif dx < 0:
                self.rect.left = tile.rect.right

        # Bölümün dışına çıkmasın
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, self.level_width)

        # --- Dikey hareket ---
        # Zıplama: sadece yerdeyken. jumped = bu karede zıpladı mı (ses çalmak için)
        self.jumped = controls.jump and self.on_ground
        if self.jumped:
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
        if self.on_ground:
            self.safe_pos = self.rect.midbottom

        self.animate(dx)

    def animate(self, dx):
        # Hareket yönüne dön; havadaysa zıplama, yürüyorsa sırayla iki yürüme resmi, yoksa duruş
        if dx:
            self.facing = 1 if dx > 0 else -1
        if not self.on_ground:
            name = "jump"
        elif dx:
            self.walk_time += 1
            name = "walk1" if (self.walk_time // ANIMATION_SPEED) % 2 == 0 else "walk2"
        else:
            self.walk_time = 0
            name = "idle"
        self.image = self.frames[name][self.facing]
