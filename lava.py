# Yükselen lav: aşağıdan yukarı çıkar, oyuncuyu acele ettirir. Değen bir can kaybeder.
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

# Resimler bir kere hazırlanır (ekran açıldıktan sonra, ilk çizimde)
IMAGES = {}


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
        if not IMAGES:
            IMAGES["waves"] = art.lava_frames()
            IMAGES["glow"] = art.lava_glow()
        surface_y = round(self.y - camera.top)  # yüzeyin ekrandaki yeri
        if surface_y >= SCREEN_HEIGHT:
            # Lav görünmüyor ama yaklaşıyorsa ekranın dibi kızarır
            if surface_y - SCREEN_HEIGHT < LAVA_WARN_DISTANCE:
                glow = IMAGES["glow"]
                screen.blit(glow, (0, SCREEN_HEIGHT - glow.get_height()))
            return
        # Dalgalı üst kenar (tepeler yüzeyin biraz üstüne taşar), altı düz lav rengi
        waves = IMAGES["waves"]
        frame = waves[(self.time // LAVA_ANIM_SPEED) % len(waves)]
        wave_top = surface_y - 2 * PIXEL_SCALE
        screen.blit(frame, (0, wave_top))
        body_top = wave_top + frame.get_height()
        if body_top < SCREEN_HEIGHT:
            screen.fill(LAVA_COLOR, (0, body_top, SCREEN_WIDTH, SCREEN_HEIGHT - body_top))
            # Derinlerde biraz daha koyu
            deep_top = max(body_top, surface_y + 60)
            if deep_top < SCREEN_HEIGHT:
                screen.fill(art.shade(LAVA_COLOR, 0.8), (0, deep_top, SCREEN_WIDTH, SCREEN_HEIGHT - deep_top))
