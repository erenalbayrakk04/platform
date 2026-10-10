# Efsanevi skinlerin izi (skins.py "trail"): karakter hareket ettikçe arkasında kalan kısa ömürlü parçacıklar.
# Parçacıklar çıktıkları yerde kalır (karakterle birlikte kaymaz), ömrü bitince silinir.
# Oyunda karakterin dünyadaki yeri verilir (çizerken kamera kadar kaydırılır); giriş ekranında ve Karakterler
# ekranında ekrandaki yeri (scale = resimler kaç kat büyük çizildi; parçacıklar da o kadar büyük olur).
import math
import random

import pygame

from settings import TRAIL_LIMIT
import theme

FIRE_COLORS = [(255, 245, 170), (255, 205, 70), (250, 125, 35), (215, 55, 25), (120, 30, 25)]
STAR_COLORS = [(255, 255, 255), (190, 210, 255), (255, 185, 245)]
GOLD_COLOR = (255, 210, 60)
GOLD_SHINE = (255, 250, 215)
SNOW_COLORS = [(255, 255, 255), (195, 235, 255)]
RAINBOW_COLORS = [(235, 60, 70), (250, 140, 40), (250, 215, 50), (90, 200, 80), (60, 150, 230), (140, 90, 220)]
SHADOW_COLOR = (150, 40, 80)
SPARK_COLORS = [(140, 230, 255), (255, 255, 255), (255, 240, 120)]
SPARKLES = {}  # Modern: parıltı resimleri (renk, kol, büyüklük) → resim


