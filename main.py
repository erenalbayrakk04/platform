# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
import sys

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TITLE,
    FPS,
    STOMP_BOUNCE,
    GAME_OVER_DELAY,
    MUTE_KEY,
    COIN_COLOR,
    ENEMY_COLOR,
    PLAYER_COLOR,
    LIFE_COLOR,
    HEART_POINTS,
    CRUMBLE_COLOR,
    MAGNET_COLOR,
)
from player import Player
from level import Level
from camera import Camera
from score import Score, draw_lives, draw_powers, load_high_score, save_high_score
from screens import draw_menu, draw_game_over
from art import Background
from controls import TouchButtons, read_controls
from effects import burst
import sound

# Toplanınca saçılan parçacıkların rengi
PICKUP_COLORS = {"heart": LIFE_COLOR, "magnet": MAGNET_COLOR}

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
    # Saçılan parçacıklar (effects.py) — dünyada dururlar, kamerayla birlikte çizilirler
    level.effects = pygame.sprite.Group()
    return level, player, camera, score


def update_game(level, player, camera, score, controls, sounds):
    # Oyun oynanırken her karede yapılanlar
    # Hareketli platformlar ilerler; üstlerinde duran karakteri de taşırlar
    for mover in level.movers:
        riding = player.standing_on(mover)
        dx = mover.move()
        if riding and dx:
            player.carry(dx, level.tiles)

    player.update(level.tiles, controls)
    if player.jumped:
        sounds.play("jump")
    # Kırılan platformlar: üstüne basılınca titrer, sonra kırılıp düşer, bir süre sonra geri gelir
    for crumbler in level.crumblers:
        if crumbler.step(player, level.tiles) == "break":
            sounds.play("crumble")
            burst(level.effects, crumbler.rect.center, CRUMBLE_COLOR)
    if player.check_springs(level.springs):
        sounds.play("spring")
    if player.expired:
        sounds.play("powerdown")

    # Mıknatıs: yakındaki altınlar karaktere doğru uçar
    if player.powers["magnet"]:
        for coin in level.coins:
            coin.attract(player.rect.center)

    # Değdiği altınları topla (True = toplanan altın haritadan silinir)
    for coin in pygame.sprite.spritecollide(player, level.coins, True):
        score.add_coin()
        sounds.play("coin")
        burst(level.effects, coin.rect.center, COIN_COLOR)
    # Kalp bir can verir (can zaten doluysa puan); güçlendirme bir süre işe yarar
    for item in pygame.sprite.spritecollide(player, level.pickups, True):
        if item.kind == "heart":
            if not player.heal():
                score.add_bonus(HEART_POINTS)
            sounds.play("life")
        else:
            player.power_up(item.kind)
            sounds.play("powerup")
        burst(level.effects, item.rect.center, PICKUP_COLORS[item.kind])
    score.update(player)

    # Düşmanlar yürüsün; karakter değdiyse: yukarıdan düştüyse düşman ölür, değilse can gider
    level.enemies.update()
    for enemy in pygame.sprite.spritecollide(player, level.enemies, False):
        if player.old_bottom <= enemy.old_top:  # önceki karede tamamen düşmanın üstündeydi
            enemy.kill()
            score.add_enemy()
            player.bounce(STOMP_BOUNCE)
            sounds.play("stomp")
            burst(level.effects, enemy.rect.center, ENEMY_COLOR)
        elif not player.invincible:
            player.hurt()
            sounds.play("hurt")
            burst(level.effects, player.rect.center, PLAYER_COLOR)

    # Silinmiş bölgeye kadar düştüyse bir can gider, son durduğu yerden devam eder
    if player.rect.top > level.bottom:
        player.hurt()
        player.respawn()
        sounds.play("hurt")

    # Animasyonlar: altınlar döner, parçacıklar uçar
    level.coins.update()
    level.pickups.update()
    level.springs.update()
    level.effects.update()

    camera.follow(player.rect, level.bottom)
    # Yukarıya yeni parçalar ekle, aşağıda kalanları sil
    level.update(camera.top, camera.bottom)


def draw_world(screen, background, level, player, camera):
    # Önce gökyüzü, sonra her şeyi kameraya göre kaydırarak çiz
    background.draw(screen, camera.top)
    screen_rect = screen.get_rect()
    # Kırık platformlar geri gelmeden az önce silik görünür
    ghosts = [crumbler for crumbler in level.crumblers if crumbler.ghost]
    sprites = [*level.tiles, *ghosts, *level.springs, *level.coins, *level.pickups, *level.enemies, *level.effects]
    if player.visible:  # dokunulmazken yanıp söner
        sprites.append(player)
    for sprite in sprites:
        # draw_rect: çizim yeri çarpışma kutusundan farklı olabilir (ör. titreyen platform)
        screen_pos = camera.apply(getattr(sprite, "draw_rect", sprite.rect))
        if screen_pos.colliderect(screen_rect):  # sadece ekranda görüneni çiz
            screen.blit(sprite.image, screen_pos)


def main():
    sound.pre_init()  # ses ayarı pygame.init()'ten önce yapılmalı
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    sounds = sound.Sounds()  # sesler ve müzik burada üretilir (bir saniye kadar sürebilir)
    background = Background()
    touch = TouchButtons()
    mute_key = pygame.key.key_code(MUTE_KEY)

    high_score = load_high_score()
    level, player, camera, score = new_game()
    # Hangi ekrandayız: "menu" (başlangıç), "playing" (oyun), "game_over" (kaybettin)
    state = "menu"
    game_over_timer = 0  # kaybettin ekranında tuşlar çalışana kadar kalan kare
    new_record = False
    sounds.start_music()

    running = True
    while running:
        # 1) Olaylar: pencere kapatma, tuşa basma vb.
        start_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == mute_key:
                sounds.toggle_mute()
            elif event.type == pygame.KEYDOWN and event.key in START_KEYS:
                start_pressed = True
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                start_pressed = True
            touch.handle_event(event)  # ekrana dokunan parmakları takip et
        touch.update()

        # 2) Güncelleme: hangi ekrandaysak onun işi
        if state == "menu":
            if start_pressed:
                state = "playing"
                sounds.play("start")

        elif state == "playing":
            update_game(level, player, camera, score, read_controls(touch), sounds)
            # Can bitti → kaybettin ekranı; rekor kırıldıysa hemen kaydet
            if player.lives <= 0:
                state = "game_over"
                game_over_timer = GAME_OVER_DELAY
                sounds.stop_music()
                sounds.play("game_over")
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
                sounds.play("start")
                sounds.start_music()

        # 3) Çizim — oyun dünyası her ekranda arkada görünür
        draw_world(screen, background, level, player, camera)
        if state == "menu":
            draw_menu(screen, high_score)
        else:
            # Puan ve canlar kameradan bağımsız: hep ekranın üst köşelerinde
            score.draw(screen)
            draw_lives(screen, player.lives)
            draw_powers(screen, player)
            if state == "playing":
                touch.draw(screen)
            if state == "game_over":
                draw_game_over(screen, score, high_score, new_record, game_over_timer == 0)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
