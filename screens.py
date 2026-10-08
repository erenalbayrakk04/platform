# Ekranlar: ana menü, ses ayarları, nasıl oynanır, rekorlar, durdu ve "Kaybettin". Oyunun üstüne karanlık bir perde
# serilip yazılar ve düğmeler (ui.py) ortalanır. Hangi düğmeye basıldığına main.py bakar.
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TITLE,
    OVERLAY_ALPHA,
    TITLE_FONT_SIZE,
    MENU_FONT_SIZE,
    MENU_SMALL_FONT_SIZE,
    TITLE_COLOR,
    GAME_OVER_COLOR,
    RECORD_COLOR,
    HINT_COLOR,
    SLOW_HINT_COLOR,
    LAVA_TOP_COLOR,
    COIN_POINTS,
    MUTE_KEY,
    VOLUME_STEPS,
    DIFFICULTY_NAMES,
)
from score import draw_text
from ui import Buttons, Slider, take_click, ACTIVATE_KEYS, UP_KEYS, DOWN_KEYS
import art

CENTER_X = SCREEN_WIDTH // 2

# Her ekranın düğmeleri (adları main.py'de kullanılır)
MAIN_BUTTONS = Buttons(["play", "difficulty", "howto", "records", "sound_menu"], top=345)
BACK_BUTTON = Buttons(["back"], top=655)
PAUSE_BUTTONS = Buttons(["resume", "sound", "menu"], top=330)
GAME_OVER_BUTTONS = Buttons(["again", "menu"], top=505)

# Düğme yazıları; değişenler ("sound", "difficulty") main.py'den gelir
LABELS = {
    "play": "Oyna",
    "sound_menu": "Ses Ayarları",
    "howto": "Nasıl Oynanır",
    "records": "Rekorlar",
    "back": "Geri",
    "resume": "Devam Et",
    "menu": "Ana Menü",
    "again": "Tekrar Oyna",
}

# Yazı tipleri, perde ve resimler ilk kullanımda bir kere hazırlanır (pygame.init()'ten sonra olmalı)
_cache = {}


def font(size):
    if size not in _cache:
        _cache[size] = pygame.font.Font(None, size)
    return _cache[size]


def draw_overlay(screen):
    if "overlay" not in _cache:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, OVERLAY_ALPHA))
        _cache["overlay"] = overlay
    screen.blit(_cache["overlay"], (0, 0))


def draw_slow_hint(screen):
    # Telefon tarayıcıyı saniyede 30 kareyle sınırlıyorsa (iPhone Düşük Güç Modu) oyuncuya söyle
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), "Daha akıcı oyun için", SLOW_HINT_COLOR, center=(CENTER_X, 682))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), "Düşük Güç Modu'nu kapat", SLOW_HINT_COLOR, center=(CENTER_X, 704))


def draw_title(screen, text, y, color=TITLE_COLOR):
    draw_text(screen, font(TITLE_FONT_SIZE), text, color, center=(CENTER_X, y))


def draw_main_menu(screen, best_height, labels, web=False):
    draw_overlay(screen)
    # Oyun adı iki satır: "Platform" / "Oyunu"
    first, _, rest = TITLE.partition(" ")
    draw_title(screen, first, 130)
    draw_title(screen, rest, 185)
    # Asıl hedef: yükseklik rekoru
    draw_text(screen, font(MENU_FONT_SIZE + 10), f"Rekor: {best_height} m", RECORD_COLOR, center=(CENTER_X, 260))
    MAIN_BUTTONS.draw(screen, {**LABELS, **labels})
    # Telefonda (tarayıcıda) hep yazsın: iPhone Düşük Güç Modu'nda oyun daha az akıcı
    if web:
        draw_slow_hint(screen)


