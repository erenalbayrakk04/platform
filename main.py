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
    SHIELD_LAVA_BOUNCE,
    POWERUP_WARN_TIME,
    LAVA_COLOR,
    DIFFICULTY_NAMES,
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    VOLUME_STEPS,
    WEB,
)
from player import Player
from level import Level
from lava import Lava
from camera import Camera
from score import Score, draw_lives, draw_powers, draw_text
from storage import load_record, save_record, load_dict, save_dict
import screens
from title import TitleScreen
from ui import PauseButton
from art import Background, shield_bubble
from controls import TouchButtons, read_controls
from effects import burst
import sound

# Toplanınca saçılan parçacıkların rengi
PICKUP_COLORS = {"heart": LIFE_COLOR, "magnet": MAGNET_COLOR, "shield": SHIELD_COLOR}
# Kalkan sürerken karakterin etrafındaki baloncuk
SHIELD_BUBBLE = []

# Saklanan istatistikler ve seçenekler (storage.py), ilk açılıştaki değerleriyle
STATS_DEFAULTS = {"games": 0, "climbed": 0, "coins": 0, "enemies": 0}
OPTIONS_DEFAULTS = {
    "muted": False,
    "difficulty": DEFAULT_DIFFICULTY,
    "music_volume": VOLUME_STEPS,  # ses ekranındaki çubuklar (0..VOLUME_STEPS)
    "effects_volume": VOLUME_STEPS,
}
# Oyun sırasında durduran tuşlar
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)


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


def hide_web_loader():
    # Web: oyunun ilk karesi çizildi → sayfanın yükleme ekranı (web.tmpl) yavaşça kaybolsun
    try:
        from platform import window

        window.loader_done()
    except Exception:
        pass


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


def new_game(best_height, mode):
    # Yeni rastgele bölüm kur, karakteri başlangıç parçasındaki P noktasına koy.
    # best_height = yükseklik rekoru (haritada "Rekor" çizgisi orada çizilir),
    # mode = zorluk modunun sayıları (settings.DIFFICULTIES): can, lav, düşman hızı...
    level = Level(mode)
    player = Player(*level.player_start, level.width, mode["lives"], mode["max_lives"])
    camera = Camera()
    camera.follow(player.rect, level.bottom, instant=True)
    level.update(camera.top, camera.bottom)
    score = Score(level.player_start[1], best_height)
    # Saçılan parçacıklar (effects.py) — dünyada dururlar, kamerayla birlikte çizilirler
    level.effects = pygame.sprite.Group()
    # Aşağıdan yükselen lav (lava.py) — zeminin altından başlar
    level.lava = Lava(mode)
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

    # Düşmanlar yürüsün/uçsun (topçular karaktere bakıp ateş eder); karakter değdiyse: yukarıdan
    # düştüyse (kirpi hariç — dikenli) veya kalkanı varsa düşman ölür, değilse can gider
    shots_before = len(level.shots)
    level.enemies.update(player.rect)
    if len(level.shots) > shots_before:
        sounds.play("shoot")
    for enemy in pygame.sprite.spritecollide(player, level.enemies, False):
        stomped = player.old_bottom <= enemy.old_top  # önceki karede tamamen düşmanın üstündeydi
        if (stomped and not enemy.spiky) or player.powers["shield"]:
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
    # Ateş topları uçar; değerse can gider (kalkan varsa sadece top söner)
    level.shots.update(level.tiles, level.width)
    for shot in pygame.sprite.spritecollide(player, level.shots, False):
        if player.powers["shield"]:
            shot.kill()
            burst(level.effects, shot.rect.center, shot.color)
        elif not player.invincible:
            shot.kill()
            player.hurt()
            sounds.play("hurt")
            burst(level.effects, player.rect.center, PLAYER_COLOR)

    # Lav yükselir; değdiyse bir can gider, son durduğu yerden devam eder, lav geri çekilir.
    # Kalkanı varsa can gitmez: lavdan yukarı fırlar ve kalkan kırılır (bir kez kurtarır)
    level.lava.update(camera.bottom)
    if level.lava.touches(player.rect):
        burst(level.effects, player.rect.center, LAVA_COLOR)
        if player.powers["shield"]:
            player.powers["shield"] = 0
            player.bounce(SHIELD_LAVA_BOUNCE)
            burst(level.effects, player.rect.center, SHIELD_COLOR)
            sounds.play("spring")
            sounds.play("powerdown")
        else:
            player.hurt()
            player.respawn()
            sounds.play("hurt")
        level.lava.push_back(player.rect.bottom)

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
    sprites = [
        *level.tiles, *ghosts, *level.springs, *level.coins, *level.pickups, *level.enemies, *level.shots,
        *level.effects,
    ]
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


