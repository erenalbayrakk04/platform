# Karakterler ekranı: skin seçme ve satın alma. Üstte gruplar (Renkler / Karakterler / Efsanevi), ortada
# önizlenen skin büyük çizilmiş, platformda yürüyüp zıplar (efsanevilerin izi de görünür), altında kutular,
# cüzdandaki altın ve elmas (reklam varsa yanında "reklam izle, bedava elmas" düğmesi), "Seç / Satın Al" düğmesi.
# Renkler altınla, Karakterler elmasla alınır.
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
    GEM_COLOR,
)
from score import draw_text
from lang import t, mark
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
CURRENCY_COLORS = {"coins": RECORD_COLOR, "gems": art.tint(GEM_COLOR, 0.3)}  # cüzdandaki sayıların rengi
# Fiyat yazısı (para cinsine göre); parası yetmiyorsa ne kadar eksik olduğuyla
PRICE_TEXTS = {"coins": mark("Fiyatı: {} altın"), "gems": mark("Fiyatı: {} elmas")}
SHORT_TEXTS = {
    "coins": mark("Fiyatı: {price} altın ({need} altın daha topla)"),
    "gems": mark("Fiyatı: {price} elmas ({need} elmas daha topla)"),
}


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
        # Klavye odağı: -1 = sekmeler, 0..n-1 = kutular, n = Seç/Satın Al, n+1 = Geri, n+2 = bedava elmas (reklam)
        # (n = gruptaki skin sayısı)
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
        self.flash = 0  # para yetmedi uyarısı (kalan adım)
        self.flash_currency = "coins"  # hangi para yetmedi
        self.offer = 0  # reklamla bedava elmas: kaç elmas (0 = teklif yok; main.py her karede söyler)
        self.free_rect = pygame.Rect(0, 0, 0, 0)  # bedava elmas düğmesi (çizerken yeri hesaplanır)

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
                f = f + self.COLUMNS if f + self.COLUMNS < n else n + 2 if self.offer else n
            if 0 <= f < n:
                self.show(self.skins_shown()[f]["id"])
        elif f == n + 2:  # bedava elmas (cüzdanın yanında)
            if key in UP_KEYS:
                f = self.index_of(self.current)
            elif key in DOWN_KEYS:
                f = n
        elif f == n:  # Seç / Satın Al
            if key in UP_KEYS:
                f = n + 2 if self.offer else self.index_of(self.current)
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
        if not wardrobe.can_afford(skin):
            self.flash = FLASH_TIME
            self.flash_currency = skin["currency"]
            return "poor", skin["id"]
        return "buy", skin["id"]

    def handle_event(self, event, wardrobe, progress):
        # Döner: ("select" | "buy" | "locked" | "poor", skin adı), "back", "free_gems" (reklam izle) ya da None
        n = len(self.skins_shown())
        if event.type == pygame.KEYDOWN:
            if event.key in ACTIVATE_KEYS:
                if not take_click():
                    return None
                if self.focus == n + 1:
                    return "back"
                if self.focus == n + 2:
                    return "free_gems"
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
            elif self.offer and self.free_rect.collidepoint(event.pos):
                self.focus = n + 2
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
        if self.offer and self.free_rect.inflate(0, 8).collidepoint(pos) and take_click():
            self.focus = n + 2
            self.sync_buttons()
            return "free_gems"
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
        n = len(self.skins_shown())
        if self.focus == n + 2 and not self.offer:  # bedava elmas düğmesi kalktı (bugünlük bitti)
            self.focus = n
            self.sync_buttons()
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
        gem = art.gem_frames()[0]
        platform = art.platform_image()
        panel = pygame.Surface(PANEL[2:], pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, PANEL_ALPHA), panel.get_rect(), border_radius=16)
        self.images = {
            "panel": panel,
            "fonts": fonts,
            "coins": coin,  # para resimleri: adları cüzdandaki paralarla aynı
            "gems": gem,
            "small_coins": scaled(coin, 0.5),
            "small_gems": scaled(gem, 0.5),
            "lock": scaled(art.lock_image(), 0.5),
            "ad": scaled(art.ad_image(), 0.75),
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
        if self.offer:  # cüzdan sola kayar, sağında bedava elmas düğmesi
            self.draw_free_gems(screen, fonts[MENU_FONT_SIZE])
            self.draw_wallet(screen, wardrobe, fonts[MENU_FONT_SIZE], (20 + self.free_rect.left - 12) // 2)
        else:
            self.draw_wallet(screen, wardrobe, fonts[MENU_FONT_SIZE])
        self.draw_action(screen, skin, owned, wardrobe)
        self.back.draw(screen, {"back": mark("Geri")})

    def info(self, skin, owned, wardrobe, progress):
        # Adın altındaki yazı: giyiliyor mu, fiyatı ya da görevi
        if skin["id"] == wardrobe.selected:
            return mark("Şu an bunu giyiyorsun"), SKIN_SELECTED_COLOR
        if owned:
            return (mark("Görevle açıldı!") if skin["goal"] else mark("Senin")), WHITE
        if skin["goal"]:
            kind, target = skin["goal"]
            return f"{skins.goal_text(skin['goal'])}  ({min(progress[kind], target)} / {target})", RECORD_COLOR
        currency = skin["currency"]
        if not wardrobe.can_afford(skin):
            need = skin["price"] - wardrobe.balance(currency)
            return t(SHORT_TEXTS[currency], need).format(price=skin["price"], need=need), HINT_COLOR
        return t(PRICE_TEXTS[currency]).format(skin["price"]), CURRENCY_COLORS[currency]

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
                self.draw_price(screen, font, skin, rect, wardrobe.can_afford(skin))
            if skin["id"] == wardrobe.selected:
                self.draw_check(screen, (rect.right - 10, rect.top + 10))

    def draw_price(self, screen, font, skin, rect, affordable):
        # Kutunun altında fiyat etiketi: küçük altın / elmas + sayı (alınabiliyorsa renkli); bir kere hazırlanır
        key = (skin["currency"], skin["price"], affordable)
        if key not in self.tags:
            icon = self.images["small_" + skin["currency"]]
            color = CURRENCY_COLORS[skin["currency"]] if affordable else HINT_COLOR
            text = font.render(str(skin["price"]), True, color)
            tag = pygame.Surface((icon.get_width() + text.get_width() + 11, 16), pygame.SRCALPHA)
            pygame.draw.rect(tag, (20, 18, 40), tag.get_rect(), border_radius=6)
            tag.blit(icon, icon.get_rect(midleft=(4, 8)))
            tag.blit(text, text.get_rect(midleft=(7 + icon.get_width(), 9)))
            self.tags[key] = tag
        tag = self.tags[key]
        screen.blit(tag, tag.get_rect(midbottom=(rect.centerx, rect.bottom - 3)))

    def draw_check(self, screen, center):
        # Giyilen skinin kutusunun köşesinde yeşil yuvarlak içinde tik
        x, y = center
        pygame.draw.circle(screen, (20, 18, 40), center, 10)
        pygame.draw.circle(screen, SKIN_SELECTED_COLOR, center, 8)
        pygame.draw.lines(screen, WHITE, False, [(x - 4, y), (x - 1, y + 3), (x + 4, y - 3)], 2)

    def draw_free_gems(self, screen, font):
        # Cüzdanın sağında: ▶ (reklam) +2 (elmas resmi) — reklam izleyince bedava elmas
        ad, gem = self.images["ad"], self.images["gems"]
        text = f"+{self.offer}"
        width = 10 + ad.get_width() + 6 + font.size(text)[0] + 4 + gem.get_width() + 10
        self.free_rect = pygame.Rect(0, 0, width, 38)
        self.free_rect.midright = (SCREEN_WIDTH - 18, WALLET_Y)
        rect = self.free_rect
        focused = self.focus == len(self.skins_shown()) + 2
        pygame.draw.rect(screen, BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR, rect, border_radius=10)
        border = BUTTON_FOCUS_BORDER_COLOR if focused else BUTTON_BORDER_COLOR
        pygame.draw.rect(screen, border, rect, 3 if focused else 2, border_radius=10)
        x = rect.left + 10
        screen.blit(ad, ad.get_rect(midleft=(x, rect.centery)))
        x += ad.get_width() + 6
        draw_text(screen, font, text, CURRENCY_COLORS["gems"], midleft=(x, rect.centery + 1))
        x += font.size(text)[0] + 4
        screen.blit(gem, gem.get_rect(midleft=(x, rect.centery)))

    def draw_wallet(self, screen, wardrobe, font, center_x=CENTER_X):
        # Cüzdan: altın ve elmas (resim + sayı); para yetmeyince o para bir süre kırmızı yanıp söner
        items = []
        for currency in ("coins", "gems"):
            flashing = self.flash and self.flash_currency == currency and (self.flash // 6) % 2 == 0
            color = GAME_OVER_COLOR if flashing else CURRENCY_COLORS[currency]
            items.append((self.images[currency], str(wardrobe.balance(currency)), color))
        widths = [icon.get_width() + 6 + font.size(text)[0] for icon, text, _ in items]
        left = center_x - (sum(widths) + 32 * (len(items) - 1)) // 2
        for (icon, text, color), width in zip(items, widths):
            screen.blit(icon, icon.get_rect(midleft=(left, WALLET_Y)))
            draw_text(screen, font, text, color, midleft=(left + icon.get_width() + 6, WALLET_Y + 1))
            left += width + 32

    def draw_action(self, screen, skin, owned, wardrobe):
        # Alttaki düğme: Seç / Seçili / Satın Al: 150 (altın ya da elmas resmiyle) / Kilitli
        disabled = ()
        if skin["id"] == wardrobe.selected:
            label, disabled = mark("Seçili"), ("action",)
        elif owned:
            label = mark("Seç")
        elif skin["goal"]:
            label, disabled = mark("Kilitli"), ("action",)
        else:
            label = t("Satın Al: {}").format(skin["price"])
            if not wardrobe.can_afford(skin):
                disabled = ("action",)
        self.action.draw(screen, {"action": label}, disabled)
        if not owned and not skin["goal"]:
            rect = self.action.rects[0]
            icon = self.images[skin["currency"]]
            screen.blit(icon, icon.get_rect(midright=(rect.right - 14, rect.centery)))


SKIN_MENU = SkinMenu()
