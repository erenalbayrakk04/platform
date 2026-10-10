# Düşmanlar. Hepsi bir yolda gidip gelir (Patrol): yürüyenler bir platformun üstünde, uçanlar havada.
#   Enemy (kırmızı), Slime (zıplayan sümük), Spiky (dikenli kirpi — üstüne basılmaz),
#   Cannon (topçu: yerinde durur, ateş topu atar → Fireball), FlyingEnemy (yarasa, yatay uçar),
#   Bee (arı, dikey uçar). Hangi yere hangisinin geleceğini level.py seçer.
#   MagmaSlime (lav sümüğü) haritada çıkmaz: boss (boss.py) vurulunca saçar.
import math

import pygame

from settings import (
    ENEMY_COLOR,
    FLYER_COLOR,
    SLIME_COLOR,
    SPIKY_COLOR,
    CANNON_COLOR,
    FIREBALL_COLOR,
    BEE_COLOR,
    ANIMATION_SPEED,
    GRAVITY,
    FLYER_BOB,
    FLYER_BOB_SPEED,
    FLYER_FLAP_SPEED,
    SLIME_SPEED,
    SLIME_JUMP_POWER,
    SLIME_JUMP_TIME,
    SLIME_SQUASH_TIME,
    SPIKY_SPEED,
    CANNON_FIRE_TIME,
    CANNON_WARN_TIME,
    CANNON_RANGE,
    FIREBALL_SPEED,
    BEE_SPEED,
    MAGMA_COLOR,
)
import art
import theme

# Aynı türdeki düşmanlar aynı resimleri kullanır; o türün ilk düşmanı yaratılınca bir kere hazırlanır (her tema için ayrı)
MAKE_FRAMES = {
    "enemy": art.enemy_frames,
    "flyer": art.flyer_frames,
    "slime": art.slime_frames,
    "magma": lambda: art.slime_frames(MAGMA_COLOR),
    "spiky": art.spiky_frames,
    "cannon": art.cannon_frames,
    "fireball": art.fireball_frames,
    "bee": art.bee_frames,
}
FRAMES = {}


def frames(kind):
    return theme.cached(FRAMES, kind, MAKE_FRAMES[kind])


class Patrol(pygame.sprite.Sprite):
    # Bütün düşmanların ortak yanı: start-end piksel arasında gidip gelir — yatayda (sol-sağ)
    # ya da vertical ise dikeyde (üst-alt)
    spiky = False  # True ise üstüne basınca düşman değil karakter yanar (main.py)
    grounded = False  # şu an bir platformun üstünde mi (Modern temada ayağının altına gölge çizilir)
    harmless = False  # True iken karaktere değmez (golemden fırlayan lav sümüğü yere inene kadar)

    def __init__(self, image, start, end, speed, vertical=False, **position):
        super().__init__()
        self.image = image
        self.rect = image.get_rect(**position)
        # Gidebileceği sınırlar (piksel)
        self.start = start
        self.end = end
        self.vertical = vertical
        self.direction = 1  # 1 = sağa/aşağı, -1 = sola/yukarı
        self.speed = speed  # her karede kaç piksel; zorluk moduna ve yüksekliğe göre (level.py)
        # Konumu ondalıklı tutuyoruz ki yavaş hızlar da çalışsın
        self.pos = float(self.rect.y if vertical else self.rect.x)
        # Önceki karedeki üst kenarı — karakter üstüne mi bastı anlamak için (main.py)
        self.old_top = self.rect.top
        self.anim_time = 0

    def patrol(self):
        self.old_top = self.rect.top
        size = self.rect.height if self.vertical else self.rect.width
        self.pos += self.speed * self.direction
        # Ucuna geldiyse geri dön
        if self.pos + size >= self.end:
            self.pos = self.end - size
            self.direction = -1
        elif self.pos <= self.start:
            self.pos = self.start
            self.direction = 1
        if self.vertical:
            self.rect.y = round(self.pos)
        else:
            self.rect.x = round(self.pos)
        self.anim_time += 1


