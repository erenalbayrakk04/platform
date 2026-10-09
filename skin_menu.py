# Karakterler ekranı: skin seçme ve satın alma. Üstte gruplar (Renkler / Karakterler / Efsanevi), ortada
# önizlenen skin büyük çizilmiş, platformda yürüyüp zıplar (efsanevilerin izi de görünür), altında kutular,
# cüzdandaki altın ve "Seç / Satın Al" düğmesi.
# Kutuya dokununca o skin önizlenir; senin olan bir skine dokununca hemen giyilir. Satın almak (ya da kilitli
# skini denemek) için alttaki düğmeye basılır. Klavyede oklar + Enter. Ne olacağına main.py karar verir.
import math
import random

import pygame

from settings import (
    SCREEN_WIDTH,
    ANIMATION_SPEED,
    GRAVITY,
    TITLE_FONT_SIZE,
    MENU_FONT_SIZE,
    MENU_SMALL_FONT_SIZE,
    TITLE_COLOR,
    HINT_COLOR,
    RECORD_COLOR,
    GAME_OVER_COLOR,
    COIN_COLOR,
    WHITE,
    BUTTON_COLOR,
    BUTTON_FOCUS_COLOR,
    BUTTON_BORDER_COLOR,
    BUTTON_FOCUS_BORDER_COLOR,
    LOCKED_COLOR,
    SKIN_SELECTED_COLOR,
    LEGENDARY_COLOR,
)
from score import draw_text
from ui import Buttons, click_pos, take_click, ACTIVATE_KEYS, UP_KEYS, DOWN_KEYS, LEFT_KEYS, RIGHT_KEYS
from trail import Trail
import skins
import art

CENTER_X = SCREEN_WIDTH // 2
# Yerleşim (y = yukarıdan piksel)
TITLE_Y = 38
TAB_Y = 86  # sekmelerin ortası
GROUND_Y = 226  # önizlemede karakterin ayağı (platformun üstü)
NAME_Y = 270
INFO_Y = 295
GRID_TOP = 312  # ilk kutu satırının üstü
PANEL = (14, 110, SCREEN_WIDTH - 28, 196)  # önizlemenin arkasındaki koyu pano (x, y, genişlik, yükseklik)
PANEL_ALPHA = 120
WALLET_Y = 547
PREVIEW_SCALE = 2  # önizlemede karakter kaç kat büyük
WALK_RANGE = 96  # önizlemede karakter ortadan en fazla kaç piksel sağa sola yürür
WALK_SPEED = 1.2
REST_TIME = 45  # uçta kaç adım bekleyip döner
HOP_TIME = 95  # kaç adımda bir zıplar
HOP_POWER = 7
FLASH_TIME = 50  # altın yetmeyince cüzdan yazısı kaç adım kırmızı yanar
CONFETTI_COLORS = [COIN_COLOR, WHITE, (255, 150, 200), (120, 220, 255)]


def scaled(image, factor):
    # Düz büyütme/küçültme (pikseller keskin kalır)
    width, height = image.get_size()
    return pygame.transform.scale(image, (round(width * factor), round(height * factor)))


