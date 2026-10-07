# Menü ve "Kaybettin" ekranları: oyunun üstüne karanlık bir perde serilip yazılar ortalanır.
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
    MUTE_KEY,
)
from score import draw_text

CENTER_X = SCREEN_WIDTH // 2

# Yazı tipleri ve perde ilk kullanımda bir kere hazırlanır (pygame.init()'ten sonra olmalı)
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


def blink_on():
    # Yarım saniye görünür, yarım saniye görünmez — "başlamak için..." yazısı yanıp sönsün
    return pygame.time.get_ticks() // 500 % 2 == 0


def draw_menu(screen, high_score):
    draw_overlay(screen)
    # Oyun adı iki satır: "Platform" / "Oyunu"
    first, _, rest = TITLE.partition(" ")
    draw_text(screen, font(TITLE_FONT_SIZE), first, TITLE_COLOR, center=(CENTER_X, 200))
    draw_text(screen, font(TITLE_FONT_SIZE), rest, TITLE_COLOR, center=(CENTER_X, 255))
    draw_text(screen, font(MENU_FONT_SIZE), f"En yüksek skor: {high_score}", center=(CENTER_X, 350))
    if blink_on():
        draw_text(screen, font(MENU_FONT_SIZE), "Başlamak için Boşluk / dokun", center=(CENTER_X, 450))
    small = font(MENU_SMALL_FONT_SIZE)
    draw_text(screen, small, "Ok tuşları / A-D: yürü", HINT_COLOR, center=(CENTER_X, 560))
    draw_text(screen, small, "Boşluk / Yukarı / W: zıpla", HINT_COLOR, center=(CENTER_X, 588))
    draw_text(screen, small, "Düşmanların üstüne zıpla!", HINT_COLOR, center=(CENTER_X, 616))
    draw_text(screen, small, f"{MUTE_KEY.upper()}: sesi aç / kapat", HINT_COLOR, center=(CENTER_X, 644))


def draw_game_over(screen, score, high_score, new_record, ready):
    draw_overlay(screen)
    draw_text(screen, font(TITLE_FONT_SIZE), "Kaybettin!", GAME_OVER_COLOR, center=(CENTER_X, 220))
    draw_text(screen, font(MENU_FONT_SIZE + 10), f"Puan: {score.total}", center=(CENTER_X, 310))
    small = font(MENU_SMALL_FONT_SIZE)
    details = f"Yükseklik: {score.height}   Altın: {score.coins}   Düşman: {score.enemies}"
    draw_text(screen, small, details, HINT_COLOR, center=(CENTER_X, 345))
    if new_record:
        draw_text(screen, font(MENU_FONT_SIZE), "YENİ REKOR!", RECORD_COLOR, center=(CENTER_X, 400))
    else:
        draw_text(screen, font(MENU_FONT_SIZE), f"En yüksek skor: {high_score}", center=(CENTER_X, 400))
    # Tuşlar çalışmaya başlayınca "tekrar oyna" yazısı çıksın
    if ready and blink_on():
        draw_text(screen, font(MENU_FONT_SIZE), "Tekrar için Boşluk / dokun", center=(CENTER_X, 500))
