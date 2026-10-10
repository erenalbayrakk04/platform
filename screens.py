# Ekranlar: ana menü, oyun seçimi (bölümler / sonsuz), bölüm seçme, ayarlar (ses, dil), nasıl oynanır, rekorlar,
# durdu, "Devam Et?", "Kaybettin" ve "Bölüm bitti". Oyunun üstüne karanlık bir perde
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
    LEGENDARY_COLOR,
    GEM_COLOR,
    COIN_POINTS,
    MUTE_KEY,
    VOLUME_STEPS,
    DIFFICULTY_NAMES,
    STAR_COIN_SHARE,
    BUTTON_WIDTH,
    SLIDER_TRACK_COLOR,
    REVIVE_GEMS,
)
from score import draw_text
from lang import t, mark
from stages import STAGE_SETS, STAGE_COUNT
from title import draw_logo
from ui import Buttons, Slider, StageGrid, draw_box, take_click, ACTIVATE_KEYS, UP_KEYS, DOWN_KEYS
import art
import boss
import skins
import theme

CENTER_X = SCREEN_WIDTH // 2

# Her ekranın düğmeleri (adları main.py'de kullanılır)
MAIN_BUTTONS = Buttons(["play", "skins", "difficulty", "howto", "records", "sound_menu"], top=335, gap=60)
BACK_BUTTON = Buttons(["back"], top=655)
PAUSE_BUTTONS = Buttons(["resume", "sound", "menu"], top=330)
PLAY_BUTTONS = Buttons(["stages", "endless", "back"], top=322, gap=84)  # aralık geniş: Sonsuz Oyun'un altında rekor yazar
PLAY_RECORD_Y = 448  # "Sonsuz Oyun" düğmesinin altındaki rekor yazısı
STAGE_GRID = StageGrid(STAGE_COUNT, list(DIFFICULTY_NAMES), back_top=655)
# Devam Et teklifi: elmasla / (reklam varsa) reklamla / Hayır
REVIVE_BUTTONS = Buttons(["revive", "give_up"], top=470)
REVIVE_AD_BUTTONS = Buttons(["revive", "revive_ad", "give_up"], top=455)
# Oyun sonu ekranları: (ekran, 2 kat elmas teklifi var mı) → düğmeler. "game_over" = kaybettin (bölümde de),
# "clear" = bölüm bitti, "last_clear" = son bölüm bitti ("Sonraki" yok). 2 kat elmas (reklamla) hep en altta
END_BUTTONS = {
    ("game_over", False): Buttons(["again", "menu"], top=505),
    ("game_over", True): Buttons(["again", "menu", "double"], top=505),
    ("clear", False): Buttons(["next", "again", "stages"], top=505),
    ("clear", True): Buttons(["next", "again", "stages", "double"], top=478, gap=58),  # alttaki bilgi yazısına değmesin
    ("last_clear", False): Buttons(["again", "stages"], top=505),
    ("last_clear", True): Buttons(["again", "stages", "double"], top=505),
}
# 2 kat elmas düğmesinin yazısı ({} = bu oyunda kazanılan elmas): teklif / alındı / reklam gelmedi
DOUBLE_LABELS = {"offer": mark("2 Kat: +{}"), "done": mark("+{} elmas alındı!"), "failed": mark("Reklam yok")}


def revive_buttons(ad):
    # Devam Et ekranının düğmeleri; ad = reklam seçeneği (None = yok, "offer", "failed")
    return REVIVE_AD_BUTTONS if ad else REVIVE_BUTTONS


def end_buttons(kind, double):
    return END_BUTTONS[kind, double is not None]

# Düğme yazıları; değişenler ("sound", "difficulty", "language") main.py'den gelir
LABELS = {
    "play": mark("Oyna"),
    "skins": mark("Karakterler"),
    "sound_menu": mark("Ayarlar"),
    "howto": mark("Nasıl Oynanır"),
    "records": mark("Rekorlar"),
    "back": mark("Geri"),
    "resume": mark("Devam Et"),
    "menu": mark("Ana Menü"),
    "again": mark("Tekrar Oyna"),
    "stages": mark("Bölümler"),
    "endless": mark("Sonsuz Oyun"),
    "next": mark("Sonraki Bölüm"),
    "revive_ad": mark("Reklam İzle"),
    "give_up": mark("Hayır"),
}

