# Sonsuz bölüm: harita parçalarını (chunks.py) üst üste dizer, geride kalanları siler.
import random

import pygame

from settings import (
    TILE_SIZE,
    TILE_COLOR,
    TILE_TOP_COLOR,
    PLATFORM_HEIGHT,
    PLATFORM_COLOR,
    COIN_SIZE,
    COIN_COLOR,
    COIN_EDGE_COLOR,
    LEVEL_SEED,
    GENERATE_AHEAD,
    REMOVE_BELOW,
    DIFFICULTY_STEP,
)
from chunks import START_CHUNK, CHUNKS


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(TILE_COLOR)
        # Üstüne ince bir çimen şeridi çiz
        pygame.draw.rect(self.image, TILE_TOP_COLOR, (0, 0, TILE_SIZE, 8))
        self.rect = self.image.get_rect(topleft=(x, y))


class Platform(pygame.sprite.Sprite):
    # İnce platform: karenin sadece üst kısmını kaplar, blok gibi katıdır
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, PLATFORM_HEIGHT))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))


class Coin(pygame.sprite.Sprite):
    # Altın: katı değil, karakter içinden geçince toplanır
    def __init__(self, x, y):
        super().__init__()
        # SRCALPHA = saydam arka plan, sadece daire görünsün
        self.image = pygame.Surface((COIN_SIZE, COIN_SIZE), pygame.SRCALPHA)
        radius = COIN_SIZE // 2
        pygame.draw.circle(self.image, COIN_EDGE_COLOR, (radius, radius), radius)
        pygame.draw.circle(self.image, COIN_COLOR, (radius, radius), radius - 3)
        # Karenin ortasına koy
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))


class Level:
    # Koordinatlar: en alttaki zeminin altı y = 0; yukarı çıktıkça y eksiye iner.
    def __init__(self, seed=LEVEL_SEED):
        # Aynı seed (sayı) hep aynı haritayı üretir; None ise her oyun farklı
        self.random = random.Random(seed)
        # Karakterin çarptığı her şey (bloklar ve ince platformlar)
        self.tiles = pygame.sprite.Group()
        # Toplanabilir altınlar
        self.coins = pygame.sprite.Group()
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
                    coin = Coin(x, y)
                    sprites.append(coin)
                    self.coins.add(coin)
                elif cell == "P":
                    # Karakterin ayakları bu kutunun altına gelsin
                    self.player_start = (x + TILE_SIZE // 2, y + TILE_SIZE)
        self.tiles.add([s for s in sprites if not isinstance(s, Coin)])
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
            self.coins.remove(sprites)  # toplanmamış altınlar da gitsin
        self.bottom = self.chunks[0][1]
