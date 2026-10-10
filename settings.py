# Oyun ayarları — bir şeyi değiştirmek istersen önce buraya bak.
import sys

# Tarayıcıda mı çalışıyor (pygbag ile yapılan web sürümü)? Otomatik anlaşılır, değiştirme.
WEB = sys.platform == "emscripten"

# Pencere — telefon gibi dikey ekran (oyun yukarı doğru ilerler)
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 720
TITLE = "Platformin"
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

HARD_CHUNK_BIAS = 3  # en zorda zor parçalar ne kadar sık gelsin (0 = hepsi eşit; 3 = en zor parça kolaydan 7 kat sık)

# Zorluk modları — ana menüdeki "Zorluk" düğmesiyle seçilir (Kolay → Orta → Zor → Ultra Zor); her modun
# rekoru ayrı. Oyun tırmandıkça da zorlaşır: başta "lava_speed" gibi sayılar, "hard_height" kadar tırmanınca
# "lava_speed_max" gibi "en zor" sayılar geçerli olur; arası karışık. Sayıların anlamı:
#   lives / max_lives        oyun kaç canla başlar / kalp toplayarak en fazla kaç can olur
#   hard_height              bu kadar piksel (40 piksel = 1 blok) tırmanınca oyun bu modun en zor hâline gelir
#   map_head_start           harita parçaları baştan bu kadar piksel tırmanılmış gibi seçilir
#                            (0 = kolay parçalarla başlar; hard_height kadar = en zor parçalar hemen ve sık gelir)
#   lava_delay               oyun başlayınca lav kaç kare bekler (60 kare = 1 saniye)
#   lava_speed               lav her karede kaç piksel yükselir (0.4 ≈ saniyede 0,6 blok)
#   enemy_speed              yürüyen düşman her karede kaç piksel gider (karakter 5 gider)
#   flyer_speed              yarasa her karede kaç piksel uçar
#   extra_enemy_chance       parçalardaki düşmansız geniş her platforma fazladan yürüyen düşman gelme ihtimali
#                            (0.25 = %25; "_max" = en zordaki)
#   extra_flyer_chance       bir platformun hemen üstündeki her boş satıra fazladan yarasa gelme ihtimali
#   heart_chance             haritadaki her altının kalbe dönüşme ihtimali (0.05 = %5; "_min" = en zordaki)
# İsteğe bağlı (yazılmazsa aşağıdaki genel ayarlar geçerli; bölümlerde hep genel ayar):
#   walker_kinds / flyer_kinds   düşman türlerinin ağırlıkları (WALKER_KINDS / FLYER_KINDS gibi)
#   cannon_fire_time             topçu kaç karede bir ateş eder (CANNON_FIRE_TIME gibi)
#   boss                         sonsuz oyunda boss (Lav Golemi) gelir; sayıları aşağıda "Boss" kısmında anlatılıyor
DIFFICULTY_NAMES = {"easy": "Kolay", "normal": "Orta", "hard": "Zor", "ultra": "Ultra Zor"}
DEFAULT_DIFFICULTY = "normal"
DIFFICULTIES = {
    "easy": {
        "lives": 4, "max_lives": 4,
        "hard_height": 12000, "map_head_start": 0,
        "lava_delay": 300, "lava_speed": 0.25, "lava_speed_max": 0.65,
        "enemy_speed": 1.2, "enemy_speed_max": 2.2,
        "flyer_speed": 1.0, "flyer_speed_max": 1.9,
        "extra_enemy_chance": 0.05, "extra_enemy_chance_max": 0.09,
        "extra_flyer_chance": 0.01, "extra_flyer_chance_max": 0.04,
        "heart_chance": 0.07, "heart_chance_min": 0.03,
    },
    "normal": {
        "lives": 3, "max_lives": 3,
        "hard_height": 8000, "map_head_start": 0,
        "lava_delay": 180, "lava_speed": 0.4, "lava_speed_max": 0.9,
        "enemy_speed": 1.5, "enemy_speed_max": 3,
        "flyer_speed": 1.2, "flyer_speed_max": 2.6,
        "extra_enemy_chance": 0.08, "extra_enemy_chance_max": 0.15,
        "extra_flyer_chance": 0.02, "extra_flyer_chance_max": 0.08,
        "heart_chance": 0.05, "heart_chance_min": 0.015,
    },
    "hard": {
        "lives": 2, "max_lives": 3,
        "hard_height": 6000, "map_head_start": 2400,
        "lava_delay": 120, "lava_speed": 0.55, "lava_speed_max": 1.0,
        "enemy_speed": 2, "enemy_speed_max": 3.3,
        "flyer_speed": 1.6, "flyer_speed_max": 2.9,
        "extra_enemy_chance": 0.11, "extra_enemy_chance_max": 0.19,
        "extra_flyer_chance": 0.035, "extra_flyer_chance_max": 0.09,
        "heart_chance": 0.03, "heart_chance_min": 0.012,
        # Zor'un boss'u Ultra'nınkinden biraz kolay (kullanıcı kararı): seyrek gelir, yavaş, uzun süre yorgun kalır
        "boss": {
            "every": 350, "health": (3, 5), "crouch": (55, 40), "air": (50, 44), "wave_speed": (3.5, 4.5),
            "tired": (140, 100), "rocks": (0, 1), "minions": (1, 1), "minion_limit": (2, 2), "gems": (5, 8),
        },
    },
    # Baştan en zor: Orta'nın en zor hâliyle başlar, oradan da zorlaşır. Tek can, kalp nadir, lav beklemez.
    # Sonsuz oyunda Zor'dan belirgin zor (kullanıcı: "Ultra, Zor gibi"): lav ~%35 hızlı, düşman ~2 kat, çoğu
    # kirpi/topçu/sümük, topçular sık ateş eder. (Bölümler bu sayılardan sadece düşman hızını ve kalbi alır)
    "ultra": {
        "lives": 1, "max_lives": 3,
        "hard_height": 6000, "map_head_start": 6000,
        "lava_delay": 0, "lava_speed": 1.0, "lava_speed_max": 1.35,
        "enemy_speed": 3, "enemy_speed_max": 3.6,
        "flyer_speed": 2.6, "flyer_speed_max": 3.2,
        "extra_enemy_chance": 0.4, "extra_enemy_chance_max": 0.55,
        "extra_flyer_chance": 0.16, "extra_flyer_chance_max": 0.22,
        "heart_chance": 0.015, "heart_chance_min": 0.008,
        "walker_kinds": {"walker": (2, 1), "slime": (3, 3), "spiky": (2, 3), "cannon": (2, 3)},
        "flyer_kinds": {"bat": (1, 1), "bee": (1, 1)},
        "cannon_fire_time": 100,
        # Ultra'nın boss'u gerçekten zor: sık gelir, hızlı, lav taşı fırlatır, vurulunca daha çok sümük saçar
        "boss": {
            "every": 200, "health": (4, 7), "crouch": (40, 28), "air": (42, 36), "wave_speed": (5, 6.5),
            "tired": (90, 65), "rocks": (1, 3), "minions": (2, 2), "minion_limit": (3, 4), "gems": (8, 12),
        },
    },
}

