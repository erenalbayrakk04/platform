# Harita: parçaları (chunks.py) üst üste dizer, geride kalanları siler. Sonsuz oyunda parçalar rastgele
# ve sonsuz; bölümde (stages.py) baştan seçilir ve tepede bayrakla biter.
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
    CANNON_FIRE_TIME,
    COIN_SPIN_SPEED,
    MAGNET_CHANCE,
    SHIELD_CHANCE,
    GEM_CHANCE,
    GEM_CHANCE_MAX,
    GEM_SPARKLE_SPEED,
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
    FOCUS_WEIGHT,
)
from chunks import (
    START_CHUNK,
    CHUNKS,
    FINISH_CHUNKS,
    ARENA_CHUNKS,
    platform_run,
    moving_platforms,
    free_span,
    walker_spots,
    flyer_spots,
    column_span,
    SOLID,
)
from stages import allowed_chunks, focused
from enemy import Enemy, Slime, Spiky, Cannon, FlyingEnemy, Bee
from boss import Golem, Arena, boss_numbers
import art
import theme


def hardness(height, mode):
    # Ne kadar zorlaştı: 0 = oyunun başı, 1 = zorluk modunun (settings.DIFFICULTIES) hard_height'ı kadar
    # tırmanıldı (en zor). height piksel, yukarı artı. Bölümlerde (stages.py) "hardness" = (baştaki, sondaki)
    t = min(1.0, max(0.0, height / mode["hard_height"]))
    low, high = mode.get("hardness", (0.0, 1.0))
    return low + (high - low) * t


def blend(easy, hard, t):
    # Kolay ve en zor sayı arasında, zorluk (t) kadar ilerlemiş değer
    return easy + (hard - easy) * t

# Resimler bir kere hazırlanır (her tema için ayrı), aynı türdeki her parça aynı resmi kullanır (art.py).
# Blok ve platformun resmi sıradaki yerine göre: ("tile", (sol uç mu, sağ uç mu)) — Modern temada uçlar yuvarlak
IMAGES = {}
MAKE_IMAGE = {
    "coin": art.coin_frames,
    "heart": lambda: art.heart_images()["full"],
    "magnet": art.magnet_image,
    "shield": art.shield_image,
    "gem": art.gem_frames,
    "spring": art.spring_frames,
    "crumble": art.crumble_frames,
    "flag": art.flag_frames,
}


def image(name, ends=None):
    if name == "tile":
        return theme.cached(IMAGES, (name, ends), lambda: art.tile_image(ends))
    if name == "platform":
        return theme.cached(IMAGES, (name, ends), lambda: art.platform_image(ends))
    return theme.cached(IMAGES, name, MAKE_IMAGE[name])


def run_ends(row, col):
    # Satırdaki aynı türden yan yana karelerin (blok / platform sırası) ucunda mı: (sol uç mu, sağ uç mu)
    cell = row[col]
    return col == 0 or row[col - 1] != cell, col == len(row) - 1 or row[col + 1] != cell


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, ends=(True, True)):
        super().__init__()
        self.ends = ends  # sıranın ucunda mı (Modern temada gölgesi uçta yana doğru silinir)
        self.image = image("tile", ends)
        self.rect = self.image.get_rect(topleft=(x, y))


class Platform(pygame.sprite.Sprite):
    # İnce platform: karenin sadece üst kısmını kaplar, blok gibi katıdır
    def __init__(self, x, y, ends=(True, True)):
        super().__init__()
        self.ends = ends
        self.image = image("platform", ends)
        self.rect = self.image.get_rect(topleft=(x, y))


def ghost_image(solid):
    # Silik hâli (boss arenasının basamakları golem yenilene kadar böyle görünür)
    ghost = solid.copy()
    ghost.set_alpha(70)
    return ghost


class Stair(Platform):
    # Boss arenasının basamağı (haritada 'Y'): golem yenilene kadar silik ve katı değil (level.tiles'ta yok);
    # yenilince belirir (boss.Arena.win)
    def __init__(self, x, y, ends=(True, True)):
        super().__init__(x, y, ends)
        self.solid_image = self.image
        self.image = theme.cached(IMAGES, ("stair ghost", ends), lambda: ghost_image(self.solid_image))

    def appear(self):
        self.image = self.solid_image


