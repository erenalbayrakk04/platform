# Yükselen lav: aşağıdan yukarı çıkar, oyuncuyu acele ettirir. Değen bir can kaybeder.
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PIXEL_SCALE,
    LAVA_START_GAP,
    LAVA_MAX_GAP,
    LAVA_PUSHBACK,
    LAVA_HIT_DEPTH,
    LAVA_WARN_DISTANCE,
    LAVA_ANIM_SPEED,
    LAVA_COLOR,
)
from level import hardness, blend
import art
import theme

# Resimler bir kere hazırlanır (ekran açıldıktan sonra, ilk çizimde; her tema için ayrı)
IMAGES = {}
LAVA_BODY_HEIGHT = 300  # Modern temada dalgaların altındaki renk geçişli kısım (altı düz koyu lav)


def images():
    def make():
        made = {"waves": art.lava_frames(), "glow": art.lava_glow()}
        if theme.modern():
            import modern

            made["body"] = modern.lava_body(LAVA_BODY_HEIGHT)
            made["light"] = modern.lava_light()
        return made

    return theme.cached(IMAGES, "lava", make)


class Lava:
    def __init__(self, mode, ground_y=0):
        # mode = zorluk modunun sayıları (settings.DIFFICULTIES): lavın hızı ve bekleme süresi
        self.mode = mode
        self.active = mode.get("lava", True)  # bazı bölümlerde lav yok (stages.py)
        # y = lavın yüzeyi (bölümdeki konum; yukarı çıktıkça eksiye iner). Başta zeminin altında
        self.y = float(ground_y + LAVA_START_GAP)
        self.wait = mode["lava_delay"]  # yükselmeye başlamasına kaç kare kaldı
        self.time = 0  # dalga animasyonu için

    def update(self, camera_bottom):
        # Her karede bir kere: yüksekte daha hızlı yükselir; ekranın çok altında da kalmaz
        self.time += 1
        if not self.active:
            return
        if self.wait > 0:
            self.wait -= 1
            return
        mode = self.mode
        self.y -= blend(mode["lava_speed"], mode["lava_speed_max"], hardness(-camera_bottom, mode))
        self.y = min(self.y, camera_bottom + LAVA_MAX_GAP)

    def touches(self, rect):
        # Ayağı lavın içine yeterince girdi mi
        return self.active and rect.bottom > self.y + LAVA_HIT_DEPTH

    def push_back(self, feet_y):
        # Can kaybedince karakterin döndüğü yerin epey altına çekil
        self.y = max(self.y, feet_y + LAVA_PUSHBACK)

    def draw(self, screen, camera):
        if not self.active:
            return
        pictures = images()
        surface_y = round(self.y - camera.top)  # yüzeyin ekrandaki yeri
        if surface_y >= SCREEN_HEIGHT:
            # Lav görünmüyor ama yaklaşıyorsa ekranın dibi kızarır
            if surface_y - SCREEN_HEIGHT < LAVA_WARN_DISTANCE:
                glow = pictures["glow"]
                screen.blit(glow, (0, SCREEN_HEIGHT - glow.get_height()))
            return
        # Dalgalı üst kenar (tepeler yüzeyin biraz üstüne taşar), altı düz lav rengi
        waves = pictures["waves"]
        frame = waves[(self.time // LAVA_ANIM_SPEED) % len(waves)]
        wave_top = surface_y - 2 * PIXEL_SCALE
        if "light" in pictures:  # Modern: lavın üstündeki her şeye kızıl ışık vurur
            light = pictures["light"]
            screen.blit(light, (0, wave_top - light.get_height() + 12), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(frame, (0, wave_top))
        body_top = wave_top + frame.get_height()
        if "body" in pictures and body_top < SCREEN_HEIGHT:  # Modern: derine indikçe yavaşça koyulaşır
            screen.blit(pictures["body"], (0, body_top))
            body_top += LAVA_BODY_HEIGHT
            if body_top < SCREEN_HEIGHT:
                screen.fill(art.shade(LAVA_COLOR, 0.72), (0, body_top, SCREEN_WIDTH, SCREEN_HEIGHT - body_top))
            return
        if body_top < SCREEN_HEIGHT:
            screen.fill(LAVA_COLOR, (0, body_top, SCREEN_WIDTH, SCREEN_HEIGHT - body_top))
            # Derinlerde biraz daha koyu
            deep_top = max(body_top, surface_y + 60)
            if deep_top < SCREEN_HEIGHT:
                screen.fill(art.shade(LAVA_COLOR, 0.8), (0, deep_top, SCREEN_WIDTH, SCREEN_HEIGHT - deep_top))
