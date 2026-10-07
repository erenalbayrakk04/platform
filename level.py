# Sonsuz bölüm: harita parçalarını (chunks.py) üst üste dizer, geride kalanları siler.
import math
import random

import pygame

from settings import (
    TILE_SIZE,
    COIN_SPIN_SPEED,
    HEART_CHANCE,
    SPRING_SQUASH_TIME,
    MOVING_PLATFORM_SPEED,
    LEVEL_SEED,
    GENERATE_AHEAD,
    REMOVE_BELOW,
    DIFFICULTY_STEP,
)
from chunks import START_CHUNK, CHUNKS, platform_run, moving_platforms
from enemy import Enemy
import art

# Resimler bir kere hazırlanır, aynı türdeki her parça aynı resmi kullanır (art.py)
IMAGES = {}


def image(name):
    if name not in IMAGES:
        IMAGES.update(
            tile=art.tile_image(),
            platform=art.platform_image(),
            coin=art.coin_frames(),
            heart=art.heart_images()["full"],
            spring=art.spring_frames(),
        )
    return IMAGES[name]


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = image("tile")
        self.rect = self.image.get_rect(topleft=(x, y))


class Platform(pygame.sprite.Sprite):
    # İnce platform: karenin sadece üst kısmını kaplar, blok gibi katıdır
    def __init__(self, x, y):
        super().__init__()
        self.image = image("platform")
        self.rect = self.image.get_rect(topleft=(x, y))


class MovingPlatform(pygame.sprite.Sprite):
    # Hareketli platform: left-right piksel arasında gidip gelir; katıdır (level.tiles içinde).
    # Üstünde duran karakteri main.py taşır (Player.carry)
    moving = True  # Player bunu görünce burayı "güvenli yer" saymaz

    def __init__(self, x, y, cells, left, right):
        super().__init__()
        key = ("mover", cells)
        if key not in IMAGES:
            IMAGES[key] = art.moving_platform_image(cells)
        self.image = IMAGES[key]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.left = left
        self.right = right
        self.direction = 1  # 1 = sağa, -1 = sola
        self.pos_x = float(x)

    def move(self):
        # Bir adım ilerle, ucuna gelince dön; kaç piksel kaydığını döndür
        old_x = self.rect.x
        self.pos_x += MOVING_PLATFORM_SPEED * self.direction
        if self.pos_x + self.rect.width >= self.right:
            self.pos_x = self.right - self.rect.width
            self.direction = -1
        elif self.pos_x <= self.left:
            self.pos_x = self.left
            self.direction = 1
        self.rect.x = round(self.pos_x)
        return self.rect.x - old_x