# Yazı tipleri, perde ve resimler ilk kullanımda bir kere hazırlanır (pygame.init()'ten sonra olmalı; resimler
# her tema için ayrı: theme.cached)
_cache = {}
_images = {}


def font(size):
    if size not in _cache:
        _cache[size] = pygame.font.Font(None, size)
    return _cache[size]


def make_overlay():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, OVERLAY_ALPHA))
    if theme.modern():  # Modern: ortası biraz açık, üstü ve altı koyu (yazılar ortada daha net)
        import modern

        alpha = OVERLAY_ALPHA
        overlay = modern.gradient(overlay.get_size(), (8, 6, 22, alpha + 30), (8, 6, 22, alpha - 10), (8, 6, 22, alpha + 30))
    return overlay


def draw_overlay(screen):
    screen.blit(theme.cached(_images, "overlay", make_overlay), (0, 0))


def ad_icon():
    return theme.cached(_images, "ad", art.ad_image)


def draw_button_icons(screen, buttons, action, left=None, right=None):
    # Düğmenin içinde solda / sağda küçük resim (▶ reklam, elmas)
    rect = buttons.rects[buttons.actions.index(action)]
    if left is not None:
        screen.blit(left, left.get_rect(midleft=(rect.left + 14, rect.centery)))
    if right is not None:
        screen.blit(right, right.get_rect(midright=(rect.right - 14, rect.centery)))


def draw_note(screen, text):
    # Ekranın altında kısa bilgi ("+2 elmas!", "Şu an reklam yok..."): koyu zemin üstünde
    text = t(text)  # genişliği çevrilmiş yazıya göre
    small = font(MENU_SMALL_FONT_SIZE + 2)
    box = pygame.Rect(0, 0, small.size(text)[0] + 28, 32)
    box.center = (CENTER_X, 700)
    draw_box(screen, box, (20, 18, 40), HINT_COLOR, 2, 10)
    draw_text(screen, small, text, center=box.center)


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
    draw_text(
        screen, font(MENU_FONT_SIZE + 10), t("Rekor: {} m").format(best_height), RECORD_COLOR, center=(CENTER_X, 260)
    )
    MAIN_BUTTONS.draw(screen, {**LABELS, **labels})
    # Telefonda (tarayıcıda) hep yazsın: iPhone Düşük Güç Modu'nda oyun daha az akıcı
    if web:
        draw_slow_hint(screen)


