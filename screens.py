# Ekranlar: ana menü, nasıl oynanır, rekorlar, durdu ve "Kaybettin". Oyunun üstüne karanlık bir perde
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
)
from score import draw_text
from ui import Buttons
import art

CENTER_X = SCREEN_WIDTH // 2

# Her ekranın düğmeleri (adları main.py'de kullanılır)
MAIN_BUTTONS = Buttons(["play", "difficulty", "howto", "records", "sound"], top=345)
BACK_BUTTON = Buttons(["back"], top=655)
PAUSE_BUTTONS = Buttons(["resume", "sound", "menu"], top=330)
GAME_OVER_BUTTONS = Buttons(["again", "menu"], top=505)

# Düğme yazıları; değişenler ("sound", "difficulty") main.py'den gelir
LABELS = {
    "play": "Oyna",
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
    ("shield", "Kalkan: düşmanlar zarar veremez"),
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


def draw_records(screen, best_height, high_score, stats):
    draw_overlay(screen)
    draw_title(screen, "Rekorlar", 90)
    rows = (
        ("En yüksek tırmanış", f"{best_height} m", RECORD_COLOR),
        ("En yüksek puan", str(high_score), RECORD_COLOR),
        ("Oynanan oyun", str(stats["games"]), None),
        ("Toplam tırmanış", f"{stats['climbed']} m", None),
        ("Toplam altın", str(stats["coins"]), None),
        ("Yenilen düşman", str(stats["enemies"]), None),
    )
    text_font = font(MENU_FONT_SIZE)
    for i, (label, value, color) in enumerate(rows):
        y = 180 + i * 62
        draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), label, HINT_COLOR, midleft=(40, y))
        draw_text(screen, text_font, value, color or (255, 255, 255), midright=(SCREEN_WIDTH - 40, y))
    BACK_BUTTON.draw(screen, LABELS)


def draw_pause(screen, labels):
    draw_overlay(screen)
    draw_title(screen, "Durdu", 220)
    PAUSE_BUTTONS.draw(screen, {**LABELS, **labels})


def draw_game_over(screen, score, best_height, high_score, new_record, ready, slow=False):
    draw_overlay(screen)
    draw_title(screen, "Kaybettin!", 200, GAME_OVER_COLOR)
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
