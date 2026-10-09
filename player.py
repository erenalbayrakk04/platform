# Oyuncunun kontrol ettiği karakter.
import pygame

from settings import (
    PLAYER_SPEED,
    GRAVITY,
    JUMP_POWER,
    MAX_FALL_SPEED,
    INVINCIBLE_TIME,
    HURT_BOUNCE,
    ANIMATION_SPEED,
    SPRING_POWER,
    MAGNET_TIME,
    SHIELD_TIME,
)
import skins
from trail import Trail


class Player(pygame.sprite.Sprite):
    # Güçlendirmeler kaç kare sürer
    POWER_TIME = {"magnet": MAGNET_TIME, "shield": SHIELD_TIME}

    def __init__(self, x, y, level_width, lives=1, max_lives=1, skin=skins.DEFAULT_SKIN):
        # lives / max_lives: kaç canla başlar / kalplerle en fazla kaç can (zorluk moduna göre, main.py verir)
        # skin = görünüşü (skins.py); sadece resimleri değiştirir, hareket hep aynı
        super().__init__()
        self.facing = 1  # 1 = sağa bakıyor, -1 = sola
        self.walk_time = 0  # yürüme animasyonu sayacı
        self.pose = "idle"  # hangi resim: "idle" duruyor, "walk1"/"walk2" yürüyor, "jump" havada
        self.set_skin(skin)
        # rect = karakterin bölümdeki konumu ve boyutu
        self.rect = self.image.get_rect()
        # En son güvenle üstünde durduğu yer — düşünce buradan devam eder
        self.safe_pos = (x, y)
        self.level_width = level_width
        self.lives = lives
        self.max_lives = max_lives
        self.hurts = 0  # kaç kere can kaybetti (bölümde 3. yıldız: hiç)
        self.invincible = 0  # dokunulmazlığın bitmesine kaç kare kaldı (0 = dokunulabilir)
        # Güçlendirmelerin bitmesine kaç kare kaldı (0 = yok); expired = bu karede bitenler (ses için)
        self.powers = dict.fromkeys(self.POWER_TIME, 0)
        self.expired = []
        self.respawn()

    def set_skin(self, skin_id):
        # Görünüşü değiştir (Karakterler ekranında seçilince menünün arkasındaki karakter de değişir)
        skin = skins.get(skin_id)
        self.frames = skins.frames(skin_id)  # {resim adı: {1: sağa, -1: sola}}
        self.image = self.frames[self.pose][self.facing]
        self.color = skin["color"]  # can kaybedince saçılan parçacıklar
        # Efsanevi skinler arkalarında iz bırakır (trail.py); main.py her adımda trail.update çağırır
        self.trail = Trail(skin["trail"]) if skin["trail"] else None

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
        self.hurts += 1
        self.invincible = INVINCIBLE_TIME
        self.velocity_y = -HURT_BOUNCE

    def heal(self):
        # Bir can kazan (en fazla max_lives). Can zaten doluysa False döner
        if self.lives >= self.max_lives:
            return False
        self.lives += 1
        return True

    def power_up(self, kind):
        # Güçlendirme başlar; zaten sürüyorsa süresi baştan başlar
        self.powers[kind] = self.POWER_TIME[kind]

    def power_fraction(self, kind):
        # Güçlendirmenin ne kadarı kaldı (1 = yeni alındı, 0 = bitti)
        return self.powers[kind] / self.POWER_TIME[kind]

    def standing_on(self, sprite):
        # Bu sprite'ın tam üstünde mi duruyor?
        return (
            self.on_ground
            and self.rect.bottom == sprite.rect.top
            and self.rect.right > sprite.rect.left
            and self.rect.left < sprite.rect.right
        )

    def carry(self, dx, tiles):
        # Hareketli platformla birlikte yana kay; duvara veya bölüm kenarına çarpacaksa kayma
        self.rect.x += dx
        blocked = any(self.rect.colliderect(tile.rect) for tile in tiles)
        if blocked or self.rect.left < 0 or self.rect.right > self.level_width:
            self.rect.x -= dx

    def check_springs(self, springs):
        # Bir yayın üstünde duruyorsa veya üstüne düştüyse çok yükseğe fırla; fırlatan yayı döndür
        if self.velocity_y < 0:
            return None  # zaten yükseliyor
        feet = pygame.Rect(self.rect.left, self.rect.bottom - 1, self.rect.width, 1)
        for spring in springs:
            if feet.colliderect(spring.rect):
                self.bounce(SPRING_POWER)
                spring.squash()
                return spring
        return None

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
        self.expired = []
        for kind, left in self.powers.items():
            if left > 0:
                self.powers[kind] = left - 1
                if left == 1:
                    self.expired.append(kind)

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
        ground = [tile for tile in tiles if feet.colliderect(tile.rect)]
        self.on_ground = bool(ground)
        # Hareketli ve kırılan platform güvenli yer sayılmaz (yeniden doğunca orada olmayabilir)
        if ground and not any(getattr(tile, "unsafe", False) for tile in ground):
            self.safe_pos = self.rect.midbottom

        self.animate(dx)

    def animate(self, dx):
        # Hareket yönüne dön; havadaysa zıplama, yürüyorsa sırayla iki yürüme resmi, yoksa duruş
        if dx:
            self.facing = 1 if dx > 0 else -1
        if not self.on_ground:
            self.pose = "jump"
        elif dx:
            self.walk_time += 1
            self.pose = "walk1" if (self.walk_time // ANIMATION_SPEED) % 2 == 0 else "walk2"
        else:
            self.walk_time = 0
            self.pose = "idle"
        self.image = self.frames[self.pose][self.facing]
