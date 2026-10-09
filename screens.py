# Ekranlar: ana menü, oyun seçimi (bölümler / sonsuz), bölüm seçme, ses ayarları, nasıl oynanır, rekorlar,
# durdu, "Kaybettin" ve "Bölüm bitti". Oyunun üstüne karanlık bir perde
# serilip yazılar ve düğmeler (ui.py) ortalanır. Hangi düğmeye basıldığına main.py bakar.
import math

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
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
    STAR_COIN_SHARE,
)
from score import draw_text
from stages import STAGES
from title import draw_logo
from ui import Buttons, Slider, StageGrid, take_click, ACTIVATE_KEYS, UP_KEYS, DOWN_KEYS
import art

CENTER_X = SCREEN_WIDTH // 2

# Her ekranın düğmeleri (adları main.py'de kullanılır)
MAIN_BUTTONS = Buttons(["play", "difficulty", "howto", "records", "sound_menu"], top=345)
BACK_BUTTON = Buttons(["back"], top=655)
PAUSE_BUTTONS = Buttons(["resume", "sound", "menu"], top=330)
GAME_OVER_BUTTONS = Buttons(["again", "menu"], top=505)
PLAY_BUTTONS = Buttons(["stages", "endless", "back"], top=345)
STAGE_GRID = StageGrid(len(STAGES), back_top=655)
CLEAR_BUTTONS = Buttons(["next", "again", "stages"], top=505)
LAST_CLEAR_BUTTONS = Buttons(["again", "stages"], top=505)  # son bölüm bitince "Sonraki" yok

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
    "stages": "Bölümler",
    "endless": "Sonsuz Oyun",
    "next": "Sonraki Bölüm",
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
    # Oyunun adı (piksel harfli logo): giriş ekranındakiyle aynı yerde — geçişte yerinden oynamaz
    draw_logo(screen)
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
    # Nasıl oynanır sayfasındaki küçük resimler: oyundaki resimlerin aynısı, en fazla HOWTO_ICON piksel
    if "howto" not in _cache:

        def fit(image, box=HOWTO_ICON):
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
            "slime": fit(art.slime_frames()["walk1"][1]),
            "spiky": fit(art.spiky_frames()[0][1]),
            "cannon": fit(art.cannon_frames()[1][1]),
            "bat": fit(art.flyer_frames()[0]),
            "bee": fit(art.bee_frames()[0][1]),
            "crumble": fit(art.crumble_frames()[1]),
            "lava": fit(art.lava_frames()[0].subsurface((0, 0, 36, 32))),
            "flag": fit(art.flag_frames()[0]),
        }
    return _cache["howto"]


HOWTO_ROWS = (
    ("flag", "Bayrak: bölümün sonu, ona ulaş!"),
    ("coin", f"Altın: +{COIN_POINTS} puan"),
    ("heart", "Kalp: +1 can"),
    ("magnet", "Mıknatıs: altınları çeker"),
    ("shield", "Kalkan: düşman ve lavdan korur"),
    ("spring", "Yay: çok yükseğe fırlatır"),
    ("crumble", "Çatlak taş: basınca kırılır"),
    ("enemy", "Düşman: üstüne zıpla, yanına değme"),
    ("slime", "Sümük: zıplar, inince üstüne bas"),
    ("spiky", "Kirpi: dikenli, üstüne BASMA!"),
    ("cannon", "Topçu: ateş atar, üstüne zıpla"),
    ("bat", "Yarasa: onun da üstüne zıpla"),
    ("bee", "Arı: aşağı yukarı uçar"),
    ("lava", "Lav: yükseliyor, acele et!"),
)
HOWTO_WARN_ROWS = ("spiky", "lava")  # yazısı uyarı renginde olanlar
HOWTO_ICON = 30  # resimlerin en fazla boyu (piksel)
HOWTO_TOP = 200  # ilk satırın ortası (y)
HOWTO_GAP = 31  # satırlar arası (piksel)


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
        y = HOWTO_TOP + i * HOWTO_GAP
        icon = icons[name]
        screen.blit(icon, icon.get_rect(center=(58, y)))
        color = LAVA_TOP_COLOR if name in HOWTO_WARN_ROWS else (255, 255, 255)
        draw_text(screen, small, text, color, midleft=(92, y))
    BACK_BUTTON.draw(screen, LABELS)


def draw_records(screen, best_heights, high_scores, stats, current, stars):
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
        ("Bölüm yıldızı", f"{sum(stars)} / {3 * len(stars)}"),
    )
    for i, (label, value) in enumerate(rows):
        y = 400 + i * 48
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


def stars_needed(total):
    # 2. yıldız için en az kaç altın (bölümdeki altınların STAR_COIN_SHARE'i, yukarı yuvarlanır)
    return math.ceil(round(total * STAR_COIN_SHARE, 6))


def stage_title(index):
    return f"{index + 1}. Bölüm: {STAGES[index]['name']}"


def draw_play_select(screen, labels, mode_name, stars):
    # Oyna'ya basınca: bölümler mi sonsuz oyun mu
    draw_overlay(screen)
    draw_logo(screen)
    draw_text(
        screen, font(MENU_FONT_SIZE + 10), f"Yıldızlar: {sum(stars)} / {3 * len(stars)}", RECORD_COLOR,
        center=(CENTER_X, 260),
    )
    PLAY_BUTTONS.draw(screen, {**LABELS, **labels})
    small = font(MENU_SMALL_FONT_SIZE)
    draw_text(screen, small, "Bölümler: sırayla bitir, yıldız topla", HINT_COLOR, center=(CENTER_X, 560))
    draw_text(screen, small, f"Sonsuz Oyun: rekor için tırman ({mode_name})", HINT_COLOR, center=(CENTER_X, 586))