class SoundMenu:
    # Ayarlar ekranı: müzik ve efekt seviyesi çubukları + "Ses: Açık/Kapalı", "Dil: Türkçe", "Tema: Nostalji" ve
    # "Geri" düğmeleri. Klavyede yukarı/aşağı ile seçilir, çubuk seçiliyken sol/sağ ok ile ayarlanır
    SLIDER_NAMES = ("music", "effects")
    TITLES = {"music": mark("Müzik"), "effects": mark("Efektler")}
    LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
    RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)

    def __init__(self):
        self.sliders = {"music": Slider(215), "effects": Slider(320)}
        self.buttons = Buttons(["sound", "language", "theme", "back"], top=420)
        self.focus = 0  # 0 = müzik, 1 = efektler, 2+ = düğmeler

    def open(self):
        self.focus = 0
        self.buttons.focus = -1  # hiçbir düğme seçili görünmesin

    def set_focus(self, index):
        count = len(self.SLIDER_NAMES)
        self.focus = index % (count + len(self.buttons.actions))
        self.buttons.focus = self.focus - count  # çubuk seçiliyse eksi (düğme seçili görünmez)

    def handle_event(self, event):
        # Değişen çubuğun adı ("music"/"effects") veya basılan düğmenin adı ("sound"/"language"/"theme"/"back"), yoksa None
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
        draw_title(screen, "Ayarlar", 95)
        for i, name in enumerate(self.SLIDER_NAMES):
            slider = self.sliders[name]
            focused = self.focus == i
            y = slider.rect.top - 32
            color = TITLE_COLOR if focused else (255, 255, 255)
            draw_text(screen, font(MENU_FONT_SIZE), self.TITLES[name], color, midleft=(slider.rect.left, y))
            percent = t("%{}").format(slider.value * 100 // VOLUME_STEPS)  # İngilizcede "100%"
            draw_text(screen, font(MENU_FONT_SIZE), percent, color, midright=(slider.rect.right, y))
            slider.draw(screen, focused, muted)
        self.buttons.draw(screen, {**LABELS, **labels})


SOUND_MENU = SoundMenu()


def howto_icons():
    # Nasıl oynanır sayfasındaki küçük resimler: oyundaki resimlerin aynısı, en fazla HOWTO_ICON piksel
    def make():
        def fit(image, box=HOWTO_ICON):
            scale = min(1, box / image.get_width(), box / image.get_height())
            return art.resize(image, (image.get_width() * scale, image.get_height() * scale))

        return {
            "coin": fit(art.coin_frames()[0]),
            "gem": fit(art.gem_frames()[0]),
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
            "golem": fit(boss.frames("golem")["stand"][0]),
            "crumble": fit(art.crumble_frames()[1]),
            "lava": fit(art.lava_frames()[0].subsurface((0, 0, 36, 32))),
            "flag": fit(art.flag_frames()[0]),
        }

    return theme.cached(_images, "howto", make)


HOWTO_ROWS = (  # {points} = altının puanı
    ("flag", mark("Bayrak: bölümün sonu, ona ulaş!")),
    ("coin", mark("Altın: +{points} puan, yeni renk al")),
    ("gem", mark("Elmas: nadir! Yeni karakter al")),
    ("heart", mark("Kalp: +1 can")),
    ("magnet", mark("Mıknatıs: altınları çeker")),
    ("shield", mark("Kalkan: düşman ve lavdan korur")),
    ("spring", mark("Yay: çok yükseğe fırlatır")),
    ("crumble", mark("Çatlak taş: basınca kırılır")),
    ("enemy", mark("Düşman: üstüne zıpla, yanına değme")),
    ("slime", mark("Sümük: zıplar, inince üstüne bas")),
    ("spiky", mark("Kirpi: dikenli, üstüne BASMA!")),
    ("cannon", mark("Topçu: ateş atar, üstüne zıpla")),
    ("bat", mark("Yarasa: onun da üstüne zıpla")),
    ("bee", mark("Arı: aşağı yukarı uçar")),
    ("golem", mark("Golem: alevi sönünce kafasına bas")),
    ("lava", mark("Lav: yükseliyor, acele et!")),
)
HOWTO_WARN_ROWS = ("spiky", "lava")  # yazısı uyarı renginde olanlar
HOWTO_ICON = 30  # resimlerin en fazla boyu (piksel)
HOWTO_TOP = 196  # ilk satırın ortası (y)
HOWTO_GAP = 27  # satırlar arası (piksel) — 16 satır Geri düğmesinin üstünde bitsin


def draw_howto(screen):
    draw_overlay(screen)
    draw_text(screen, font(MENU_FONT_SIZE + 10), "Nasıl Oynanır", TITLE_COLOR, center=(CENTER_X, 45))
    small = font(MENU_SMALL_FONT_SIZE)
    draw_text(screen, small, "Amaç: en yükseğe tırman, rekorunu geç!", RECORD_COLOR, center=(CENTER_X, 90))
    draw_text(screen, small, "Ok tuşları / A-D: yürü    Boşluk / W: zıpla", HINT_COLOR, center=(CENTER_X, 122))
    draw_text(screen, small, "Telefonda: alttaki düğmeler", HINT_COLOR, center=(CENTER_X, 146))
    draw_text(
        screen, small, t("ESC / P: durdur    {}: ses").format(MUTE_KEY.upper()), HINT_COLOR, center=(CENTER_X, 170)
    )
    icons = howto_icons()
    for i, (name, text) in enumerate(HOWTO_ROWS):
        y = HOWTO_TOP + i * HOWTO_GAP
        icon = icons[name]
        screen.blit(icon, icon.get_rect(center=(58, y)))
        color = LAVA_TOP_COLOR if name in HOWTO_WARN_ROWS else (255, 255, 255)
        draw_text(screen, small, t(text).format(points=COIN_POINTS), color, midleft=(92, y))
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
        (mark("Oynanan oyun"), str(stats["games"])),
        (mark("Toplam tırmanış"), f"{stats['climbed']} m"),
        (mark("Toplam altın"), str(stats["coins"])),
        (mark("Yenilen düşman"), str(stats["enemies"])),
        (mark("Bölüm yıldızı"), f"{sum(stars)} / {3 * len(stars)}"),
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


def draw_game_over(screen, score, mode_name, best_height, high_score, new_record, slow=False):
    # mode_name = oynanan zorluk modu (rekorlar o modun rekorları). Düğmeleri main.py çizer (draw_end_buttons)
    draw_overlay(screen)
    draw_title(screen, "Kaybettin!", 200, GAME_OVER_COLOR)
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), t("Zorluk: {}").format(t(mode_name)), HINT_COLOR, center=(CENTER_X, 243))
    # Büyük yazı: ne kadar tırmandın (asıl hedef). Puan ve ayrıntılar altında küçük
    draw_text(screen, font(TITLE_FONT_SIZE), f"{score.height} m", center=(CENTER_X, 290))
    small = font(MENU_SMALL_FONT_SIZE)
    details = "   ".join((t("Puan: {}").format(score.total), score.loot_text(), t("Düşman: {}").format(score.enemies)))
    draw_text(screen, small, details, HINT_COLOR, center=(CENTER_X, 335))
    if new_record:
        draw_text(screen, font(MENU_FONT_SIZE), "YENİ REKOR!", RECORD_COLOR, center=(CENTER_X, 390))
    else:
        draw_text(screen, font(MENU_FONT_SIZE), t("Rekor: {} m").format(best_height), RECORD_COLOR, center=(CENTER_X, 390))
    draw_text(screen, small, t("En yüksek puan: {}").format(high_score), HINT_COLOR, center=(CENTER_X, 420))
    if slow:
        draw_slow_hint(screen)


