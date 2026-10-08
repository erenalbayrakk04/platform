# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
# Web sürümü de bu dosyadan yapılır (pygbag); bu yüzden oyun döngüsü "async" çalışır.
import asyncio
import sys
import time

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TITLE,
    FPS,
    MAX_CATCH_UP,
    SHOW_FPS,
    LOW_FPS_LIMIT,
    STOMP_BOUNCE,
    GAME_OVER_DELAY,
    MUTE_KEY,
    COIN_COLOR,
    PLAYER_COLOR,
    LIFE_COLOR,
    HEART_POINTS,
    CRUMBLE_COLOR,
    MAGNET_COLOR,
    SHIELD_COLOR,
    POWERUP_WARN_TIME,
    LAVA_COLOR,
    WEB,
)
from player import Player
from level import Level
from lava import Lava
from camera import Camera
from score import Score, draw_lives, draw_powers, draw_text, load_record, save_record
from screens import draw_menu, draw_game_over
from art import Background, shield_bubble
from controls import TouchButtons, read_controls
from effects import burst
import sound

# Toplanınca saçılan parçacıkların rengi
PICKUP_COLORS = {"heart": LIFE_COLOR, "magnet": MAGNET_COLOR, "shield": SHIELD_COLOR}
# Kalkan sürerken karakterin etrafındaki baloncuk
SHIELD_BUBBLE = []

# Menüde ve kaybettin ekranında oyunu başlatan tuşlar (fare tıklaması da çalışır)
START_KEYS = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)


class StepTimer:
    # Oyun hızı ekranın kare hızına bağlı olmasın: her karede gerçekten geçen süre ölçülür ve oyun o
    # kadar "adım" ilerletilir (1 adım = 1/FPS saniye). Telefon saniyede 30 kare gösterirse (ör. iPhone
    # Düşük Güç Modu) her karede 2 adım, 120 Hz ekranda iki karede bir adım oynanır → oyun hep aynı hızda.
    def __init__(self):
        self.last = time.perf_counter()
        self.lag = 0.0  # geçmiş ama henüz oynanmamış süre (adım cinsinden)

    def steps(self):
        now = time.perf_counter()
        passed = (now - self.last) * FPS  # son kareden beri geçen süre, adım cinsinden
        self.last = now
        # Ekran düzenli yeniler ama ölçüm biraz oynar (16 ms, 17 ms...). Tam sayıya çok yakınsa tam
        # sayı say; yoksa bazı karelerde 0, bazılarında 2 adım oynanır ve görüntü titrer
        whole = round(passed)
        if whole >= 1 and abs(passed - whole) < 0.1:
            passed = whole
        self.lag = min(self.lag + passed, MAX_CATCH_UP)
        steps = int(self.lag)
        self.lag -= steps
        return steps


def fps_wanted():
    # Kare sayacı açık mı: settings.py'de SHOW_FPS ya da web'de adresin sonunda #fps
    if SHOW_FPS:
        return True
    if WEB:
        try:
            from platform import window

            return "fps" in str(window.location.hash)
        except Exception:
            return False
    return False


