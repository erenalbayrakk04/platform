# Boss: Lav Golemi. Sonsuz oyunda Zor ve Ultra Zor'da her birkaç yüz metrede bir boss arenası gelir (chunks.py
# ARENA_CHUNKS; level.py yerleştirir; sayıları settings.py DIFFICULTIES "boss" ve "Boss" kısmı).
# Arena: karakter zemine basınca alttaki delik kapanır, golem uyanır, lav durur. Golem yenilince basamaklar belirir,
# elmaslar düşer, lav yine yükselir.
# Golem: karaktere doğru zıplar, yere çakılınca iki yana alev dalgası (Shockwave) yayılır (üstünden atlanır). İndikten
# sonra alevi söner ve yorulur: o zaman kafasına basılır; alevi yanarken dokunan yanar. Bazı modlarda zıplamadan önce
# lav taşı (LavaRock) fırlatır. Vurulunca lav sümüğü (enemy.MagmaSlime) saçar ve sinirlenip daha kısa çömelir.
import random

import pygame

from settings import (
    TILE_SIZE,
    PIXEL_SCALE,
    BOSS_HARDEST,
    BOSS_GRAVITY,
    BOSS_WAKE_TIME,
    BOSS_ROCK_GAP,
    BOSS_ROCK_FLIGHT,
    BOSS_HIT_TIME,
    BOSS_HIT_SLIDE,
    BOSS_DEATH_TIME,
    BOSS_RAGE,
    BOSS_MIN_CROUCH,
    BOSS_LAVA_GRACE,
    BOSS_POINTS,
    BOSS_SHAKE,
    BOSS_BANNER_TIME,
    BOSS_ROCK_COLOR,
    MAGMA_COLOR,
    LAVA_COLOR,
    LAVA_TOP_COLOR,
    CRUMBLE_COLOR,
)
from enemy import MagmaSlime
from effects import burst
from lang import mark
import art
import theme

# Resimler bir kere hazırlanır (her tema için ayrı)
MAKE_FRAMES = {"golem": art.golem_frames, "wave": art.wave_frames, "rock": art.rock_frames}
FRAMES = {}
ROMAN = ["", " II", " III", " IV", " V", " VI", " VII", " VIII", " IX", " X"]  # ikinci golemden sonra adının sonuna


def frames(kind):
    return theme.cached(FRAMES, kind, MAKE_FRAMES[kind])


def prepare():
    # Resimleri önceden hazırla (sonsuz oyun başlarken): arena gelince oyun bir an takılmasın (tarayıcıda yavaş)
    import enemy

    for kind in MAKE_FRAMES:
        frames(kind)
    enemy.frames("magma")


def boss_numbers(config, index):
    # index. boss'un (0 = ilk) sayıları: modun "boss" sayıları (ilk boss, en güçlü boss) arası; BOSS_HARDEST'te en güçlü
    t = min(1.0, index / BOSS_HARDEST)
    numbers = {}
    for key, value in config.items():
        if isinstance(value, tuple):
            first, hardest = value
            value = first + (hardest - first) * t
            if key != "wave_speed":
                value = round(value)
        numbers[key] = value
    return numbers