# Boss: Lav Golemi (boss.py) — sonsuz oyunda Zor ve Ultra Zor'da her "every" m'de bir boss arenası gelir.
# Arenaya girince alttaki kapı kapanır ve lav durur; golem yenilince yukarı çıkan basamaklar belirir, lav yine
# yükselir. Golem karaktere doğru zıplar, yere çakılınca iki yana alev dalgası yayılır (üstünden atla). İndikten
# sonra alevi söner ve yorulur: o zaman kafasına basılır. Alevi yanarken dokunan yanar. Vurulunca lav sümükleri
# saçar. Moddaki "boss" sayıları (ilk boss, en güçlü boss): sonraki her boss biraz daha güçlü, BOSS_HARDEST'ten
# sonra hep en güçlüsü. Sayıların anlamı:
#   every          kaç m'de bir boss gelir          health        kaç kez kafasına basılmalı
#   crouch         zıplamadan önce kaç kare çömelir (uyarı)       air           zıplayınca kaç kare havada kalır
#   wave_speed     alev dalgası her karede kaç piksel gider        tired         indikten sonra kaç kare yorgun kalır
#   rocks          zıplamadan önce kaç lav taşı fırlatır          minions       her vuruşta kaç lav sümüğü saçar
#   minion_limit   arenada aynı anda en fazla kaç lav sümüğü olur  gems          yenilince kaç elmas düşürür
BOSS_TEST = False  # True = ilk boss BOSS_TEST_HEIGHT m'de gelir (denemek için); web'de adres sonu #boss
BOSS_TEST_HEIGHT = 20
BOSS_HARDEST = 3  # kaçıncı boss'ta en güçlü hâline ulaşır (0 = ilk boss; 3 = dördüncüsü)
BOSS_GRAVITY = 0.9  # golemin düşüşü (karakterinki 0.8; ağır olduğu için biraz daha hızlı düşer)
BOSS_WAKE_TIME = 100  # arenaya girince golem kaç kare kükrer (bu arada saldırmaz)
BOSS_ROCK_GAP = 28  # lav taşları arasında kaç kare
BOSS_ROCK_FLIGHT = 52  # lav taşı kaç karede yere iner (karakterin taş atıldığı andaki yerine)
BOSS_HIT_TIME = 50  # kafasına basılınca kaç kare yanıp söner (bu arada zararsızdır, kenara kayar)
BOSS_HIT_SLIDE = 6  # vurulunca karakterden uzağa ne hızla kayar (piksel/kare; giderek yavaşlar)
BOSS_DEATH_TIME = 90  # yenilince kaç kare titreyip patlar
BOSS_RAGE = 0.85  # her vuruşta çömelme süresi bununla çarpılır (sinirlendikçe hızlanır)
BOSS_MIN_CROUCH = 20  # çömelme en az kaç kare (sinirlense de zıplayacağı görülsün)
BOSS_STOMP_BOUNCE = 13  # kafasına basınca karakter ne kadar sıçrar
BOSS_LAVA_GRACE = 240  # golem yenilince lav kaç kare bekler (60 kare = 1 saniye)
BOSS_POINTS = 100  # golemi yenmek kaç puan
BOSS_SHAKE = 14  # golem yere çakılınca ekran kaç kare sallanır
BOSS_BANNER_TIME = 150  # "Lav Golemi" / "Golem yenildi!" yazısı kaç kare görünür
BOSS_ROCK_COLOR = (90, 76, 84)  # golemin taşı (bazalt)
MAGMA_COLOR = (240, 110, 40)  # golemin saçtığı lav sümükleri (turuncu)
BOSS_BAR_COLOR = (240, 90, 40)  # ekranın üstündeki can çubuğu

