# Oyunu başlatan dosya. Çalıştırmak için terminalde: python main.py
# Web sürümü de bu dosyadan yapılır (pygbag); bu yüzden oyun döngüsü "async" çalışır.
import asyncio
import math
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
    REVIVE_GEMS,
    REVIVE_TIME,
    REVIVE_INVINCIBLE,
    ADS_TEST,
    ADS_AFTER_GAMES,
    FREE_GEMS,
    NOTE_TIME,
    MUTE_KEY,
    COIN_COLOR,
    LIFE_COLOR,
    HEART_POINTS,
    CRUMBLE_COLOR,
    MAGNET_COLOR,
    SHIELD_COLOR,
    GEM_COLOR,
    GEMS_PER_STAR,
    GEM_RECORD_METERS,
    GEM_RECORD_MAX,
    SHIELD_LAVA_BOUNCE,
    POWERUP_WARN_TIME,
    LAVA_COLOR,
    DIFFICULTY_NAMES,
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    VOLUME_STEPS,
    STAGE_INTRO_TIME,
    STAGE_CLEAR_DELAY,
    UNLOCK_ALL_STAGES,
    WEB,
)
from player import Player
from level import Level
from stages import STAGE_SETS, STAGE_COUNT, stage_mode
from lava import Lava
from camera import Camera
from score import Score, draw_lives, draw_powers, draw_text
from storage import load_record, save_record, load_dict, save_dict
import screens
from title import TitleScreen
from ui import PauseButton
from skin_menu import SKIN_MENU
from ads import Ads
from lang import t, mark, LANGUAGES, language, set_language, device_language
import skins
import theme
from art import Background, shield_bubble
from controls import TouchButtons, read_controls
from effects import burst
import sound

# Toplanınca saçılan parçacıkların rengi
PICKUP_COLORS = {"heart": LIFE_COLOR, "magnet": MAGNET_COLOR, "shield": SHIELD_COLOR, "gem": GEM_COLOR}
# Kalkan sürerken karakterin etrafındaki baloncuk (her tema için bir kere hazırlanır)
SHIELD_BUBBLE = {}