class Game:
    # Oyunun bütün durumu: hangi ekrandayız, rekorlar, seçenekler ve şu an oynanan bölüm.
    # Ekranlar (state): "title" (giriş ekranı, oyun bununla açılır), "menu" (ana menü), "sound" (ses ayarları),
    # "howto" (nasıl oynanır), "records" (rekorlar), "playing" (oyun), "paused" (durdu), "game_over" (kaybettin)
    def __init__(self, sounds):
        self.sounds = sounds
        # Rekorlar her zorluk modunun ayrı: asıl hedef en yüksek tırmanış (blok), ayrıca en yüksek puan
        self.best_heights = {mode: load_record("height", mode) for mode in DIFFICULTY_NAMES}
        self.high_scores = {mode: load_record("score", mode) for mode in DIFFICULTY_NAMES}
        self.stats = load_dict("stats", STATS_DEFAULTS)
        self.options = load_dict("options", OPTIONS_DEFAULTS)
        if self.options["difficulty"] not in DIFFICULTY_NAMES:
            self.options["difficulty"] = DEFAULT_DIFFICULTY
        if self.options["muted"]:
            sounds.toggle_mute()
        # Ses seviyeleri: kayıttaki değer çubuklara ve seslere
        sliders = screens.SOUND_MENU.sliders
        for name in sliders:
            key = f"{name}_volume"
            self.options[key] = max(0, min(VOLUME_STEPS, self.options[key]))
            sliders[name].value = self.options[key]
        self.apply_volume()
        self.state = "title"
        self.title = TitleScreen(WEB)  # menüye geçiş bitince silinir
        self.game_over_timer = 0  # kaybettin ekranında düğmeler çıkana kadar kalan kare
        self.new_record = False
        self.pause_button = PauseButton()
        self.reset()

    @property
    def mode(self):
        # Seçili zorluk modu: "easy", "normal", "hard", "ultra"
        return self.options["difficulty"]

    @property
    def best_height(self):
        return self.best_heights[self.mode]

    @property
    def high_score(self):
        return self.high_scores[self.mode]

    def reset(self):
        # Yeni bölüm kur (menünün arkasında da bu görünür)
        self.level, self.player, self.camera, self.score = new_game(self.best_height, DIFFICULTIES[self.mode])

    def labels(self):
        # Yazısı değişen düğmeler
        return {
            "sound": "Ses: Kapalı" if self.sounds.muted else "Ses: Açık",
            "difficulty": f"Zorluk: {DIFFICULTY_NAMES[self.options['difficulty']]}",
        }

    def save_options(self):
        self.options["muted"] = self.sounds.muted
        save_dict("options", self.options)

    def apply_volume(self):
        # Ses ekranındaki çubukların değeri seslere geçer
        sliders = screens.SOUND_MENU.sliders
        self.sounds.set_levels(
            sliders["music"].value / VOLUME_STEPS, sliders["effects"].value / VOLUME_STEPS
        )

    def change_volume(self, name):
        # Çubuk oynatıldı: ses kapalıysa aç (duyulsun), yeni seviyeyi kaydet
        self.options[f"{name}_volume"] = screens.SOUND_MENU.sliders[name].value
        self.apply_volume()
        if self.sounds.muted:
            self.sounds.toggle_mute()
        self.save_options()
        if name == "effects":
            self.sounds.play("coin")  # efekt sesi ne kadar yüksek, hemen duyulsun

    def toggle_sound(self):
        self.sounds.toggle_mute()
        self.save_options()

    def next_difficulty(self):
        # Kolay → Orta → Zor → Ultra Zor → Kolay ...
        names = list(DIFFICULTY_NAMES)
        index = names.index(self.mode)
        self.options["difficulty"] = names[(index + 1) % len(names)]
        self.save_options()
        self.reset()  # menünün arkasındaki bölüm ve rekor çizgisi yeni moda göre olsun

    def start(self):
        # Yeni oyuna başla
        self.reset()
        self.state = "playing"
        self.sounds.play("start")
        self.sounds.play_music("game")

    def to_menu(self):
        # Oyundan (durdurup ya da kaybedip) ana menüye: açılış müziği yeniden başlar
        self.sounds.play_music("title")
        self.reset()
        self.state = "menu"

    def finish(self):
        # Oyun bitti (kaybetti ya da yarıda ana menüye döndü): bu modun rekorlarını ve toplamları kaydet
        score = self.score
        self.new_record = score.new_record  # yükseklik rekoru
        if self.new_record:
            self.best_heights[self.mode] = score.height
            save_record("height", score.height, self.mode)
        if score.total > self.high_score:
            self.high_scores[self.mode] = score.total
            save_record("score", score.total, self.mode)
        self.stats["games"] += 1
        self.stats["climbed"] += score.height
        self.stats["coins"] += score.coins
        self.stats["enemies"] += score.enemies
        save_dict("stats", self.stats)

    def handle_event(self, event):
        # Ekrana göre tuş / dokunuş / tıklama. Oyundan çıkılacaksa False döner
        key = event.key if event.type == pygame.KEYDOWN else None
        if self.state == "title":
            if key == pygame.K_ESCAPE and not WEB:
                return False
            if self.title.handle_event(event):  # dokunuldu: karakter fırlar, ana menü belirir
                self.sounds.play("spring")

        elif self.state == "menu":
            if key == pygame.K_ESCAPE and not WEB:
                return False  # tarayıcıda çıkış yok (sayfa kapatılır)
            action = screens.MAIN_BUTTONS.handle_event(event)
            if action == "play":
                self.start()
            elif action == "difficulty":
                self.next_difficulty()
            elif action == "sound_menu":
                self.state = "sound"
                screens.SOUND_MENU.open()
            elif action in ("howto", "records"):
                self.state = action
                screens.BACK_BUTTON.focus = 0

        elif self.state == "sound":
            action = screens.SOUND_MENU.handle_event(event)
            if key == pygame.K_ESCAPE or action == "back":
                self.state = "menu"
            elif action == "sound":
                self.toggle_sound()
            elif action in ("music", "effects"):
                self.change_volume(action)

        elif self.state in ("howto", "records"):
            if key == pygame.K_ESCAPE or screens.BACK_BUTTON.handle_event(event) == "back":
                self.state = "menu"

        elif self.state == "playing":
            if key in PAUSE_KEYS or self.pause_button.clicked(event):
                self.state = "paused"
                screens.PAUSE_BUTTONS.focus = 0

        elif self.state == "paused":
            action = screens.PAUSE_BUTTONS.handle_event(event)
            if key in PAUSE_KEYS or action == "resume":
                self.state = "playing"
            elif action == "sound":
                self.toggle_sound()
            elif action == "menu":
                self.finish()
                self.to_menu()

        elif self.state == "game_over" and self.game_over_timer == 0:
            action = screens.GAME_OVER_BUTTONS.handle_event(event)
            if action == "again":
                self.start()
            elif action == "menu" or key == pygame.K_ESCAPE:
                self.to_menu()
        return True

    def update(self, steps, touch):
        # Oyun, geçen süre kadar adım ilerler (StepTimer)
        if self.state == "playing":
            controls = read_controls(touch)
            for _ in range(steps):
                update_game(self.level, self.player, self.camera, self.score, controls, self.sounds)
                # Can bitti → kaybettin ekranı; rekor kırıldıysa hemen kaydet
                if self.player.lives <= 0:
                    self.state = "game_over"
                    self.game_over_timer = GAME_OVER_DELAY
                    screens.GAME_OVER_BUTTONS.focus = 0
                    self.sounds.stop_music()
                    self.sounds.play("game_over")
                    self.finish()
                    break
        elif self.state == "game_over":
            self.game_over_timer = max(0, self.game_over_timer - steps)
        elif self.state == "title":
            for _ in range(steps):
                self.title.update()
            if self.title.done:  # menüye geçiş bitti
                self.state = "menu"
                self.title = None
                screens.MAIN_BUTTONS.focus = 0

    def draw(self, screen, background, touch, slow):
        # Giriş ekranının kendi sahnesi var; dokununca altında ana menü çizilir, giriş ekranı üstünde silinir
        if self.state == "title" and not self.title.leaving:
            self.title.draw(screen, background)
            return
        # Oyun dünyası diğer her ekranda arkada görünür
        draw_world(screen, background, self.level, self.player, self.camera, self.score)
        if self.state in ("menu", "title"):
            screens.draw_main_menu(screen, self.best_height, self.labels(), WEB)
            if self.state == "title":
                self.title.draw_fading(screen, background)
        elif self.state == "sound":
            screens.SOUND_MENU.draw(screen, self.labels(), self.sounds.muted)
        elif self.state == "howto":
            screens.draw_howto(screen)
        elif self.state == "records":
            screens.draw_records(screen, self.best_heights, self.high_scores, self.stats, self.mode)
        else:
            # Puan ve canlar kameradan bağımsız: hep ekranın üst köşelerinde
            self.score.draw(screen)
            draw_lives(screen, self.player.lives, self.player.max_lives)
            draw_powers(screen, self.player)
            if self.state == "playing":
                touch.draw(screen)
                self.pause_button.draw(screen)
            elif self.state == "paused":
                screens.draw_pause(screen, self.labels())
            elif self.state == "game_over":
                screens.draw_game_over(
                    screen,
                    self.score,
                    DIFFICULTY_NAMES[self.mode],
                    self.best_height,
                    self.high_score,
                    self.new_record,
                    self.game_over_timer == 0,
                    slow,
                )


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

    game = Game(sounds)
    sounds.play_music("title")  # açılış müziği (web'de ilk dokunuşla duyulur, bkz. web.tmpl ses kilidi)
    timer = StepTimer()
    fps_meter = FpsMeter()
    show_fps = fps_wanted()
    first_frame = True

    running = True
    while running:
        # 1) Olaylar: pencere kapatma, tuşa basma, dokunma vb.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == mute_key:
                game.toggle_sound()
            elif not game.handle_event(event):
                running = False
            touch.handle_event(event)  # ekrana dokunan parmakları takip et
        touch.update()

        # 2) Güncelleme: hangi ekrandaysak onun işi
        steps = timer.steps()
        game.update(steps, touch)

        # 3) Çizim. Bu karede adım oynanmadıysa (hızlı ekranlarda olur) hiçbir şey değişmedi,
        # yeniden çizmeye gerek yok
        if steps:
            fps_meter.count()
            # Telefon saniyede az kare gösteriyorsa (Düşük Güç Modu) kaybettin ekranında ipucu çıkar
            game.draw(screen, background, touch, WEB and fps_meter.slow)
            if show_fps:
                fps_meter.draw(screen)
            pygame.display.flip()
            if first_frame and WEB:
                hide_web_loader()
            first_frame = False

        # Bilgisayarda döngü saniyede FPS kez döner. Tarayıcıda hızı tarayıcı belirler (ekran her
        # yenilendiğinde bir tur); orada beklemek tarayıcıyı meşgul eder, kare kaçırtır
        if not WEB:
            clock.tick(FPS)
        await asyncio.sleep(0)  # tarayıcıya sıra ver — web sürümü bunsuz donar

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