# Bölümler — "Oyna → Bölümler"; her bölümün haritası, düşmanları, lavı stages.py'de. Bir bölüm bitince
# (en az 1 yıldız) sıradakinin kilidi açılır. Yıldızlar: bitirdin / altınların çoğu / hiç can kaybetmeden
# Her zorluğun kendi bölüm listesi var (stages.py STAGE_SETS); bölüme kaç canla başlanır, kalple en fazla kaç can
STAGE_LIVES = {"easy": (4, 4), "normal": (3, 3), "hard": (2, 3), "ultra": (1, 3)}
ITEM_BOOST = 5  # bölümde tanıtılan güçlendirme (stages.py "boost") kaç kat sık çıksın
STAR_COIN_SHARE = 0.6  # 2. yıldız için bölümdeki altınların en az ne kadarı toplanmalı (0.6 = %60)
FOCUS_WEIGHT = 4  # bölümde yeni tanıtılan şeyin (ör. yay) olduğu parçalar kaç kat sık gelsin
STAGE_INTRO_TIME = 180  # bölüm başlarken adı ve "Yeni: ..." yazısı kaç kare görünür
STAGE_CLEAR_DELAY = 70  # bölüm bitti ekranında düğmeler kaç kare sonra çıkar (yıldızlar o arada belirir)
UNLOCK_ALL_STAGES = False  # True = bütün bölümler açık (deneme için)
FLAG_COLOR = (60, 200, 110)  # bitiş bayrağının yeşili (beyazla dama)
STAR_COLOR = (255, 210, 40)  # kazanılan yıldız
STAR_EMPTY_COLOR = (80, 80, 100)  # kazanılmayan yıldız
LOCKED_COLOR = (60, 56, 90)  # kilitli bölüm kutusu
PROGRESS_EMPTY_COLOR = (60, 56, 90)  # oyunda sol üstteki "bayrağa ne kadar kaldı" çubuğunun boş kısmı

