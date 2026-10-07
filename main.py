# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, SKY_BLUE, STOMP_BOUNCE
from player import Player
from level import Level
from camera import Camera
from score import Score, draw_lives


def new_game():
    # Yeni rastgele bölüm kur, karakteri başlangıç parçasındaki P noktasına koy
    level = Level()
    player = Player(*level.player_start, level.width)
    camera = Camera()
    camera.follow(player.rect, level.bottom, instant=True)
    level.update(camera.top, camera.bottom)
    score = Score(level.player_start[1])
    return level, player, camera, score


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    level, player, camera, score = new_game()
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

        # Değdiği altınları topla (True = toplanan altın haritadan silinir)
        for _ in pygame.sprite.spritecollide(player, level.coins, True):
            score.add_coin()
        score.update(player)

        # Düşmanlar yürüsün; karakter değdiyse: yukarıdan düştüyse düşman ölür, değilse can gider
        level.enemies.update()
        for enemy in pygame.sprite.spritecollide(player, level.enemies, False):
            if player.old_bottom <= enemy.rect.top:  # önceki karede tamamen düşmanın üstündeydi
                enemy.kill()
                score.add_enemy()
                player.bounce(STOMP_BOUNCE)
            elif not player.invincible:
                player.hurt()

        # Silinmiş bölgeye kadar düştüyse bir can gider, son durduğu yerden devam eder
        if player.rect.top > level.bottom:
            player.hurt()
            player.respawn()

        # Can bittiyse yeni oyun (kaybettin ekranı Aşama 7'de gelecek)
        if player.lives <= 0:
            level, player, camera, score = new_game()

        camera.follow(player.rect, level.bottom)
        # Yukarıya yeni parçalar ekle, aşağıda kalanları sil
        level.update(camera.top, camera.bottom)

        # 3) Çizim — her şeyi kameraya göre kaydırarak çiz
        screen.fill(SKY_BLUE)
        sprites = [*level.tiles, *level.coins, *level.enemies]
        if player.visible:  # dokunulmazken yanıp söner
            sprites.append(player)
        for sprite in sprites:
            screen_pos = camera.apply(sprite.rect)
            if screen_pos.colliderect(screen_rect):  # sadece ekranda görüneni çiz
                screen.blit(sprite.image, screen_pos)
        # Puan yazısı kameradan bağımsız: hep ekranın sol üstünde
        score.draw(screen)
        draw_lives(screen, player.lives)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