class SoundMenu:
    # Ses ayarları ekranı: müzik ve efekt seviyesi çubukları + "Ses: Açık/Kapalı" ve "Geri" düğmeleri.
    # Klavyede yukarı/aşağı ile seçilir, çubuk seçiliyken sol/sağ ok ile ayarlanır
    SLIDER_NAMES = ("music", "effects")
    TITLES = {"music": "Müzik", "effects": "Efektler"}
    LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
    RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)

    def __init__(self):
        self.sliders = {"music": Slider(255), "effects": Slider(370)}
        self.buttons = Buttons(["sound", "back"], top=480)
        self.focus = 0  # 0 = müzik, 1 = efektler, 2+ = düğmeler

    def open(self):
        self.focus = 0
        self.buttons.focus = -1  # hiçbir düğme seçili görünmesin

    def set_focus(self, index):
        count = len(self.SLIDER_NAMES)
        self.focus = index % (count + len(self.buttons.actions))
        self.buttons.focus = self.focus - count  # çubuk seçiliyse eksi (düğme seçili görünmez)

    def handle_event(self, event):
        # Değişen çubuğun adı ("music"/"effects") veya basılan düğmenin adı ("sound"/"back"), yoksa None
        count = len(self.SLIDER_NAMES)
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self.set_focus(self.focus - 1)
            elif event.key in DOWN_KEYS:
                self.set_focus(self.focus + 1)
            elif self.focus < count:
                name = self.SLIDER_NAMES[self.focus]
                step = -1 if event.key in self.LEFT_KEYS else 1 if event.key in self.RIGHT_KEYS else 0
                if step and self.sliders[name].nudge(step):
                    return name
            elif event.key in ACTIVATE_KEYS and take_click():
                return self.buttons.actions[self.focus - count]
            return None
        for i, name in enumerate(self.SLIDER_NAMES):
            slider = self.sliders[name]
            if slider.handle_event(event):
                self.set_focus(i)
                return name
            if event.type == pygame.MOUSEMOTION and slider.touch_area().collidepoint(event.pos):
                self.set_focus(i)
        action = self.buttons.handle_event(event)
        if self.buttons.focus >= 0:  # fare bir düğmenin üstüne geldi
            self.focus = self.buttons.focus + count
        return action

    def draw(self, screen, labels, muted):
        draw_overlay(screen)
        draw_title(screen, "Ses Ayarları", 120)
        for i, name in enumerate(self.SLIDER_NAMES):
            slider = self.sliders[name]
            focused = self.focus == i
            y = slider.rect.top - 32
            color = TITLE_COLOR if focused else (255, 255, 255)
            draw_text(screen, font(MENU_FONT_SIZE), self.TITLES[name], color, midleft=(slider.rect.left, y))
            percent = f"%{slider.value * 100 // VOLUME_STEPS}"
            draw_text(screen, font(MENU_FONT_SIZE), percent, color, midright=(slider.rect.right, y))
            slider.draw(screen, focused, muted)
        self.buttons.draw(screen, {**LABELS, **labels})


SOUND_MENU = SoundMenu()


def howto_icons():
    # Nasıl oynanır sayfasındaki küçük resimler: oyundaki resimlerin aynısı, en fazla 36 piksel
    if "howto" not in _cache:

        def fit(image, box=36):
            scale = min(1, box / image.get_width(), box / image.get_height())
            size = (round(image.get_width() * scale), round(image.get_height() * scale))
            return pygame.transform.scale(image, size)

        _cache["howto"] = {
            "coin": fit(art.coin_frames()[0]),
            "heart": fit(art.heart_images()["full"]),
            "magnet": fit(art.magnet_image()),
            "shield": fit(art.shield_image()),
            "spring": fit(art.spring_frames()[0]),
            "enemy": fit(art.enemy_frames()[0][1]),
            "bat": fit(art.flyer_frames()[0]),
            "crumble": fit(art.crumble_frames()[1]),
            "lava": fit(art.lava_frames()[0].subsurface((0, 0, 36, 32))),
        }
    return _cache["howto"]


HOWTO_ROWS = (
    ("coin", f"Altın: +{COIN_POINTS} puan"),
    ("heart", "Kalp: +1 can"),
    ("magnet", "Mıknatıs: altınları çeker"),
    ("shield", "Kalkan: düşman ve lavdan korur"),
    ("spring", "Yay: çok yükseğe fırlatır"),
    ("enemy", "Düşman: üstüne zıpla, yanına değme"),
    ("bat", "Yarasa: onun da üstüne zıpla"),
    ("crumble", "Çatlak taş: basınca kırılır"),
    ("lava", "Lav: yükseliyor, acele et!"),
)