class FpsMeter:
    # Saniyede kaç kare çizildiğini sayar (her çizilen karede count()); istenirse ekranın üstüne yazar
    def __init__(self):
        self.font = pygame.font.Font(None, 22)
        self.frames = 0
        self.start = time.perf_counter()
        self.text = "..."
        self.low_seconds = 0  # kaç saniyedir üst üste LOW_FPS_LIMIT'in altında

    def count(self):
        self.frames += 1
        now = time.perf_counter()
        if now - self.start >= 1:
            fps = self.frames / (now - self.start)
            self.text = f"{fps:.0f} kare/sn"
            self.low_seconds = self.low_seconds + 1 if fps < LOW_FPS_LIMIT else 0
            self.frames = 0
            self.start = now

    @property
    def slow(self):
        # Tek seferlik takılma sayılmasın: 2 saniye üst üste düşük olmalı
        return self.low_seconds >= 2

    def draw(self, screen):
        draw_text(screen, self.font, self.text, center=(SCREEN_WIDTH // 2, 80))


def new_game(best_height):
    # Yeni rastgele bölüm kur, karakteri başlangıç parçasındaki P noktasına koy.
    # best_height = yükseklik rekoru (haritada "Rekor" çizgisi orada çizilir)
    level = Level()
    player = Player(*level.player_start, level.width)
    camera = Camera()
    camera.follow(player.rect, level.bottom, instant=True)
    level.update(camera.top, camera.bottom)
    score = Score(level.player_start[1], best_height)
    # Saçılan parçacıklar (effects.py) — dünyada dururlar, kamerayla birlikte çizilirler
    level.effects = pygame.sprite.Group()
    # Aşağıdan yükselen lav (lava.py) — zeminin altından başlar
    level.lava = Lava()
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
    if score.update(player):  # yükseklik rekoru şimdi kırıldı
        sounds.play("powerup")

    # Düşmanlar yürüsün; karakter değdiyse: yukarıdan düştüyse veya kalkanı varsa düşman ölür,
    # değilse can gider
    level.enemies.update()
    for enemy in pygame.sprite.spritecollide(player, level.enemies, False):
        stomped = player.old_bottom <= enemy.old_top  # önceki karede tamamen düşmanın üstündeydi
        if stomped or player.powers["shield"]:
            enemy.kill()
            score.add_enemy()
            if stomped:
                player.bounce(STOMP_BOUNCE)
            sounds.play("stomp")
            burst(level.effects, enemy.rect.center, enemy.color)
        elif not player.invincible:
            player.hurt()
            sounds.play("hurt")
            burst(level.effects, player.rect.center, PLAYER_COLOR)

    # Lav yükselir; değdiyse (kalkan olsa da) bir can gider, son durduğu yerden devam eder, lav geri çekilir
    level.lava.update(camera.bottom)
    if level.lava.touches(player.rect):
        burst(level.effects, player.rect.center, LAVA_COLOR)
        player.hurt()
        player.respawn()
        level.lava.push_back(player.rect.bottom)
        sounds.play("hurt")

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


def draw_world(screen, background, level, player, camera, score):
    # Önce gökyüzü, sonra her şeyi kameraya göre kaydırarak çiz
    background.draw(screen, camera.top)
    score.draw_record_line(screen, camera)  # rekor yüksekliği (platformların arkasında)
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
    # Lav her şeyin önünde (içine düşen kaybolur)
    level.lava.draw(screen, camera)
    # Kalkan: karakterin etrafında baloncuk; bitmesine az kalınca yanıp söner
    shield = player.powers["shield"]
    if shield and (shield > POWERUP_WARN_TIME or (shield // 8) % 2 == 0):
        if not SHIELD_BUBBLE:
            SHIELD_BUBBLE.append(shield_bubble(player.rect.height // 2 + 8))
        bubble = SHIELD_BUBBLE[0]
        screen.blit(bubble, bubble.get_rect(center=camera.apply(player.rect).center))


async def main():
    sound.pre_init()  # ses ayarı pygame.init()'ten önce yapılmalı
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    sounds = sound.Sounds()  # sesler ve müzik burada üretilir (bir saniye kadar sürebilir)
    background = Background()
    touch = TouchButtons()
    mute_key = pygame.key.key_code(MUTE_KEY)

    # Rekorlar: asıl hedef en yüksek tırmanış (blok), ayrıca en yüksek puan
    best_height = load_record("height")
    high_score = load_record("score")
    level, player, camera, score = new_game(best_height)
    # Hangi ekrandayız: "menu" (başlangıç), "playing" (oyun), "game_over" (kaybettin)
    state = "menu"
    game_over_timer = 0  # kaybettin ekranında tuşlar çalışana kadar kalan kare
    new_record = False
    sounds.start_music()
    timer = StepTimer()
    fps_meter = FpsMeter()
    show_fps = fps_wanted()

    running = True
    while running:
        # 1) Olaylar: pencere kapatma, tuşa basma vb.
        start_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not WEB:
                running = False  # tarayıcıda çıkış yok (sayfa kapatılır)
            elif event.type == pygame.KEYDOWN and event.key == mute_key:
                sounds.toggle_mute()
            elif event.type == pygame.KEYDOWN and event.key in START_KEYS:
                start_pressed = True
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                start_pressed = True
            touch.handle_event(event)  # ekrana dokunan parmakları takip et
        touch.update()

        # 2) Güncelleme: hangi ekrandaysak onun işi. Oyun, geçen süre kadar adım ilerler
        steps = timer.steps()
        if state == "menu":
            if start_pressed:
                state = "playing"
                sounds.play("start")

        elif state == "playing":
            controls = read_controls(touch)
            for _ in range(steps):
                update_game(level, player, camera, score, controls, sounds)
                # Can bitti → kaybettin ekranı; rekor kırıldıysa hemen kaydet
                if player.lives <= 0:
                    state = "game_over"
                    game_over_timer = GAME_OVER_DELAY
                    sounds.stop_music()
                    sounds.play("game_over")
                    new_record = score.new_record  # yükseklik rekoru
                    if new_record:
                        best_height = score.height
                        save_record("height", best_height)
                    if score.total > high_score:
                        high_score = score.total
                        save_record("score", high_score)
                    break

        elif state == "game_over":
            if game_over_timer > 0:
                game_over_timer = max(0, game_over_timer - steps)
            elif start_pressed:
                level, player, camera, score = new_game(best_height)
                state = "playing"
                sounds.play("start")
                sounds.start_music()

        # 3) Çizim — oyun dünyası her ekranda arkada görünür. Bu karede adım oynanmadıysa (hızlı
        # ekranlarda olur) hiçbir şey değişmedi, yeniden çizmeye gerek yok
        if steps:
            fps_meter.count()
            # Telefon saniyede az kare gösteriyorsa (Düşük Güç Modu) menülerde ipucu çıkar
            slow = WEB and fps_meter.slow
            draw_world(screen, background, level, player, camera, score)
            if state == "menu":
                draw_menu(screen, best_height, high_score, slow)
            else:
                # Puan ve canlar kameradan bağımsız: hep ekranın üst köşelerinde
                score.draw(screen)
                draw_lives(screen, player.lives)
                draw_powers(screen, player)
                if state == "playing":
                    touch.draw(screen)
                if state == "game_over":
                    draw_game_over(
                        screen, score, best_height, high_score, new_record, game_over_timer == 0, slow
                    )
            if show_fps:
                fps_meter.draw(screen)
            pygame.display.flip()

        # Bilgisayarda döngü saniyede FPS kez döner. Tarayıcıda hızı tarayıcı belirler (ekran her
        # yenilendiğinde bir tur); orada beklemek tarayıcıyı meşgul eder, kare kaçırtır
        if not WEB:
            clock.tick(FPS)
        await asyncio.sleep(0)  # tarayıcıya sıra ver — web sürümü bunsuz donar

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