# Karakterler (skinler) — ana menüdeki "Karakterler" ekranı. Çizimleri, fiyatları ve görevleri skins.py'de.
# Sadece görünüş: hız ve zıplama her skinde aynı. İki para var, toplanınca cüzdanda birikir: Renkler altınla,
# Karakterler elmasla alınır; efsaneviler parayla değil görevle açılır ve arkalarında iz bırakır (trail.py)
UNLOCK_ALL_SKINS = False  # True = bütün skinler açık (deneme için)
# Elmas — haritada altının yerine nadiren çıkar (yükseldikçe biraz daha sık); ayrıca başarılar elmas verir
GEM_CHANCE = 0.03  # bir altının elmasa dönüşme ihtimali, oyunun başında (0.03 = %3; 100 m'de ~1 elmas)
GEM_CHANCE_MAX = 0.07  # en zorda / en yüksekte
GEM_POINTS = 25  # her elmas kaç puan
GEMS_PER_STAR = 1  # bölümde İLK KEZ kazanılan her yıldız kaç elmas verir
GEM_RECORD_METERS = 10  # sonsuz oyunda rekoru her bu kadar m geçince 1 elmas (rekor kırılınca en az 1).
# O modda ilk oyunda (rekor 0) ödül yok — yoksa bütün tırmanış "rekoru geçmek" sayılıp çok elmas veriyordu
GEM_RECORD_MAX = 5  # rekor ödülü bir oyunda en fazla kaç elmas
GEM_COLOR = (60, 220, 150)  # zümrüt yeşili
GEM_SPARKLE_SPEED = 14  # elmasın ışıltısı: her resim kaç kare ekranda kalır
SKIN_SELECTED_COLOR = (90, 220, 120)  # giyilen skinin kutusundaki işaret
LEGENDARY_COLOR = (255, 190, 60)  # efsanevi skinin adı
TRAIL_LIMIT = 60  # izde aynı anda en fazla kaç parçacık olur (telefonda yavaşlamasın)

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

# Düşmanlar (haritada 'E') — platformun üstünde sağa-sola yürür (hızları yukarıda, DIFFICULTIES içinde).
# Yerine bazen sümük, kirpi veya topçu gelir (aşağıda, WALKER_KINDS)
ENEMY_WIDTH = 32
ENEMY_HEIGHT = 28
ENEMY_COLOR = (220, 60, 60)  # kırmızı
ENEMY_EYE_COLOR = WHITE
STOMP_BOUNCE = 10  # düşmanın üstüne basınca karakter ne kadar sıçrar

# Uçan düşmanlar (haritada 'F') — havada kendi satırında sağa-sola uçar; üstüne basılınca ölür (hızı DIFFICULTIES'te).
# Yerine bazen arı gelir (aşağıda, FLYER_KINDS)
FLYER_COLOR = (150, 90, 220)  # mor yarasa
FLYER_BOB = 6  # uçarken kaç piksel aşağı-yukarı süzülür
FLYER_BOB_SPEED = 15  # süzülmenin yavaşlığı (büyürse daha yavaş)
FLYER_FLAP_SPEED = 6  # kanat çırpma: her resim kaç kare ekranda kalır

# Düşman türleri — haritadaki her yürüyen düşman yeri (E) ve uçan düşman yeri (F) rastgele bir türe dönüşür.
# Düşman SAYISI değişmez (kullanıcı kararı: oran böyle kalsın), sadece çeşidi. Sayılar ağırlık:
# (başta, en zorda) — büyük sayı = daha sık. Yükseldikçe "en zorda" değerine kayar
WALKER_KINDS = {"walker": (4, 2), "slime": (2, 3), "spiky": (1, 2), "cannon": (1, 2)}
FLYER_KINDS = {"bat": (2, 1), "bee": (1, 1)}

