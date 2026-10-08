# Oyun ayarları — bir şeyi değiştirmek istersen önce buraya bak.
import sys

# Tarayıcıda mı çalışıyor (pygbag ile yapılan web sürümü)? Otomatik anlaşılır, değiştirme.
WEB = sys.platform == "emscripten"

# Pencere — telefon gibi dikey ekran (oyun yukarı doğru ilerler)
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 720
TITLE = "Platform Oyunu"
FPS = 60  # oyun saniyede kaç adım ilerler — telefon daha az kare gösterse de oyun hep bu hızda akar
# Telefon bir an takılırsa bir karede en fazla kaç adım telafi edilir. Fazlası atlanır: oyun bir an
# yavaşlar ama karakter ışınlanmaz (ör. sekme değiştirip dönünce)
MAX_CATCH_UP = 4
# True = ekranın üstünde saniyede kaç kare çizildiği yazar (akıcılık testi için).
# Web'de adresin sonuna #fps eklenince de açılır: .../platform/#fps
SHOW_FPS = False
# Web'de saniyedeki kare 2 saniye üst üste bundan az olursa menüde "Düşük Güç Modu'nu kapat" ipucu çıkar
# (iPhone Düşük Güç Modu'nda tarayıcı saniyede 30 kare gösterir)
LOW_FPS_LIMIT = 45

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

# Zorluk — oyun tırmandıkça yavaş yavaş zorlaşır. Başlangıçta aşağıdaki "kolay" sayılar (ör. ENEMY_SPEED),
# HARD_HEIGHT kadar tırmanınca "en zor" sayılar (ör. ENEMY_SPEED_MAX) geçerli olur; arası karışık
HARD_HEIGHT = 8000  # bu kadar piksel (200 blok) tırmanınca oyun en zor hâline gelir
HARD_CHUNK_BIAS = 3  # en zorda zor parçalar ne kadar sık gelsin (0 = hepsi eşit; 3 = en zor parça kolaydan 7 kat sık)

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

# Hareketli platformlar (haritada 'M') — kendi satırında sağa-sola gidip gelir, üstündekini taşır
MOVING_PLATFORM_SPEED = 2  # her karede kaç piksel gider
MOVING_PLATFORM_COLOR = (100, 150, 220)  # mavi metal

# Kırılan platformlar (haritada 'K') — üstüne basınca titrer, kırılıp düşer, sonra geri gelir
CRUMBLE_DELAY = 30  # üstüne basınca kaç kare sonra kırılır (60 kare = 1 saniye)
CRUMBLE_RESPAWN = 180  # kırıldıktan kaç kare sonra yerine geri gelir
CRUMBLE_COLOR = (150, 140, 130)  # çatlak taş rengi

# Yaylar (haritada 'S') — üstüne basınca çok yükseğe fırlatır
SPRING_POWER = 24  # fırlatma gücü (zıplama 15; 24 ≈ 9 blok yükseğe)
SPRING_COLOR = (80, 220, 120)  # yayın üst plakası (yeşil)
SPRING_SQUASH_TIME = 10  # fırlatınca kaç kare basık görünür

# Düşmanlar (haritada 'E') — platformun üstünde sağa-sola yürür
ENEMY_WIDTH = 32
ENEMY_HEIGHT = 28
ENEMY_COLOR = (220, 60, 60)  # kırmızı
ENEMY_EYE_COLOR = WHITE
ENEMY_SPEED = 1.5  # her karede kaç piksel yürür (oyunun başında)
ENEMY_SPEED_MAX = 3  # en zorda (HARD_HEIGHT) kaç piksel yürür
STOMP_BOUNCE = 10  # düşmanın üstüne basınca karakter ne kadar sıçrar

# Uçan düşmanlar (haritada 'F') — havada kendi satırında sağa-sola uçar; üstüne basılınca ölür
FLYER_COLOR = (150, 90, 220)  # mor yarasa
FLYER_SPEED = 1.2  # her karede kaç piksel uçar (oyunun başında)
FLYER_SPEED_MAX = 2.6  # en zorda kaç piksel uçar
FLYER_BOB = 6  # uçarken kaç piksel aşağı-yukarı süzülür
FLYER_BOB_SPEED = 15  # süzülmenin yavaşlığı (büyürse daha yavaş)
FLYER_FLAP_SPEED = 6  # kanat çırpma: her resim kaç kare ekranda kalır

