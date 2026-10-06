# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, SKY_BLUE
from player import Player
from level import Level
from camera import Camera


def new_game():
    # Yeni rastgele bölüm kur, karakteri başlangıç parçasındaki P noktasına koy
    level = Level()
    player = Player(*level.player_start, level.width)
    camera = Camera()
    camera.follow(player.rect, level.bottom, instant=True)
    level.update(camera.top, camera.bottom)
    return level, player, camera


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    level, player, camera = new_game()
    screen_rect = screen.get_rect()

    running = True
    while running:
        # 1) Olaylar: pencere kapatma, tuşa basma vb.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 2) Güncelleme: oyun mantığı
        player.update(level.tiles)

        # Silinmiş bölgeye kadar düştüyse yeni oyun (can sistemi Aşama 6'da gelecek)
        if player.rect.top > level.bottom:
            level, player, camera = new_game()

        camera.follow(player.rect, level.bottom)
        # Yukarıya yeni parçalar ekle, aşağıda kalanları sil
        level.update(camera.top, camera.bottom)

        # 3) Çizim — her şeyi kameraya göre kaydırarak çiz
        screen.fill(SKY_BLUE)
        for sprite in [*level.tiles, player]:
            screen_pos = camera.apply(sprite.rect)
            if screen_pos.colliderect(screen_rect):  # sadece ekranda görüneni çiz
                screen.blit(sprite.image, screen_pos)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