# Zıplayan sümük — yürür, arada bir önce basılır (uyarı), sonra zıplar
SLIME_COLOR = (90, 200, 90)  # yeşil
SLIME_SPEED = 0.8  # yürüme hızı, yürüyen düşmanın hızının kaç katı
SLIME_JUMP_POWER = 9  # zıplama gücü (9 ≈ 1,2 blok yükseğe)
SLIME_JUMP_TIME = 110  # kaç karede bir zıplar (60 kare = 1 saniye)
SLIME_SQUASH_TIME = 20  # zıplamadan önce kaç kare basılıp bekler

# Dikenli kirpi — üstüne basılamaz (basarsan canın gider), sadece kalkan öldürür; üstünden atla
SPIKY_COLOR = (150, 105, 65)  # kahverengi
SPIKY_SPEED = 0.6  # yürüme hızı, yürüyen düşmanın hızının kaç katı (yavaş)

# Topçu — yerinde durur; karakter yakınındayken ona dönüp ateş topu atar, atmadan önce namlusu kızarır
CANNON_COLOR = (140, 140, 165)  # metal grisi
CANNON_FIRE_TIME = 150  # kaç karede bir ateş eder
CANNON_WARN_TIME = 40  # ateş etmeden kaç kare önce kızarır (uyarı)
CANNON_RANGE = 160  # karakter dikeyde bu kadar yakındaysa (piksel) ateş eder
FIREBALL_SPEED = 3  # ateş topu her karede kaç piksel gider (katı bir şeye çarpınca söner)
FIREBALL_COLOR = (255, 130, 30)  # turuncu

# Arı — kendi sütununda aşağı-yukarı uçar; altındaki platformda duranın kafasına inmez
BEE_COLOR = (250, 200, 40)  # sarı
BEE_SPEED = 0.8  # uçuş hızı, yarasanın hızının kaç katı
BEE_RANGE = 2  # başladığı yerden en fazla kaç blok yukarı ve aşağı uçar
BEE_MIN_PATH = 2  # yolu en az kaç blok olmalı (yer yoksa arı yerine yarasa gelir)

# Lav — aşağıdan yükselir; değersen bir can gider, son durduğun yere dönersin (kalkan varsa can gitmez, aşağıda).
# Hızı ve bekleme süresi her zorluk modunda farklı (yukarıda, DIFFICULTIES)
LAVA_START_GAP = 80  # başta zeminin kaç piksel altında
LAVA_MAX_GAP = 160  # ekranın altından en fazla bu kadar aşağıda kalır (hızlı tırmansan da peşini bırakmaz)
LAVA_PUSHBACK = 240  # değince lav, döndüğün yerin bu kadar altına çekilir (hemen yine yanma diye)
LAVA_HIT_DEPTH = 10  # ayağın lavın bu kadar içine girince yanarsın (kenarına sürtmek affedilir)
LAVA_WARN_DISTANCE = 240  # lav ekranın bu kadar altındayken ekranın dibi kızarır (yaklaşıyor uyarısı)
LAVA_ANIM_SPEED = 6  # dalga animasyonu: her resim kaç kare ekranda kalır
LAVA_COLOR = (225, 70, 20)  # lavın kendisi (turuncu-kırmızı)
LAVA_TOP_COLOR = (255, 210, 80)  # dalgaların parlak tepesi
LAVA_GLOW_COLOR = (255, 80, 20)  # lav yaklaşırken ekranın dibindeki kızıllık

# Can — kaç canla başlanacağı ve kalp ihtimali her zorluk modunda farklı (yukarıda, DIFFICULTIES)
INVINCIBLE_TIME = 90  # can kaybedince kaç kare dokunulmaz kalır (60 kare = 1 saniye), bu sürede yanıp söner
HURT_BOUNCE = 7  # düşman çarpınca karakter ne kadar sıçrar
LIFE_COLOR = (230, 50, 70)  # sağ üstteki dolu kalpler
LIFE_EMPTY_COLOR = (80, 80, 100)  # kaybedilen can

