# Oyun ayarları — bir şeyi değiştirmek istersen önce buraya bak.

# Pencere
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 560
TITLE = "Platform Oyunu"
FPS = 60  # saniyedeki kare sayısı

# Renkler (Kırmızı, Yeşil, Mavi) — her biri 0-255 arası
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (30, 30, 50)

# Karakter
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 50
PLAYER_COLOR = (240, 180, 40)  # turuncu-sarı
PLAYER_SPEED = 5  # her karede kaç piksel gider

# Fizik
GRAVITY = 0.8  # her karede düşme hızına eklenen miktar (büyürse daha hızlı düşer)
JUMP_POWER = 15  # zıplama gücü (büyürse daha yükseğe zıplar)
MAX_FALL_SPEED = 18  # karakter bundan daha hızlı düşemez

# Bloklar (zemin ve platformlar) — haritası level.py içinde
TILE_SIZE = 40  # her bloğun kenar uzunluğu (piksel)
TILE_COLOR = (120, 80, 50)  # toprak kahvesi
TILE_TOP_COLOR = (60, 160, 70)  # üstteki çimen yeşili
