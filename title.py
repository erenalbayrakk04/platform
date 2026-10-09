# Giriş ekranı: oyun açılınca ilk görünen ekran. Üstte oyunun adı (piksel harfler: yukarıdan düşüp zıplayarak
# yerine oturur, sonra dalgalanır), ortada uçan adacıkta gezinip zıplayan karakter, altınlar, yarasa, aşağıda
# kaynayan lav ve kıvılcımlar. Dokununca (tıklayınca / tuşa basınca) karakter yukarı fırlar, ana menü belirir.
# Web'de bu ilk dokunuş tarayıcının ses kilidini de açar (web.tmpl): müzik o an duyulmaya başlar.
# Logo ana menüde de aynı yerde çizilir (draw_logo) — geçişte yerinden oynamaz.
import math
import random

import pygame

from settings import (
    SCREEN_WIDTH,
    TITLE,
    GRAVITY,
    WHITE,
    PIXEL_SCALE,
    ANIMATION_SPEED,
    COIN_SPIN_SPEED,
    FLYER_FLAP_SPEED,
    FLYER_BOB,
    FLYER_BOB_SPEED,
    LAVA_ANIM_SPEED,
    LAVA_COLOR,
    LAVA_TOP_COLOR,
    MENU_SMALL_FONT_SIZE,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    BUTTON_FONT_SIZE,
    BUTTON_FOCUS_COLOR,
    BUTTON_FOCUS_BORDER_COLOR,
    LOGO_PIXEL,
    LOGO_TOP,
    LOGO_LINE_GAP,
    LOGO_COLORS,
    LOGO_WAVE,
    LOGO_WAVE_TIME,
    LOGO_SHINE_TIME,
    TITLE_SCALE,
    TITLE_WALK_SPEED,
    TITLE_HOP_TIME,
    TITLE_HOP_POWER,
    TITLE_LAUNCH_POWER,
    TITLE_LEAVE_TIME,
    TITLE_EMBER_CHANCE,
)
import art
import skins
from score import draw_text
from trail import Trail
from ui import click_pos, take_click

# Ekrandaki yerleşim (y = yukarıdan piksel)
TAGLINE_Y = 256  # logonun altındaki yazı
BAT_Y = 312  # yarasanın uçtuğu yükseklik
ISLAND_Y = 470  # adacığın üst yüzü (karakter bunun üstünde durur)
COIN_SPOTS = ((52, 440), (88, 384), (312, 384), (348, 440))  # adacığın iki yanında süzülen altınlar
BUTTON_Y = 612  # "Dokun ve Başla" düğmesinin ortası
LAVA_Y = 674  # lavın yüzeyi
TAGLINE = "Lavdan kaç, en yükseğe tırman!"
REST_TIME = 50  # karakter adacığın ucunda kaç kare durup sonra döner
BAT_SPEED = 1.3  # yarasa her karede kaç piksel uçar
# Logo harfleri sırayla yukarıdan düşer: ilki kaç kare sonra (web'de yükleme ekranı bu sırada kaybolur),
# aralarında kaç kare, düşüş kaç kare sürer, nereden (piksel yukarıdan)
DROP_DELAY = 36
DROP_STAGGER = 3
DROP_TIME = 32
DROP_HEIGHT = 260
# Logonun üstünden geçen parıltı: geçişi kaç saniye sürer, şeridin genişliği, eğikliği (aşağı indikçe sola kayar)
SHINE_SWEEP = 0.7
SHINE_WIDTH = 16
SHINE_SLANT = 0.5