# Lav — aşağıdan yükselir; değersen bir can gider (kalkan korumaz), son durduğun yere dönersin
LAVA_SPEED = 0.4  # başta her karede kaç piksel yükselir (0.4 ≈ saniyede 0,6 blok)
LAVA_SPEED_MAX = 0.9  # en zorda (HARD_HEIGHT) kaç piksel yükselir (0.9 ≈ saniyede 1,35 blok)
LAVA_DELAY = 180  # oyun başlayınca kaç kare bekler (60 kare = 1 saniye)
LAVA_START_GAP = 80  # başta zeminin kaç piksel altında
LAVA_MAX_GAP = 160  # ekranın altından en fazla bu kadar aşağıda kalır (hızlı tırmansan da peşini bırakmaz)
LAVA_PUSHBACK = 240  # değince lav, döndüğün yerin bu kadar altına çekilir (hemen yine yanma diye)
LAVA_HIT_DEPTH = 10  # ayağın lavın bu kadar içine girince yanarsın (kenarına sürtmek affedilir)
LAVA_WARN_DISTANCE = 240  # lav ekranın bu kadar altındayken ekranın dibi kızarır (yaklaşıyor uyarısı)
LAVA_ANIM_SPEED = 6  # dalga animasyonu: her resim kaç kare ekranda kalır
LAVA_COLOR = (225, 70, 20)  # lavın kendisi (turuncu-kırmızı)
LAVA_TOP_COLOR = (255, 210, 80)  # dalgaların parlak tepesi
LAVA_GLOW_COLOR = (255, 80, 20)  # lav yaklaşırken ekranın dibindeki kızıllık

# Can
PLAYER_LIVES = 3  # oyun kaç canla başlar
INVINCIBLE_TIME = 90  # can kaybedince kaç kare dokunulmaz kalır (60 kare = 1 saniye), bu sürede yanıp söner
HURT_BOUNCE = 7  # düşman çarpınca karakter ne kadar sıçrar
LIFE_COLOR = (230, 50, 70)  # sağ üstteki dolu kalpler
LIFE_EMPTY_COLOR = (80, 80, 100)  # kaybedilen can
HEART_CHANCE = 0.05  # haritadaki her altının kalbe dönüşme ihtimali (0.05 = %5); kalp 1 can verir
HEART_CHANCE_MIN = 0.015  # en zorda kalp ihtimali (yükseldikçe kalpler seyrekleşir)

# Güçlendirmeler — kalp gibi altınların yerine nadiren çıkar; alınca bir süre işe yarar
POWERUP_WARN_TIME = 120  # bitmesine bu kadar kare kala sağ üstteki simgesi yanıp söner
MAGNET_CHANCE = 0.03  # bir altının mıknatısa dönüşme ihtimali (0.03 = %3)
MAGNET_TIME = 600  # mıknatıs kaç kare sürer (60 kare = 1 saniye)
MAGNET_RADIUS = 180  # bu kadar yakındaki altınlar karaktere doğru uçar (piksel)
MAGNET_PULL = 8  # çekilen altın her karede kaç piksel yaklaşır
MAGNET_COLOR = (230, 60, 70)  # kırmızı mıknatıs
SHIELD_CHANCE = 0.03  # bir altının kalkana dönüşme ihtimali
SHIELD_TIME = 600  # kalkan kaç kare sürer — bu sürede düşmanlar zarar veremez, değdiğin düşman ölür
SHIELD_COLOR = (90, 200, 255)  # mavi kalkan ve karakterin etrafındaki baloncuk

# Puan
ENEMY_POINTS = 10  # üstüne basılıp yenilen her düşman kaç puan
HEART_POINTS = 20  # canın doluyken kalp toplarsan kaç puan
COIN_POINTS = 5  # her altın kaç puan
HEIGHT_POINTS = 1  # tırmanılan her blok (40 piksel) kaç puan — sadece üstüne basılan en yüksek yer sayılır
SCORE_COLOR = WHITE
SCORE_SHADOW_COLOR = BLACK  # yazının arkasındaki gölge (her zeminde okunsun)
SCORE_FONT_SIZE = 40  # büyük puan yazısı
SCORE_SMALL_FONT_SIZE = 24  # altındaki yükseklik / altın yazısı
HIGHSCORE_FILE = "highscore.txt"  # en yüksek skorun saklandığı dosya (oyun klasöründe)
HIGHSCORE_KEY = "platform-oyunu-rekor"  # web sürümünde rekorun tarayıcı hafızasındaki adı