def draw_revive(screen, score, gems, time_left, ad):
    # Canlar bitti: oyun başına bir kez elmasla (ya da reklam izleyerek) kaldığın yerden devam (main.py "revive").
    # gems = cüzdandaki elmas, time_left = geri sayım çubuğu (1 → 0; None = düğmeler henüz çıkmadı),
    # ad = reklam seçeneği (None = yok, "offer", "failed" = reklam gelmedi)
    buttons = revive_buttons(ad)
    draw_overlay(screen)
    draw_title(screen, "Devam Et?", 185)
    small = font(MENU_SMALL_FONT_SIZE)
    draw_text(screen, small, "Kaldığın yerden 1 canla", HINT_COLOR, center=(CENTER_X, 230))
    height = f"{score.height} / {score.goal} m" if score.goal else f"{score.height} m"
    draw_text(screen, font(TITLE_FONT_SIZE), height, center=(CENTER_X, 290))
    # Neyi kaçıracağı: bayrağa / rekora ne kadar kaldı (ilk oyunda rekor yok)
    note = None
    if score.goal:
        note = t("Bayrağa {} m kaldı!").format(max(0, score.goal - score.height))
    elif score.record > 0:
        note = "YENİ REKOR!" if score.new_record else t("Rekora {} m kaldı!").format(score.record - score.height)
    if note:
        draw_text(screen, font(MENU_FONT_SIZE), note, RECORD_COLOR, center=(CENTER_X, 340))
    icon = gem_icon()
    if time_left is not None:
        bar = pygame.Rect(0, 0, BUTTON_WIDTH, 10)
        bar.center = (CENTER_X, 400)
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, bar, border_radius=5)
        fill = bar.copy()
        fill.width = round(bar.width * time_left)
        if fill.width > 0:
            pygame.draw.rect(screen, GEM_COLOR, fill, border_radius=5)
        disabled = [name for name, off in (("revive", gems < REVIVE_GEMS), ("revive_ad", ad == "failed")) if off]
        labels = {**LABELS, "revive": t("Devam Et: {}").format(REVIVE_GEMS)}
        if ad == "failed":
            labels["revive_ad"] = "Reklam yok"
        buttons.draw(screen, labels, disabled)
        draw_button_icons(screen, buttons, "revive", right=icon)
        if ad == "offer":
            draw_button_icons(screen, buttons, "revive_ad", left=ad_icon())
    # Cüzdandaki elmas (düğmelerin altında)
    text = t("Cüzdan: {}").format(gems)
    y = buttons.rects[-1].bottom + 36
    left = CENTER_X - (icon.get_width() + 6 + small.size(text)[0]) // 2
    screen.blit(icon, icon.get_rect(midleft=(left, y)))
    draw_text(screen, small, text, art.tint(GEM_COLOR, 0.3), midleft=(left + icon.get_width() + 6, y + 1))