# Saklanan istatistikler ve seçenekler (storage.py), ilk açılıştaki değerleriyle
STATS_DEFAULTS = {"games": 0, "climbed": 0, "coins": 0, "enemies": 0}
OPTIONS_DEFAULTS = {
    "muted": False,
    "difficulty": DEFAULT_DIFFICULTY,
    "music_volume": VOLUME_STEPS,  # ses ekranındaki çubuklar (0..VOLUME_STEPS)
    "effects_volume": VOLUME_STEPS,
    "language": "",  # "tr" / "en"; boş = cihazın dili (ayarlardan seçilince kaydedilir)
    "theme": theme.DEFAULT_THEME,  # görünüş: "retro" (Nostalji) / "modern" (theme.py)
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


def web_hash():
    # Web'de adresin # işaretinden sonrası (deneme ayarları: .../platform/#fps#reklam); bilgisayarda boş
    if WEB:
        try:
            from platform import window

            return str(window.location.hash)
        except Exception:
            pass
    return ""


def fps_wanted():
    # Kare sayacı açık mı: settings.py'de SHOW_FPS ya da web'de adresin sonunda #fps
    return SHOW_FPS or "fps" in web_hash()


def ads_test_wanted():
    # Deneme reklamı (ads.py): settings.py'de ADS_TEST ya da web'de adresin sonunda #reklam
    return ADS_TEST or "reklam" in web_hash()


def hide_web_loader():
    # Web: oyunun ilk karesi çizildi → sayfanın yükleme ekranı (web.tmpl) yavaşça kaybolsun
    try:
        from platform import window

        window.loader_done()
    except Exception:
        pass


def web_smoothing():
    # Web: telefon ekranı oyunu büyütürken Nostalji'de pikseller keskin kalsın, Modern'de yumuşak büyüsün
    if WEB:
        try:
            from platform import window

            window.canvas.style.imageRendering = "auto" if theme.modern() else "pixelated"
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
            self.text = t("{} kare/sn").format(round(fps))
            self.low_seconds = self.low_seconds + 1 if fps < LOW_FPS_LIMIT else 0
            self.frames = 0
            self.start = now

    @property
    def slow(self):
        # Tek seferlik takılma sayılmasın: 2 saniye üst üste düşük olmalı
        return self.low_seconds >= 2

    def draw(self, screen):
        draw_text(screen, self.font, self.text, center=(SCREEN_WIDTH // 2, 80))


def load_stars(mode):
    # Bir zorluğun bölüm yıldızları (storage.py): eksik/bozuk değerler 0, liste bölüm sayısına uydurulur
    saved = load_dict("stages", {"stars": []}, mode)["stars"]
    return [
        max(0, min(3, saved[i])) if i < len(saved) and isinstance(saved[i], int) else 0
        for i in range(STAGE_COUNT)
    ]


def new_game(best_height, mode, stage=None, skin=skins.DEFAULT_SKIN):
    # Yeni harita kur, karakteri başlangıç parçasındaki P noktasına koy.
    # best_height = yükseklik rekoru (haritada "Rekor" çizgisi orada çizilir),
    # mode = zorluk modunun sayıları (settings.DIFFICULTIES; bölümde stages.stage_mode): can, lav, düşman hızı...
    # stage = oynanacak bölüm (stages.py; harita hep aynı, tepede bayrak) ya da None (sonsuz, rastgele)
    # skin = karakterin görünüşü (skins.py)
    level = Level(mode, stage["seed"], stage) if stage else Level(mode)
    player = Player(*level.player_start, level.width, mode["lives"], mode["max_lives"], skin)
    camera = Camera()
    camera.follow(player.rect, level.bottom, instant=True)
    level.update(camera.top, camera.bottom)
    score = Score(level.player_start[1], best_height, level.goal_height)
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
    # Kalp bir can verir (can zaten doluysa puan); elmas cüzdana (oyun bitince); güçlendirme bir süre işe yarar
    for item in pygame.sprite.spritecollide(player, level.pickups, True):
        if item.kind == "heart":
            if not player.heal():
                score.add_bonus(HEART_POINTS)
            sounds.play("life")
        elif item.kind == "gem":
            score.add_gem()
            sounds.play("gem")
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
            burst(level.effects, player.rect.center, player.color)
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
            burst(level.effects, player.rect.center, player.color)

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
    level.goals.update()
    level.effects.update()
    if player.trail:  # efsanevi skinin izi
        player.trail.update(player.rect, player.image, player.facing)

    camera.follow(player.rect, level.bottom)
    # Yukarıya yeni parçalar ekle, aşağıda kalanları sil
    level.update(camera.top, camera.bottom)


def draw_sprites(screen, sprites, camera):
    screen_rect = screen.get_rect()
    for sprite in sprites:
        # draw_rect: çizim yeri çarpışma kutusundan farklı olabilir (ör. titreyen platform)
        screen_pos = camera.apply(getattr(sprite, "draw_rect", sprite.rect))
        if screen_pos.colliderect(screen_rect):  # sadece ekranda görüneni çiz
            screen.blit(sprite.image, screen_pos)


# Modern temada derinlik veren resimler (modern.py): platform gölgeleri, toplananların ışığı, ayak gölgesi
DEPTH = {}


def draw_shadows(screen, level, camera):
    # Modern: platformların ve blokların altına yumuşak gölge düşer
    import modern

    for tile in level.tiles:
        rect = camera.apply(tile.rect)
        if -modern.SHADOW_DEPTH < rect.bottom < SCREEN_HEIGHT:
            shadow = theme.cached(DEPTH, ("shadow", rect.width, tile.ends), lambda: modern.drop_shadow(rect.width, tile.ends))
            screen.blit(shadow, (rect.x, rect.bottom))


def draw_glows(screen, level, player, camera):
    # Modern: altınların ve toplananların arkasında hafifçe yanıp sönen ışık; yerde duranların ayağının altında gölge
    import modern

    pulse = round(190 + 65 * math.sin(pygame.time.get_ticks() / 260))
    for sprite in (*level.coins, *level.pickups):
        center = camera.apply(sprite.rect).center
        if -30 < center[1] < SCREEN_HEIGHT + 30:
            color = PICKUP_COLORS.get(getattr(sprite, "kind", None), COIN_COLOR)
            glow = theme.cached(DEPTH, ("glow", color), lambda: modern.glow_image(color, 22))
            glow.set_alpha(pulse)
            screen.blit(glow, glow.get_rect(center=center))
    feet = [enemy for enemy in level.enemies if enemy.grounded]
    if player.on_ground and player.visible:
        feet.append(player)
    for sprite in feet:
        rect = camera.apply(sprite.rect)
        if 0 < rect.bottom < SCREEN_HEIGHT + 10:
            shadow = theme.cached(DEPTH, ("feet", rect.width), lambda: modern.foot_shadow(rect.width - 6))
            screen.blit(shadow, shadow.get_rect(center=(rect.centerx, rect.bottom)))


def draw_world(screen, background, level, player, camera, score):
    # Önce gökyüzü, sonra her şeyi kameraya göre kaydırarak çiz
    background.draw(screen, camera.top)
    score.draw_record_line(screen, camera)  # rekor yüksekliği (platformların arkasında)
    # Kırık platformlar geri gelmeden az önce silik görünür
    ghosts = [crumbler for crumbler in level.crumblers if crumbler.ghost]
    if theme.modern():
        draw_shadows(screen, level, camera)
    draw_sprites(screen, [*level.goals, *level.tiles, *ghosts], camera)
    if theme.modern():
        draw_glows(screen, level, player, camera)
    sprites = [*level.springs, *level.coins, *level.pickups, *level.enemies, *level.shots, *level.effects]
    draw_sprites(screen, sprites, camera)
    # Efsanevi skinin izi karakterin arkasında
    if player.trail:
        player.trail.draw(screen, -round(camera.top))
    if player.visible:  # dokunulmazken yanıp söner
        screen.blit(player.image, camera.apply(player.rect))
    # Lav her şeyin önünde (içine düşen kaybolur)
    level.lava.draw(screen, camera)
    # Kalkan: karakterin etrafında baloncuk; bitmesine az kalınca yanıp söner
    shield = player.powers["shield"]
    if shield and (shield > POWERUP_WARN_TIME or (shield // 8) % 2 == 0):
        bubble = theme.cached(SHIELD_BUBBLE, "bubble", lambda: shield_bubble(player.rect.height // 2 + 8))
        screen.blit(bubble, bubble.get_rect(center=camera.apply(player.rect).center))


class Game:
    # Oyunun bütün durumu: hangi ekrandayız, rekorlar, seçenekler ve şu an oynanan bölüm.
    # Ekranlar (state): "title" (giriş ekranı, oyun bununla açılır), "menu" (ana menü), "play_select" (bölümler mi
    # sonsuz mu), "stages" (bölüm seçme), "skins" (karakterler), "sound" (ses ayarları), "howto" (nasıl oynanır),
    # "records" (rekorlar), "playing" (oyun), "paused" (durdu), "revive" (canlar bitti: elmasla / reklamla devam
    # teklifi), "game_over" (kaybettin), "stage_clear" (bölüm bitti), "ad" (oyuncunun seçtiği reklam oynuyor)
    def __init__(self, sounds):
        self.sounds = sounds
        # Rekorlar her zorluk modunun ayrı: asıl hedef en yüksek tırmanış (blok), ayrıca en yüksek puan
        self.best_heights = {mode: load_record("height", mode) for mode in DIFFICULTY_NAMES}
        self.high_scores = {mode: load_record("score", mode) for mode in DIFFICULTY_NAMES}
        self.stats = load_dict("stats", STATS_DEFAULTS)
        # Bölümler: her zorluğun kendi listesi (stages.STAGE_SETS); her bölümün en iyi yıldızı (0-3)
        self.stage_stars = {mode: load_stars(mode) for mode in DIFFICULTY_NAMES}
        self.stage = None  # oynanan bölümün sırası (seçili zorluğun listesinde); None = sonsuz oyun
        self.intro = 0  # bölüm başında adının görüneceği kalan kare
        self.clear_timer = 0  # bölüm bitti ekranında düğmeler çıkana kadar kalan kare
        self.clear_result = None  # bölüm bitince: yıldızlar ve şartlar (screens.draw_stage_clear)
        self.stars_shown = 0  # bölüm bitti ekranında şimdiye kadar beliren yıldız
        self.options = load_dict("options", OPTIONS_DEFAULTS)
        if self.options["difficulty"] not in DIFFICULTY_NAMES:
            self.options["difficulty"] = DEFAULT_DIFFICULTY
        # Dil (lang.py): ayarlardan seçilen, seçilmediyse telefonun / bilgisayarın dili
        chosen = self.options["language"]
        set_language(chosen if chosen in LANGUAGES else device_language(WEB))
        # Görünüş teması (theme.py): Nostalji ya da Modern — resimler hazırlanmadan önce seçilmeli
        theme.set_theme(self.options["theme"])
        self.options["theme"] = theme.current()
        web_smoothing()
        if self.options["muted"]:
            sounds.toggle_mute()
        # Ses seviyeleri: kayıttaki değer çubuklara ve seslere
        sliders = screens.SOUND_MENU.sliders
        for name in sliders:
            key = f"{name}_volume"
            self.options[key] = max(0, min(VOLUME_STEPS, self.options[key]))
            sliders[name].value = self.options[key]
        self.apply_volume()
        # Skinler: cüzdandaki altın, satın alınanlar, giyilen (skins.py); ilk açılışta cüzdan eski altınlarla dolar
        self.wardrobe = skins.Wardrobe(self.stats["coins"])
        if not self.wardrobe.owns(skins.get(self.wardrobe.selected), self.progress()):
            self.wardrobe.select(skins.DEFAULT_SKIN)  # artık açık değilse (ör. UNLOCK_ALL_SKINS kapatıldı)
        self.new_skins = []  # bu oyunda görevi tamamlanan efsaneviler (oyun sonu ekranında yazar)
        # Bu oyunda kazanılan elmas: haritada toplanan, ödül (rekor ya da yeni yıldız) ve ödülün nedeni (ekranda yazar)
        self.gems_found = 0
        self.gems_bonus = 0
        self.gems_reason = "rekor"
        self.state = "title"
        self.title = TitleScreen(WEB, self.wardrobe.selected)  # menüye geçiş bitince silinir
        self.game_over_timer = 0  # kaybettin ekranında düğmeler çıkana kadar kalan kare
        self.revived = False  # bu oyunda Devam Et kullanıldı mı (oyun başına bir kez)
        self.revive_timer = 0  # Devam Et teklifinin bitmesine kalan kare (düğmeler çıkana kadarki bekleme dahil)
        # Ödüllü reklamlar (ads.py): şimdilik sadece deneme reklamı (#reklam), yoksa hiç teklif edilmez
        self.ads = Ads(ads_test_wanted())
        self.session_games = 0  # bu açılışta biten oyun (ADS_AFTER_GAMES: önce biraz oynasın)
        self.revive_ad = None  # Devam Et'te reklam seçeneği: None (yok), "offer", "failed" (reklam gelmedi)
        self.double = None  # oyun sonunda 2 kat elmas (reklamla): None (teklif yok), "offer", "done", "failed"
        self.ad_reward = None  # oynayan reklamın ödülü: "revive" / "double" / "free_gems"
        self.ad_back = None  # reklam bitince dönülecek ekran
        self.ad_quiet = False  # reklam için ses kısıldı mı
        self.note = ""  # ekranın altında kısa bilgi yazısı ("+2 elmas!", "Şu an reklam yok...")
        self.note_timer = 0
        self.new_record = False
        self.pause_button = PauseButton()
        self.reset()

    @property
    def mode(self):
        # Seçili zorluk modu: "easy", "normal", "hard", "ultra"
        return self.options["difficulty"]

    @property
    def stages(self):
        # Seçili zorluğun bölümleri
        return STAGE_SETS[self.mode]

    @property
    def stars(self):
        # Seçili zorluğun bölüm yıldızları
        return self.stage_stars[self.mode]

    @property
    def best_height(self):
        return self.best_heights[self.mode]

    @property
    def high_score(self):
        return self.high_scores[self.mode]

    def reset(self):
        # Yeni harita kur (menünün arkasında da bu görünür): bölüm oynanıyorsa onun haritası, yoksa sonsuz oyun
        skin = self.wardrobe.selected
        if self.stage is not None:
            stage = self.stages[self.stage]
            self.level, self.player, self.camera, self.score = new_game(0, stage_mode(stage), stage, skin)
        else:
            self.level, self.player, self.camera, self.score = new_game(
                self.best_height, DIFFICULTIES[self.mode], None, skin
            )

    def unlocked(self, index):
        # Bölüm açık mı: ilki hep açık, sonrakiler bir öncekinden en az 1 yıldız alınınca
        return UNLOCK_ALL_STAGES or index == 0 or self.stars[index - 1] > 0

    def labels(self):
        # Yazısı değişen düğmeler
        return {
            "sound": mark("Ses: Kapalı") if self.sounds.muted else mark("Ses: Açık"),
            "difficulty": t("Zorluk: {}").format(t(DIFFICULTY_NAMES[self.options["difficulty"]])),
            "menu": mark("Bölümler") if self.stage is not None else mark("Ana Menü"),
            "language": t("Dil: {}").format(LANGUAGES[language()]),
            "theme": t("Tema: {}").format(t(theme.THEMES[theme.current()])),
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

    def next_language(self):
        # Ayarlar ekranındaki Dil düğmesi: sıradaki dil (Türkçe ↔ English), kaydedilir
        names = list(LANGUAGES)
        self.options["language"] = names[(names.index(language()) + 1) % len(names)]
        set_language(self.options["language"])
        self.save_options()

    def next_theme(self):
        # Ayarlar ekranındaki Tema düğmesi: Nostalji ↔ Modern, kaydedilir. Menünün arkasındaki harita ve karakter
        # yeni temanın resimleriyle yeniden kurulur
        names = list(theme.THEMES)
        theme.set_theme(names[(names.index(theme.current()) + 1) % len(names)])
        self.options["theme"] = theme.current()
        self.save_options()
        web_smoothing()
        self.reset()

    def toggle_sound(self):
        self.sounds.toggle_mute()
        self.save_options()

    def set_difficulty(self, mode):
        # Zorluk değişti (ana menüdeki düğme ya da bölümler ekranındaki sekmeler): hem sonsuz oyunu hem bölümleri belirler
        self.options["difficulty"] = mode
        self.save_options()
        self.reset()  # menünün arkasındaki bölüm ve rekor çizgisi yeni moda göre olsun

    def next_difficulty(self):
        # Kolay → Orta → Zor → Ultra Zor → Kolay ...
        names = list(DIFFICULTY_NAMES)
        self.set_difficulty(names[(names.index(self.mode) + 1) % len(names)])

    def all_stars(self):
        # Bütün zorlukların bölüm yıldızları tek listede (toplam için)
        return [star for stars in self.stage_stars.values() for star in stars]

    def progress(self):
        # Efsanevi skinlerin görevleri için sayılar (skins.py goal): toplamlar, yıldızlar, her modun tırmanış rekoru
        return {
            "games": self.stats["games"],
            "climbed": self.stats["climbed"],
            "enemies": self.stats["enemies"],
            "coins": self.stats["coins"],
            "stars": sum(self.all_stars()),
            **{f"height-{mode}": best for mode, best in self.best_heights.items()},
        }

    def wear(self, skin_id):
        # Skini giy: kaydedilir, menünün arkasındaki karakter de hemen değişir
        self.wardrobe.select(skin_id)
        self.player.set_skin(skin_id)

    def last_unlocked(self):
        return max(i for i in range(STAGE_COUNT) if self.unlocked(i))

    def start(self, stage=None):
        # Yeni oyuna başla: stage = bölümün sırası, None = sonsuz oyun
        self.stage = stage
        self.reset()
        self.state = "playing"
        self.revived = False
        self.new_skins = []
        self.gems_found = self.gems_bonus = 0
        self.intro = STAGE_INTRO_TIME if stage is not None else 0
        self.sounds.play("start")
        self.sounds.start_music()

    def to_menu(self):
        # Oyundan çık: bölümdeysen bölüm seçme ekranına, sonsuz oyundaysan ana menüye
        if self.stage is not None:
            self.open_stages()
            return
        if self.state == "game_over":
            self.sounds.start_music()  # kaybedince durmuştu
        self.reset()
        self.state = "menu"

    def open_stages(self):
        # Bölüm seçme ekranı: bitirilen bölümün sonrakisi, oynanan bölüm ya da açık olan son bölüm seçili gelir
        if self.state in ("game_over", "stage_clear"):
            self.sounds.start_music()  # oyun bitince durmuştu
        if self.state == "stage_clear" and self.stage + 1 < STAGE_COUNT:
            focus = self.stage + 1
        elif self.stage is not None:
            focus = self.stage
        else:
            focus = self.last_unlocked()
        screens.STAGE_GRID.set_focus(focus)
        if self.stage is not None:
            self.stage = None
            self.reset()  # arkada yine sonsuz oyunun haritası
        self.state = "stages"

    def clear_stage(self):
        # Bayrağa ulaştı: yıldızları hesapla, en iyisini kaydet, sıradaki bölümün kilidini aç
        coins_total = self.level.coins_total
        enough_coins = self.score.coins >= screens.stars_needed(coins_total)
        no_hurt = self.player.hurts == 0
        stars = 1 + enough_coins + no_hurt
        has_next = self.stage + 1 < STAGE_COUNT
        next_was_locked = has_next and not self.unlocked(self.stage + 1)
        new_stars = max(0, stars - self.stars[self.stage])  # ilk kez kazanılan yıldızlar elmas verir
        if stars > self.stars[self.stage]:
            self.stars[self.stage] = stars
            save_dict("stages", {"stars": self.stars}, self.mode)
        self.clear_result = {
            "stars": stars,
            "coins": self.score.coins,
            "coins_total": coins_total,
            "no_hurt": no_hurt,
            "unlocked": next_was_locked and self.unlocked(self.stage + 1),
        }
        self.state = "stage_clear"
        self.clear_timer = STAGE_CLEAR_DELAY
        self.stars_shown = 0
        self.sounds.stop_music()
        self.sounds.play("win")
        for goal in self.level.goals:
            burst(self.level.effects, goal.rect.center, COIN_COLOR)
        self.finish(gem_bonus=new_stars * GEMS_PER_STAR)
        self.offer_double()

    def lose(self):
        # Canlar bitti: oyun başına bir kez "Devam Et?" teklifi (cüzdanda elmas yetiyorsa ya da reklam izlenebiliyorsa),
        # yoksa hemen kaybettin
        self.sounds.stop_music()
        can_pay = self.wardrobe.balance("gems") >= REVIVE_GEMS
        self.revive_ad = "offer" if self.ads_allowed() else None
        if self.revived or not (can_pay or self.revive_ad):
            self.game_over()
            return
        self.state = "revive"
        self.revive_timer = REVIVE_TIME + GAME_OVER_DELAY  # düğmeler GAME_OVER_DELAY kare sonra çıkar
        screens.revive_buttons(self.revive_ad).focus = 0 if can_pay else 1  # elmas yetmiyorsa reklam seçili

    def revive(self, paid=True):
        # Devam Et: elmas cüzdandan düşer (paid; reklam izlendiyse bedava); karakter son durduğu güvenli yerde 1 canla,
        # bir süre dokunulmaz devam eder, lav aşağı çekilir
        if paid and not self.wardrobe.spend("gems", REVIVE_GEMS):
            self.sounds.play("powerdown")  # elmas yetmiyor (düğme gri)
            return
        self.revived = True
        player = self.player
        player.lives = 1
        player.respawn()
        player.invincible = REVIVE_INVINCIBLE
        self.level.lava.push_back(player.rect.bottom)
        burst(self.level.effects, player.rect.center, GEM_COLOR)
        self.state = "playing"
        self.sounds.play("powerup")
        self.sounds.start_music()

    def game_over(self):
        # Kaybettin ekranı; oyun burada kaydedilir (rekor, toplamlar, cüzdan)
        self.state = "game_over"
        self.game_over_timer = GAME_OVER_DELAY
        self.sounds.play("game_over")
        self.finish()
        self.offer_double()

    def end_buttons(self):
        # Oyun sonu ekranının düğmeleri (kaybettin / bölüm bitti), 2 kat elmas teklifi varsa onunla
        if self.state == "stage_clear":
            kind = "clear" if self.stage + 1 < STAGE_COUNT else "last_clear"
        else:
            kind = "game_over"
        return screens.end_buttons(kind, self.double)

    def offer_double(self):
        # Oyun sonunda: bu oyunda elmas kazanıldıysa reklamla 2 katı teklif edilir (reklam varsa); düğmeler sıfırlanır
        earned = self.gems_found + self.gems_bonus
        self.double = "offer" if earned > 0 and self.ads_allowed() else None
        self.end_buttons().focus = 0

    def ads_allowed(self):
        # Reklam teklif edilebilir mi: reklam sistemi var ve oyuncu bu açılışta en az ADS_AFTER_GAMES oyun bitirdi
        return self.ads.available() and self.session_games >= ADS_AFTER_GAMES

    def free_gems_offer(self):
        # Karakterler ekranında reklamla bedava elmas: kaç elmas (0 = teklif yok; günde FREE_GEM_ADS kez)
        return FREE_GEMS if self.ads_allowed() and self.ads.free_gems_left() > 0 else 0

    def watch_ad(self, reward):
        # Oyuncu ödüllü reklamı seçti: oyun durur, reklam oynar ("ad"); bitince end_ad ödülü verir
        self.ad_reward = reward
        self.ad_back = self.state
        self.state = "ad"
        self.ads.show()

    def quiet_for_ad(self, quiet):
        # Reklam oynarken oyunun sesi kısılır, bitince ayarlardaki seviyesine döner
        if quiet != self.ad_quiet:
            self.ad_quiet = quiet
            if quiet:
                self.sounds.set_levels(0, 0)
            else:
                self.apply_volume()

    def end_ad(self, watched):
        # Reklam bitti: sonuna kadar izlendiyse ödül, yoksa "reklam yok" (ödül yok, düğme gri)
        self.quiet_for_ad(False)
        self.state = self.ad_back
        reward = self.ad_reward
        if not watched:
            self.show_note("Şu an reklam yok, sonra tekrar dene")  # draw_note çevirir
            if reward == "revive":
                self.revive_ad = "failed"
            elif reward == "double":
                self.double = "failed"
            return
        if reward == "revive":
            self.revive(paid=False)
            return
        gems = self.gems_found + self.gems_bonus if reward == "double" else FREE_GEMS
        self.wardrobe.add_money(gems=gems)
        if reward == "double":
            self.double = "done"
        else:
            self.ads.count_free_gems()
            SKIN_MENU.celebrate()
        self.sounds.play("gem")
        self.show_note(t("+{} elmas!", gems).format(gems))

    def show_note(self, text):
        self.note = text
        self.note_timer = NOTE_TIME

    def finish(self, ended=True, gem_bonus=0):
        # Oyun bitti (kaybetti, bölümü bitirdi ya da yarıda menüye döndü): bu modun rekorlarını ve toplamları
        # kaydet. Bölümlerde rekor tutulmaz (sonsuz oyunun rekorları değişmez), sadece toplamlar.
        # Toplanan altın ve elmaslar cüzdana eklenir; sonsuz oyunda rekor kırınca her GEM_RECORD_METERS m için
        # 1 elmas (en az 1, en fazla GEM_RECORD_MAX; o moddaki ilk oyunda — rekor 0 — yok), gem_bonus = bölümde yeni
        # yıldızların elması. ended = oyun sonu ekranı çıkacak mı (görevi yeni tamamlanan efsaneviler orada yazar;
        # yarıda bırakınca bir sonraki oyunun sonunda)
        score = self.score
        endless = self.stage is None
        self.new_record = endless and score.new_record  # yükseklik rekoru
        if self.new_record:
            if score.record > 0:
                gem_bonus += min(GEM_RECORD_MAX, max(1, (score.height - score.record) // GEM_RECORD_METERS))
            self.best_heights[self.mode] = score.height
            save_record("height", score.height, self.mode)
        if endless and score.total > self.high_score:
            self.high_scores[self.mode] = score.total
            save_record("score", score.total, self.mode)
        self.stats["games"] += 1
        self.session_games += 1
        self.stats["climbed"] += score.height
        self.stats["coins"] += score.coins
        self.stats["enemies"] += score.enemies
        save_dict("stats", self.stats)
        self.gems_found, self.gems_bonus = score.gems, gem_bonus
        self.gems_reason = "rekor" if endless else "yıldız"
        self.wardrobe.add_money(score.coins, score.gems + gem_bonus)
        if ended:
            self.new_skins = self.wardrobe.new_unlocks(self.progress())

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
                self.state = "play_select"
                screens.PLAY_BUTTONS.focus = 0
            elif action == "skins":
                self.state = "skins"
                SKIN_MENU.open(self.wardrobe.selected)
                SKIN_MENU.offer = self.free_gems_offer()
            elif action == "difficulty":
                self.next_difficulty()
            elif action == "sound_menu":
                self.state = "sound"
                screens.SOUND_MENU.open()
            elif action in ("howto", "records"):
                self.state = action
                screens.BACK_BUTTON.focus = 0

        elif self.state == "play_select":
            action = screens.PLAY_BUTTONS.handle_event(event)
            if key == pygame.K_ESCAPE or action == "back":
                self.state = "menu"
            elif action == "stages":
                self.open_stages()
            elif action == "endless":
                self.start()

        elif self.state == "stages":
            choice = screens.STAGE_GRID.handle_event(event, self.unlocked, self.mode)
            if key == pygame.K_ESCAPE or choice == "back":
                self.state = "play_select"
            elif choice in DIFFICULTY_NAMES:  # üstteki sekmelerden zorluk değişti
                self.set_difficulty(choice)
                if screens.STAGE_GRID.focus >= 0:  # sekmeler seçili değilse o zorluğun açık son bölümü seçilsin
                    screens.STAGE_GRID.set_focus(self.last_unlocked())
            elif choice == "locked":
                self.sounds.play("powerdown")
            elif choice is not None:
                self.start(choice)

        elif self.state == "stage_clear" and self.clear_timer == 0:
            action = self.end_buttons().handle_event(event)
            if action == "double":
                self.double_gems()
            elif action == "next":
                self.start(self.stage + 1)
            elif action == "again":
                self.start(self.stage)
            elif action == "stages" or key == pygame.K_ESCAPE:
                self.open_stages()

        elif self.state == "skins":
            result = SKIN_MENU.handle_event(event, self.wardrobe, self.progress())
            if key == pygame.K_ESCAPE or result == "back":
                self.state = "menu"
            elif result == "free_gems":
                if self.free_gems_offer():
                    self.watch_ad("free_gems")
            elif result:
                self.choose_skin(*result)

        elif self.state == "sound":
            action = screens.SOUND_MENU.handle_event(event)
            if key == pygame.K_ESCAPE or action == "back":
                self.state = "menu"
            elif action == "sound":
                self.toggle_sound()
            elif action == "language":
                self.next_language()
            elif action == "theme":
                self.next_theme()
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
                self.finish(ended=False)
                self.to_menu()

        elif self.state == "revive" and self.revive_timer <= REVIVE_TIME:  # düğmeler çıktıysa
            action = screens.revive_buttons(self.revive_ad).handle_event(event)
            if action == "revive":
                self.revive()
            elif action == "revive_ad":
                if self.revive_ad == "offer":
                    self.watch_ad("revive")
            elif action == "give_up" or key in PAUSE_KEYS:
                self.game_over()

        elif self.state == "game_over" and self.game_over_timer == 0:
            action = self.end_buttons().handle_event(event)
            if action == "double":
                self.double_gems()
            elif action == "again":
                self.start(self.stage)
            elif action == "menu" or key == pygame.K_ESCAPE:
                self.to_menu()
        return True

    def double_gems(self):
        # Oyun sonunda "2 Kat" düğmesi: reklamı izleyince bu oyunda kazanılan elmas bir kez daha verilir
        if self.double == "offer":
            self.watch_ad("double")

    def choose_skin(self, action, skin_id):
        # Karakterler ekranında bir şeye basıldı (skin_menu.py): giy, satın al, ya da olmadı (kilitli / altın yetmedi)
        if action == "select":
            self.wear(skin_id)
            self.sounds.play("coin")
        elif action == "buy":
            if self.wardrobe.buy(skins.get(skin_id)):
                self.player.set_skin(skin_id)
                SKIN_MENU.celebrate()
                self.sounds.play("buy")
        elif action in ("locked", "poor"):
            self.sounds.play("powerdown")

    def update(self, steps, touch):
        # Oyun, geçen süre kadar adım ilerler (StepTimer)
        self.note_timer = max(0, self.note_timer - steps)
        if self.state == "playing":
            controls = read_controls(touch)
            for _ in range(steps):
                update_game(self.level, self.player, self.camera, self.score, controls, self.sounds)
                self.intro = max(0, self.intro - 1)
                # Bayrağa değdi → bölüm bitti
                if pygame.sprite.spritecollideany(self.player, self.level.goals):
                    self.clear_stage()
                    break
                # Can bitti → Devam Et teklifi ya da kaybettin ekranı
                if self.player.lives <= 0:
                    self.lose()
                    break
        elif self.state == "revive":
            # Teklif süresi biter → kaybettin; bu arada ölünce saçılan parçacıklar uçmaya devam eder
            self.revive_timer = max(0, self.revive_timer - steps)
            for _ in range(steps):
                self.level.effects.update()
            if self.revive_timer == 0:
                self.game_over()
        elif self.state == "game_over":
            self.game_over_timer = max(0, self.game_over_timer - steps)
        elif self.state == "skins":
            SKIN_MENU.offer = self.free_gems_offer()
            SKIN_MENU.update(steps)
        elif self.state == "ad":
            # Reklam oynuyor: oyun bekler, ses kısılır; bitince ödül (ya da "reklam yok")
            result = self.ads.update(steps)
            self.quiet_for_ad(self.ads.playing)
            if result:
                self.end_ad(result == "done")
        elif self.state == "stage_clear":
            # Yıldızlar sırayla belirir (her biri bir "çın" sesiyle), sonra düğmeler çıkar
            self.clear_timer = max(0, self.clear_timer - steps)
            for _ in range(steps):
                self.level.effects.update()
                self.level.goals.update()
            shown = min(self.clear_result["stars"], (STAGE_CLEAR_DELAY - self.clear_timer) // 18)
            if shown > self.stars_shown:
                self.stars_shown = shown
                self.sounds.play("coin")
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
        if self.state == "ad":
            self.ads.draw(screen)
            return
        # Oyun dünyası diğer her ekranda arkada görünür
        draw_world(screen, background, self.level, self.player, self.camera, self.score)
        if self.state in ("menu", "title"):
            screens.draw_main_menu(screen, self.best_height, self.labels(), WEB)
            if self.state == "title":
                self.title.draw_fading(screen, background)
        elif self.state == "play_select":
            screens.draw_play_select(
                screen, self.labels(), DIFFICULTY_NAMES[self.mode], self.all_stars(), self.best_height
            )
        elif self.state == "stages":
            screens.draw_stages(screen, self.mode, self.stars, self.unlocked)
        elif self.state == "skins":
            screens.draw_overlay(screen)
            SKIN_MENU.draw(screen, self.wardrobe, self.progress())
        elif self.state == "sound":
            screens.SOUND_MENU.draw(screen, self.labels(), self.sounds.muted)
        elif self.state == "howto":
            screens.draw_howto(screen)
        elif self.state == "records":
            screens.draw_records(
                screen, self.best_heights, self.high_scores, self.stats, self.mode, self.all_stars()
            )
        else:
            # Puan ve canlar kameradan bağımsız: hep ekranın üst köşelerinde
            self.score.draw(screen)
            draw_lives(screen, self.player.lives, self.player.max_lives)
            draw_powers(screen, self.player)
            if self.state == "playing":
                touch.draw(screen)
                self.pause_button.draw(screen)
                if self.intro:
                    screens.draw_stage_intro(screen, self.mode, self.stage, self.score.goal)
            elif self.state == "paused":
                screens.draw_pause(screen, self.labels())
            elif self.state == "revive":
                time_left = self.revive_timer / REVIVE_TIME if self.revive_timer <= REVIVE_TIME else None
                screens.draw_revive(screen, self.score, self.wardrobe.balance("gems"), time_left, self.revive_ad)
            elif self.state == "stage_clear":
                screens.draw_stage_clear(screen, self.mode, self.stage, self.clear_result, self.stars_shown)
            elif self.state == "game_over" and self.stage is not None:
                screens.draw_stage_failed(screen, self.mode, self.stage, self.score, slow)
            elif self.state == "game_over":
                screens.draw_game_over(
                    screen,
                    self.score,
                    DIFFICULTY_NAMES[self.mode],
                    self.best_height,
                    self.high_score,
                    self.new_record,
                    slow,
                )
            # Oyun sonu düğmeleri biraz bekledikten sonra çıkar (yanlışlıkla basılmasın)
            ready = self.game_over_timer == 0 if self.state == "game_over" else self.clear_timer == 0
            if self.state in ("game_over", "stage_clear") and ready:
                stage_failed = self.state == "game_over" and self.stage is not None
                earned = self.gems_found + self.gems_bonus
                screens.draw_end_buttons(screen, self.end_buttons(), stage_failed, self.double, earned)
            if self.state in screens.NEW_SKIN_Y:  # görevle yeni açılan efsanevi skin, kazanılan elmas
                screens.draw_new_skins(screen, self.new_skins, screens.NEW_SKIN_Y[self.state])
                end_screen = "stage_failed" if self.state == "game_over" and self.stage is not None else self.state
                screens.draw_gems_earned(
                    screen, self.gems_found, self.gems_bonus, self.gems_reason, screens.GEMS_EARNED_Y[end_screen]
                )
        if self.note_timer:  # kısa bilgi ("+2 elmas!", "Şu an reklam yok...")
            screens.draw_note(screen, self.note)


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
    sounds.start_music()
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
