# Ödüllü reklamlar (para kazanma hazırlığı). Reklamı oyuncu KENDİSİ seçer: canlar bitince "Devam Et", oyun sonunda
# "2 kat elmas", Karakterler ekranında "bedava elmas". Ne zaman teklif edileceğine ve ödüle main.py karar verir.
# Şimdilik gerçek reklam YOK: oyun bir platforma (CrazyGames / Google Play) konunca buraya onun bağlayıcısı yazılacak
# (ör. web.tmpl'de JS köprüsü reklamın durumunu window'a yazar, update() her karede okur). O zamana kadar
# available() False → reklam düğmeleri hiç görünmez.
# Deneme: settings ADS_TEST = True ya da web'de adresin sonunda #reklam → AD_TEST_TIME kare süren sahte reklam, sonra ödül.
import math
import time

import pygame

from settings import (
    SCREEN_WIDTH,
    FPS,
    AD_TEST_TIME,
    AD_RETRY_TIME,
    FREE_GEM_ADS,
    TITLE_FONT_SIZE,
    MENU_FONT_SIZE,
    MENU_SMALL_FONT_SIZE,
    AD_COLOR,
    HINT_COLOR,
)
from storage import load_dict, save_dict
from score import draw_text

AD_BACKGROUND = (12, 10, 24)  # deneme reklamının ekranı


def today():
    return time.strftime("%Y-%m-%d")


class Ads:
    def __init__(self, test=False):
        self.backend = "test" if test else None  # None = reklam yok (düğmeler görünmez)
        self.playing = False  # reklam şu an ekranda mı (main.py oyunun sesini kısar)
        self.timer = 0  # deneme reklamının bitmesine kalan kare
        self.retry_at = 0  # reklam gelmeyince bu zamana kadar (get_ticks, ms) yeniden teklif edilmez
        saved = load_dict("ads", {"day": "", "free_gems": 0})
        self.day = saved["day"]  # bedava elmas sayısının günü ("2026-10-09")
        self.free_used = saved["free_gems"]  # o gün reklamla kaç kez bedava elmas alındı
        self.fonts = None

    def available(self):
        # Şu an reklam teklif edilebilir mi (reklam sistemi var ve az önce reklam gelmemezlik etmedi)
        return self.backend is not None and pygame.time.get_ticks() >= self.retry_at

    def show(self):
        # Reklamı başlat; nasıl bittiğini update() söyler
        self.playing = True
        self.timer = AD_TEST_TIME

    def update(self, steps):
        # Reklam bitti mi: "done" (sonuna kadar izlendi → ödül), "failed" (reklam gelmedi / yarıda kapandı → ödül
        # yok, bir süre teklif edilmez); sürüyorsa None
        if not self.playing:
            return None
        self.timer = max(0, self.timer - steps)
        if self.timer:
            return None
        return self.end("done")

    def end(self, result):
        self.playing = False
        if result == "failed":
            self.retry_at = pygame.time.get_ticks() + AD_RETRY_TIME
        return result

    def free_gems_left(self):
        # Bugün reklamla kaç kez daha bedava elmas alınabilir (FREE_GEM_ADS)
        used = self.free_used if self.day == today() else 0
        return max(0, FREE_GEM_ADS - used)

    def count_free_gems(self):
        # Reklamla bedava elmas alındı: bugünün sayısı artar ve kaydedilir
        if self.day != today():
            self.day, self.free_used = today(), 0
        self.free_used += 1
        save_dict("ads", {"day": self.day, "free_gems": self.free_used})

    def draw(self, screen):
        # Deneme reklamı: koyu ekran, "REKLAM" ve geri sayım (gerçek reklamı platform kendisi gösterir)
        if self.fonts is None:
            self.fonts = [pygame.font.Font(None, size) for size in (TITLE_FONT_SIZE, MENU_FONT_SIZE, MENU_SMALL_FONT_SIZE)]
        big, mid, small = self.fonts
        center_x = SCREEN_WIDTH // 2
        screen.fill(AD_BACKGROUND)
        draw_text(screen, big, "REKLAM", AD_COLOR, center=(center_x, 300))
        draw_text(screen, small, "Deneme reklamı (gerçek reklam değil)", HINT_COLOR, center=(center_x, 350))
        draw_text(screen, mid, str(math.ceil(self.timer / FPS)), center=(center_x, 420))
