# Oyun ayarları — bir şeyi değiştirmek istersen önce buraya bak.

# Pencere — telefon gibi dikey ekran (oyun yukarı doğru ilerler)
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 720
TITLE = "Platform Oyunu"
FPS = 60  # saniyedeki kare sayısı

# Renkler (Kırmızı, Yeşil, Mavi) — her biri 0-255 arası
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Karakter
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 50
PLAYER_COLOR = (240, 180, 40)  # turuncu-sarı
PLAYER_SPEED = 5  # her karede kaç piksel gider

# Fizik
GRAVITY = 0.8  # her karede düşme hızına eklenen miktar (büyürse daha hızlı düşer)
JUMP_POWER = 15  # zıplama gücü (büyürse daha yükseğe zıplar)
MAX_FALL_SPEED = 18  # karakter bundan daha hızlı düşemez

# Sonsuz bölüm — harita parçaları chunks.py içinde
LEVEL_SEED = None  # None = her oyunda farklı harita; bir sayı (ör. 42) = hep aynı harita
GENERATE_AHEAD = SCREEN_HEIGHT  # ekranın bu kadar yukarısına kadar parçalar hazır olsun (piksel)
REMOVE_BELOW = SCREEN_HEIGHT  # ekranın bu kadar altında kalan parçalar silinir (piksel)
DIFFICULTY_STEP = 1200  # her bu kadar piksel (30 kare) tırmanınca daha zor parçalar da gelir

# Bloklar (zemin ve platformlar)
TILE_SIZE = 40  # her bloğun kenar uzunluğu (piksel)
TILE_COLOR = (120, 80, 50)  # toprak kahvesi
TILE_TOP_COLOR = (60, 160, 70)  # üstteki çimen yeşili

# İnce platformlar (haritada '-') — bloklar gibi katı, sadece daha ince
PLATFORM_HEIGHT = 12  # kalınlığı (piksel)
PLATFORM_COLOR = (170, 120, 70)  # tahta rengi

# Altınlar (haritada 'C')
COIN_SIZE = 20  # çapı (piksel)
COIN_COLOR = (255, 210, 40)  # altın sarısı
COIN_EDGE_COLOR = (200, 140, 20)  # kenarındaki koyu halka

# Düşmanlar (haritada 'E') — platformun üstünde sağa-sola yürür
ENEMY_WIDTH = 32
ENEMY_HEIGHT = 28
ENEMY_COLOR = (220, 60, 60)  # kırmızı
ENEMY_EYE_COLOR = WHITE
ENEMY_SPEED = 1.5  # her karede kaç piksel yürür
STOMP_BOUNCE = 10  # düşmanın üstüne basınca karakter ne kadar sıçrar

# Can
PLAYER_LIVES = 3  # oyun kaç canla başlar
INVINCIBLE_TIME = 90  # can kaybedince kaç kare dokunulmaz kalır (60 kare = 1 saniye), bu sürede yanıp söner
HURT_BOUNCE = 7  # düşman çarpınca karakter ne kadar sıçrar
LIFE_COLOR = (230, 50, 70)  # sağ üstteki dolu kalpler
LIFE_EMPTY_COLOR = (80, 80, 100)  # kaybedilen can

# Puan
ENEMY_POINTS = 10  # üstüne basılıp yenilen her düşman kaç puan
COIN_POINTS = 5  # her altın kaç puan
HEIGHT_POINTS = 1  # tırmanılan her blok (40 piksel) kaç puan — sadece üstüne basılan en yüksek yer sayılır
SCORE_COLOR = WHITE
SCORE_SHADOW_COLOR = BLACK  # yazının arkasındaki gölge (her zeminde okunsun)
SCORE_FONT_SIZE = 40  # büyük puan yazısı
SCORE_SMALL_FONT_SIZE = 24  # altındaki yükseklik / altın yazısı
HIGHSCORE_FILE = "highscore.txt"  # en yüksek skorun saklandığı dosya (oyun klasöründe)

# Menü ve "Kaybettin" ekranı
OVERLAY_ALPHA = 170  # oyunun üstüne serilen karanlık perdenin koyuluğu (0 = yok, 255 = simsiyah)
TITLE_FONT_SIZE = 64  # büyük başlık yazısı
MENU_FONT_SIZE = 30  # menüdeki diğer yazılar
MENU_SMALL_FONT_SIZE = 22  # kontrol bilgisi gibi küçük yazılar
TITLE_COLOR = (255, 210, 40)  # oyun adı (altın sarısı)
GAME_OVER_COLOR = (230, 50, 70)  # "Kaybettin!" yazısı
RECORD_COLOR = (255, 210, 40)  # "Yeni rekor!" yazısı
HINT_COLOR = (180, 180, 200)  # soluk bilgi yazıları
GAME_OVER_DELAY = 60  # kaybettin ekranında tuşların kaç kare sonra çalışacağı (yanlışlıkla geçilmesin)

# Görünüş — resimler art.py'de kodla piksel piksel çiziliyor (renkleri yukarıdaki ayarlardan alır)
PIXEL_SCALE = 4  # piksel sanatındaki her kare ekranda kaç piksel (büyürse daha "kaba" görünür)
ANIMATION_SPEED = 8  # yürüme ve düşman animasyonunda her resim kaç kare ekranda kalır
COIN_SPIN_SPEED = 7  # altının dönme animasyonu: her resim kaç kare (küçüldükçe hızlı döner)
SKY_TOP_COLOR = (12, 12, 32)  # gökyüzü: ekranın üstü
SKY_BOTTOM_COLOR = (50, 34, 84)  # gökyüzü: ekranın altı (arada yumuşak geçiş)
STAR_COUNT = 70  # arka plandaki yıldız sayısı
STAR_PARALLAX = 0.25  # yıldızlar haritaya göre ne kadar yavaş kaysın (0 = hiç, 1 = harita kadar) — derinlik hissi
PARTICLE_COUNT = 10  # altın alınca / düşman ölünce saçılan parça sayısı
PARTICLE_LIFE = 30  # parçaların kaç kare ekranda kaldığı

# Ses — sesler ve müzik sound.py'de kodla üretiliyor
SOUND_VOLUME = 0.5  # efekt sesleri (0-1 arası)
MUSIC_VOLUME = 0.25  # müzik (0-1 arası)
MUTE_KEY = "m"  # bu tuş sesi açıp kapatır

# Dokunmatik butonlar (telefonda oynamak için; bilgisayarda fareyle de basılır)
SHOW_TOUCH_BUTTONS = True  # False = butonları gizle
TOUCH_BUTTON_SIZE = 84  # butonların çapı (piksel)
TOUCH_BUTTON_MARGIN = 16  # ekran kenarına uzaklık
TOUCH_BUTTON_ALPHA = 60  # saydamlık (0 = görünmez, 255 = tam dolu); basılıyken daha belirgin

# Kamera
CAMERA_SMOOTHNESS = 0.12  # 0-1 arası: 1 = karakteri anında takip eder, küçüldükçe daha yumuşak
CAMERA_PLAYER_Y = 0.6  # karakter ekranın yukarıdan ne kadar aşağısında dursun (0.6 = biraz alt; yukarısı daha çok görünür)