class Logo:
    # Oyunun adı iki satır ("PLATFORM" / "OYUNU"), her harf ayrı resim (art.logo_letters): harfler sırayla
    # aşağı yukarı dalgalanır, arada bir üstlerinden çapraz bir parıltı geçer
    def __init__(self):
        self.letters = []  # [(resim, parıltı, x, y)] — ekrandaki yerleri (dalgalanmadan)
        top = LOGO_TOP
        for i, line in enumerate(TITLE.upper().split()):
            top_color, bottom_color = LOGO_COLORS[i % len(LOGO_COLORS)]
            letters = art.logo_letters(line, top_color, bottom_color)
            last_image, _, last_x = letters[-1]
            left = (SCREEN_WIDTH - last_x - last_image.get_width()) // 2
            self.letters += [(image, shine, left + x, top) for image, shine, x in letters]
            top += last_image.get_height() + LOGO_LINE_GAP
        self.left = min(x for _, _, x, _ in self.letters)
        self.right = max(x + image.get_width() for image, _, x, _ in self.letters)
        self.height = top - LOGO_LINE_GAP - LOGO_TOP

    def draw(self, screen, drop=None):
        # drop(i) = i. harf şu an kaç piksel yukarıda (giriş ekranında harfler düşerek gelir)
        seconds = pygame.time.get_ticks() / 1000
        # Parıltı her LOGO_SHINE_TIME saniyede bir soldan sağa geçer; shine_x = şeridin en üstteki yeri
        sweep = (seconds % LOGO_SHINE_TIME) / SHINE_SWEEP
        shine_x = None
        if sweep < 1:
            start = self.left - SHINE_WIDTH
            end = self.right + self.height * SHINE_SLANT
            shine_x = start + (end - start) * sweep
        for i, (image, shine, x, y) in enumerate(self.letters):
            y += round(LOGO_WAVE * math.sin(2 * math.pi * seconds / LOGO_WAVE_TIME - i * 0.6))
            if drop:
                y -= drop(i)
            screen.blit(image, (x, y))
            if shine_x is not None:
                self.draw_shine(screen, shine, x, y, shine_x)

    def draw_shine(self, screen, shine, x, y, shine_x):
        # Harfin parıltı resminin sadece şeridin içinde kalan kısmı çizilir; şerit eğik olduğu için ince ince
        width, height = shine.get_size()
        strip = 2 * LOGO_PIXEL
        for top in range(0, height, strip):
            left = round(shine_x - (y + top - LOGO_TOP) * SHINE_SLANT) - x  # şeridin bu satırdaki yeri (harfe göre)
            area = pygame.Rect(left, top, SHINE_WIDTH, strip).clip((0, 0, width, height))
            if area.width:
                screen.blit(shine, (x + area.x, y + area.y), area)


_logo = []


def logo():
    # Logo ilk kullanımda bir kere hazırlanır (pygame açıldıktan sonra)
    if not _logo:
        _logo.append(Logo())
    return _logo[0]


def draw_logo(screen, drop=None):
    logo().draw(screen, drop)


def bounce(p):
    # 0'dan 1'e giden, sonunda birkaç kez sekerek duran hareket (p = geçen süre, 0-1 arası)
    if p < 1 / 2.75:
        return 7.5625 * p * p
    if p < 2 / 2.75:
        p -= 1.5 / 2.75
        return 7.5625 * p * p + 0.75
    if p < 2.5 / 2.75:
        p -= 2.25 / 2.75
        return 7.5625 * p * p + 0.9375
    p -= 2.625 / 2.75
    return 7.5625 * p * p + 0.984375


def scaled(image):
    # Giriş ekranında resimler TITLE_SCALE kat büyük (düz büyütme: pikseller keskin kalır)
    width, height = image.get_size()
    return pygame.transform.scale(image, (width * TITLE_SCALE, height * TITLE_SCALE))


def button_glow(rect):
    # Düğmenin etrafındaki yumuşak altın ışık: içe doğru koyulaşan iç içe yuvarlak kutular
    glow = pygame.Surface(rect.inflate(28, 28).size, pygame.SRCALPHA)
    for i, alpha in enumerate((25, 45, 70, 100)):
        box = glow.get_rect().inflate(-6 * i, -6 * i)
        pygame.draw.rect(glow, (*BUTTON_FOCUS_BORDER_COLOR, alpha), box, border_radius=28 - 3 * i)
    return glow