class Coin(pygame.sprite.Sprite):
    # Altın: katı değil, karakter içinden geçince toplanır
    def __init__(self, x, y):
        super().__init__()
        self.frames = image("coin")
        self.image = self.frames[0]
        # Karenin ortasına koy
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
        # Hepsi aynı anda dönmesin diye her altın farklı bir yerden başlar
        self.spin = (x + y) // 7

    def update(self):
        # Dönme animasyonu: resimler sırayla değişir
        self.spin += 1
        self.image = self.frames[(self.spin // COIN_SPIN_SPEED) % len(self.frames)]


class Heart(pygame.sprite.Sprite):
    # Toplanabilir kalp: 1 can verir. Altın yerine nadiren çıkar (HEART_CHANCE)
    def __init__(self, x, y):
        super().__init__()
        self.image = image("heart")
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
        self.base_y = self.rect.y
        self.time = 0

    def update(self):
        # Yavaşça aşağı yukarı süzülsün
        self.time += 1
        self.rect.y = self.base_y + round(3 * math.sin(self.time / 12))


class Spring(pygame.sprite.Sprite):
    # Yay: altındaki platformun üstüne oturur; karakter üstüne basınca fırlar (Player.check_springs)
    def __init__(self, x, y):
        super().__init__()
        self.frames = image("spring")
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(x + TILE_SIZE // 2, y + TILE_SIZE))
        self.squashed = 0  # basık görünmesine kaç kare kaldı

    def squash(self):
        self.squashed = SPRING_SQUASH_TIME

    def update(self):
        if self.squashed > 0:
            self.squashed -= 1
        self.image = self.frames[1 if self.squashed else 0]


class Level:
    # Koordinatlar: en alttaki zeminin altı y = 0; yukarı çıktıkça y eksiye iner.
    def __init__(self, seed=LEVEL_SEED):
        # Aynı seed (sayı) hep aynı haritayı üretir; None ise her oyun farklı
        self.random = random.Random(seed)
        # Karakterin çarptığı her şey (bloklar ve ince platformlar)
        self.tiles = pygame.sprite.Group()
        # Toplanabilir altınlar
        self.coins = pygame.sprite.Group()
        # Toplanabilir kalpler (can)
        self.hearts = pygame.sprite.Group()
        # Yaylar
        self.springs = pygame.sprite.Group()
        # Hareketli platformlar (ayrıca tiles içinde de varlar, çünkü katılar)
        self.movers = pygame.sprite.Group()
        # Platformlarda yürüyen düşmanlar
        self.enemies = pygame.sprite.Group()
        self.width = len(START_CHUNK["rows"][0]) * TILE_SIZE
        self.player_start = (TILE_SIZE, 0)
        # Şu an bellekteki parçalar, aşağıdan yukarıya: (üst y, alt y, sprite listesi)
        self.chunks = []
        self.top = 0  # en üstteki parçanın tepesi
        self.bottom = 0  # en alttaki parçanın altı — bunun altına düşen kaybeder
        self.exit_side = None  # en üstteki parçanın çıkışı hangi tarafta
        self.add_chunk(START_CHUNK)

    def add_chunk(self, chunk):
        # Parçayı şu anki tepenin hemen üstüne yerleştir
        rows = chunk["rows"]
        top = self.top - len(rows) * TILE_SIZE
        sprites = []
        for row_index, row in enumerate(rows):
            for col_index, cell in enumerate(row):
                x = col_index * TILE_SIZE
                y = top + row_index * TILE_SIZE
                if cell == "#":
                    sprites.append(Tile(x, y))
                elif cell == "-":
                    sprites.append(Platform(x, y))
                elif cell == "C":
                    # Altın, nadiren de kalp
                    if self.random.random() < HEART_CHANCE:
                        heart = Heart(x, y)
                        sprites.append(heart)
                        self.hearts.add(heart)
                    else:
                        coin = Coin(x, y)
                        sprites.append(coin)
                        self.coins.add(coin)
                elif cell == "S":
                    spring = Spring(x, y)
                    sprites.append(spring)
                    self.springs.add(spring)
                elif cell == "E":
                    # Altındaki platformun kenarları arasında yürüsün
                    left, right = platform_run(rows, row_index, col_index)
                    enemy = Enemy(
                        x + TILE_SIZE // 2, y + TILE_SIZE, left * TILE_SIZE, (right + 1) * TILE_SIZE
                    )
                    sprites.append(enemy)
                    self.enemies.add(enemy)
                elif cell == "P":
                    # Karakterin ayakları bu kutunun altına gelsin
                    self.player_start = (x + TILE_SIZE // 2, y + TILE_SIZE)
        for r, left, width, span_left, span_right in moving_platforms(rows):
            mover = MovingPlatform(
                left * TILE_SIZE,
                top + r * TILE_SIZE,
                width,
                span_left * TILE_SIZE,
                (span_right + 1) * TILE_SIZE,
            )
            sprites.append(mover)
            self.movers.add(mover)
        self.tiles.add([s for s in sprites if isinstance(s, (Tile, Platform, MovingPlatform))])
        self.chunks.append((top, self.top, sprites))
        self.top = top
        self.exit_side = chunk["exit"]

    def pick_chunk(self):
        # Girişi, alttaki parçanın çıkışının karşı tarafında olan parçalardan rastgele seç
        entry = "R" if self.exit_side == "L" else "L"
        # Yükseldikçe daha zor parçalar da seçilebilir
        max_difficulty = 1 + int(-self.top // DIFFICULTY_STEP)
        options = [c for c in CHUNKS if c["entry"] == entry and c["difficulty"] <= max_difficulty]
        return self.random.choice(options)

    def update(self, view_top, view_bottom):
        # Ekranın yukarısı için yeterince parça hazır olsun
        while self.top > view_top - GENERATE_AHEAD:
            self.add_chunk(self.pick_chunk())
        # Ekranın çok altında kalan parçaları unut (bellekten sil)
        while len(self.chunks) > 1 and self.chunks[0][0] > view_bottom + REMOVE_BELOW:
            _, _, sprites = self.chunks.pop(0)
            self.tiles.remove(sprites)
            self.coins.remove(sprites)  # toplanmamış altınlar, kalpler ve düşmanlar da gitsin
            self.hearts.remove(sprites)
            self.springs.remove(sprites)
            self.movers.remove(sprites)
            self.enemies.remove(sprites)
        self.bottom = self.chunks[0][1]