class Golem(pygame.sprite.Sprite):
    # Durumlar (state): "sleep" (arena kapanana kadar), "wake" (kükrer), "throw" (lav taşı atar), "crouch" (çömelir:
    # zıplayacak!), "air" (havada), "tired" (indi, alevi söndü: kafasına basılır), "hit" (vuruldu: yanıp söner, kenara
    # kayar, zararsız), "dying" (titreyip patlar), "dead"
    color = MAGMA_COLOR  # ölünce saçılan parçacıklar
    INSET = 8  # çarpışma kutusu resmin iki yanından bu kadar dar (kollarının ucuna sürtmek affedilir)

    def __init__(self, center_x, floor_y, left, right, numbers):
        super().__init__()
        self.frames = frames("golem")
        self.numbers = numbers  # bu golemin sayıları (boss_numbers)
        self.health = self.max_health = numbers["health"]
        self.crouch_time = numbers["crouch"]  # her vuruşta kısalır (BOSS_RAGE)
        self.left, self.right = left, right  # arenanın kenarları (piksel)
        self.floor = floor_y
        self.half = self.frames["sleep"].get_width() // 2
        self.x = float(center_x)
        self.bottom = float(floor_y)
        self.vx = self.vy = 0.0
        self.state = "sleep"
        self.timer = 0  # şu anki durumun bitmesine kaç kare kaldı
        self.rocks_left = 0
        self.time = 0
        self.events = []  # bu adımda olanlar (Arena işler): ("land",), ("rock", x, y, hedef x), ("boom",), ("dead",)
        self.pose()
        self.old_top = self.hitbox.top

    @property
    def flaming(self):
        # Alevi yanıyor: dokunan yanar
        return self.state in ("wake", "throw", "crouch", "air")

    @property
    def vulnerable(self):
        return self.state == "tired"

    @property
    def grounded(self):
        # Yerde mi (Modern temada ayağının altına gölge çizilir)
        return self.state != "air"

    @property
    def hitbox(self):
        # Çarpışma kutusu: gövdesi (alevler ve kollarının ucu hariç)
        top = self.rect.top + (art.GOLEM_FLAME_HEIGHT if self.flaming else 0)
        return pygame.Rect(self.rect.left + self.INSET, top, self.rect.width - 2 * self.INSET, self.rect.bottom - top)

    @property
    def draw_rect(self):
        # Zıplamak üzereyken ve ölürken titrer; çarpışma kutusu yerinde kalır
        if (self.state == "crouch" and self.timer < 24) or self.state == "dying":
            return self.rect.move(2 if (self.time // 2) % 2 else -2, 0)
        return self.rect

    def wake(self):
        self.state = "wake"
        self.timer = BOSS_WAKE_TIME

    def next_attack(self):
        # Sıradaki saldırı: önce (varsa) lav taşları, sonra çömelip zıplar
        if self.numbers["rocks"] > 0:
            self.state = "throw"
            self.rocks_left = self.numbers["rocks"]
            self.timer = BOSS_ROCK_GAP
        else:
            self.crouch()

    def crouch(self):
        self.state = "crouch"
        self.timer = round(self.crouch_time)

    def jump(self, target):
        # Karakterin şu anki yerine zıpla (arenadan taşmadan); havada "air" kare kalır
        goal = min(max(target.centerx, self.left + self.half), self.right - self.half)
        air = self.numbers["air"]
        self.vx = (goal - self.x) / air
        self.vy = -BOSS_GRAVITY * air / 2
        self.state = "air"

    def land(self):
        self.bottom = self.floor
        self.vx = self.vy = 0.0
        self.state = "tired"
        self.timer = self.numbers["tired"]
        self.events.append(("land",))

    def throw(self, target):
        # Ağzından karakterin şu anki yerine lav taşı
        mouth_y = self.rect.top + art.GOLEM_FLAME_HEIGHT + 10 * PIXEL_SCALE
        self.events.append(("rock", self.rect.centerx, mouth_y, target.centerx))
        self.rocks_left -= 1
        if self.rocks_left > 0:
            self.timer = BOSS_ROCK_GAP
        else:
            self.crouch()

    def stomp(self, from_x):
        # Kafasına basıldı (yorgunken): bir can gider, karakterden uzağa kayar, sinirlenir (sonra daha kısa çömelir)
        self.health -= 1
        self.crouch_time = max(BOSS_MIN_CROUCH, self.crouch_time * BOSS_RAGE)
        if self.health <= 0:
            self.state = "dying"
            self.timer = BOSS_DEATH_TIME
            return
        self.state = "hit"
        self.timer = BOSS_HIT_TIME
        away = 1 if self.x >= from_x else -1
        if (away > 0 and self.x + self.half >= self.right - 4) or (away < 0 and self.x - self.half <= self.left + 4):
            away = -away  # duvara dayanmışsa öbür yana kayar
        self.vx = away * BOSS_HIT_SLIDE

    def update(self, target):
        # Her adımda bir kere; target = karakterin kutusu (zıplayacağı, taş atacağı yer)
        self.events = []
        self.old_top = self.hitbox.top
        self.time += 1
        if self.state in ("sleep", "dead"):
            return
        self.timer -= 1
        if self.state == "air":
            self.vy += BOSS_GRAVITY
            self.x += self.vx
            self.bottom += self.vy
            if self.vy > 0 and self.bottom >= self.floor:
                self.land()
        elif self.state == "hit":
            self.x += self.vx
            self.vx *= 0.9
            if self.timer <= 0:
                self.next_attack()
        elif self.state == "dying":
            if self.timer % 15 == 0:
                self.events.append(("boom",))
            if self.timer <= 0:
                self.state = "dead"
                self.events.append(("dead",))
        elif self.timer <= 0:
            if self.state == "throw":
                self.throw(target)
            elif self.state == "crouch":
                self.jump(target)
            else:  # kükremesi ya da yorgunluğu bitti
                self.next_attack()
        self.x = min(max(self.x, self.left + self.half), self.right - self.half)
        self.pose()

    def pose(self):
        # Duruma göre resim; alevler titrer, vurulunca / ölürken beyaz yanıp söner
        flicker = (self.time // 6) % 2
        state = self.state
        if state in ("sleep", "dead"):
            image = self.frames["sleep"]
        elif state in ("wake", "throw"):
            image = self.frames["stand"][flicker]
        elif state in ("crouch", "air"):
            image = self.frames[state][flicker]
        elif state == "tired":
            image = self.frames["tired"]
        else:
            blink = 3 if state == "dying" else 5
            image = self.frames["flash"] if (self.time // blink) % 2 else self.frames["tired"]
        self.image = image
        self.rect = image.get_rect(midbottom=(round(self.x), round(self.bottom)))


class Shockwave(pygame.sprite.Sprite):
    # Golem yere çakılınca iki yana yayılan alev dalgası: zeminde gider, arenadan çıkınca söner. Değen yanar
    # (üstünden atlanır). level.shots'ta (ateş topu gibi; kalkan söndürür)
    color = LAVA_COLOR

    def __init__(self, x, floor_y, direction, speed):
        super().__init__()
        self.frames = frames("wave")
        self.direction = direction
        self.speed = speed
        self.x = float(x)
        self.floor = floor_y
        self.time = 0
        self.image = self.frames[0][direction]
        self.place()

    def place(self):
        # Çarpışma kutusu resimden küçük: sivri tepesi ve yanları affedilir
        self.draw_rect = self.image.get_rect(midbottom=(round(self.x), self.floor))
        self.rect = self.draw_rect.inflate(-10, -8)
        self.rect.bottom = self.floor

    def update(self, tiles, level_width):
        self.x += self.speed * self.direction
        self.time += 1
        self.image = self.frames[(self.time // 4) % 2][self.direction]
        self.place()
        if self.rect.right < 0 or self.rect.left > level_width:
            self.kill()


class LavaRock(pygame.sprite.Sprite):
    # Golemin fırlattığı lav taşı: kavis çizip BOSS_ROCK_FLIGHT karede karakterin atıldığı andaki yerine iner,
    # yere değince parçalanır. Değen yanar (kenara çekilerek kaçılır). level.shots'ta
    color = LAVA_COLOR
    GRAVITY = 0.35  # taşın düşüşü (hafif: uzun kavis, nereye ineceği görünsün)

    def __init__(self, x, y, target_x, floor_y, effects):
        super().__init__()
        self.frames = frames("rock")
        self.image = self.frames[0]
        self.x, self.y = float(x), float(y)
        flight = BOSS_ROCK_FLIGHT
        drop = floor_y - self.image.get_height() / 2 - y  # yere değene kadar ne kadar alçalacak
        self.vx = (target_x - x) / flight
        self.vy = (drop - self.GRAVITY * flight * (flight + 1) / 2) / flight
        self.floor = floor_y
        self.effects = effects  # yere değince saçılan parçacıklar
        self.time = 0
        self.place()

    def place(self):
        self.draw_rect = self.image.get_rect(center=(round(self.x), round(self.y)))
        self.rect = self.draw_rect.inflate(-8, -8)

    def update(self, tiles, level_width):
        self.vy += self.GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.time += 1
        self.image = self.frames[(self.time // 5) % 2]
        self.place()
        if self.draw_rect.bottom >= self.floor or (self.vy > 0 and pygame.sprite.spritecollideany(self, tiles)):
            burst(self.effects, (self.draw_rect.centerx, self.floor - 4), LAVA_COLOR, 8)
            self.kill()


class Arena:
    # Boss arenası (Level kurar → level.arena): "waiting" (karakter gelmedi) → "fight" → "won".
    # gates = zemindeki deliğin blokları (kapanınca level.tiles'a girer), stairs = golem yenilince beliren basamaklar
    # (level.Stair; o zamana kadar silik), sprites = arenanın parçasının sprite listesi (parça silinince bunlar da)
    def __init__(self, golem, gates, stairs, floor_y, sprites, numbers, index):
        self.golem = golem
        self.gates = gates
        self.stairs = stairs
        self.floor_y = floor_y
        self.sprites = sprites
        self.numbers = numbers
        self.index = index  # kaçıncı boss (0 = ilk)
        self.suffix = ROMAN[index] if index < len(ROMAN) else f" {index + 1}"  # adının sonu: "Lav Golemi II"
        self.state = "waiting"
        self.minions = pygame.sprite.Group()  # saçtığı lav sümükleri (en fazla minion_limit)
        self.shake = 0  # ekranın sallanmasına kalan kare
        self.banner = None  # ortadaki büyük yazı: (başlık, alt yazı)
        self.banner_time = 0

    @property
    def fighting(self):
        return self.state == "fight"

    def ghosts(self):
        # Silik çizilecek basamaklar (golem yenilene kadar)
        return self.stairs if self.state != "won" else []

    def start(self, level):
        # Karakter zemine çıktı: delik kapanır, lav durur, golem uyanır
        self.state = "fight"
        for gate in self.gates:
            level.tiles.add(gate)
            burst(level.effects, gate.rect.center, CRUMBLE_COLOR, 5)
        level.lava.paused = True
        self.golem.wake()
        self.banner = (mark("Lav Golemi"), mark("Alevi sönünce kafasına bas!"))
        self.banner_time = BOSS_BANNER_TIME

    def update(self, player, level, score):
        # Her adımda bir kere: arena kapanır mı, golem ne yaptı. Çalınacak seslerin adlarını döndürür
        sounds = []
        self.shake = max(0, self.shake - 1)
        self.banner_time = max(0, self.banner_time - 1)
        if self.state == "waiting" and player.on_ground and player.rect.bottom == self.floor_y:
            self.start(level)
            sounds += ["crumble", "roar"]
        if self.state != "fight":
            return sounds
        golem = self.golem
        golem.update(player.rect)
        for event in golem.events:
            kind = event[0]
            if kind == "land":  # yere çakıldı: iki yana alev dalgası, ekran sallanır
                self.shake = BOSS_SHAKE
                hitbox = golem.hitbox
                speed = self.numbers["wave_speed"]
                level.shots.add(Shockwave(hitbox.left, self.floor_y, -1, speed))
                level.shots.add(Shockwave(hitbox.right, self.floor_y, 1, speed))
                for x in (hitbox.left, hitbox.right):
                    burst(level.effects, (x, self.floor_y - 6), CRUMBLE_COLOR, 6)
                sounds.append("slam")
            elif kind == "rock":
                _, x, y, target_x = event
                level.shots.add(LavaRock(x, y, target_x, self.floor_y, level.effects))
                sounds.append("shoot")
            elif kind == "boom":  # ölürken yer yer patlar
                rect = golem.rect
                spot = (random.randint(rect.left, rect.right), random.randint(rect.top, rect.bottom))
                burst(level.effects, spot, random.choice((MAGMA_COLOR, LAVA_TOP_COLOR, BOSS_ROCK_COLOR)))
                sounds.append("crumble")
            elif kind == "dead":
                self.win(level, score)
                sounds.append("win")
        return sounds

    def touch(self, player, level):
        # Karakter golemin kutusuna değdi mi: "hit" (yorgunken kafasına bastı), "hurt" (alevi yanarken değdi),
        # "bounce" (vurulmuş, yanıp sönerken üstüne düştü) ya da None. Vurulunca lav sümükleri saçılır
        golem = self.golem
        if self.state != "fight" or golem.state in ("dying", "dead") or not player.rect.colliderect(golem.hitbox):
            return None
        from_above = player.old_bottom <= golem.old_top and player.velocity_y >= 0
        if golem.vulnerable and from_above:
            golem.stomp(player.rect.centerx)
            burst(level.effects, (player.rect.centerx, golem.hitbox.top), MAGMA_COLOR)
            if golem.state != "dying":
                self.spawn_minions(level)
            return "hit"
        if golem.flaming:
            return "hurt"
        return "bounce" if from_above else None

    def spawn_minions(self, level):
        # Vurulan golemin iki yanından lav sümükleri fırlar (arenada en fazla minion_limit tane); yere inene kadar
        # zararsızdırlar (enemy.MagmaSlime)
        golem = self.golem
        hitbox = golem.hitbox
        count = min(self.numbers["minions"], self.numbers["minion_limit"] - len(self.minions))
        for i in range(count):
            side = 1 if i % 2 == 0 else -1
            x = hitbox.right - 12 if side > 0 else hitbox.left + 12
            minion = MagmaSlime(x, self.floor_y, 0, level.width, level.mode["enemy_speed"])
            minion.throw(x, hitbox.top + 24, side, 9 + 2 * (i // 2))
            level.enemies.add(minion)
            self.minions.add(minion)
            self.sprites.append(minion)

    def win(self, level, score):
        # Golem yenildi: basamaklar belirir, lav sümükleri patlar, elmaslar düşer, lav biraz bekleyip yine yükselir
        self.state = "won"
        golem = self.golem
        burst(level.effects, golem.rect.center, MAGMA_COLOR, 24)
        burst(level.effects, golem.rect.center, BOSS_ROCK_COLOR, 16)
        golem.kill()
        for minion in self.minions:
            burst(level.effects, minion.rect.center, minion.color)
            minion.kill()
        for stair in self.stairs:
            stair.appear()
            level.tiles.add(stair)
            burst(level.effects, stair.rect.center, LAVA_TOP_COLOR, 4)
        # Elmaslar zeminin üstüne sıra sıra (sırada en fazla 8; fazlası bir üst sıraya)
        columns = range(1, level.width // TILE_SIZE - 1)
        for i in range(self.numbers["gems"]):
            row = 1 + i // len(columns)
            level.drop_item(columns[i % len(columns)] * TILE_SIZE, self.floor_y - row * TILE_SIZE, "gem", self.sprites)
        level.lava.paused = False
        level.lava.wait = BOSS_LAVA_GRACE
        score.add_bonus(BOSS_POINTS)
        score.bosses += 1
        self.banner = (mark("Golem yenildi!"), mark("Basamaklardan tırman!"))
        self.banner_time = BOSS_BANNER_TIME