# Menü ve "Kaybettin" ekranı
OVERLAY_ALPHA = 170  # oyunun üstüne serilen karanlık perdenin koyuluğu (0 = yok, 255 = simsiyah)
TITLE_FONT_SIZE = 64  # büyük başlık yazısı
MENU_FONT_SIZE = 30  # menüdeki diğer yazılar
MENU_SMALL_FONT_SIZE = 22  # kontrol bilgisi gibi küçük yazılar
TITLE_COLOR = (255, 210, 40)  # oyun adı (altın sarısı)
GAME_OVER_COLOR = (230, 50, 70)  # "Kaybettin!" yazısı
RECORD_COLOR = (255, 210, 40)  # "Yeni rekor!" yazısı
HINT_COLOR = (180, 180, 200)  # soluk bilgi yazıları
SLOW_HINT_COLOR = (255, 210, 40)  # "Düşük Güç Modu'nu kapat" ipucu (sarı, dikkat çeksin)
GAME_OVER_DELAY = 60  # kaybettin ekranında tuşların kaç kare sonra çalışacağı (yanlışlıkla geçilmesin)

# Görünüş — resimler art.py'de kodla piksel piksel çiziliyor (renkleri yukarıdaki ayarlardan alır)
PIXEL_SCALE = 4  # piksel sanatındaki her kare ekranda kaç piksel (büyürse daha "kaba" görünür)
ANIMATION_SPEED = 8  # yürüme ve düşman animasyonunda her resim kaç kare ekranda kalır
COIN_SPIN_SPEED = 7  # altının dönme animasyonu: her resim kaç kare (küçüldükçe hızlı döner)
# Gökyüzü renkleri: (ekranın üstü, ekranın altı). Yükseldikçe sıradakine geçer, sonuncudan sonra başa döner
SKY_THEMES = [
    ((12, 12, 32), (50, 34, 84)),  # mor gece
    ((6, 18, 40), (20, 70, 100)),  # derin mavi
    ((8, 24, 28), (30, 100, 80)),  # kuzey ışıkları yeşili
    ((30, 8, 30), (120, 40, 60)),  # gün batımı kızılı
    ((2, 2, 8), (20, 20, 40)),  # uzay karanlığı
]
SKY_CHANGE_HEIGHT = 2400  # her bu kadar piksel (60 blok) tırmanınca gökyüzü sıradaki renge geçer
SKY_BLEND_HEIGHT = 600  # renk geçişi bu kadar piksel boyunca yavaş yavaş olur
STAR_COUNT = 70  # arka plandaki yıldız sayısı
STAR_PARALLAX = 0.25  # yıldızlar haritaya göre ne kadar yavaş kaysın (0 = hiç, 1 = harita kadar) — derinlik hissi
PARTICLE_COUNT = 10  # altın alınca / düşman ölünce saçılan parça sayısı
PARTICLE_LIFE = 30  # parçaların kaç kare ekranda kaldığı

# Ses — sesler ve müzik sound.py'de kodla üretiliyor
SOUND_VOLUME = 0.5  # efekt sesleri (0-1 arası)
MUSIC_VOLUME = 0.25  # müzik (0-1 arası)
MUTE_KEY = "m"  # bu tuş sesi açıp kapatır
# Web sürümünde ses tamponu (örnek sayısı, 2'nin kuvveti): küçükse ses cızırdar, büyükse sesler
# biraz geç duyulur. 2048 ≈ 0,04 saniye. Telefonda hâlâ cızırdarsa 4096 yap
WEB_AUDIO_BUFFER = 2048

# Dokunmatik butonlar (telefonda oynamak için; bilgisayarda fareyle de basılır)
SHOW_TOUCH_BUTTONS = True  # False = butonları gizle
TOUCH_BUTTON_SIZE = 84  # butonların çapı (piksel)
TOUCH_BUTTON_MARGIN = 16  # ekran kenarına uzaklık
TOUCH_BUTTON_ALPHA = 60  # saydamlık (0 = görünmez, 255 = tam dolu); basılıyken daha belirgin

# Kamera
CAMERA_SMOOTHNESS = 0.12  # 0-1 arası: 1 = karakteri anında takip eder, küçüldükçe daha yumuşak
CAMERA_PLAYER_Y = 0.6  # karakter ekranın yukarıdan ne kadar aşağısında dursun (0.6 = biraz alt; yukarısı daha çok görünür)