def draw_howto(screen):
    draw_overlay(screen)
    draw_text(screen, font(MENU_FONT_SIZE + 10), "Nasıl Oynanır", TITLE_COLOR, center=(CENTER_X, 45))
    small = font(MENU_SMALL_FONT_SIZE)
    draw_text(screen, small, "Amaç: en yükseğe tırman, rekorunu geç!", RECORD_COLOR, center=(CENTER_X, 90))
    draw_text(screen, small, "Ok tuşları / A-D: yürü    Boşluk / W: zıpla", HINT_COLOR, center=(CENTER_X, 122))
    draw_text(screen, small, "Telefonda: alttaki düğmeler", HINT_COLOR, center=(CENTER_X, 146))
    draw_text(
        screen, small, f"ESC / P: durdur    {MUTE_KEY.upper()}: ses", HINT_COLOR, center=(CENTER_X, 170)
    )
    icons = howto_icons()
    for i, (name, text) in enumerate(HOWTO_ROWS):
        y = 220 + i * 44
        icon = icons[name]
        screen.blit(icon, icon.get_rect(center=(58, y)))
        color = LAVA_TOP_COLOR if name == "lava" else None
        draw_text(screen, small, text, color or (255, 255, 255), midleft=(92, y))
    BACK_BUTTON.draw(screen, LABELS)


def draw_records(screen, best_heights, high_scores, stats, current):
    draw_overlay(screen)
    draw_title(screen, "Rekorlar", 70)
    text_font = font(MENU_FONT_SIZE)
    label_font = font(MENU_SMALL_FONT_SIZE + 2)
    # Her zorluk modunun rekorları: en yüksek tırmanış (asıl hedef) ve en yüksek puan. Seçili mod sarı
    height_x, score_x = 265, SCREEN_WIDTH - 40  # sütunların sağ kenarı
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), "Tırmanış", HINT_COLOR, midright=(height_x, 130))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), "Puan", HINT_COLOR, midright=(score_x, 130))
    for i, (mode, name) in enumerate(DIFFICULTY_NAMES.items()):
        y = 170 + i * 44
        color = RECORD_COLOR if mode == current else (255, 255, 255)
        draw_text(screen, text_font, name, color, midleft=(40, y))
        draw_text(screen, text_font, f"{best_heights[mode]} m", color, midright=(height_x, y))
        draw_text(screen, text_font, str(high_scores[mode]), color, midright=(score_x, y))
    # Bütün modların toplamı
    rows = (
        ("Oynanan oyun", str(stats["games"])),
        ("Toplam tırmanış", f"{stats['climbed']} m"),
        ("Toplam altın", str(stats["coins"])),
        ("Yenilen düşman", str(stats["enemies"])),
    )
    for i, (label, value) in enumerate(rows):
        y = 400 + i * 52
        draw_text(screen, label_font, label, HINT_COLOR, midleft=(40, y))
        draw_text(screen, text_font, value, midright=(score_x, y))
    BACK_BUTTON.draw(screen, LABELS)


def draw_pause(screen, labels):
    draw_overlay(screen)
    draw_title(screen, "Durdu", 220)
    PAUSE_BUTTONS.draw(screen, {**LABELS, **labels})


def draw_game_over(screen, score, mode_name, best_height, high_score, new_record, ready, slow=False):
    # mode_name = oynanan zorluk modu (rekorlar o modun rekorları)
    draw_overlay(screen)
    draw_title(screen, "Kaybettin!", 200, GAME_OVER_COLOR)
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), f"Zorluk: {mode_name}", HINT_COLOR, center=(CENTER_X, 243))
    # Büyük yazı: ne kadar tırmandın (asıl hedef). Puan ve ayrıntılar altında küçük
    draw_text(screen, font(TITLE_FONT_SIZE), f"{score.height} m", center=(CENTER_X, 290))
    small = font(MENU_SMALL_FONT_SIZE)
    details = f"Puan: {score.total}   Altın: {score.coins}   Düşman: {score.enemies}"
    draw_text(screen, small, details, HINT_COLOR, center=(CENTER_X, 335))
    if new_record:
        draw_text(screen, font(MENU_FONT_SIZE), "YENİ REKOR!", RECORD_COLOR, center=(CENTER_X, 390))
    else:
        draw_text(screen, font(MENU_FONT_SIZE), f"Rekor: {best_height} m", RECORD_COLOR, center=(CENTER_X, 390))
    draw_text(screen, small, f"En yüksek puan: {high_score}", HINT_COLOR, center=(CENTER_X, 420))
    # Düğmeler biraz bekledikten sonra çıkar (yanlışlıkla basılmasın)
    if ready:
        GAME_OVER_BUTTONS.draw(screen, LABELS)
    if slow:
        draw_slow_hint(screen)