class MovingPlatform(pygame.sprite.Sprite):
    # Hareketli platform: left-right piksel arasında gidip gelir; katıdır (level.tiles içinde).
    # Üstünde duran karakteri main.py taşır (Player.carry)
    unsafe = True  # Player bunu görünce burayı "güvenli yer" saymaz
    ends = (True, True)  # tek parça (iki ucu da açık)

    def __init__(self, x, y, cells, left, right):
        super().__init__()
        self.image = theme.cached(IMAGES, ("mover", cells), lambda: art.moving_platform_image(cells))
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
    ends = (True, True)  # her kare ayrı taş
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
    # Altın yerine nadiren çıkan toplanabilir (Level.pick_item): kind = "heart" (1 can), bir güçlendirme
    # ("magnet", "shield") ya da "gem" (elmas: skin parası, ışıldar). Ne işe yaradığına main.py bakar
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        frames = image(kind)
        self.frames = frames if isinstance(frames, list) else [frames]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
        self.base_y = self.rect.y
        self.time = 0

    def update(self):
        # Yavaşça aşağı yukarı süzülsün (birden çok resmi varsa sırayla değişsin)
        self.time += 1
        self.rect.y = self.base_y + round(3 * math.sin(self.time / 12))
        self.image = self.frames[(self.time // GEM_SPARKLE_SPEED) % len(self.frames)]


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


class Goal(pygame.sprite.Sprite):
    # Bölümün sonundaki bayrak: altındaki zirveye oturur, dalgalanır; karakter değince bölüm biter (main.py)
    def __init__(self, x, y):
        super().__init__()
        self.frames = image("flag")
        self.image = self.frames[0]
        self.rect = self.image.get_rect(midbottom=(x + TILE_SIZE // 2, y + TILE_SIZE))
        self.time = 0

    def update(self):
        self.time += 1
        self.image = self.frames[(self.time // 8) % len(self.frames)]


class Level:
    # Koordinatlar: en alttaki zeminin altı y = 0; yukarı çıktıkça y eksiye iner.
    def __init__(self, mode, seed=LEVEL_SEED, stage=None):
        # mode = zorluk modunun sayıları (settings.DIFFICULTIES; bölümde stages.stage_mode): düşman hızı,
        # kalp ihtimali, parça seçimi. stage = bölüm (stages.py) ya da None (sonsuz oyun)
        self.mode = mode
        self.stage = stage
        # Aynı seed (sayı) hep aynı haritayı üretir; None ise her oyun farklı
        self.random = random.Random(seed)
        # Düşman türleri ve ağırlıkları (bölümde sadece o bölümünkiler)
        self.walker_kinds = mode.get("walker_kinds", WALKER_KINDS)
        self.boost = stage["boost"] if stage else None  # henüz konmamış tanıtılan güçlendirme
        self.flyer_kinds = mode.get("flyer_kinds", FLYER_KINDS)
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
        # Bölümün sonundaki bayrak (sonsuz oyunda boş)
        self.goals = pygame.sprite.Group()
        # Boss (boss.py): sonsuz oyunda modun "boss" sayıları varsa her boss_every m'de bir arena gelir.
        # bosses = golem (çizim için), arena = en son konan arena (yoksa None)
        self.bosses = pygame.sprite.Group()
        self.arena = None
        self.boss_config = mode.get("boss") if stage is None else None
        self.boss_count = 0  # şimdiye kadar konan arena
        self.next_boss = self.boss_config["every"] if self.boss_config else None  # sıradaki arenanın yüksekliği (m)
        self.coins_total = 0  # haritaya konan altın sayısı (bölümde yıldız için)
        self.width = len(START_CHUNK["rows"][0]) * TILE_SIZE
        self.player_start = (TILE_SIZE, 0)
        # Şu an bellekteki parçalar, aşağıdan yukarıya: (üst y, alt y, sprite listesi)
        self.chunks = []
        self.top = 0  # en üstteki parçanın tepesi
        self.bottom = 0  # en alttaki parçanın altı — bunun altına düşen kaybeder
        self.exit_side = None  # en üstteki parçanın çıkışı hangi tarafta
        self.add_chunk(START_CHUNK)
        # Bölümde bütün parçalar baştan seçilir (sonunda bitiş parçası): bayrağın yüksekliği baştan belli olur.
        # Parçalar yine ekrana yaklaştıkça kurulur. goal_height = bayrağın durduğu zirve, başlangıçtan kaç blok
        self.plan = []
        self.goal_height = None
        if stage:
            self.make_plan()

    def make_plan(self):
        # Bölümün tanıttığı şey (focus) rastgele seçimde hiç gelmediyse baştan seç: bu sefer ilk parça onlardan
        self.plan, self.goal_height = self.plan_chunks()
        if self.stage["focus"] and not any(focused(self.stage, chunk) for chunk in self.plan):
            self.plan, self.goal_height = self.plan_chunks(force_focus=True)

    def plan_chunks(self, force_focus=False):
        # Bölümün parça sırası (sonunda bitiş parçası) ve bayrağın zirvesinin yüksekliği (blok)
        finish_rise = len(FINISH_CHUNKS["L"]["rows"]) - FINISH_CHUNKS["L"]["goal_row"]  # zirve, parçanın altından kaç blok yukarıda
        goal_y = self.player_start[1] - self.stage["goal"] * TILE_SIZE
        plan = []
        top, side = self.top, self.exit_side
        while top - finish_rise * TILE_SIZE > goal_y:
            chunk = self.pick_chunk(top, side, force_focus and not plan)
            plan.append(chunk)
            top -= len(chunk["rows"]) * TILE_SIZE
            side = chunk["exit"]
        plan.append(FINISH_CHUNKS["R" if side == "L" else "L"])
        return plan, (self.player_start[1] - (top - finish_rise * TILE_SIZE)) // TILE_SIZE

    def add_chunk(self, chunk):
        # Parçayı şu anki tepenin hemen üstüne yerleştir
        rows = chunk["rows"]
        top = self.top - len(rows) * TILE_SIZE
        mode = self.mode
        t = hardness(-top, mode)  # yükseklerdeki parçada düşmanlar hızlı ve çok, kalpler seyrek
        arena = "floor_row" in chunk  # boss arenası: fazladan düşman yok, kendi işaretleri var (X, Y, B, H)
        numbers = boss_numbers(self.boss_config, self.boss_count) if arena else None  # bu golemin sayıları
        if chunk is not START_CHUNK and not arena:
            rows = self.add_extra_enemies(rows, t)
        # Bölümde olmayan düşman türlerinin yerleri boş kalır (parça yine çıkılabilir; düşmanlar katı değil)
        if not self.walker_kinds:
            rows = [row.replace("E", ".") for row in rows]
        if not self.flyer_kinds:
            rows = [row.replace("F", ".") for row in rows]
        sprites = []
        gates, stairs, golem = [], [], None  # arenanın kapısı, basamakları ve golemi (katı değiller, tiles'a sonra girer)
        for row_index, row in enumerate(rows):
            for col_index, cell in enumerate(row):
                x = col_index * TILE_SIZE
                y = top + row_index * TILE_SIZE
                if cell in "#X" and arena:  # kapı kapanınca zemin tek parça görünsün
                    block = Tile(x, y, run_ends(row.replace("X", "#"), col_index))
                    (gates if cell == "X" else sprites).append(block)
                elif cell == "Y":
                    stairs.append(Stair(x, y, run_ends(row, col_index)))
                elif cell == "B":  # golem: ayakları altındaki zeminde, bütün arenada zıplar
                    golem = Golem(x + TILE_SIZE // 2, y + TILE_SIZE, 0, self.width, numbers)
                elif cell == "H":  # arenadan önce kesin bir kalp
                    item = Pickup(x, y, "heart")
                    sprites.append(item)
                    self.pickups.add(item)
                elif cell == "#":
                    sprites.append(Tile(x, y, run_ends(row, col_index)))
                elif cell == "-":
                    sprites.append(Platform(x, y, run_ends(row, col_index)))
                elif cell == "K":
                    crumbler = CrumblingPlatform(x, y)
                    sprites.append(crumbler)
                    self.crumblers.add(crumbler)
                elif cell == "C":
                    # Altın; nadiren de kalp veya güçlendirme
                    kind = self.pick_item(t)
                    # Bölümün tanıttığı güçlendirme (stages "boost") ilk altının yerine kesin gelsin
                    if self.boost and chunk is not START_CHUNK:
                        kind, self.boost = self.boost, None
                    if kind != "coin":
                        item = Pickup(x, y, kind)
                        sprites.append(item)
                        self.pickups.add(item)
                    else:
                        coin = Coin(x, y)
                        sprites.append(coin)
                        self.coins.add(coin)
                        self.coins_total += 1
                elif cell == "S":
                    spring = Spring(x, y)
                    sprites.append(spring)
                    self.springs.add(spring)
                elif cell == "E":
                    # Yürüyen düşman yeri: altındaki platformun kenarları arasında yürür.
                    # Türü rastgele; sümüğün zıplayacak yeri (platformun iki üstü boş) olmalı
                    # Topçu kıpırdamaz ve karakter onun tepesine bir alt platformdan zıplayamaz (topçu + 3 blok,
                    # zıplamadan yüksek): platformun kenarında durursa oraya inilemez, yol kapanır. Bu yüzden hep
                    # platformun iç karelerinden birinde durur; platform dar ise topçu gelmez
                    left, right = platform_run(rows, row_index, col_index)
                    roof = rows[row_index - 1][left : right + 1]
                    cannon_col = self.cannon_spot(rows[row_index], left, right, col_index)
                    banned = (("slime",) if any(c in SOLID for c in roof) else ()) + (() if cannon_col is not None else ("cannon",))
                    kind = self.pick_enemy(self.walker_kinds, t, banned)
                    feet = (x + TILE_SIZE // 2, y + TILE_SIZE)
                    if kind is None:  # bölümde buraya uyan tür yok
                        continue
                    if kind == "cannon":
                        fire_time = mode.get("cannon_fire_time", CANNON_FIRE_TIME)
                        enemy = Cannon(cannon_col * TILE_SIZE + TILE_SIZE // 2, feet[1], self.shots, fire_time)
                    else:
                        walker = {"walker": Enemy, "slime": Slime, "spiky": Spiky}[kind]
                        speed = blend(mode["enemy_speed"], mode["enemy_speed_max"], t)
                        enemy = walker(*feet, left * TILE_SIZE, (right + 1) * TILE_SIZE, speed)
                    sprites.append(enemy)
                    self.enemies.add(enemy)
                elif cell == "F":
                    # Uçan düşman yeri: yarasa satırında duvara veya kenara kadar uçar, arı aşağı-yukarı
                    # (aynı satırda yeri olan en yakın sütunda; hiç yeri yoksa arı gelmez)
                    spot = self.bee_spot(rows, top, row_index, col_index)
                    kind = self.pick_enemy(self.flyer_kinds, t, () if spot else ("bee",))
                    center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                    speed = blend(mode["flyer_speed"], mode["flyer_speed_max"], t)
                    if kind is None:
                        continue
                    if kind == "bee":
                        bee_col, path = spot
                        center = (bee_col * TILE_SIZE + TILE_SIZE // 2, center[1])
                        facing = 1 if center[0] < self.width // 2 else -1  # ortaya baksın
                        flyer = Bee(*center, *path, speed, facing)
                    else:
                        left, right = free_span(row, col_index, col_index)
                        flyer = FlyingEnemy(*center, left * TILE_SIZE, (right + 1) * TILE_SIZE, speed)
                    sprites.append(flyer)
                    self.enemies.add(flyer)
                elif cell == "G":
                    goal = Goal(x, y)
                    sprites.append(goal)
                    self.goals.add(goal)
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
        if arena:
            sprites += gates + stairs + [golem]
            self.bosses.add(golem)
            self.arena = Arena(golem, gates, stairs, golem.floor, sprites, numbers, self.boss_count)
            self.boss_count += 1
            self.next_boss += self.boss_config["every"]
        self.chunks.append((top, self.top, sprites))
        self.top = top
        self.exit_side = chunk["exit"]

    def arena_due(self):
        # Sıradaki parça boss arenası mı: arenanın zemini sıradaki boss'un yüksekliğine (next_boss m) ulaşıyorsa
        # o arena (girişi alttaki parçanın çıkışının karşısında), değilse None
        if not self.boss_config or (self.arena and self.arena.state != "won"):
            return None  # önceki golem yenilmeden yeni arena kurulmaz (level.arena hep en son arena)
        arena = ARENA_CHUNKS["R" if self.exit_side == "L" else "L"]
        floor_height = (self.player_start[1] - self.top) // TILE_SIZE + len(arena["rows"]) - arena["floor_row"]
        return arena if floor_height >= self.next_boss else None

    def drop_item(self, x, y, kind, sprites):
        # Haritaya sonradan toplanacak bir şey koy (golem yenilince düşen elmaslar); sprites = ait olduğu parçanın listesi
        item = Pickup(x, y, kind)
        sprites.append(item)
        self.pickups.add(item)

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
        # Uyan tür yoksa (bölümde sadece o türler var) None
        options = [kind for kind in kinds if kind not in banned]
        if not options:
            return None
        weights = [blend(*kinds[kind], t) for kind in options]
        return self.random.choices(options, weights)[0]

    def cannon_spot(self, row, left, right, col):
        # Topçunun durabileceği sütun: platformun (left-right) kenarı olmayan, col'a en yakın boş kare; yoksa None
        inside = [c for c in range(left + 1, right) if c == col or row[c] == "."]
        return min(inside, key=lambda c: abs(c - col)) if inside else None

    def bee_spot(self, rows, top, row, col):
        # Arının uçabileceği yer: bu satırda col'a en yakın, aşağı-yukarı uçacak yeri olan boş sütun.
        # (sütun, bee_path) ya da None. Uçan düşman yerleri çoğu zaman bir platformun hemen üstünde, orada yer yok
        for c in sorted(range(len(rows[row])), key=lambda c: abs(c - col)):
            if c == col or rows[row][c] == ".":
                path = self.bee_path(rows, top, row, c)
                if path:
                    return c, path
        return None

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
        # Bir platformun kenarında, tam onun hizasına kadar inen arı oraya çıkmanın tek yolunu kapatır
        # (Ultra 13. bölüm 36 m: geçilemiyordu) — bu sütuna arı gelmez, bee_spot yandaki sütunları dener
        if rows[last + 1][col] not in SOLID:
            for side in (col - 1, col + 1):
                if 0 <= side < len(rows[row]) and rows[last + 1][side] in SOLID:
                    return None
        if low - high < BEE_MIN_PATH * TILE_SIZE:
            return None
        return high, low

    def pick_item(self, t=0.0):
        # Altın karesine ne gelecek: çoğunlukla "coin", nadiren kalp, güçlendirme veya elmas.
        # Kalpler zorluk (t) arttıkça seyrekleşir, elmaslar sıklaşır. Elmas sonda: bölüm haritalarındaki kalp ve
        # güçlendirmelerin yeri değişmesin (aynı zar, sadece bazı altınlar elmas olur)
        chances = (
            ("heart", blend(self.mode["heart_chance"], self.mode["heart_chance_min"], t)),
            ("magnet", self.mode.get("magnet_chance", MAGNET_CHANCE)),
            ("shield", self.mode.get("shield_chance", SHIELD_CHANCE)),
            ("gem", blend(GEM_CHANCE, GEM_CHANCE_MAX, t)),
        )
        roll = self.random.random()
        for kind, chance in chances:
            if roll < chance:
                return kind
            roll -= chance
        return "coin"

    def pick_chunk(self, top, exit_side, force_focus=False):
        # top = parçanın konacağı yer (alttaki parçanın tepesi), exit_side = alttaki parçanın çıkışı.
        # force_focus = bölümde sadece tanıtılan şeyin olduğu parçalardan seç (varsa).
        # Girişi, alttaki parçanın çıkışının karşı tarafında olan parçalardan rastgele seç
        entry = "R" if exit_side == "L" else "L"
        # Yükseldikçe daha zor parçalar da seçilebilir. Zor modlarda harita baştan yukarıdaymış gibi seçilir
        height = -top + self.mode["map_head_start"]
        stage = self.stage
        if stage:
            # Bölümde: sadece bölümün izin verdiği parçalar; tanıttığı şeyin olduğu parçalar daha sık
            options = allowed_chunks(stage, entry)
            if force_focus:
                options = [c for c in options if focused(stage, c)] or options
        else:
            max_difficulty = 1 + int(height // DIFFICULTY_STEP)
            options = [c for c in CHUNKS if c["entry"] == entry and c["difficulty"] <= max_difficulty]
        # Çok yükseklerde kolay parçalar seyrekleşir, zorlar sıklaşır
        t = hardness(height, self.mode)
        weights = [1 + t * HARD_CHUNK_BIAS * (c["difficulty"] - 1) for c in options]
        if stage:
            weights = [w * (FOCUS_WEIGHT if focused(stage, c) else 1) for w, c in zip(weights, options)]
        return self.random.choices(options, weights)[0]

    def update(self, view_top, view_bottom):
        # Ekranın yukarısı için yeterince parça hazır olsun (bölümde plan bitince — bayraktan sonra — durur)
        while self.top > view_top - GENERATE_AHEAD:
            if self.stage:
                if not self.plan:
                    break
                self.add_chunk(self.plan.pop(0))
            else:  # sonsuz oyun: sırası geldiyse boss arenası, yoksa rastgele parça
                self.add_chunk(self.arena_due() or self.pick_chunk(self.top, self.exit_side))
        # Ekranın çok altında kalan parçaları unut (bellekten sil)
        while len(self.chunks) > 1 and self.chunks[0][0] > view_bottom + REMOVE_BELOW:
            _, _, sprites = self.chunks.pop(0)
            if self.arena and self.arena.sprites is sprites:
                self.arena = None
            self.bosses.remove(sprites)
            self.tiles.remove(sprites)
            self.coins.remove(sprites)  # toplanmamış altınlar, kalpler ve düşmanlar da gitsin
            self.pickups.remove(sprites)
            self.springs.remove(sprites)
            self.movers.remove(sprites)
            self.crumblers.remove(sprites)
            self.enemies.remove(sprites)
            self.goals.remove(sprites)
        self.bottom = self.chunks[0][1]
