# Sonsuz bölüm: harita parçalarını (chunks.py) üst üste dizer, geride kalanları siler.
import math
import random

import pygame

from settings import (
    TILE_SIZE,
    PLAYER_HEIGHT,
    WALKER_KINDS,
    FLYER_KINDS,
    BEE_RANGE,
    BEE_MIN_PATH,
    COIN_SPIN_SPEED,
    MAGNET_CHANCE,
    SHIELD_CHANCE,
    MAGNET_RADIUS,
    MAGNET_PULL,
    SPRING_SQUASH_TIME,
    CRUMBLE_DELAY,
    CRUMBLE_RESPAWN,
    MOVING_PLATFORM_SPEED,
    LEVEL_SEED,
    GENERATE_AHEAD,
    REMOVE_BELOW,
    DIFFICULTY_STEP,
    HARD_CHUNK_BIAS,
)
from chunks import (
    START_CHUNK,
    CHUNKS,
    platform_run,
    moving_platforms,
    free_span,
    walker_spots,
    flyer_spots,
    column_span,
    SOLID,
)
from enemy import Enemy, Slime, Spiky, Cannon, FlyingEnemy, Bee
import art


def hardness(height, mode):
    # Ne kadar zorlaştı: 0 = oyunun başı, 1 = zorluk modunun (settings.DIFFICULTIES) hard_height'ı kadar
    # tırmanıldı (en zor). height piksel, yukarı artı
    return min(1.0, max(0.0, height / mode["hard_height"]))


def blend(easy, hard, t):
    # Kolay ve en zor sayı arasında, zorluk (t) kadar ilerlemiş değer
    return easy + (hard - easy) * t

# Resimler bir kere hazırlanır, aynı türdeki her parça aynı resmi kullanır (art.py)
IMAGES = {}