class Trail:
    def __init__(self, kind, scale=1):
        self.kind = kind  # "spark", "fire", "stars", "gold", "snow", "rainbow", "shadow"
        self.scale = scale
        self.parts = []  # parçacıklar: {"x", "y", "vx", "vy", "age", "life", ...}
        self.time = 0
        self.last = None  # karakterin önceki adımdaki yeri (yürüyor/zıplıyor mu anlamak için)
        self.rng = random.Random()
        self.silhouettes = {}  # gölge izi: karakter resmi → aynı şekilde düz renkli resim (bir kere hazırlanır)
        self.modern = theme.modern()  # Modern temada parçacıklar yuvarlak, parıltılar yumuşak

    def dot(self, screen, color, x, y, size):
        # Kare (Nostalji) ya da yuvarlak (Modern) parçacık; x, y ortası
        if self.modern:
            pygame.draw.circle(screen, color, (round(x), round(y)), size / 2 + 0.5)
        else:
            screen.fill(color, (round(x - size / 2), round(y - size / 2), size, size))

    def add(self, x, y, life, vx=0.0, vy=0.0, **extra):
        self.parts.append({"x": x, "y": y, "vx": vx, "vy": vy, "age": 0, "life": life, **extra})

    def update(self, rect, image=None, facing=1):
        # Her adımda bir kere: rect = karakterin yeri, image = şu anki resmi (gölge izi), facing = baktığı yön
        self.time += 1
        moved = self.last is not None and self.last != rect.topleft
        self.last = rect.topleft
        getattr(self, "spawn_" + self.kind)(rect, image, facing, moved)
        for part in self.parts:
            part["age"] += 1
            part["x"] += part["vx"]
            part["y"] += part["vy"]
            part["vy"] += part.get("gravity", 0)
        self.parts = [part for part in self.parts if part["age"] < part["life"]]
        if len(self.parts) > TRAIL_LIMIT:
            del self.parts[: len(self.parts) - TRAIL_LIMIT]  # en eskiler gider

    def draw(self, screen, dy=0):
        # dy = dikeyde kaydırma (oyunda kamera)
        draw = getattr(self, "draw_" + self.kind)
        for part in self.parts:
            draw(screen, part, part["x"], part["y"] + dy, part["age"] / part["life"])

    def plus(self, screen, color, x, y, arm):
        # Artı şeklinde parıltı: ortası 2 kare, kolları arm kare (scale kadar büyük). Modern: yumuşak dört kollu parıltı
        u = 2 * self.scale
        x, y = round(x), round(y)
        if self.modern:
            key = (color, arm, self.scale)
            if key not in SPARKLES:
                import modern

                SPARKLES[key] = modern.trail_sparkle(color, (arm + 0.6) * u)
            image = SPARKLES[key]
            screen.blit(image, image.get_rect(center=(x + u // 2, y + u // 2)))
            return
        screen.fill(color, (x - arm * u, y, (2 * arm + 1) * u, u))
        screen.fill(color, (x, y - arm * u, u, (2 * arm + 1) * u))

    # --- Ejderha: arkasından yükselen alevler (sarıdan kızıla döner, küçülür) ---
    def spawn_fire(self, rect, image, facing, moved):
        if moved or self.time % 2 == 0:
            r, s = self.rng, self.scale
            for _ in range(2 if moved else 1):
                x = rect.centerx - facing * rect.width * 0.25 + r.uniform(-0.25, 0.25) * rect.width
                y = rect.bottom - rect.height * r.uniform(0.1, 0.6)
                self.add(x, y, r.randint(18, 30), r.uniform(-0.35, 0.35) * s, r.uniform(-1.5, -0.5) * s)

    def draw_fire(self, screen, part, x, y, old):
        color = FIRE_COLORS[min(len(FIRE_COLORS) - 1, int(old * len(FIRE_COLORS)))]
        size = (6 if old < 0.2 else 5 if old < 0.45 else 4 if old < 0.7 else 2) * self.scale
        self.dot(screen, color, x, y, size)

    # --- Kozmik: etrafında parlayıp sönen yıldız tozu ---
    def spawn_stars(self, rect, image, facing, moved):
        if self.time % (2 if moved else 4) == 0:
            r, s = self.rng, self.scale
            area = rect.inflate(14 * s, 10 * s)
            self.add(
                r.uniform(area.left, area.right), r.uniform(area.top, area.bottom), r.randint(24, 40),
                r.uniform(-0.1, 0.1) * s, r.uniform(-0.15, 0.05) * s, color=r.choice(STAR_COLORS),
            )

    def draw_stars(self, screen, part, x, y, old):
        arm = round(2 * math.sin(math.pi * old))  # büyür, sonra küçülür
        self.plus(screen, part["color"], x, y, arm)

    # --- Kral: dökülen altın pırıltılar ---
    def spawn_gold(self, rect, image, facing, moved):
        if moved or self.time % 5 == 0:
            r, s = self.rng, self.scale
            x = rect.centerx + r.uniform(-0.4, 0.4) * rect.width
            y = rect.centery + r.uniform(-0.1, 0.4) * rect.height
            self.add(x, y, r.randint(26, 36), r.uniform(-0.5, 0.5) * s, r.uniform(-1.6, -0.6) * s, gravity=0.12 * s)

    def draw_gold(self, screen, part, x, y, old):
        shine = (part["age"] // 3) % 3 == 0  # arada bir beyaz parlar
        self.plus(screen, GOLD_SHINE if shine else GOLD_COLOR, x, y, 1 if old < 0.7 else 0)

    # --- Buz: süzülerek düşen kar taneleri ---
    def spawn_snow(self, rect, image, facing, moved):
        if self.time % (2 if moved else 4) == 0:
            r, s = self.rng, self.scale
            x = rect.centerx + r.uniform(-0.6, 0.6) * rect.width
            y = rect.top + r.uniform(0.0, 0.8) * rect.height
            self.add(x, y, r.randint(40, 60), 0.0, r.uniform(0.3, 0.7) * s, phase=r.uniform(0, 6.3),
                     color=r.choice(SNOW_COLORS))

    def draw_snow(self, screen, part, x, y, old):
        x += 3 * self.scale * math.sin(part["age"] / 8 + part["phase"])  # sağa sola salınır
        self.plus(screen, part["color"], x, y, 1 if old < 0.7 else 0)

    # --- Tekboynuz: arkasında gökkuşağı şeridi ---
    def spawn_rainbow(self, rect, image, facing, moved):
        if moved:
            s = self.scale
            x = rect.centerx - facing * rect.width * 0.3
            self.add(x, rect.centery - 3 * len(RAINBOW_COLORS) * s / 2, 22)

    def draw_rainbow(self, screen, part, x, y, old):
        s = self.scale
        width, height = 6 * s, 3 * s
        for i, color in enumerate(RAINBOW_COLORS):
            if old > 0.7 and (i + part["age"]) % 2:  # sönerken seyrekleşir
                continue
            if self.modern:  # yuvarlak uçlu şerit
                pygame.draw.rect(screen, color, (round(x - width / 2), round(y + i * height), width, height), border_radius=height // 2)
                continue
            screen.fill(color, (round(x - width / 2), round(y + i * height), width, height))

    # --- Gölge: arkasında kalan, yavaşça silinen gölgeler ---
    def spawn_shadow(self, rect, image, facing, moved):
        if moved and image is not None and self.time % 4 == 0:
            self.add(rect.x, rect.y, 16, image=image)

    def draw_shadow(self, screen, part, x, y, old):
        image = part["image"]
        if image not in self.silhouettes:
            # Resmin şekli düz renkle: önce siyaha boya (saydamlık kalır), sonra rengi ekle
            ghost = image.copy()
            ghost.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
            ghost.fill((*SHADOW_COLOR, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.silhouettes[image] = ghost
        ghost = self.silhouettes[image]
        ghost.set_alpha(round(150 * (1 - old)))
        screen.blit(ghost, (round(x), round(y)))

    # --- Şimşek: etrafında çakan elektrik kıvılcımları, arkasında elektrik tozu ---
    def spawn_spark(self, rect, image, facing, moved):
        r, s = self.rng, self.scale
        if self.time % (2 if moved else 5) == 0:
            angle = r.uniform(0, 2 * math.pi)
            dx, dy = math.cos(angle), math.sin(angle)
            x = rect.centerx + dx * rect.width * 0.5
            y = rect.centery + dy * rect.height * 0.45
            points = [(0.0, 0.0)]
            for k in range(1, 5):  # dışarı doğru zikzak
                side = (1 if k % 2 else -1) * r.uniform(2, 5) * s
                points.append((dx * 6 * s * k - dy * side, dy * 6 * s * k + dx * side))
            self.add(x, y, r.randint(5, 8), points=points, color=r.randrange(len(SPARK_COLORS)))
        if moved:
            x = rect.centerx - facing * rect.width * 0.3 + r.uniform(-0.15, 0.15) * rect.width
            y = rect.centery + r.uniform(-0.35, 0.35) * rect.height
            self.add(x, y, r.randint(10, 16), r.uniform(-0.2, 0.2) * s, r.uniform(-0.2, 0.2) * s,
                     color=r.randrange(len(SPARK_COLORS)))

    def draw_spark(self, screen, part, x, y, old):
        color = SPARK_COLORS[(part["color"] + part["age"] // 2) % len(SPARK_COLORS)]  # titreşir
        if "points" not in part:  # elektrik tozu
            size = (3 if old < 0.5 else 2) * self.scale
            if self.modern:
                self.dot(screen, color, x + size / 2, y + size / 2, size)
                return
            screen.fill(color, (round(x), round(y), size, size))
            return
        points = [(round(x + px), round(y + py)) for px, py in part["points"]]
        pygame.draw.lines(screen, color, False, points, 2 * self.scale)
