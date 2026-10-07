# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TITLE,
    FPS,
    SKY_BLUE,
    STOMP_BOUNCE,
    GAME_OVER_DELAY,
)
from player import Player
from level import Level
from camera import Camera
from score import Score, draw_lives, load_high_score, save_high_score
from screens import draw_menu, draw_game_over

# Menüde ve kaybettin ekranında oyunu başlatan tuşlar (fare tıklaması da çalışır)
START_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)


def new_game():
    # Yeni rastgele bölüm kur, karakteri başlangıç parçasındaki P noktasına koy
    level = Level()
    player = Player(*level.player_start, level.width)
    camera = Camera()
    camera.follow(player.rect, level.bottom, instant=True)
    level.update(camera.top, camera.bottom)
    score = Score(level.player_start[1])
    return level, player, camera, score


def update_game(level, player, camera, score):
    # Oyun oynanırken her karede yapılanlar
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

    camera.follow(player.rect, level.bottom)
    # Yukarıya yeni parçalar ekle, aşağıda kalanları sil
    level.update(camera.top, camera.bottom)


def draw_world(screen, level, player, camera):
    # Her şeyi kameraya göre kaydırarak çiz
    screen.fill(SKY_BLUE)
    screen_rect = screen.get_rect()
    sprites = [*level.tiles, *level.coins, *level.enemies]
    if player.visible:  # dokunulmazken yanıp söner
        sprites.append(player)
    for sprite in sprites:
        screen_pos = camera.apply(sprite.rect)
        if screen_pos.colliderect(screen_rect):  # sadece ekranda görüneni çiz
            screen.blit(sprite.image, screen_pos)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    high_score = load_high_score()
    level, player, camera, score = new_game()
    # Hangi ekrandayız: "menu" (başlangıç), "playing" (oyun), "game_over" (kaybettin)
    state = "menu"
    game_over_timer = 0  # kaybettin ekranında tuşlar çalışana kadar kalan kare
    new_record = False

    running = True
    while running:
        # 1) Olaylar: pencere kapatma, tuşa basma vb.
        start_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in START_KEYS:
                start_pressed = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                start_pressed = True

        # 2) Güncelleme: hangi ekrandaysak onun işi
        if state == "menu":
            if start_pressed:
                state = "playing"

        elif state == "playing":
            update_game(level, player, camera, score)
            # Can bitti → kaybettin ekranı; rekor kırıldıysa hemen kaydet
            if player.lives <= 0:
                state = "game_over"
                game_over_timer = GAME_OVER_DELAY
                new_record = score.total > high_score
                if new_record:
                    high_score = score.total
                    save_high_score(high_score)

        elif state == "game_over":
            if game_over_timer > 0:
                game_over_timer -= 1
            elif start_pressed:
                level, player, camera, score = new_game()
                state = "playing"

        # 3) Çizim — oyun dünyası her ekranda arkada görünür
        draw_world(screen, level, player, camera)
        if state == "menu":
            draw_menu(screen, high_score)
        else:
            # Puan ve canlar kameradan bağımsız: hep ekranın üst köşelerinde
            score.draw(screen)
            draw_lives(screen, player.lives)
            if state == "game_over":
                draw_game_over(screen, score, high_score, new_record, game_over_timer == 0)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