# Güçlendirmeler — kalp gibi altınların yerine nadiren çıkar; alınca bir süre işe yarar
POWERUP_WARN_TIME = 120  # bitmesine bu kadar kare kala sağ üstteki simgesi yanıp söner
MAGNET_CHANCE = 0.03  # bir altının mıknatısa dönüşme ihtimali (0.03 = %3)
MAGNET_TIME = 600  # mıknatıs kaç kare sürer (60 kare = 1 saniye)
MAGNET_RADIUS = 180  # bu kadar yakındaki altınlar karaktere doğru uçar (piksel)
MAGNET_PULL = 8  # çekilen altın her karede kaç piksel yaklaşır
MAGNET_COLOR = (230, 60, 70)  # kırmızı mıknatıs
SHIELD_CHANCE = 0.03  # bir altının kalkana dönüşme ihtimali
SHIELD_TIME = 600  # kalkan kaç kare sürer — bu sürede düşmanlar zarar veremez, değdiğin düşman ölür
SHIELD_LAVA_BOUNCE = 24  # kalkanla lava düşünce can gitmez, bu güçle yukarı fırlarsın (24 ≈ 9 blok) ve kalkan kırılır
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
HIGHSCORE_FILE = "highscore.txt"  # en yüksek puanın saklandığı dosya (oyun klasöründe)
HIGHSCORE_KEY = "platform-oyunu-rekor"  # web sürümünde en yüksek puanın tarayıcı hafızasındaki adı
# Asıl rekor: en yüksek tırmanış (blok = "m"). Oyunda o yükseklikte "Rekor" çizgisi görünür
BEST_HEIGHT_FILE = "bestheight.txt"
BEST_HEIGHT_KEY = "platform-oyunu-yukseklik-rekor"
RECORD_TOAST_TIME = 120  # rekoru geçince "YENİ REKOR!" yazısı kaç kare görünür
# İstatistikler (oynanan oyun, toplam altın...) ve seçenekler (ses, zorluk) — aynı şekilde saklanır
STATS_FILE = "stats.json"
STATS_KEY = "platform-oyunu-istatistik"
OPTIONS_FILE = "options.json"
OPTIONS_KEY = "platform-oyunu-secenekler"
STAGES_FILE = "stages.json"  # her bölümün en iyi yıldızı
STAGES_KEY = "platform-oyunu-bolumler"
SKINS_FILE = "skins.json"  # cüzdandaki altın, satın alınan ve seçili skin
SKINS_KEY = "platform-oyunu-karakterler"
ADS_FILE = "ads.json"  # bugün reklamla kaç kez bedava elmas alındı (ads.py)
ADS_KEY = "platform-oyunu-reklam"

# Menü düğmeleri
BUTTON_WIDTH = 250
BUTTON_HEIGHT = 52
BUTTON_FONT_SIZE = 32
BUTTON_COLOR = (40, 36, 80)  # düğmenin içi
BUTTON_FOCUS_COLOR = (90, 70, 150)  # seçili (klavyeyle üstüne gelinen / fareyle üstünde) düğme
BUTTON_BORDER_COLOR = (150, 140, 210)
BUTTON_FOCUS_BORDER_COLOR = (255, 210, 40)
BUTTON_CLICK_GAP = 250  # iki tıklama arası en az kaç milisaniye (telefonda bir dokunuş iki kez sayılmasın)
PAUSE_BUTTON_SIZE = 36  # oyun sırasında sağ üstteki durdur düğmesi (piksel)
# Ses ekranındaki kaydırma çubukları (müzik / efekt seviyesi)
VOLUME_STEPS = 10  # çubuk kaç basamak (10 = %10'ar)
SLIDER_HEIGHT = 14  # çubuğun kalınlığı
SLIDER_KNOB_RADIUS = 15  # tutulan yuvarlak düğmenin yarıçapı
SLIDER_TRACK_COLOR = (40, 36, 80)  # çubuğun boş kısmı
SLIDER_FILL_COLOR = (255, 210, 40)  # dolu kısmı (ses seviyesi)
SLIDER_MUTED_COLOR = (110, 110, 130)  # ses kapalıyken dolu kısım

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
# Devam Et: canlar bitince elmasla kaldığın yerden devam (main.py "revive" durumu). Bir oyunda tekrar tekrar
# kullanılabilir ama her seferinde fiyat bir öncekinin 2 katı (3, 6, 12, 24...). Reklamla devam oyun başına bir kez.
# Düğmeler de GAME_OVER_DELAY kare sonra çıkar (ölürken basılan zıplama tuşu elması harcamasın)
REVIVE_GEMS = 3  # ilk Devam Et kaç elmas (cüzdanda o anki fiyat kadar yoksa ve reklam da yoksa teklif hiç çıkmaz)
REVIVE_TIME = 480  # düğmeler çıktıktan sonra teklif kaç kare durur (60 kare = 1 saniye); bitince "Kaybettin"
REVIVE_INVINCIBLE = 150  # devam edince kaç kare dokunulmaz (normal can kaybında INVINCIBLE_TIME)