class SkinMenu:
    COLUMNS = 5
    BOX = 64  # kutunun kenarı
    GAP = 8
    TAB_HEIGHT = 36
    TAB_GAP = 8
    TAB_FONT_SIZE = 24

    def __init__(self):
        self.groups = list(skins.GROUP_NAMES)
        self.group = self.groups[0]
        self.current = skins.DEFAULT_SKIN  # önizlenen skin (alttaki düğme bunun için)
        # Klavye odağı: -1 = sekmeler, 0..n-1 = kutular, n = Seç/Satın Al, n+1 = Geri (n = gruptaki skin sayısı)
        self.focus = 0
        width = SCREEN_WIDTH - 40
        tab_width = (width - (len(self.groups) - 1) * self.TAB_GAP) // len(self.groups)
        self.tabs = [
            pygame.Rect(20 + i * (tab_width + self.TAB_GAP), TAB_Y - self.TAB_HEIGHT // 2, tab_width, self.TAB_HEIGHT)
            for i in range(len(self.groups))
        ]
        grid_width = self.COLUMNS * self.BOX + (self.COLUMNS - 1) * self.GAP
        left = (SCREEN_WIDTH - grid_width) // 2
        step = self.BOX + self.GAP
        self.boxes = [
            pygame.Rect(left + (i % self.COLUMNS) * step, GRID_TOP + (i // self.COLUMNS) * step, self.BOX, self.BOX)
            for i in range(skins.GROUP_SIZE)
        ]
        self.action = Buttons(["action"], top=592)
        self.back = Buttons(["back"], top=654)
        self.images = None  # ilk çizimde hazırlanır (pygame açıldıktan sonra)
        self.big = {}  # skin → önizleme resimleri (büyütülmüş)
        self.thumbs = {}  # skin → (kutudaki resim, sönük hâli)
        self.tags = {}  # (fiyat, alınabilir mi) → fiyat etiketi resmi
        # Önizlemedeki karakter: x = ortası, lift = ayağının platformdan yüksekliği, vy = dikey hız (yukarı +)
        self.time = 0
        self.x = float(CENTER_X)
        self.facing = 1
        self.lift = 0.0
        self.vy = 0.0
        self.rest = 0
        self.trail = None
        self.confetti = []  # satın alınca saçılan parçalar: [x, y, vx, vy, yaş, renk]
        self.flash = 0  # altın yetmedi uyarısı

    # --- Açma, seçim ---
    def skins_shown(self):
        return skins.in_group(self.group)

    def open(self, selected):
        # Ekran açılınca giyilen skin önizlenir ve onun grubu açılır
        self.show(selected)
        self.focus = self.index_of(selected)
        self.sync_buttons()

    def index_of(self, skin_id):
        ids = [skin["id"] for skin in self.skins_shown()]
        return ids.index(skin_id) if skin_id in ids else 0

    def show(self, skin_id):
        # Önizlenen skini değiştir (iz baştan başlar)
        skin = skins.get(skin_id)
        self.group = skin["group"]
        if skin_id != self.current:
            self.confetti = []
            self.flash = 0
        self.current = skin_id
        self.trail = Trail(skin["trail"], PREVIEW_SCALE) if skin["trail"] else None

    def set_group(self, group, selected):
        # Sekme değişti: o gruptaki giyilen skin (yoksa ilki) önizlenir
        ids = [skin["id"] for skin in skins.in_group(group)]
        self.show(selected if selected in ids else ids[0])

    def sync_buttons(self):
        n = len(self.skins_shown())
        self.action.focus = 0 if self.focus == n else -1
        self.back.focus = 0 if self.focus == n + 1 else -1

    def move_focus(self, key, selected):
        n = len(self.skins_shown())
        f = self.focus
        if f < 0:  # sekmeler: sağ/sol grubu değiştirir, aşağı kutulara iner
            if key in LEFT_KEYS + RIGHT_KEYS:
                i = self.groups.index(self.group) + (-1 if key in LEFT_KEYS else 1)
                if 0 <= i < len(self.groups):
                    self.set_group(self.groups[i], selected)
            elif key in DOWN_KEYS:
                f = self.index_of(self.current)
        elif f < n:  # kutular
            if key in LEFT_KEYS and f % self.COLUMNS > 0:
                f -= 1
            elif key in RIGHT_KEYS and f % self.COLUMNS < self.COLUMNS - 1 and f + 1 < n:
                f += 1
            elif key in UP_KEYS:
                f = f - self.COLUMNS if f >= self.COLUMNS else -1
            elif key in DOWN_KEYS:
                f = f + self.COLUMNS if f + self.COLUMNS < n else n
            if 0 <= f < n:
                self.show(self.skins_shown()[f]["id"])
        elif f == n:  # Seç / Satın Al
            if key in UP_KEYS:
                f = self.index_of(self.current)
            elif key in DOWN_KEYS:
                f = n + 1
        elif key in UP_KEYS:  # Geri
            f = n
        self.focus = f
        self.sync_buttons()

    def press(self, wardrobe, progress):
        # Alttaki düğme: önizlenen skini giy / satın al. Döner: (ne oldu, skin adı) ya da None (zaten giyili)
        skin = skins.get(self.current)
        if wardrobe.owns(skin, progress):
            return None if skin["id"] == wardrobe.selected else ("select", skin["id"])
        if skin["goal"]:
            return "locked", skin["id"]
        if wardrobe.coins < skin["price"]:
            self.flash = FLASH_TIME
            return "poor", skin["id"]
        return "buy", skin["id"]

    def handle_event(self, event, wardrobe, progress):
        # Döner: ("select" | "buy" | "locked" | "poor", skin adı), "back" ya da None
        n = len(self.skins_shown())
        if event.type == pygame.KEYDOWN:
            if event.key in ACTIVATE_KEYS:
                if not take_click():
                    return None
                if self.focus == n + 1:
                    return "back"
                if self.focus == n:
                    return self.press(wardrobe, progress)
                if 0 <= self.focus < n:
                    skin = self.skins_shown()[self.focus]
                    if wardrobe.owns(skin, progress):
                        return "select", skin["id"]
                    self.focus = n  # satın almak için bir kez daha Enter (alttaki düğme)
                    self.sync_buttons()
                return None
            self.move_focus(event.key, wardrobe.selected)
            return None
        if event.type == pygame.MOUSEMOTION:
            # Fare sadece düğmeleri seçili gösterir; önizleme ancak kutuya tıklayınca değişir
            # (yoksa düğmeye giderken üstünden geçilen kutu önizlenip yanlış skin alınabilirdi)
            if self.action.rects[0].collidepoint(event.pos):
                self.focus = n
            elif self.back.rects[0].collidepoint(event.pos):
                self.focus = n + 1
            self.sync_buttons()
            return None
        pos = click_pos(event)
        if pos is None:
            return None
        for group, rect in zip(self.groups, self.tabs):
            if rect.inflate(0, 8).collidepoint(pos) and take_click():
                if group != self.group:
                    self.set_group(group, wardrobe.selected)
                    self.focus = self.index_of(self.current)
                    self.sync_buttons()
                return None
        for i, skin in enumerate(self.skins_shown()):
            if self.boxes[i].collidepoint(pos) and take_click():
                self.show(skin["id"])
                self.focus = i
                self.sync_buttons()
                if wardrobe.owns(skin, progress):
                    return "select", skin["id"]
                return None
        if self.action.rects[0].inflate(0, 8).collidepoint(pos) and take_click():
            self.focus = n
            self.sync_buttons()
            return self.press(wardrobe, progress)
        if self.back.rects[0].inflate(0, 8).collidepoint(pos) and take_click():
            return "back"
        return None

    def celebrate(self):
        # Satın alındı: önizlemedeki karakterin etrafına renkli parçalar saçılır
        self.flash = 0
        rng = random.Random()
        center = (self.x, GROUND_Y - self.lift - 50)
        for _ in range(28):
            angle = rng.uniform(0, 2 * math.pi)
            speed = rng.uniform(1.5, 4.5)
            self.confetti.append(
                [center[0], center[1], math.cos(angle) * speed, math.sin(angle) * speed - 2, 0, rng.choice(CONFETTI_COLORS)]
            )

    # --- Önizlemedeki karakterin hareketi ---
    def update(self, steps):
        for _ in range(steps):
            self.time += 1
            self.flash = max(0, self.flash - 1)
            self.walk()
            if self.trail:
                image = self.preview_image()
                self.trail.update(image.get_rect(midbottom=self.feet()), image, self.facing)
            for piece in self.confetti:
                piece[0] += piece[2]
                piece[1] += piece[3]
                piece[3] += GRAVITY * 0.25
                piece[4] += 1
            self.confetti = [piece for piece in self.confetti if piece[4] < 45]

    def walk(self):
        # Platformun bir ucundan öbürüne yürür, uçta biraz bekleyip döner; arada bir zıplar (giriş ekranı gibi)
        if self.lift > 0 or self.vy > 0:
            self.lift += self.vy
            self.vy -= GRAVITY
            if self.lift <= 0:
                self.lift = self.vy = 0.0
        elif self.time % HOP_TIME == 0:
            self.vy = HOP_POWER
        if self.rest:
            self.rest -= 1
            if not self.rest:
                self.facing = -self.facing
            return
        self.x += self.facing * WALK_SPEED
        if abs(self.x - CENTER_X) >= WALK_RANGE:
            self.x = CENTER_X + self.facing * WALK_RANGE
            self.rest = REST_TIME

    def feet(self):
        return round(self.x), GROUND_Y - round(self.lift)

    def preview_image(self):
        if self.current not in self.big:
            self.big[self.current] = {
                name: {side: scaled(image, PREVIEW_SCALE) for side, image in pair.items()}
                for name, pair in skins.frames(self.current).items()
            }
        if self.lift > 0:
            name = "jump"
        elif self.rest:
            name = "idle"
        else:
            name = "walk1" if (self.time // ANIMATION_SPEED) % 2 == 0 else "walk2"
        return self.big[self.current][name][self.facing]

    # --- Çizim ---
    def prepare(self):
        fonts = {size: pygame.font.Font(None, size) for size in (TITLE_FONT_SIZE, MENU_FONT_SIZE + 4, MENU_FONT_SIZE,
                                                                   MENU_SMALL_FONT_SIZE, self.TAB_FONT_SIZE, 20)}
        coin = art.coin_frames()[0]
        platform = art.platform_image()
        panel = pygame.Surface(PANEL[2:], pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, PANEL_ALPHA), panel.get_rect(), border_radius=16)
        self.images = {
            "panel": panel,
            "fonts": fonts,
            "coin": coin,
            "small_coin": scaled(coin, 0.5),
            "lock": scaled(art.lock_image(), 0.5),
            "platform": scaled(platform, PREVIEW_SCALE),
        }

    def thumb(self, skin_id):
        # Kutudaki küçük resim ve sönük hâli (henüz senin değilse)
        if skin_id not in self.thumbs:
            image = skins.frames(skin_id)["idle"][1]
            dim = image.copy()
            dim.fill((105, 105, 130), special_flags=pygame.BLEND_RGB_MULT)
            self.thumbs[skin_id] = (image, dim)
        return self.thumbs[skin_id]

    def draw(self, screen, wardrobe, progress):
        if self.images is None:
            self.prepare()
        fonts = self.images["fonts"]
        draw_text(screen, fonts[TITLE_FONT_SIZE], "Karakterler", TITLE_COLOR, center=(CENTER_X, TITLE_Y))
        self.draw_tabs(screen, fonts[self.TAB_FONT_SIZE])
        self.draw_preview(screen)
        skin = skins.get(self.current)
        owned = wardrobe.owns(skin, progress)
        name_color = LEGENDARY_COLOR if skin["group"] == "legendary" else WHITE
        draw_text(screen, fonts[MENU_FONT_SIZE + 4], skin["name"], name_color, center=(CENTER_X, NAME_Y))
        info, info_color = self.info(skin, owned, wardrobe, progress)
        draw_text(screen, fonts[MENU_SMALL_FONT_SIZE], info, info_color, center=(CENTER_X, INFO_Y))
        self.draw_grid(screen, wardrobe, progress)
        self.draw_wallet(screen, wardrobe.coins, fonts[MENU_FONT_SIZE])
        self.draw_action(screen, skin, owned, wardrobe)
        self.back.draw(screen, {"back": "Geri"})

    def info(self, skin, owned, wardrobe, progress):
        # Adın altındaki yazı: giyiliyor mu, fiyatı ya da görevi
        if skin["id"] == wardrobe.selected:
            return "Şu an bunu giyiyorsun", SKIN_SELECTED_COLOR
        if owned:
            return ("Görevle açıldı!" if skin["goal"] else "Senin"), WHITE
        if skin["goal"]:
            kind, target = skin["goal"]
            return f"{skins.goal_text(skin['goal'])}  ({min(progress[kind], target)} / {target})", RECORD_COLOR
        if wardrobe.coins < skin["price"]:
            return f"Fiyatı: {skin['price']} altın ({skin['price'] - wardrobe.coins} altın daha topla)", HINT_COLOR
        return f"Fiyatı: {skin['price']} altın", RECORD_COLOR

    def draw_tabs(self, screen, font):
        for group, rect in zip(self.groups, self.tabs):
            selected = group == self.group
            pygame.draw.rect(screen, BUTTON_FOCUS_COLOR if selected else BUTTON_COLOR, rect, border_radius=10)
            border = BUTTON_FOCUS_BORDER_COLOR if selected and self.focus < 0 else BUTTON_BORDER_COLOR
            pygame.draw.rect(screen, border, rect, 3 if selected else 2, border_radius=10)
            color = BUTTON_FOCUS_BORDER_COLOR if selected else WHITE
            draw_text(screen, font, skins.GROUP_NAMES[group], color, center=rect.center)

    def draw_preview(self, screen):
        screen.blit(self.images["panel"], PANEL[:2])
        platform = self.images["platform"]
        count = 4
        left = CENTER_X - count * platform.get_width() // 2
        for i in range(count):
            screen.blit(platform, (left + i * platform.get_width(), GROUND_Y))
        if self.trail:
            self.trail.draw(screen)
        image = self.preview_image()
        screen.blit(image, image.get_rect(midbottom=self.feet()))
        for x, y, _, _, age, color in self.confetti:
            size = 6 if age < 25 else 4
            screen.fill(color, (round(x), round(y), size, size))

    def draw_grid(self, screen, wardrobe, progress):
        font = self.images["fonts"][20]
        for i, skin in enumerate(self.skins_shown()):
            rect = self.boxes[i]
            owned = wardrobe.owns(skin, progress)
            current = skin["id"] == self.current
            fill = BUTTON_FOCUS_COLOR if current else BUTTON_COLOR if owned else LOCKED_COLOR
            pygame.draw.rect(screen, fill, rect, border_radius=10)
            border = BUTTON_FOCUS_BORDER_COLOR if current else BUTTON_BORDER_COLOR
            pygame.draw.rect(screen, border, rect, 3 if current else 2, border_radius=10)
            image, dim = self.thumb(skin["id"])
            screen.blit(image if owned else dim, image.get_rect(midbottom=(rect.centerx, rect.bottom - 6)))
            if not owned and skin["goal"]:
                lock = self.images["lock"]
                screen.blit(lock, lock.get_rect(bottomright=(rect.right - 4, rect.bottom - 4)))
            elif not owned:
                self.draw_price(screen, font, skin["price"], rect, wardrobe.coins >= skin["price"])
            if skin["id"] == wardrobe.selected:
                self.draw_check(screen, (rect.right - 10, rect.top + 10))

    def draw_price(self, screen, font, price, rect, affordable):
        # Kutunun altında fiyat etiketi: küçük altın + sayı (alınabiliyorsa sarı); her etiket bir kere hazırlanır
        key = (price, affordable)
        if key not in self.tags:
            coin = self.images["small_coin"]
            text = font.render(str(price), True, RECORD_COLOR if affordable else HINT_COLOR)
            tag = pygame.Surface((coin.get_width() + text.get_width() + 11, 16), pygame.SRCALPHA)
            pygame.draw.rect(tag, (20, 18, 40), tag.get_rect(), border_radius=6)
            tag.blit(coin, coin.get_rect(midleft=(4, 8)))
            tag.blit(text, text.get_rect(midleft=(7 + coin.get_width(), 9)))
            self.tags[key] = tag
        tag = self.tags[key]
        screen.blit(tag, tag.get_rect(midbottom=(rect.centerx, rect.bottom - 3)))

    def draw_check(self, screen, center):
        # Giyilen skinin kutusunun köşesinde yeşil yuvarlak içinde tik
        x, y = center
        pygame.draw.circle(screen, (20, 18, 40), center, 10)
        pygame.draw.circle(screen, SKIN_SELECTED_COLOR, center, 8)
        pygame.draw.lines(screen, WHITE, False, [(x - 4, y), (x - 1, y + 3), (x + 4, y - 3)], 2)

    def draw_wallet(self, screen, coins, font):
        # Cüzdan: altın resmi + "Altının: 245" (altın yetmeyince bir süre kırmızı yanıp söner)
        color = GAME_OVER_COLOR if self.flash and (self.flash // 6) % 2 == 0 else RECORD_COLOR
        text = f"Altının: {coins}"
        coin = self.images["coin"]
        width = coin.get_width() + 8 + font.size(text)[0]
        left = CENTER_X - width // 2
        screen.blit(coin, coin.get_rect(midleft=(left, WALLET_Y)))
        draw_text(screen, font, text, color, midleft=(left + coin.get_width() + 8, WALLET_Y + 1))

    def draw_action(self, screen, skin, owned, wardrobe):
        # Alttaki düğme: Seç / Seçili / Satın Al: 150 / Kilitli
        disabled = ()
        if skin["id"] == wardrobe.selected:
            label, disabled = "Seçili", ("action",)
        elif owned:
            label = "Seç"
        elif skin["goal"]:
            label, disabled = "Kilitli", ("action",)
        else:
            label = f"Satın Al: {skin['price']}"
            if wardrobe.coins < skin["price"]:
                disabled = ("action",)
        self.action.draw(screen, {"action": label}, disabled)
        if not owned and not skin["goal"]:
            rect = self.action.rects[0]
            coin = self.images["coin"]
            screen.blit(coin, coin.get_rect(midright=(rect.right - 14, rect.centery)))


SKIN_MENU = SkinMenu()
