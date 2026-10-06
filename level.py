# Bölüm haritası ve bloklar.
import pygame

from settings import TILE_SIZE, TILE_COLOR, TILE_TOP_COLOR, PLATFORM_HEIGHT, PLATFORM_COLOR

# Bölüm haritası — her karakter bir kare (40x40 piksel):
#   #  = blok (katı; içinden geçilmez)
#   -  = ince platform (o da katı: üstüne basılır, alttan kafa çarpar)
#   .  = boşluk
#   P  = karakterin başladığı yer
# Oyun yukarı doğru ilerler: karakter en alttan başlar, en tepeye tırmanır.
# Her satır aynı uzunlukta olmalı (10 karakter = ekran genişliği).
# Basılabilen yüzeyler arası yükseklik farkı en fazla 3 satır olsun (karakter ancak o kadar zıplar).
LEVEL_MAP = [
    "..........",
    "..........",
    "..######..",
    "..........",
    "..........",
    "........--",
    "..........",
    "..........",
    "....----..",
    "..........",
    "..........",
    "-----.....",
    "..........",
    "......##..",
    "..........",
    "..........",
    "..----....",
    "..........",
    "..........",
    "......----",
    "..........",
    "..........",
    "#..---....",
    "..........",
    "..........",
    "......---.",
    "..........",
    "..##......",
    "..........",
    "..........",
    "------....",
    "..........",
    "..........",
    ".....-----",
    "..........",
    "..........",
    "---.......",
    "..........",
    "..........",
    ".....###..",
    "..........",
    "..........",
    "-----.....",
    "..........",
    ".P........",
    "##########",
]


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


class Level:
    def __init__(self, level_map):
        # Karakterin çarptığı her şey (bloklar ve ince platformlar)
        self.tiles = pygame.sprite.Group()
        self.player_start = (TILE_SIZE, TILE_SIZE)
        # Bölümün piksel cinsinden boyutu
        self.width = len(level_map[0]) * TILE_SIZE
        self.height = len(level_map) * TILE_SIZE

        # Haritayı satır satır, karakter karakter oku
        for row_index, row in enumerate(level_map):
            for col_index, cell in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                if cell == "#":
                    self.tiles.add(Tile(x, y))
                elif cell == "-":
                    self.tiles.add(Platform(x, y))
                elif cell == "P":
                    # Karakterin ayakları bu kutunun altına gelsin
                    self.player_start = (x + TILE_SIZE // 2, y + TILE_SIZE)
