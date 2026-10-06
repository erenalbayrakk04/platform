# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, SKY_BLUE
from player import Player
from level import Level, LEVEL_MAP


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Bölümü haritadan kur, karakteri haritadaki P noktasına koy
    level = Level(LEVEL_MAP)
    player = Player(*level.player_start)
    all_sprites = pygame.sprite.Group(player)

    running = True
    while running:
        # 1) Olaylar: pencere kapatma, tuşa basma vb.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 2) Güncelleme: oyun mantığı
        all_sprites.update(level.tiles)

        # 3) Çizim
        screen.fill(SKY_BLUE)
        level.tiles.draw(screen)
        all_sprites.draw(screen)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