class TitleScreen:
    def __init__(self, web, skin=skins.DEFAULT_SKIN):
        # web = tarayıcıda mı (telefonda "dokun", bilgisayarda "tıkla" yazsın), skin = giyilen skin (skins.py)
        self.button_text = "Dokun ve Başla" if web else "Tıkla ve Başla"
        self.time = 0  # ekrana geleli kaç adım (kare) oldu
        self.leaving = 0  # dokunulalı kaç adım oldu (0 = henüz dokunulmadı)
        self.rng = random.Random()
        # Resimler oyundakilerin aynısı (art.py); karakter, adacık ve altınlar büyük, yarasa uzakta (küçük)
        self.player = {
            name: {side: scaled(image) for side, image in pair.items()} for name, pair in skins.frames(skin).items()
        }
        trail = skins.get(skin)["trail"]
        self.trail = Trail(trail, TITLE_SCALE) if trail else None  # efsanevi skinin izi
        self.island = scaled(art.island_image())
        self.coins = [scaled(image) for image in art.coin_frames()]
        self.bat = art.flyer_frames()
        self.waves = art.lava_frames()
        glow = art.lava_glow()
        self.lava_glow = pygame.transform.scale(glow, (glow.get_width(), glow.get_height() * 2))
        self.font = pygame.font.Font(None, MENU_SMALL_FONT_SIZE + 4)
        self.button_font = pygame.font.Font(None, BUTTON_FONT_SIZE)
        self.button = pygame.Rect(0, 0, BUTTON_WIDTH + 20, BUTTON_HEIGHT + 4)
        self.glow = button_glow(self.button)
        self.layer = None  # menüye geçerken giriş ekranı önce buraya çizilir (yavaşça silinebilsin diye)
        # Karakter adacıkta: x = ortası, lift = ayağının adacıktan yüksekliği, vy = dikey hız (yukarı +)
        self.x = SCREEN_WIDTH / 2
        self.facing = 1
        self.lift = 0.0
        self.vy = 0.0
        self.rest = 0  # adacığın ucunda daha kaç kare bekleyecek
        self.walk_range = (self.island.get_width() - self.player["idle"][1].get_width()) / 2 + 4
        self.bat_x = -40.0
        self.embers = []  # lavdan yükselen kıvılcımlar: [x, y, yatay hız, dikey hız, yaş, ömür]
        # Parıldayan yıldızlar: (x, y, faz) — hep aynı yerlerde
        stars = random.Random(3)
        self.twinkles = [
            (stars.randrange(16, SCREEN_WIDTH - 16), stars.randrange(20, 420), stars.uniform(0, 6.3)) for _ in range(10)
        ]
        # Logonun son harfi yerine oturunca alttaki yazı ve düğme görünür
        self.ready_time = DROP_DELAY + (len(logo().letters) - 1) * DROP_STAGGER + DROP_TIME

    def handle_event(self, event):
        # Dokunma / tıklama / tuş: karakter fırlar, menüye geçiş başlar. Başladıysa True döner (main.py ses çalar)
        if self.leaving or (click_pos(event) is None and event.type != pygame.KEYDOWN):
            return False
        if not take_click():  # aynı dokunuş hem parmak hem fare olayı olarak gelebilir
            return False
        self.leaving = 1
        self.vy = TITLE_LAUNCH_POWER
        return True

    @property
    def done(self):
        # Menüye geçiş bitti mi
        return self.leaving > TITLE_LEAVE_TIME

    def update(self):
        self.time += 1
        if self.leaving:
            self.leaving += 1
            self.lift += self.vy  # yukarı fırlıyor, ekrandan çıkana kadar yavaşlamaz
        else:
            self.move_player()
        if self.trail:
            image = self.player_image()
            self.trail.update(image.get_rect(midbottom=self.player_feet()), image, self.facing)
        # Yarasa soldan sağa uçar; ekrandan çıkınca bir süre sonra soldan yine gelir
        self.bat_x += BAT_SPEED
        if self.bat_x > SCREEN_WIDTH + 300:
            self.bat_x = -40.0
        self.move_embers()

    def move_player(self):
        # Adacığın bir ucundan öbürüne yürür, uçta biraz bekleyip döner; arada bir zıplar
        if self.lift > 0 or self.vy > 0:  # havada
            self.lift += self.vy
            self.vy -= GRAVITY
            if self.lift <= 0:
                self.lift = self.vy = 0.0
        elif self.time % TITLE_HOP_TIME == 0:
            self.vy = TITLE_HOP_POWER
        if self.rest:
            self.rest -= 1
            if not self.rest:
                self.facing = -self.facing
            return
        self.x += self.facing * TITLE_WALK_SPEED
        if abs(self.x - SCREEN_WIDTH / 2) >= self.walk_range:
            self.x = SCREEN_WIDTH / 2 + self.facing * self.walk_range
            self.rest = REST_TIME

    def move_embers(self):
        # Lavdan kıvılcımlar çıkar, sağa sola salınarak yükselir ve söner
        if self.rng.random() < TITLE_EMBER_CHANCE:
            x = self.rng.uniform(0, SCREEN_WIDTH)
            speed_x, speed_y = self.rng.uniform(-0.3, 0.3), self.rng.uniform(-1.8, -0.6)
            self.embers.append([x, float(LAVA_Y), speed_x, speed_y, 0, self.rng.randint(50, 110)])
        for ember in self.embers:
            ember[0] += ember[2] + 0.3 * math.sin((self.time + ember[5] * 7) / 9)
            ember[1] += ember[3]
            ember[4] += 1
        self.embers = [ember for ember in self.embers if ember[4] < ember[5]]

    def drop(self, i):
        # Logonun i. harfi şu an kaç piksel yukarıda: sırayla düşer, sekerek yerine oturur
        p = (self.time - DROP_DELAY - i * DROP_STAGGER) / DROP_TIME
        if p >= 1:
            return 0
        return round((1 - bounce(max(0.0, p))) * DROP_HEIGHT)

    # --- Çizim ---
    def draw(self, screen, background):
        background.draw(screen, 0)  # oyunun başındaki gökyüzü ve yıldızlar
        self.draw_twinkles(screen)
        frame = self.bat[(self.time // FLYER_FLAP_SPEED) % len(self.bat)]
        bat_y = BAT_Y + FLYER_BOB * math.sin(self.time / FLYER_BOB_SPEED)
        screen.blit(frame, frame.get_rect(center=(round(self.bat_x), round(bat_y))))
        screen.blit(self.lava_glow, (0, LAVA_Y - self.lava_glow.get_height()))
        self.draw_island(screen)
        self.draw_lava(screen)
        # Harfler düşerken dalgalanmasın diye drop verilir; menüye geçerken harfler hep yerinde
        draw_logo(screen, None if self.leaving else self.drop)
        if self.time >= self.ready_time:
            draw_text(screen, self.font, TAGLINE, WHITE, center=(SCREEN_WIDTH // 2, TAGLINE_Y))
            if not self.leaving:
                self.draw_button(screen)

    def draw_twinkles(self, screen):
        # Arada bir parlayıp sönen yıldızlar: parladıkça "+" şeklinde kolları uzar
        for x, y, phase in self.twinkles:
            light = math.sin(self.time / 30 + phase)
            if light < 0.4:
                continue
            arm = 4 if light > 0.85 else 2
            color = (255, 250, 210)
            screen.fill(color, (x - arm, y, 2 * arm + 2, 2))
            screen.fill(color, (x, y - arm, 2, 2 * arm + 2))

    def island_top(self):
        # Adacık havada hafifçe süzülür
        return ISLAND_Y + round(3 * math.sin(self.time / 45))

    def player_feet(self):
        return round(self.x), self.island_top() - round(self.lift)

    def player_image(self):
        if self.lift > 0 or self.leaving:
            name = "jump"
        elif self.rest:
            name = "idle"
        else:
            name = "walk1" if (self.time // ANIMATION_SPEED) % 2 == 0 else "walk2"
        return self.player[name][self.facing]

    def draw_island(self, screen):
        # Havada hafifçe süzülen adacık, iki yanında dönen altınlar, üstünde karakter (efsanevi skinse arkasında izi)
        screen.blit(self.island, self.island.get_rect(midtop=(SCREEN_WIDTH // 2, self.island_top())))
        coin = self.coins[(self.time // COIN_SPIN_SPEED) % len(self.coins)]
        for i, (x, y) in enumerate(COIN_SPOTS):
            screen.blit(coin, coin.get_rect(center=(x, y + round(4 * math.sin(self.time / 30 + i * 1.7)))))
        if self.trail:
            self.trail.draw(screen)
        image = self.player_image()
        screen.blit(image, image.get_rect(midbottom=self.player_feet()))

    def draw_lava(self, screen):
        # Ekranın dibinde kaynayan lav (oyundaki gibi dalgalı) ve içinden yükselen kıvılcımlar
        frame = self.waves[(self.time // LAVA_ANIM_SPEED) % len(self.waves)]
        wave_top = LAVA_Y - 2 * PIXEL_SCALE
        screen.blit(frame, (0, wave_top))
        body_top = wave_top + frame.get_height()
        screen.fill(LAVA_COLOR, (0, body_top, SCREEN_WIDTH, screen.get_height() - body_top))
        for x, y, _, _, age, life in self.embers:
            old = age / life
            color = art.mix(LAVA_TOP_COLOR, LAVA_COLOR, min(1.0, old * 1.5))
            size = 4 if old < 0.5 else 2
            screen.fill(color, (round(x), round(y), size, size))

    def draw_button(self, screen):
        # "Dokun ve Başla": menüdeki seçili düğme gibi; yavaşça nefes alır (etrafı parlayıp söner, hafifçe süzülür)
        pulse = (math.sin(self.time / 16) + 1) / 2  # 0-1 arası
        self.button.center = (SCREEN_WIDTH // 2, BUTTON_Y + round(2 * math.sin(self.time / 16)))
        self.glow.set_alpha(round(80 + 175 * pulse))
        screen.blit(self.glow, self.glow.get_rect(center=self.button.center))
        pygame.draw.rect(screen, BUTTON_FOCUS_COLOR, self.button, border_radius=16)
        border = art.mix(BUTTON_FOCUS_BORDER_COLOR, WHITE, pulse * 0.6)
        pygame.draw.rect(screen, border, self.button, 3, border_radius=16)
        draw_text(screen, self.button_font, self.button_text, center=self.button.center)

    def draw_fading(self, screen, background):
        # Menüye geçerken giriş ekranı, altta çizilmiş menünün üstünde yavaşça silinir (önce yavaş, sonra hızlı)
        if self.layer is None:
            self.layer = pygame.Surface(screen.get_size()).convert()
        self.draw(self.layer, background)
        progress = min(1.0, self.leaving / TITLE_LEAVE_TIME)
        self.layer.set_alpha(round(255 * (1 - progress * progress)))
        screen.blit(self.layer, (0, 0))
