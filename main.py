# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, SKY_BLUE
from player import Player
from level import Level, LEVEL_MAP
from camera import Camera


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # Bölümü haritadan kur, karakteri haritadaki P noktasına koy
    level = Level(LEVEL_MAP)
    player = Player(*level.player_start, level.width)
    all_sprites = pygame.sprite.Group(player)

    camera = Camera(level.width)
    camera.follow(player.rect, instant=True)
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
        all_sprites.update(level.tiles)

        # Çukura düştüyse başa dön (can sistemi Aşama 6'da gelecek)
        if player.rect.top > level.height:
            player.respawn()
            camera.follow(player.rect, instant=True)

        camera.follow(player.rect)

        # 3) Çizim — her şeyi kameraya göre kaydırarak çiz
        screen.fill(SKY_BLUE)
        for sprite in [*level.tiles, *all_sprites]:
            screen_pos = camera.apply(sprite.rect)
            if screen_pos.colliderect(screen_rect):  # sadece ekranda görüneni çiz
                screen.blit(sprite.image, screen_pos)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