class Enemy(Patrol):
    # Yürüyen düşman: platformun kenarları arasında yürür. update(target): target = karakterin
    # kutusu (sadece topçu kullanır, ama hepsine verilir)
    color = ENEMY_COLOR  # ölünce saçılan parçacıkların rengi
    kind = "enemy"  # resimleri (frames)
    grounded = True

    def __init__(self, center_x, bottom, left, right, speed):
        self.frames = frames(self.kind)
        super().__init__(self.frames[0][1], left, right, speed, midbottom=(center_x, bottom))

    def update(self, target):
        self.patrol()
        # İki resim arasında kıpırdasın, yürüdüğü yöne baksın
        frame = self.frames[(self.anim_time // (ANIMATION_SPEED * 2)) % 2]
        self.image = frame[self.direction]


class Spiky(Enemy):
    # Dikenli kirpi: yavaş yürür; üstüne basan karakter yanar, sadece kalkan öldürür
    color = SPIKY_COLOR
    kind = "spiky"
    spiky = True

    def __init__(self, center_x, bottom, left, right, speed):
        super().__init__(center_x, bottom, left, right, speed * SPIKY_SPEED)


class Slime(Patrol):
    # Zıplayan sümük: yürür; SLIME_JUMP_TIME karede bir durup SLIME_SQUASH_TIME kare basılır
    # (uyarı), sonra zıplar. Havadayken de yürümeye devam eder
    color = SLIME_COLOR
    kind = "slime"  # resimleri (frames)

    def __init__(self, center_x, bottom, left, right, speed):
        self.frames = frames(self.kind)
        super().__init__(
            self.frames["walk1"][1], left, right, speed * SLIME_SPEED, midbottom=(center_x, bottom)
        )
        self.ground = bottom  # durduğu platformun üstü
        self.bottom_y = float(bottom)  # ayaklarının yeri (ondalıklı)
        self.velocity_y = 0.0
        self.airborne = False
        self.timer = SLIME_JUMP_TIME - center_x % 40  # hepsi aynı anda zıplamasın

    @property
    def grounded(self):
        return not self.airborne

    def update(self, target):
        if self.airborne:
            self.patrol()
            self.velocity_y += GRAVITY
            self.bottom_y += self.velocity_y
            if self.bottom_y >= self.ground:  # yere indi
                self.bottom_y = self.ground
                self.airborne = False
                self.timer = SLIME_JUMP_TIME
            self.rect.bottom = round(self.bottom_y)
            name = "jump"
        else:
            self.timer -= 1
            if self.timer > SLIME_SQUASH_TIME:
                self.patrol()
                name = "walk1" if (self.anim_time // (ANIMATION_SPEED * 2)) % 2 == 0 else "walk2"
            else:
                self.old_top = self.rect.top  # basılmış bekliyor
                name = "squash"
            if self.timer <= 0:
                self.airborne = True
                self.velocity_y = -SLIME_JUMP_POWER
        self.image = self.frames[name][self.direction]


class MagmaSlime(Slime):
    # Lav sümüğü: boss (Lav Golemi, boss.py) vurulunca saçılır; turuncu sümük, aynı davranış
    color = MAGMA_COLOR
    kind = "magma"
    FLING_SPEED = 4  # fırlarken yana hızı (golemin dibine değil, biraz uzağa düşsün)
    walk_speed = None  # fırlarken asıl yürüme hızı (inince geri gelir)

    @property
    def harmless(self):
        # Fırlarken zararsız: golemin kafasına basan karakterin içinden çıkıp onu yakmasın
        return self.walk_speed is not None

    def throw(self, center_x, bottom, direction, power):
        # Golemin içinden fırlar: havada direction yönüne uçar, yere (ground) inince yürümeye başlar
        self.rect.midbottom = (center_x, bottom)
        self.pos = float(self.rect.x)
        self.bottom_y = float(bottom)
        self.old_top = self.rect.top
        self.direction = direction
        self.airborne = True
        self.velocity_y = -power
        self.walk_speed, self.speed = self.speed, self.FLING_SPEED

    def update(self, target):
        flying = self.airborne
        super().update(target)
        if flying and not self.airborne and self.walk_speed:
            self.speed, self.walk_speed = self.walk_speed, None  # indi: kendi hızında yürür


class Cannon(Patrol):
    # Topçu: yerinde durur, karaktere döner. Karakter dikeyde CANNON_RANGE kadar yakındayken
    # fire_time (CANNON_FIRE_TIME; Ultra Zor'da daha sık) karede bir ateş topu atar; atmadan CANNON_WARN_TIME
    # kare önce namlusu kızarır. Attığı ateş topları shots grubuna (level.shots) girer. Üstüne basılınca ölür
    color = CANNON_COLOR
    grounded = True

    def __init__(self, center_x, bottom, shots, fire_time=CANNON_FIRE_TIME):
        self.frames = frames("cannon")
        super().__init__(self.frames[0][1], center_x, center_x, 0, midbottom=(center_x, bottom))
        self.shots = shots
        self.facing = 1
        self.fire_time = fire_time
        self.timer = fire_time - center_x % 60  # hepsi aynı anda ateş etmesin

    def update(self, target):
        self.old_top = self.rect.top
        self.facing = 1 if target.centerx >= self.rect.centerx else -1
        near = abs(target.centery - self.rect.centery) <= CANNON_RANGE
        # Kızarmaya (uyarıya) ancak karakter yakındayken başlar; başladıysa sonunda ateş eder
        if near or self.timer != CANNON_WARN_TIME + 1:
            self.timer -= 1
        if self.timer <= 0:
            self.timer = self.fire_time
            muzzle_x = self.rect.right if self.facing == 1 else self.rect.left
            self.shots.add(Fireball(muzzle_x, self.rect.top + art.CANNON_MUZZLE_Y, self.facing))
        warning = self.timer <= CANNON_WARN_TIME
        self.image = self.frames[warning][self.facing]


class Fireball(pygame.sprite.Sprite):
    # Topçunun ateş topu: düz gider; katı bir şeye veya bölümün kenarına gelince söner.
    # Değen karakter yanar (kalkan varsa sadece top söner)
    color = FIREBALL_COLOR

    def __init__(self, center_x, center_y, direction):
        super().__init__()
        self.frames = frames("fireball")
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(center_x, center_y))
        self.direction = direction
        self.pos_x = float(self.rect.x)
        self.anim_time = 0

    def update(self, tiles, level_width):
        self.pos_x += FIREBALL_SPEED * self.direction
        self.rect.x = round(self.pos_x)
        self.anim_time += 1
        self.image = self.frames[(self.anim_time // 4) % 2]
        outside = self.rect.right < 0 or self.rect.left > level_width
        if outside or pygame.sprite.spritecollideany(self, tiles):
            self.kill()


class FlyingEnemy(Patrol):
    # Uçan düşman (yarasa): havada uçar, bir yandan hafifçe aşağı-yukarı süzülür
    color = FLYER_COLOR

    def __init__(self, center_x, center_y, left, right, speed):
        self.frames = frames("flyer")
        super().__init__(self.frames[0], left, right, speed, center=(center_x, center_y))
        self.center_y = center_y
        self.anim_time = center_x % 60  # hepsi aynı anda kanat çırpmasın

    def update(self, target):
        self.patrol()
        bob = FLYER_BOB * math.sin(self.anim_time / FLYER_BOB_SPEED)
        self.rect.centery = self.center_y + round(bob)
        self.image = self.frames[(self.anim_time // FLYER_FLAP_SPEED) % 2]


class Bee(Patrol):
    # Arı: kendi sütununda top-bottom piksel arasında aşağı-yukarı uçar (yolu level.py hesaplar).
    # facing = baktığı yön (ekranın ortasına doğru)
    color = BEE_COLOR

    def __init__(self, center_x, center_y, top, bottom, speed, facing):
        self.frames = frames("bee")
        super().__init__(
            self.frames[0][facing], top, bottom, speed * BEE_SPEED, vertical=True, center=(center_x, center_y)
        )
        self.facing = facing
        self.direction = -1  # önce yukarı
        self.anim_time = center_x % 60
        # Başladığı kare yolunun dışında kalıyorsa (ör. alttaki platforma çok yakınsa) yola sok
        self.pos = min(max(self.pos, top), bottom - self.rect.height)
        self.rect.y = round(self.pos)
        self.old_top = self.rect.top

    def update(self, target):
        self.patrol()
        self.image = self.frames[(self.anim_time // FLYER_FLAP_SPEED) % 2][self.facing]
