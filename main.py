# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, SKY_BLUE
from player import Player


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Karakteri ekranın ortasına, alt kısma yakın yerleştir
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)
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
        all_sprites.update()

        # 3) Çizim
        screen.fill(SKY_BLUE)
        all_sprites.draw(screen)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
