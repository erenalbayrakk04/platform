# Bölüm haritası ve bloklar.
import pygame

from settings import TILE_SIZE, TILE_COLOR, TILE_TOP_COLOR

# Bölüm haritası — her karakter bir blok (40x40 piksel):
#   #  = blok (üstüne basılabilir)
#   .  = boşluk
#   P  = karakterin başladığı yer
# Haritayı değiştirmek için karakterleri değiştirmen yeterli.
# Her satır aynı uzunlukta olmalı (şimdilik 24 karakter = ekran genişliği).
LEVEL_MAP = [
    "........................",
    "........................",
    "........................",
    "........................",
    "........#####...........",
    "........................",
    "........................",
    "...####............####.",
    "........................",
    "........................",
    ".........####...###.....",
    "........................",
    ".P............#.........",
    "########################",
]


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(TILE_COLOR)
        # Üstüne ince bir çimen şeridi çiz
        pygame.draw.rect(self.image, TILE_TOP_COLOR, (0, 0, TILE_SIZE, 8))
        self.rect = self.image.get_rect(topleft=(x, y))


class Level:
    def __init__(self, level_map):
        self.tiles = pygame.sprite.Group()
        self.player_start = (TILE_SIZE, TILE_SIZE)

        # Haritayı satır satır, karakter karakter oku
        for row_index, row in enumerate(level_map):
            for col_index, cell in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                if cell == "#":
                    self.tiles.add(Tile(x, y))
                elif cell == "P":
                    # Karakterin ayakları bu kutunun altına gelsin
                    self.player_start = (x + TILE_SIZE // 2, y + TILE_SIZE)