def image(name):
    if name not in IMAGES:
        IMAGES.update(
            tile=art.tile_image(),
            platform=art.platform_image(),
            coin=art.coin_frames(),
            heart=art.heart_images()["full"],
            magnet=art.magnet_image(),
            shield=art.shield_image(),
            spring=art.spring_frames(),
            crumble=art.crumble_frames(),
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
    unsafe = True  # Player bunu görünce burayı "güvenli yer" saymaz

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


class CrumblingPlatform(pygame.sprite.Sprite):
    # Kırılan platform: üstüne basılınca CRUMBLE_DELAY kare titrer, sonra kırılır (level.tiles'tan
    # çıkar, içinden düşülür). CRUMBLE_RESPAWN kare sonra yerine geri gelir.
    unsafe = True  # Player burayı "güvenli yer" saymaz (yeniden doğunca kırık olabilir)
    GHOST_TIME = 60  # geri gelmeden son kaç karede silik görünür (nereye geleceği belli olsun)

    def __init__(self, x, y):
        super().__init__()
        self.frames = image("crumble")
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.shaking = 0  # kırılmasına kaç kare kaldı (0 = kimse basmadı)
        self.broken = 0  # geri gelmesine kaç kare kaldı (0 = yerinde)

    @property
    def ghost(self):
        return 0 < self.broken <= self.GHOST_TIME

    @property
    def draw_rect(self):
        # Titrerken resim sağa-sola oynar; çarpışma kutusu (rect) yerinde kalır
        if self.shaking:
            return self.rect.move(2 if (self.shaking // 3) % 2 else -2, 0)
        return self.rect

    def step(self, player, tiles):
        # Her karede bir kere çağrılır. Kırıldığı karede "break", geri geldiği karede "back" döner
        if self.broken:
            self.broken -= 1
            if self.ghost:
                self.image = self.frames[2]
            if self.broken == 0:
                if self.rect.colliderect(player.rect):
                    self.broken = 1  # karakter tam buradaysa içine gömülmesin, biraz daha bekle
                    return None
                self.image = self.frames[0]
                tiles.add(self)
                return "back"
            return None
        if not self.shaking and player.standing_on(self):
            self.shaking = CRUMBLE_DELAY
            self.image = self.frames[1]  # çatlaklar büyür
        if self.shaking:
            self.shaking -= 1
            if self.shaking == 0:
                self.broken = CRUMBLE_RESPAWN
                tiles.remove(self)
                return "break"
        return None


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
        self.pos = pygame.Vector2(self.rect.center)  # mıknatısla uçarken ondalıklı konum
        self.pulled = False  # mıknatıs çekmeye başladı mı

    def attract(self, target):
        # Mıknatıs: yeterince yakınsa (bir kere çekilmeye başladıysa artık hep) hedefe doğru uç
        offset = pygame.Vector2(target) - self.pos
        if self.pulled or offset.length() < MAGNET_RADIUS:
            self.pulled = True
            if offset.length() > MAGNET_PULL:
                offset.scale_to_length(MAGNET_PULL)
            self.pos += offset
            self.rect.center = (round(self.pos.x), round(self.pos.y))

    def update(self):
        # Dönme animasyonu: resimler sırayla değişir
        self.spin += 1
        self.image = self.frames[(self.spin // COIN_SPIN_SPEED) % len(self.frames)]


class Pickup(pygame.sprite.Sprite):
    # Altın yerine nadiren çıkan toplanabilir (Level.pick_item): kind = "heart" (1 can) veya
    # bir güçlendirme ("magnet", "shield"). Ne işe yaradığına main.py bakar
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = image(kind)
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
    def __init__(self, mode, seed=LEVEL_SEED):
        # mode = zorluk modunun sayıları (settings.DIFFICULTIES): düşman hızı, kalp ihtimali, parça seçimi
        self.mode = mode
        # Aynı seed (sayı) hep aynı haritayı üretir; None ise her oyun farklı
        self.random = random.Random(seed)
        # Karakterin çarptığı her şey (bloklar ve ince platformlar)
        self.tiles = pygame.sprite.Group()
        # Toplanabilir altınlar
        self.coins = pygame.sprite.Group()
        # Kalpler ve güçlendirmeler (Pickup)
        self.pickups = pygame.sprite.Group()
        # Yaylar
        self.springs = pygame.sprite.Group()
        # Hareketli platformlar (ayrıca tiles içinde de varlar, çünkü katılar)
        self.movers = pygame.sprite.Group()
        # Kırılan platformlar (sağlamken tiles içinde de varlar; kırıkken sadece burada)
        self.crumblers = pygame.sprite.Group()
        # Düşmanlar: platformlarda yürüyenler ve uçanlar
        self.enemies = pygame.sprite.Group()
        # Topçuların attığı ateş topları (hiçbir parçaya ait değiller; çarpınca kendileri söner)
        self.shots = pygame.sprite.Group()
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
        mode = self.mode
        t = hardness(-top, mode)  # yükseklerdeki parçada düşmanlar hızlı ve çok, kalpler seyrek
        if chunk is not START_CHUNK:
            rows = self.add_extra_enemies(rows, t)
        sprites = []
        for row_index, row in enumerate(rows):
            for col_index, cell in enumerate(row):
                x = col_index * TILE_SIZE
                y = top + row_index * TILE_SIZE
                if cell == "#":
                    sprites.append(Tile(x, y))
                elif cell == "-":
                    sprites.append(Platform(x, y))
                elif cell == "K":
                    crumbler = CrumblingPlatform(x, y)
                    sprites.append(crumbler)
                    self.crumblers.add(crumbler)
                elif cell == "C":
                    # Altın; nadiren de kalp veya güçlendirme
                    kind = self.pick_item(t)
                    if kind != "coin":
                        item = Pickup(x, y, kind)
                        sprites.append(item)
                        self.pickups.add(item)
                    else:
                        coin = Coin(x, y)
                        sprites.append(coin)
                        self.coins.add(coin)
                elif cell == "S":
                    spring = Spring(x, y)
                    sprites.append(spring)
                    self.springs.add(spring)
                elif cell == "E":
                    # Yürüyen düşman yeri: altındaki platformun kenarları arasında yürür.
                    # Türü rastgele; sümüğün zıplayacak yeri (platformun iki üstü boş) olmalı
                    left, right = platform_run(rows, row_index, col_index)
                    roof = rows[row_index - 1][left : right + 1]
                    kind = self.pick_enemy(WALKER_KINDS, t, ("slime",) if any(c in SOLID for c in roof) else ())
                    feet = (x + TILE_SIZE // 2, y + TILE_SIZE)
                    if kind == "cannon":
                        enemy = Cannon(*feet, self.shots)
                    else:
                        walker = {"walker": Enemy, "slime": Slime, "spiky": Spiky}[kind]
                        speed = blend(mode["enemy_speed"], mode["enemy_speed_max"], t)
                        enemy = walker(*feet, left * TILE_SIZE, (right + 1) * TILE_SIZE, speed)
                    sprites.append(enemy)
                    self.enemies.add(enemy)
                elif cell == "F":
                    # Uçan düşman yeri: yarasa satırında duvara veya kenara kadar uçar, arı sütununda
                    # aşağı-yukarı (yeri yoksa arı gelmez)
                    path = self.bee_path(rows, top, row_index, col_index)
                    kind = self.pick_enemy(FLYER_KINDS, t, () if path else ("bee",))
                    center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                    speed = blend(mode["flyer_speed"], mode["flyer_speed_max"], t)
                    if kind == "bee":
                        facing = 1 if center[0] < self.width // 2 else -1  # ortaya baksın
                        flyer = Bee(*center, *path, speed, facing)
                    else:
                        left, right = free_span(row, col_index, col_index)
                        flyer = FlyingEnemy(*center, left * TILE_SIZE, (right + 1) * TILE_SIZE, speed)
                    sprites.append(flyer)
                    self.enemies.add(flyer)
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
        self.tiles.add([s for s in sprites if isinstance(s, (Tile, Platform, MovingPlatform, CrumblingPlatform))])
        self.chunks.append((top, self.top, sprites))
        self.top = top
        self.exit_side = chunk["exit"]

    def add_extra_enemies(self, rows, t):
        # Elle çizilenlere ek, rastgele düşmanlar: düşmansız geniş her platforma extra_enemy_chance
        # ihtimalle yürüyen düşman, platform üstündeki boş her satıra extra_flyer_chance ihtimalle yarasa.
        # İhtimaller yükseldikçe (t) artar. Düşmanlar satırlara 'E'/'F' olarak yazılır; parçanın kendisi değişmez
        mode = self.mode
        rows = list(rows)

        def put(r, cells, mark):
            c = self.random.choice(cells)
            rows[r] = rows[r][:c] + mark + rows[r][c + 1 :]

        walker_chance = blend(mode["extra_enemy_chance"], mode["extra_enemy_chance_max"], t)
        for r, cells in walker_spots(rows):
            if self.random.random() < walker_chance:
                put(r, cells, "E")
        flyer_chance = blend(mode["extra_flyer_chance"], mode["extra_flyer_chance_max"], t)
        for r, cells in flyer_spots(rows):  # yürüyen düşman konan satırlara yarasa gelmez
            if self.random.random() < flyer_chance:
                put(r, cells, "F")
        return rows

    def pick_enemy(self, kinds, t, banned=()):
        # Düşman yerine hangi tür gelecek (settings WALKER_KINDS / FLYER_KINDS): ağırlıklar
        # (başta, en zorda), zorluk (t) arttıkça "en zorda"ya kayar. banned = o yere uymayan türler
        options = [kind for kind in kinds if kind not in banned]
        weights = [blend(*kinds[kind], t) for kind in options]
        return self.random.choices(options, weights)[0]

    def bee_path(self, rows, top, row, col):
        # Arının uçabileceği yol: (üst, alt) piksel; yeterince yer yoksa None. top = parçanın tepesi
        first, last = column_span(rows, row, col, BEE_RANGE)
        high = top + first * TILE_SIZE
        low = top + (last + 1) * TILE_SIZE
        # Altındaki platformda duran karakterin kafasına inmesin (karakter bir bloktan uzun,
        # o yüzden iki satır aşağıya kadar bak)
        for below in (last + 1, last + 2):
            if rows[below][col] in SOLID:
                low = min(low, top + below * TILE_SIZE - PLAYER_HEIGHT - 4)
                break
        if low - high < BEE_MIN_PATH * TILE_SIZE:
            return None
        return high, low

    def pick_item(self, t=0.0):
        # Altın karesine ne gelecek: çoğunlukla "coin", nadiren kalp veya güçlendirme.
        # Kalpler zorluk (t) arttıkça seyrekleşir
        chances = (
            ("heart", blend(self.mode["heart_chance"], self.mode["heart_chance_min"], t)),
            ("magnet", MAGNET_CHANCE),
            ("shield", SHIELD_CHANCE),
        )
        roll = self.random.random()
        for kind, chance in chances:
            if roll < chance:
                return kind
            roll -= chance
        return "coin"

    def pick_chunk(self):
        # Girişi, alttaki parçanın çıkışının karşı tarafında olan parçalardan rastgele seç
        entry = "R" if self.exit_side == "L" else "L"
        # Yükseldikçe daha zor parçalar da seçilebilir. Zor modlarda harita baştan yukarıdaymış gibi seçilir
        height = -self.top + self.mode["map_head_start"]
        max_difficulty = 1 + int(height // DIFFICULTY_STEP)
        options = [c for c in CHUNKS if c["entry"] == entry and c["difficulty"] <= max_difficulty]
        # Çok yükseklerde kolay parçalar seyrekleşir, zorlar sıklaşır
        t = hardness(height, self.mode)
        weights = [1 + t * HARD_CHUNK_BIAS * (c["difficulty"] - 1) for c in options]
        return self.random.choices(options, weights)[0]

    def update(self, view_top, view_bottom):
        # Ekranın yukarısı için yeterince parça hazır olsun
        while self.top > view_top - GENERATE_AHEAD:
            self.add_chunk(self.pick_chunk())
        # Ekranın çok altında kalan parçaları unut (bellekten sil)
        while len(self.chunks) > 1 and self.chunks[0][0] > view_bottom + REMOVE_BELOW:
            _, _, sprites = self.chunks.pop(0)
            self.tiles.remove(sprites)
            self.coins.remove(sprites)  # toplanmamış altınlar, kalpler ve düşmanlar da gitsin
            self.pickups.remove(sprites)
            self.springs.remove(sprites)
            self.movers.remove(sprites)
            self.crumblers.remove(sprites)
            self.enemies.remove(sprites)
        self.bottom = self.chunks[0][1]