def draw_stages(screen, stars, unlocked):
    # Bölüm seçme ekranı: kutular + seçili bölümün adı ve hedefi
    draw_overlay(screen)
    draw_title(screen, "Bölümler", 60)
    draw_text(
        screen, font(MENU_SMALL_FONT_SIZE + 2), f"Yıldızlar: {sum(stars)} / {3 * len(stars)}", RECORD_COLOR,
        center=(CENTER_X, 108),
    )
    STAGE_GRID.draw(screen, stars, unlocked)
    focus = STAGE_GRID.focus
    if focus < len(STAGES):
        if unlocked(focus):
            draw_text(screen, font(MENU_FONT_SIZE), stage_title(focus), center=(CENTER_X, 588))
            info = f"Hedef: {STAGES[focus]['goal']} m" + ("   Lav var!" if STAGES[focus]["lava"] else "")
            draw_text(screen, font(MENU_SMALL_FONT_SIZE), info, HINT_COLOR, center=(CENTER_X, 614))
        else:
            draw_text(screen, font(MENU_FONT_SIZE), "Kilitli", HINT_COLOR, center=(CENTER_X, 588))
            draw_text(
                screen, font(MENU_SMALL_FONT_SIZE), "Önceki bölümü bitirince açılır", HINT_COLOR,
                center=(CENTER_X, 614),
            )


def draw_stage_intro(screen, index, goal):
    # Bölüm başlarken birkaç saniye: bölümün adı, hedefi ve yeni tanıtılan şey
    stage = STAGES[index]
    draw_text(screen, font(MENU_FONT_SIZE), f"{index + 1}. Bölüm", HINT_COLOR, center=(CENTER_X, 170))
    draw_text(screen, font(MENU_FONT_SIZE + 14), stage["name"], TITLE_COLOR, center=(CENTER_X, 210))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), stage["intro"], center=(CENTER_X, 250))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), f"Hedef: {goal} m", HINT_COLOR, center=(CENTER_X, 278))


STAR_IMAGES = {}


def star_images():
    if not STAR_IMAGES:
        STAR_IMAGES.update(
            big=art.star_image(True, 64), big_empty=art.star_image(False, 64),
            small=art.star_image(True, 22), small_empty=art.star_image(False, 22),
        )
    return STAR_IMAGES


def draw_stage_clear(screen, index, result, shown, ready):
    # Bölüm bitti: yıldızlar (shown = şimdiye kadar beliren), hangi şart tuttu, düğmeler (ready olunca).
    # result = {"stars", "coins", "coins_total", "no_hurt", "unlocked"} (main.py)
    draw_overlay(screen)
    draw_title(screen, "Tebrikler!", 140)
    draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), stage_title(index), HINT_COLOR, center=(CENTER_X, 185))
    images = star_images()
    for k in range(3):
        image = images["big" if k < shown else "big_empty"]
        y = 255 - (12 if k == 1 else 0)  # ortadaki biraz yukarıda
        screen.blit(image, image.get_rect(center=(CENTER_X + (k - 1) * 80, y)))
    need = stars_needed(result["coins_total"])
    conditions = (
        (True, "Bayrağa ulaştın"),
        (result["coins"] >= need, f"Altın: {result['coins']} / {result['coins_total']}  (en az {need})"),
        (result["no_hurt"], "Hiç can kaybetmeden"),
    )
    small = font(MENU_SMALL_FONT_SIZE + 2)
    for i, (done, text) in enumerate(conditions):
        y = 330 + i * 32
        icon = images["small" if done else "small_empty"]
        screen.blit(icon, icon.get_rect(center=(80, y)))
        draw_text(screen, small, text, (255, 255, 255) if done else HINT_COLOR, midleft=(102, y))
    if result["unlocked"]:
        draw_text(screen, font(MENU_FONT_SIZE), "Yeni bölüm açıldı!", RECORD_COLOR, center=(CENTER_X, 450))
    elif index == len(STAGES) - 1:
        draw_text(screen, font(MENU_FONT_SIZE), "Bütün bölümler bitti!", RECORD_COLOR, center=(CENTER_X, 450))
    if ready:
        buttons = CLEAR_BUTTONS if index < len(STAGES) - 1 else LAST_CLEAR_BUTTONS
        buttons.draw(screen, LABELS)


def draw_stage_failed(screen, index, score, ready, slow=False):
    # Bölümde canlar bitti: ne kadar kalmıştı; Tekrar Dene / Bölümler
    draw_overlay(screen)
    draw_title(screen, "Kaybettin!", 200, GAME_OVER_COLOR)
    draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), stage_title(index), HINT_COLOR, center=(CENTER_X, 243))
    draw_text(screen, font(TITLE_FONT_SIZE), f"{score.height} / {score.goal} m", center=(CENTER_X, 295))
    left = max(0, score.goal - score.height)
    draw_text(screen, font(MENU_FONT_SIZE), f"Bayrağa {left} m kalmıştı", RECORD_COLOR, center=(CENTER_X, 350))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), f"Altın: {score.coins}", HINT_COLOR, center=(CENTER_X, 385))
    if ready:
        GAME_OVER_BUTTONS.draw(screen, {**LABELS, "again": "Tekrar Dene", "menu": "Bölümler"})
    if slow:
        draw_slow_hint(screen)