def draw_end_buttons(screen, buttons, stage_failed, double, earned):
    # Oyun sonu ekranının düğmeleri (main.py hangi düğmeler olduğunu end_buttons ile seçer). stage_failed = bölümde
    # kaybedildi (Tekrar Dene / Bölümler), double = 2 kat elmas (None / "offer" / "done" / "failed"),
    # earned = bu oyunda kazanılan elmas
    labels = {**LABELS, "double": t(DOUBLE_LABELS.get(double, ""), earned).format(earned)}
    if stage_failed:
        labels.update(again=mark("Tekrar Dene"), menu=mark("Bölümler"))
    buttons.draw(screen, labels, ("double",) if double in ("done", "failed") else ())
    if double == "offer":
        draw_button_icons(screen, buttons, "double", left=ad_icon(), right=gem_icon())


# Oyun sonu ekranlarında görevi yeni tamamlanan efsanevi skinlerin yazısının yüksekliği (y)
NEW_SKIN_Y = {"game_over": 130, "stage_clear": 96}


def draw_new_skins(screen, new_skins, y):
    # Görevi bu oyunda tamamlanan efsanevi skin(ler): küçük resmi + "Yeni karakter: Ejderha!"
    if not new_skins:
        return
    names = ", ".join(t(skin["name"]) for skin in new_skins)
    text = (t("Yeni karakter: {}!") if len(new_skins) == 1 else t("Yeni karakterler: {}!")).format(names)
    small = font(MENU_SMALL_FONT_SIZE + 4)
    if small.size(text)[0] > SCREEN_WIDTH - 70:
        text = t("{} yeni karakter açıldı!").format(len(new_skins))
    image = skins.frames(new_skins[0]["id"])["idle"][1]
    icon = theme.cached(
        _images, ("skin_icon", new_skins[0]["id"]),
        lambda: art.resize(image, (image.get_width() // 2, image.get_height() // 2)),
    )
    width = icon.get_width() + 8 + small.size(text)[0]
    left = CENTER_X - width // 2
    screen.blit(icon, icon.get_rect(midleft=(left, y)))
    draw_text(screen, small, text, LEGENDARY_COLOR, midleft=(left + icon.get_width() + 8, y + 1))


# Oyun sonu ekranlarında kazanılan elmas yazısının yüksekliği (y)
GEMS_EARNED_Y = {"game_over": 452, "stage_failed": 418, "stage_clear": 405}


def gems_text(found, bonus, reason):
    # Kazanılan elmasın yazısı, nereden geldiğiyle: "+2 elmas topladın", "+3 elmas: rekor ödülü",
    # "+5 elmas: 2 toplandı + 3 rekor ödülü" (reason = "rekor" / "yıldız")
    if not bonus:
        return t("+{} elmas topladın", found).format(found)
    if reason == "rekor":
        only, both = mark("+{} elmas: rekor ödülü"), mark("+{total} elmas: {found} toplandı + {bonus} rekor ödülü")
    else:
        only, both = mark("+{} elmas: yıldız ödülü"), mark("+{total} elmas: {found} toplandı + {bonus} yıldız ödülü")
    if not found:
        return t(only, bonus).format(bonus)
    return t(both).format(total=found + bonus, found=found, bonus=bonus)


def gem_icon():
    return theme.cached(_images, "gem", lambda: art.gem_frames()[0])


def draw_gems_earned(screen, found, bonus, reason, y):
    # Bu oyunda kazanılan elmas: elmas resmi + nereden geldiği (haritada toplanan, rekor / yeni yıldız ödülü)
    if found + bonus <= 0:
        return
    icon = gem_icon()
    text = gems_text(found, bonus, reason)
    small = font(MENU_SMALL_FONT_SIZE + 4)
    if icon.get_width() + 8 + small.size(text)[0] > SCREEN_WIDTH - 24:
        small = font(MENU_SMALL_FONT_SIZE)  # uzun yazı sığsın
    width = icon.get_width() + 8 + small.size(text)[0]
    left = CENTER_X - width // 2
    screen.blit(icon, icon.get_rect(midleft=(left, y)))
    draw_text(screen, small, text, art.tint(GEM_COLOR, 0.3), midleft=(left + icon.get_width() + 8, y + 1))


def stars_needed(total):
    # 2. yıldız için en az kaç altın (bölümdeki altınların STAR_COIN_SHARE'i, yukarı yuvarlanır)
    return math.ceil(round(total * STAR_COIN_SHARE, 6))


def stage_title(mode, index):
    return t("{}. Bölüm: {}").format(index + 1, t(STAGE_SETS[mode][index]["name"]))


def stage_subtitle(mode, index):
    # "Orta - 3. Bölüm: İlk Düşman"
    return f"{t(DIFFICULTY_NAMES[mode])} - {stage_title(mode, index)}"


def draw_play_select(screen, labels, mode_name, stars, best_height):
    # Oyna'ya basınca: bölümler mi sonsuz oyun mu. stars = bütün zorlukların yıldızları,
    # best_height = seçili zorlukta sonsuz oyunun tırmanış rekoru (Sonsuz Oyun düğmesinin altında)
    draw_overlay(screen)
    draw_logo(screen)
    draw_text(
        screen, font(MENU_FONT_SIZE + 10), t("Yıldızlar: {} / {}").format(sum(stars), 3 * len(stars)), RECORD_COLOR,
        center=(CENTER_X, 260),
    )
    PLAY_BUTTONS.draw(screen, {**LABELS, **labels})
    draw_text(
        screen, font(MENU_SMALL_FONT_SIZE + 2), t("Rekor: {} m").format(best_height), RECORD_COLOR,
        center=(CENTER_X, PLAY_RECORD_Y),
    )
    small = font(MENU_SMALL_FONT_SIZE)
    text = t("Bölümler: her zorlukta {} bölüm, yıldız topla").format(STAGE_COUNT)
    draw_text(screen, small, text, HINT_COLOR, center=(CENTER_X, 560))
    text = t("Sonsuz Oyun: rekor için tırman ({})").format(t(mode_name))
    draw_text(screen, small, text, HINT_COLOR, center=(CENTER_X, 586))


def draw_stages(screen, mode, stars, unlocked):
    # Bölüm seçme ekranı: üstte zorluk sekmeleri, kutular, seçili bölümün adı ve hedefi
    draw_overlay(screen)
    draw_title(screen, "Bölümler", 40)
    draw_text(
        screen, font(MENU_SMALL_FONT_SIZE + 2), t("Yıldızlar: {} / {}").format(sum(stars), 3 * len(stars)),
        RECORD_COLOR, center=(CENTER_X, 130),
    )
    STAGE_GRID.draw(screen, stars, unlocked, mode)
    focus = STAGE_GRID.focus
    stages = STAGE_SETS[mode]
    if 0 <= focus < len(stages):
        if unlocked(focus):
            draw_text(screen, font(MENU_FONT_SIZE), stage_title(mode, focus), center=(CENTER_X, 584))
            info = t("Hedef: {} m").format(stages[focus]["goal"])
            if stages[focus]["lava"]:
                info += "   " + t("Lav var!")
            draw_text(screen, font(MENU_SMALL_FONT_SIZE), info, HINT_COLOR, center=(CENTER_X, 610))
        else:  # kilitli: adı görünür (merak uyandırsın) ama hedefi gizli; adın solunda asma kilit
            title = stage_title(mode, focus)
            lock = theme.cached(_images, "lock", art.lock_image)
            width = lock.get_width() + 8 + font(MENU_FONT_SIZE).size(title)[0]
            left = CENTER_X - width // 2
            screen.blit(lock, lock.get_rect(midleft=(left, 584)))
            draw_text(
                screen, font(MENU_FONT_SIZE), title, HINT_COLOR, midleft=(left + lock.get_width() + 8, 584)
            )
            draw_text(
                screen, font(MENU_SMALL_FONT_SIZE), "Önceki bölümü bitirince açılır", HINT_COLOR,
                center=(CENTER_X, 610),
            )
    elif focus < 0:
        draw_text(
            screen, font(MENU_SMALL_FONT_SIZE), "Her zorluğun bölümleri ayrı", HINT_COLOR, center=(CENTER_X, 597)
        )


def draw_stage_intro(screen, mode, index, goal):
    # Bölüm başlarken birkaç saniye: bölümün adı, hedefi ve tanıttığı şey
    stage = STAGE_SETS[mode][index]
    title = t("{}. Bölüm ({})").format(index + 1, t(DIFFICULTY_NAMES[mode]))
    draw_text(screen, font(MENU_FONT_SIZE), title, HINT_COLOR, center=(CENTER_X, 170))
    draw_text(screen, font(MENU_FONT_SIZE + 14), stage["name"], TITLE_COLOR, center=(CENTER_X, 210))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), stage["intro"], center=(CENTER_X, 250))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), t("Hedef: {} m").format(goal), HINT_COLOR, center=(CENTER_X, 278))