# Reklamlar (ads.py; para kazanma hazırlığı). Oyuncu reklamı KENDİSİ seçer: Devam Et, oyun sonunda 2 kat elmas,
# Karakterler ekranında bedava elmas. Şimdilik gerçek reklam yok → reklam düğmeleri görünmez
ADS_TEST = False  # True = deneme reklamı (sahte, AD_TEST_TIME kare) ile reklamlı ekranları dene; web'de adres sonu #reklam
AD_TEST_TIME = 180  # deneme reklamı kaç kare sürer (60 kare = 1 saniye)
AD_RETRY_TIME = 30000  # reklam gelmezse kaç milisaniye yeniden teklif edilmez
ADS_AFTER_GAMES = 1  # oyun açıldıktan sonra bu kadar oyun bitmeden reklam teklif edilmez (önce biraz oynasın)
FREE_GEMS = 2  # Karakterler ekranında bir reklam kaç elmas verir
FREE_GEM_ADS = 3  # günde en fazla kaç kez
NOTE_TIME = 150  # ekranın altındaki kısa bilgi yazısı ("Şu an reklam yok...") kaç kare görünür
AD_COLOR = (255, 210, 40)  # reklam düğmelerindeki ▶ işareti

# Oyunun adı (logo): giriş ekranında ve ana menüde aynı yerde, kalın piksel harflerle (art.py, LOGO_FONT)
LOGO_PIXEL = 3  # harflerin her ince karesi kaç piksel (büyürse logo büyür)
LOGO_TOP = 140  # logonun üst kenarı (y)
LOGO_LINE_GAP = 10  # iki satır arası (piksel)
LOGO_COLORS = [  # her satırın (üst rengi, alt rengi): ilk satır altın, ikinci satır lav gibi
    ((255, 240, 150), (250, 160, 30)),
    ((255, 205, 100), (235, 85, 35)),
]
LOGO_OUTLINE_COLOR = (40, 18, 48)  # harflerin koyu kenarı
LOGO_WAVE = 3  # harfler kaç piksel aşağı yukarı dalgalanır
LOGO_WAVE_TIME = 1.6  # bir dalga kaç saniye sürer
LOGO_SHINE_TIME = 4  # kaç saniyede bir logonun üstünden parıltı geçer

# Giriş ekranı (oyun açılınca ilk ekran; dokununca ana menü gelir)
TITLE_SCALE = 2  # karakter, adacık ve altınlar kaç kat büyük çizilir
TITLE_WALK_SPEED = 1  # karakter adacıkta her karede kaç piksel yürür
TITLE_HOP_TIME = 110  # karakter kaç karede bir zıplar (60 kare = 1 saniye)
TITLE_HOP_POWER = 9  # zıplama gücü
TITLE_LAUNCH_POWER = 22  # dokununca karakter bu güçle yukarı fırlar
TITLE_LEAVE_TIME = 40  # dokunduktan sonra ana menünün belirmesi kaç kare sürer
TITLE_EMBER_CHANCE = 0.35  # her karede lavdan kıvılcım çıkma ihtimali

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
