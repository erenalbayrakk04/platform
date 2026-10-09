# Yükseklik (asıl hedef, büyük yazı) ve puan: tırmanılan yükseklik + altınlar + yenilen düşmanlar.
# Ekranın sol üstünde, kameradan bağımsız çizilir. Canlar (kalpler) sağ üstte.
# Rekorların saklanması storage.py'de.
import pygame

from art import heart_images, magnet_image, shield_image
from settings import (
    TILE_SIZE,
    COIN_POINTS,
    ENEMY_POINTS,
    HEIGHT_POINTS,
    SCORE_COLOR,
    SCORE_SHADOW_COLOR,
    SCORE_FONT_SIZE,
    SCORE_SMALL_FONT_SIZE,
    SCREEN_WIDTH,
    PAUSE_BUTTON_SIZE,
    RECORD_TOAST_TIME,
    RECORD_COLOR,
    POWERUP_WARN_TIME,
    PROGRESS_EMPTY_COLOR,
)


class Score:
    def __init__(self, start_y, record=0, goal=None):
        # Karakterin ayaklarının başladığı yükseklik — yükseklik buna göre ölçülür
        self.start_y = start_y
        self.record = record  # oyun başlarken en yüksek tırmanış rekoru (blok)
        self.goal = goal  # bölümde bayrağın yüksekliği (blok); sonsuz oyunda None
        self.height = 0  # üstüne basılan en yüksek yer (blok sayısı)
        self.coins = 0  # toplanan altın sayısı
        self.enemies = 0  # üstüne basılıp yenilen düşman sayısı
        self.bonus = 0  # diğer puanlar (ör. canın doluyken alınan kalp)
        self.toast = 0  # "YENİ REKOR!" yazısının kalan süresi
        # None = pygame'in kendi yazı tipi
        self.font = pygame.font.Font(None, SCORE_FONT_SIZE)
        self.small_font = pygame.font.Font(None, SCORE_SMALL_FONT_SIZE)

    @property
    def new_record(self):
        # Bu oyunda yükseklik rekoru kırıldı mı
        return self.height > self.record

    @property
    def total(self):
        return (
            self.height * HEIGHT_POINTS
            + self.coins * COIN_POINTS
            + self.enemies * ENEMY_POINTS
            + self.bonus
        )

    def update(self, player):
        # Sadece üstüne bastığı yer sayılır (havada zıplamak puan vermesin);
        # aşağı düşünce puan azalmaz, en yükseği hatırlanır.
        # Rekor bu karede kırıldıysa True döner (ses için); ilk oyunda (rekor 0) kutlama yok
        if self.toast:
            self.toast -= 1
        if not player.on_ground:
            return False
        was_record = self.new_record
        climbed = (self.start_y - player.rect.bottom) // TILE_SIZE
        self.height = max(self.height, climbed)
        if self.new_record and not was_record and self.record > 0:
            self.toast = RECORD_TOAST_TIME
            return True
        return False

    def add_coin(self):
        self.coins += 1

    def add_enemy(self):
        self.enemies += 1

    def add_bonus(self, points):
        self.bonus += points

    def draw(self, screen):
        # Büyük yazı yükseklik (asıl hedef); puan ve altın altında küçük.
        # Rekor kırıldıysa yükseklik rekor renginde. Bölümde: "37 / 62 m", altın ve bayrağa ilerleme çubuğu
        if self.goal:
            draw_text(screen, self.font, f"{self.height} / {self.goal} m", topleft=(12, 10))
            draw_text(screen, self.small_font, f"Altın: {self.coins}", topleft=(12, 44))
            bar = pygame.Rect(12, 66, 140, 6)
            screen.fill(SCORE_SHADOW_COLOR, bar.move(2, 2))
            screen.fill(PROGRESS_EMPTY_COLOR, bar)
            bar.width = round(bar.width * min(1, self.height / self.goal))
            screen.fill(RECORD_COLOR, bar)
            return
        color = RECORD_COLOR if self.new_record and self.record > 0 else SCORE_COLOR
        draw_text(screen, self.font, f"{self.height} m", color, topleft=(12, 10))
        draw_text(
            screen, self.small_font, f"Puan: {self.total}   Altın: {self.coins}", topleft=(12, 44)
        )
        if self.toast and (self.toast // 10) % 2 == 0:  # yanıp söner
            draw_text(screen, self.font, "YENİ REKOR!", RECORD_COLOR, center=(SCREEN_WIDTH // 2, 120))

    def draw_record_line(self, screen, camera):
        # Haritada rekor yüksekliğinde kesikli çizgi + "Rekor" yazısı (rekor kırılınca kaybolur)
        if self.record <= 0 or self.new_record:
            return
        y = round(self.start_y - self.record * TILE_SIZE - camera.top)
        if not -20 < y < screen.get_height():
            return
        for x in range(0, SCREEN_WIDTH, 16):
            screen.fill(RECORD_COLOR, (x, y - 1, 10, 3))
        draw_text(
            screen, self.small_font, f"Rekor {self.record} m", RECORD_COLOR, bottomright=(SCREEN_WIDTH - 8, y - 4)
        )


# Yazılan yazıların resimleri: aynı yazı her karede yeniden yazılmasın (tarayıcıda yavaş)
TEXT_CACHE = {}


def draw_text(screen, font, text, color=SCORE_COLOR, **position):
    # Gölgeli yazı: önce 2 piksel kaydırılmış gölge, sonra asıl yazı — her zeminde okunsun.
    # Konum rect gibi verilir: topleft=(x, y) veya center=(x, y) vb.
    key = (font, text, color)
    if key not in TEXT_CACHE:
        if len(TEXT_CACHE) > 100:  # eski puan yazıları birikmesin
            TEXT_CACHE.clear()
        TEXT_CACHE[key] = (font.render(text, True, color), font.render(text, True, SCORE_SHADOW_COLOR))
    image, shadow = TEXT_CACHE[key]
    rect = image.get_rect(**position)
    screen.blit(shadow, rect.move(2, 2))
    screen.blit(image, rect)


HEART_IMAGES = {}


def draw_lives(screen, lives, max_lives):
    # Sağ üstte (durdur düğmesinin solunda) max_lives kadar kalp: kalan canlar dolu, kaybedilenler gri
    if not HEART_IMAGES:  # ilk çizimde bir kere hazırla
        HEART_IMAGES.update(heart_images())
    width = HEART_IMAGES["full"].get_width() + 6
    right = SCREEN_WIDTH - 12 - PAUSE_BUTTON_SIZE - 6
    for i in range(max_lives):
        image = HEART_IMAGES["full" if i < lives else "empty"]
        screen.blit(image, (right - (max_lives - i) * width, 14))


POWER_ICONS = {}


def draw_powers(screen, player):
    # Kalplerin altında süren güçlendirmeler: simge + altında kalan süre çubuğu (sağdan sola dizilir).
    # Bitmesine az kalınca simge yanıp söner
    if not POWER_ICONS:
        POWER_ICONS.update(magnet=magnet_image(), shield=shield_image())
    right = SCREEN_WIDTH - 12
    for kind, left in player.powers.items():
        if not left:
            continue
        icon = POWER_ICONS[kind]
        rect = icon.get_rect(bottomright=(right, 80))  # simgeler alta hizalı, çubuklar aynı hizada
        if left > POWERUP_WARN_TIME or (left // 8) % 2 == 0:
            screen.blit(icon, rect)
        bar = pygame.Rect(rect.left, rect.bottom + 4, rect.width, 4)
        screen.fill(SCORE_SHADOW_COLOR, bar)  # boş çubuk
        bar.width = round(bar.width * player.power_fraction(kind))
        screen.fill(SCORE_COLOR, bar)
        right = rect.left - 10