def star_images():
    return theme.cached(_images, "stars", lambda: {
        "big": art.star_image(True, 64), "big_empty": art.star_image(False, 64),
        "small": art.star_image(True, 22), "small_empty": art.star_image(False, 22),
    })


def draw_stage_clear(screen, mode, index, result, shown):
    # Bölüm bitti: yıldızlar (shown = şimdiye kadar beliren), hangi şart tuttu. Düğmeleri main.py çizer.
    # result = {"stars", "coins", "coins_total", "no_hurt", "unlocked"} (main.py)
    draw_overlay(screen)
    draw_title(screen, "Tebrikler!", 140)
    draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), stage_subtitle(mode, index), HINT_COLOR, center=(CENTER_X, 185))
    images = star_images()
    for k in range(3):
        image = images["big" if k < shown else "big_empty"]
        y = 245 - (12 if k == 1 else 0)  # ortadaki biraz yukarıda
        screen.blit(image, image.get_rect(center=(CENTER_X + (k - 1) * 80, y)))
    need = stars_needed(result["coins_total"])
    conditions = (
        (True, mark("Bayrağa ulaştın")),
        (result["coins"] >= need, t("Altın: {} / {}  (en az {})").format(result["coins"], result["coins_total"], need)),
        (result["no_hurt"], mark("Hiç can kaybetmeden")),
    )
    small = font(MENU_SMALL_FONT_SIZE + 2)
    for i, (done, text) in enumerate(conditions):
        y = 316 + i * 30
        icon = images["small" if done else "small_empty"]
        screen.blit(icon, icon.get_rect(center=(80, y)))
        draw_text(screen, small, text, (255, 255, 255) if done else HINT_COLOR, midleft=(102, y))
    if result["unlocked"]:
        draw_text(screen, font(MENU_FONT_SIZE), "Yeni bölüm açıldı!", RECORD_COLOR, center=(CENTER_X, 438))
    elif index == STAGE_COUNT - 1:
        text = t("{} bölümleri bitti!").format(t(DIFFICULTY_NAMES[mode]))
        draw_text(screen, font(MENU_FONT_SIZE), text, RECORD_COLOR, center=(CENTER_X, 438))


def draw_stage_failed(screen, mode, index, score, slow=False):
    # Bölümde canlar bitti: ne kadar kalmıştı (düğmeler Tekrar Dene / Bölümler: draw_end_buttons)
    draw_overlay(screen)
    draw_title(screen, "Kaybettin!", 200, GAME_OVER_COLOR)
    draw_text(screen, font(MENU_SMALL_FONT_SIZE + 2), stage_subtitle(mode, index), HINT_COLOR, center=(CENTER_X, 243))
    draw_text(screen, font(TITLE_FONT_SIZE), f"{score.height} / {score.goal} m", center=(CENTER_X, 295))
    left = max(0, score.goal - score.height)
    draw_text(screen, font(MENU_FONT_SIZE), t("Bayrağa {} m kalmıştı").format(left), RECORD_COLOR, center=(CENTER_X, 350))
    draw_text(screen, font(MENU_SMALL_FONT_SIZE), score.loot_text(), HINT_COLOR, center=(CENTER_X, 385))
    if slow:
        draw_slow_hint(screen)
