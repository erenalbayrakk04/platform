# Modern tema (theme.py): oyunun resimleri yumuşak kenarlı, renk geçişli ve parlak çizilir. Nostalji temasının
# piksel sanatı art.py'de; modern temada art.py'deki fonksiyonlar buradaki aynı adlı fonksiyonları çağırır.
# - Karakterler, düşmanlar, güçlendirmeler: art.py / skins.py'deki harf haritaları smooth() ile yumuşatılır (her
#   rengin bölgesi büyütülüp hafifçe bulanıklaştırılır, her nokta en baskın rengi alır: köşeler yuvarlanır,
#   merdivenler düz çizgi olur), üstüne ışık (üstü açık, altı koyu) ve gözlere parıltı eklenir. Yeni skin / düşman
#   eklenince modern hâli kendiliğinden olur.
# - Bloklar, platformlar, altın, elmas, kalp, yıldız, bayrak, yay, ateş topu, lav, gökyüzü, adacık, logo ve menü
#   kutuları doğrudan kodla (yuvarlak köşe, renk geçişi, parıltı) çizilir.
# Her şey AA kat büyük çizilip küçültülür: kenarlar yumuşak olur (kenar yumuşatma).
# Resimlerin boyları Nostalji'dekilerle AYNI olmalı: çarpışma kutuları resim boyundan geliyor (tema oyunu değiştirmez).
import math
import random

import pygame

from art import shade, tint, mix
from settings import (
    PIXEL_SCALE,
    WHITE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    TILE_COLOR,
    TILE_TOP_COLOR,
    PLATFORM_HEIGHT,
    PLATFORM_COLOR,
    COIN_SIZE,
    COIN_COLOR,
    COIN_EDGE_COLOR,
    CRUMBLE_COLOR,
    MOVING_PLATFORM_COLOR,
    SPRING_COLOR,
    GEM_COLOR,
    STAR_COLOR,
    STAR_EMPTY_COLOR,
    FLAG_COLOR,
    FIREBALL_COLOR,
    LAVA_COLOR,
    LAVA_TOP_COLOR,
    SHIELD_COLOR,
    SKY_THEMES,
    SKY_CHANGE_HEIGHT,
    SKY_BLEND_HEIGHT,
    STAR_COUNT,
    STAR_PARALLAX,
    LOGO_PIXEL,
    LOGO_OUTLINE_COLOR,
)

AA = 4  # her şey kaç kat büyük çizilip küçültülür


# --- Yardımcılar ---
def canvas(width, height):
    # AA kat büyük, saydam tuval (width, height = asıl boy, piksel)
    surface = pygame.Surface((round(width * AA), round(height * AA)), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    return surface


def bleed(big, steps=AA):
    # Saydam piksellerin rengini yandaki boyalı piksellerin rengiyle doldurur (saydamlıkları değişmez). Küçültürken
    # kenar pikselleri saydam yerlerin rengiyle ortalanır; yoksa siyahla karışıp kararırlardı
    grown = big.copy()
    for _ in range(steps):
        step = grown.copy()
        for offset in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            step.blit(grown, offset, special_flags=pygame.BLEND_RGBA_MAX)
        grown = step
    grown.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)  # her yer opak (renkler aynı)
    grown.blit(big, (0, 0))  # boyalı yerler asıl renginde
    alpha = big.copy()
    alpha.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)  # beyaz, saydamlığı asıl resminki
    grown.blit(alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return grown


def finish(big, size, opaque=False):
    # Büyük çizimi asıl boyuna küçült. opaque = hiç saydam yeri yok (blok gibi): tarayıcıda çok daha hızlı çizilir
    image = pygame.transform.smoothscale(bleed(big), (round(size[0]), round(size[1])))
    if opaque and pygame.display.get_surface():
        image = image.convert()
    return image


def fast(image):
    # Tarayıcıda yarı saydam çizim yavaş (her piksel karıştırılır). RLE: resmin tamamen saydam ve tamamen opak
    # sıraları önceden ayrılır, sadece kenarlar karıştırılır — görüntü aynı, 100 kata kadar hızlı. Sonradan
    # saydamlığı değiştirilecek (set_alpha) ya da üstüne çizilecek resimlere uygulanmaz
    image.set_alpha(255, pygame.RLEACCEL)
    return image


def fast_all(images):
    return [fast(image) for image in images]


def gradient(size, *colors):
    # Dikey renk geçişi: colors yukarıdan aşağı eşit aralıklı duraklar (renk 3 ya da 4 sayı)
    width, height = round(size[0]), round(size[1])
    stops = [tuple(color) + (255,) * (4 - len(color)) for color in colors]
    strip = pygame.Surface((1, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / max(1, height - 1) * (len(stops) - 1)
        i = min(int(t), len(stops) - 2)
        strip.set_at((0, y), mix(stops[i], stops[i + 1], t - i))
    return pygame.transform.scale(strip, (width, height))


def masked(fill, shape):
    # fill (renk ya da renk geçişi resmi) sadece shape'in (beyaz şekil) olduğu yerde kalır
    if isinstance(fill, pygame.Surface):
        layer = fill.copy()
    else:
        layer = pygame.Surface(shape.get_size(), pygame.SRCALPHA)
        layer.fill(fill)
    layer.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return layer


def ends_radius(ends, radius):
    # Yuvarlak köşeler sadece sıranın uçlarında (ends = (sol uç mu, sağ uç mu)): ortadakiler yan yana birleşir
    left, right = ends
    return {
        "border_top_left_radius": radius if left else 0,
        "border_bottom_left_radius": radius if left else 0,
        "border_top_right_radius": radius if right else 0,
        "border_bottom_right_radius": radius if right else 0,
    }


def radial(radius, inner, outer, steps=24):
    # Ortadan dışa renk geçişli daire (renkler 4 sayı: saydamlık da geçer); büyük çizim, çapı 2 * radius
    size = round(2 * radius)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((*outer[:3], 0))
    for i in range(steps, 0, -1):
        t = i / steps
        pygame.draw.circle(surface, mix(inner, outer, t), (radius, radius), radius * t)
    return surface


def thick_lines(surface, color, points, width):
    # Kalın çizgi; köşelerdeki boşluklar yuvarlak doldurulur
    pygame.draw.lines(surface, color, False, points, round(width))
    for point in points:
        pygame.draw.circle(surface, color, point, width / 2)


# --- Harf haritalarının yumuşatılması (karakterler, düşmanlar, simgeler) ---
SOFT = 4  # yumuşatma ara boyu: her kare kaç piksel (bulanıklaştırma bu küçük boyda yapılır, ucuz)
SOFT_COLORS = 1  # renk bölgelerinin bulanıklığı (ara boyda piksel): iç köşeler yuvarlanır
SOFT_OUTSIDE = 2  # dış kenarın bulanıklığı: siluet daha yuvarlak
LIGHT_TOP = 30  # üstteki ışık (renklere eklenir, 0-255)
LIGHT_BOTTOM = 0.8  # alttaki gölge (renkler bununla çarpılır)
_lights = {}


def smooth(rows, palette, size=None, zoom=1, cell=None, light=True):
    # art.render'ın modern hâli: harf haritasını ('.' saydam) yumuşak çiz. size = resmin boyu (çizim alta-ortaya
    # yaslı; zoom ile büyür), cell = bir karenin boyu (piksel; verilmezse PIXEL_SCALE * zoom),
    # light = üstü açık altı koyu ışık + gözlere (E) parıltı
    cell = cell or PIXEL_SCALE * zoom
    width, height = len(rows[0]), len(rows)
    opaque = not any("." in row for row in rows)
    if opaque:  # saydamsız resmin kenarı düz kalsın: kenar kareleri dışa kopyalanır
        grid = [row[0] + row + row[-1] for row in rows]
        grid = [grid[0]] + grid + [grid[-1]]
    else:
        grid = ["." * (width + 2)] + ["." + row + "." for row in rows] + ["." * (width + 2)]
    # Büyük çizimde bir kare (SOFT'a tam bölünmeli). Büyük resimlerde (zoom) daha az büyütmek yeter: hızlı
    unit = cell * max(2, AA // zoom)
    step = SOFT
    # Her harfin bölgesi: önce küçük resim (kare başına 1 piksel), ara boya büyütülüp bulanıklaştırılır, sonra
    # büyük boya. pygame büyütürken piksel ortalarını uçlara oturtur: boylar (n - 1) * kat seçilince kareler tam
    # yerine denk gelir
    middle = ((width + 1) * step, (height + 1) * step)
    big_size = ((middle[0] - 1) * unit // step, (middle[1] - 1) * unit // step)
    small = {}
    for r, row in enumerate(grid):
        for c, letter in enumerate(row):
            if letter not in small:
                small[letter] = pygame.Surface((width + 2, height + 2), pygame.SRCALPHA)
                small[letter].fill((255, 255, 255, 0))
            small[letter].set_at((c, r), (255, 255, 255, 255))
    fields = {}
    for letter, surface in small.items():
        field = pygame.transform.smoothscale(surface, middle)
        blur = SOFT_OUTSIDE if letter == "." else SOFT_COLORS
        if blur:
            field = pygame.transform.gaussian_blur(field, blur, True)
        fields[letter] = pygame.transform.smoothscale(field, big_size)
    strongest = None
    for field in fields.values():
        if strongest is None:
            strongest = field.copy()
        else:
            strongest.blit(field, (0, 0), special_flags=pygame.BLEND_RGBA_MAX)
    # Her nokta en baskın harfin rengini alır
    big = pygame.Surface(big_size, pygame.SRCALPHA)
    big.fill((0, 0, 0, 0))
    for letter, field in fields.items():
        if letter == ".":
            continue
        weaker = strongest.copy()
        weaker.blit(field, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        wins = pygame.mask.from_surface(weaker, 0)
        wins.invert()
        color = palette[letter]
        wins.to_surface(big, setcolor=(*color[:3], color[3] if len(color) > 3 else 255), unsetcolor=None)
    half = unit // 2
    big = big.subsurface((half, half, width * unit, height * unit)).copy()
    if light and "E" in palette and sum(palette["E"][:3]) < 300:
        eye_sparkles(big, rows, unit)
    image = finish(big, (width * cell, height * cell))
    if light:
        add_light(image)
    if size:
        size = (round(size[0] * zoom), round(size[1] * zoom))
        if size != image.get_size():
            framed = pygame.Surface(size, pygame.SRCALPHA)
            framed.fill((0, 0, 0, 0))
            framed.blit(image, ((size[0] - image.get_width()) // 2, size[1] - image.get_height()))
            image = framed
    if opaque and image.get_size() == (width * cell, height * cell) and pygame.display.get_surface():
        image = image.convert()
    return image


def eye_sparkles(big, rows, unit):
    # Göz bebeklerinin (E) her birinin sol üstüne küçük beyaz parıltı: modern, sevimli bakış
    seen = set()
    for r, row in enumerate(rows):
        for c, letter in enumerate(row):
            if letter != "E" or (r, c) in seen:
                continue
            group, todo = [], [(r, c)]
            while todo:
                cell = todo.pop()
                if cell in seen:
                    continue
                seen.add(cell)
                group.append(cell)
                y, x = cell
                for near in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= near[0] < len(rows) and 0 <= near[1] < len(row) and rows[near[0]][near[1]] == "E":
                        todo.append(near)
            top, left = min(group)
            pygame.draw.circle(big, (255, 255, 255, 255), ((left + 0.42) * unit, (top + 0.4) * unit), 0.24 * unit)


def add_light(image):
    # Üstten gelen ışık: üst kısım biraz açık, alt kısım biraz koyu (saydamlık değişmez)
    size = image.get_size()
    if size not in _lights:
        dark = gradient(size, (255, 255, 255), (255, 255, 255), [round(255 * LIGHT_BOTTOM)] * 3)
        bright = gradient(size, [LIGHT_TOP] * 3, (0, 0, 0), (0, 0, 0), (0, 0, 0))
        _lights[size] = (dark, bright)
    dark, bright = _lights[size]
    image.blit(dark, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    image.blit(bright, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


# --- Bloklar ve platformlar: yan yana olanlar tek parça, sıranın uçları yuvarlak ---
TILE_RADIUS = 9  # sıranın uçlarındaki köşelerin yuvarlaklığı (piksel)
OUTLINE = 2  # blok ve platformların dış çizgisi (piksel)
GRASS_DEPTH = 11  # çimenin kalınlığı (dalgaların ortası)
GRASS_WAVE = 20  # çimenin alt kenarındaki dalgaların genişliği (40'ı tam bölmeli: yan yana bloklar birleşsin)
PEBBLES = ((6, 22, 6, 4, True), (25, 27, 7, 5, False), (15, 33, 5, 3, True), (31, 19, 4, 3, True), (3, 31, 4, 3, False))


def grass_edge(x):
    # Çimenin alt kenarı (x piksel → y piksel)
    return GRASS_DEPTH + 2 * math.sin(2 * math.pi * x / GRASS_WAVE) + 0.8 * math.sin(4 * math.pi * x / GRASS_WAVE + 1)


def grass_layer(width, height, top=0, zoom=1):
    # Çimen (büyük çizim): yukarıdan aşağı açıktan koyuya, alt kenarı dalgalı, altında hafif gölge; en üstte parlak
    # çizgi. top = çimenin üst kenarı (piksel), zoom = kaç kat büyük
    s = AA * zoom  # bir pikselin büyük çizimdeki boyu
    big = canvas(width * zoom, height * zoom)
    w = width * s
    edge = [(x * s, (top + grass_edge(x)) * s) for x in range(width, -1, -1)]
    shadow = canvas(width * zoom, height * zoom)
    pygame.draw.polygon(shadow, WHITE, [(0, 0), (w, 0)] + [(x, y + 2 * s) for x, y in edge])
    big.blit(masked((*shade(TILE_COLOR, 0.55), 170), shadow), (0, 0))
    shape = canvas(width * zoom, height * zoom)
    pygame.draw.polygon(shape, WHITE, [(0, 0), (w, 0)] + edge)
    green = gradient(
        (w, (top + GRASS_DEPTH + 3) * s), tint(TILE_TOP_COLOR, 0.45), tint(TILE_TOP_COLOR, 0.1), shade(TILE_TOP_COLOR, 0.8)
    )
    fill = pygame.Surface(shape.get_size(), pygame.SRCALPHA)
    fill.fill((*shade(TILE_TOP_COLOR, 0.8), 255))
    fill.blit(green, (0, 0))
    big.blit(masked(fill, shape), (0, 0))
    pygame.draw.rect(big, (*tint(TILE_TOP_COLOR, 0.65), 255), (0, top * s, w, round(1.5 * s)))
    return big


def tile_image(ends=(True, True)):
    # Blok: üstü çimen, altı çakıllı toprak, koyu dış çizgi
    size = TILE_SIZE
    s = size * AA
    left, right = ends
    big = canvas(size, size)
    pygame.draw.rect(big, shade(TILE_COLOR, 0.42), (0, 0, s, s), **ends_radius(ends, TILE_RADIUS * AA))
    edge = OUTLINE * AA
    inner = pygame.Rect(edge if left else 0, edge, s - edge * (left + right), s - 2 * edge)
    shape = canvas(size, size)
    pygame.draw.rect(shape, WHITE, inner, **ends_radius(ends, (TILE_RADIUS - OUTLINE) * AA))
    dirt = gradient((s, s), tint(TILE_COLOR, 0.22), TILE_COLOR, shade(TILE_COLOR, 0.68))
    for x, y, w, h, light in PEBBLES:
        color = tint(TILE_COLOR, 0.25) if light else shade(TILE_COLOR, 0.78)
        pygame.draw.ellipse(dirt, color, (x * AA, y * AA, w * AA, h * AA))
    big.blit(masked(dirt, shape), (0, 0))
    big.blit(masked(grass_layer(size, size, OUTLINE), shape), (0, 0))
    image = finish(big, (size, size), opaque=not (left or right))
    return fast(image) if left or right else image


def plank(width, height, color, ends, grain=True, zoom=1):
    # Tahta / metal platform (büyük çizim): dış çizgi; üstte açık renkli yüzey (parlak kenarlı), altında daha koyu
    # yan yüz — üstten bakılıyormuş gibi. width, height piksel; zoom = kaç kat büyük
    s = AA * zoom
    w, h = width * s, height * s
    left, right = ends
    big = canvas(width * zoom, height * zoom)
    radius = height // 2 * s
    pygame.draw.rect(big, shade(color, 0.42), (0, 0, w, h), **ends_radius(ends, radius))
    edge = OUTLINE * s
    inner = pygame.Rect(edge if left else 0, edge, w - edge * (left + right), h - 2 * edge)
    shape = canvas(width * zoom, height * zoom)
    pygame.draw.rect(shape, WHITE, inner, **ends_radius(ends, radius - edge))
    top = round(3.5 * s)  # üst yüzeyin kalınlığı
    fill = gradient((w, h), color, color, shade(color, 0.68))
    fill.blit(gradient((w, top), tint(color, 0.5), tint(color, 0.3)), (0, edge))
    pygame.draw.rect(fill, shade(color, 0.78), (0, edge + top, w, round(0.8 * s)))
    if grain:  # tahta damarı (yan yüzde)
        for y, start, stop in ((0.72, 0.06, 0.42), (0.72, 0.58, 0.93), (0.6, 0.3, 0.68)):
            pygame.draw.line(fill, shade(color, 0.82), (start * w, y * h), (stop * w, y * h), round(0.7 * s))
    pygame.draw.rect(fill, tint(color, 0.72), (0, edge, w, round(0.9 * s)))
    big.blit(masked(fill, shape), (0, 0))
    return big


def platform_image(ends=(True, True), zoom=1):
    # İnce platform: tahta
    big = plank(TILE_SIZE, PLATFORM_HEIGHT, PLATFORM_COLOR, ends, zoom=zoom)
    image = finish(big, (TILE_SIZE * zoom, PLATFORM_HEIGHT * zoom), opaque=not any(ends))
    return fast(image) if any(ends) else image


def moving_platform_image(cells):
    # Hareketli platform: uçları yuvarlak mavi metal, perçinli, ortasında parlayan şerit
    width = TILE_SIZE * cells
    big = plank(width, PLATFORM_HEIGHT, MOVING_PLATFORM_COLOR, (True, True), grain=False)
    h = PLATFORM_HEIGHT * AA
    glow = (*tint(MOVING_PLATFORM_COLOR, 0.75), 255)
    pygame.draw.line(big, glow, (14 * AA, 0.62 * h), ((width - 14) * AA, 0.62 * h), round(1.4 * AA))
    for i in range(cells):
        for x in (i * TILE_SIZE + 7, (i + 1) * TILE_SIZE - 7):
            center = (x * AA, 0.55 * h)
            pygame.draw.circle(big, shade(MOVING_PLATFORM_COLOR, 0.45), center, 2 * AA)
            pygame.draw.circle(big, tint(MOVING_PLATFORM_COLOR, 0.7), (center[0] - 0.4 * AA, center[1] - 0.4 * AA), 1.1 * AA)
    return fast(finish(big, (width, PLATFORM_HEIGHT)))


CRACKS = (
    [[(9, 0), (12, 4), (10, 7)], [(29, 12), (27, 8), (30, 5)]],
    [[(9, 0), (12, 4), (10, 7), (14, 12)], [(29, 12), (27, 8), (30, 5), (26, 0)], [(19, 0), (21, 5), (18, 9)]],
)


def crumble_frames():
    # Kırılan platform: çatlak taş (her kare ayrı taş); ikincisi kırılmak üzere (çatlaklar büyür), üçüncüsü silik
    frames = []
    for cracks in CRACKS:
        w, h = TILE_SIZE, PLATFORM_HEIGHT
        big = canvas(w, h)
        body = pygame.Rect(AA, 0, (w - 2) * AA, h * AA)
        pygame.draw.rect(big, shade(CRUMBLE_COLOR, 0.42), body, border_radius=4 * AA)
        shape = canvas(w, h)
        pygame.draw.rect(shape, WHITE, body.inflate(-2 * OUTLINE * AA, -2 * OUTLINE * AA), border_radius=3 * AA)
        stone = gradient((w * AA, h * AA), tint(CRUMBLE_COLOR, 0.4), CRUMBLE_COLOR, shade(CRUMBLE_COLOR, 0.75))
        big.blit(masked(stone, shape), (0, 0))
        for crack in cracks:
            thick_lines(big, shade(CRUMBLE_COLOR, 0.4), [(x * AA, y * AA) for x, y in crack], 1.2 * AA)
        frames.append(finish(big, (w, h)))
    ghost = frames[0].copy()
    ghost.set_alpha(70)
    return fast_all(frames) + [ghost]


def spring_frames():
    # Yay: yeşil plaka, metal sarmal, koyu ayak; ikinci resim basık (sarmal görünmez)
    from art import SPRING_SIZE

    w, h = SPRING_SIZE
    frames = []
    for squashed in (False, True):
        big = canvas(w, h)
        base = pygame.Rect(1 * AA, 12 * AA, 22 * AA, 4 * AA)
        pygame.draw.rect(big, (60, 60, 80), base, border_radius=round(2 * AA))
        pygame.draw.rect(big, (130, 130, 155), base.inflate(-2 * AA, -2.2 * AA).move(0, -0.4 * AA), border_radius=AA)
        top = 7 if squashed else 0
        if not squashed:
            coil = [(12 * AA, 12.5 * AA)]
            for i in range(1, 4):
                coil.append(((5 if i % 2 else 19) * AA, (12.5 - i * 2.2) * AA))
            coil.append((12 * AA, 5 * AA))
            thick_lines(big, (70, 70, 90), coil, 3.2 * AA)
            thick_lines(big, (205, 205, 225), coil, 1.6 * AA)
        pad = pygame.Rect(0, top * AA, w * AA, 6 * AA)
        pygame.draw.rect(big, shade(SPRING_COLOR, 0.4), pad, border_radius=round(3 * AA))
        shape = canvas(w, h)
        pygame.draw.rect(shape, WHITE, pad.inflate(-2.4 * AA, -2.4 * AA), border_radius=round(2 * AA))
        fill = pygame.Surface(big.get_size(), pygame.SRCALPHA)
        fill.blit(gradient((w * AA, 6 * AA), tint(SPRING_COLOR, 0.55), SPRING_COLOR, shade(SPRING_COLOR, 0.75)), (0, top * AA))
        big.blit(masked(fill, shape), (0, 0))
        pygame.draw.rect(big, (*tint(SPRING_COLOR, 0.75), 255), (3 * AA, (top + 1.6) * AA, (w - 6) * AA, AA), border_radius=AA)
        frames.append(finish(big, (w, h)))
    return fast_all(frames)


# --- Toplananlar ---
def coin_face(diameter):
    # Altının ön yüzü (büyük çizim): kenar halkası, renk geçişli yüz, iç halka, parlama
    big = canvas(diameter, diameter)
    d = diameter * AA
    center = (d / 2, d / 2)
    pygame.draw.circle(big, COIN_EDGE_COLOR, center, d / 2)
    shape = canvas(diameter, diameter)
    pygame.draw.circle(shape, WHITE, center, d / 2 - 1.6 * AA * diameter / COIN_SIZE)
    face = gradient((d, d), tint(COIN_COLOR, 0.6), COIN_COLOR, shade(COIN_COLOR, 0.86))
    big.blit(masked(face, shape), (0, 0))
    pygame.draw.circle(big, shade(COIN_COLOR, 0.8), center, d * 0.27, round(0.07 * d))
    shine = canvas(diameter, diameter)
    pygame.draw.ellipse(shine, (255, 255, 255, 170), (d * 0.22, d * 0.17, d * 0.24, d * 0.17))
    big.blit(shine, (0, 0))
    return big


def coin_frames(zoom=1):
    # Dönen altın: düz, yarı dönmüş (arkasında kalınlığı görünür), yan (ince kenar), yarı dönmüş
    diameter = COIN_SIZE * zoom
    d = diameter * AA
    face = coin_face(diameter)
    frames = [finish(face, (diameter, diameter))]
    half = canvas(diameter, diameter)
    width = d * 0.56
    edge = pygame.Rect(0, 0, width, d).move((d - width) / 2 - 0.12 * d, 0)
    pygame.draw.ellipse(half, shade(COIN_EDGE_COLOR, 0.8), edge.inflate(0.08 * d, 0))
    half.blit(pygame.transform.smoothscale(face, (round(width), d)), ((d - width) / 2, 0))
    frames.append(finish(half, (diameter, diameter)))
    thin = canvas(diameter, diameter)
    bar = pygame.Rect(0, 0, 0.2 * d, d).move(0.4 * d, 0)
    pygame.draw.rect(thin, COIN_EDGE_COLOR, bar, border_radius=round(0.1 * d))
    pygame.draw.rect(thin, tint(COIN_COLOR, 0.4), bar.inflate(-0.1 * d, -0.2 * d), border_radius=round(0.05 * d))
    frames.append(finish(thin, (diameter, diameter)))
    frames = fast_all(frames)
    return [frames[0], frames[1], frames[2], frames[1]]


GEM_SIZE = (28, 24)
GEM_FACETS = (  # (köşeler, renk tonu: + açık, - koyu)
    (((6, 2), (11, 2), (8, 8), (1, 8)), 0.35),
    (((11, 2), (17, 2), (20, 8), (8, 8)), 0.65),
    (((17, 2), (22, 2), (27, 8), (20, 8)), 0.15),
    (((1, 8), (8, 8), (14, 23)), 0.0),
    (((8, 8), (20, 8), (14, 23)), 0.3),
    (((20, 8), (27, 8), (14, 23)), -0.25),
)
GEM_OUTLINE = ((6, 2), (22, 2), (27, 8), (14, 23), (1, 8))


def sparkle(surface, center, size, alpha=255):
    # Dört kollu parıltı (büyük çizim)
    x, y = center
    color = (255, 255, 255, alpha)
    pygame.draw.polygon(surface, color, [(x, y - size), (x + size * 0.22, y), (x, y + size), (x - size * 0.22, y)])
    pygame.draw.polygon(surface, color, [(x - size, y), (x, y - size * 0.22), (x + size, y), (x, y + size * 0.22)])


def gem_frames():
    # Elmas: yüzeyleri farklı tonlarda parlayan zümrüt, koyu kenar; parıltı iki resim arasında yer değiştirir
    frames = []
    for glint in ((9, 5), (19, 12)):
        big = canvas(*GEM_SIZE)
        outline = [(x * AA, y * AA) for x, y in GEM_OUTLINE]
        pygame.draw.polygon(big, shade(GEM_COLOR, 0.4), outline)
        pygame.draw.lines(big, shade(GEM_COLOR, 0.4), True, outline, 3 * AA)
        for points, tone in GEM_FACETS:
            color = tint(GEM_COLOR, tone) if tone >= 0 else shade(GEM_COLOR, 1 + tone)
            pygame.draw.polygon(big, color, [(x * AA, y * AA) for x, y in points])
        for points, _ in GEM_FACETS:  # yüzeylerin arasındaki ince parlak çizgiler
            pygame.draw.lines(big, (*tint(GEM_COLOR, 0.7), 255), True, [(x * AA, y * AA) for x, y in points], round(0.5 * AA))
        sparkle(big, (glint[0] * AA, glint[1] * AA), 4 * AA)
        frames.append(finish(big, GEM_SIZE))
    return fast_all(frames)


HEART_SIZE = (28, 24)


def heart_shape(big, color, grow=0.0):
    # Kalp şekli (büyük çizim): iki daire + sivri alt; grow = her yandan ne kadar büyük (piksel)
    radius = (7 + grow) * AA
    for x in (8.5, 19.5):
        pygame.draw.circle(big, color, (x * AA, 8.5 * AA), radius)
    pygame.draw.polygon(big, color, [((1.9 - grow) * AA, 11 * AA), ((26.1 + grow) * AA, 11 * AA), (14 * AA, (22.6 + grow) * AA)])


def heart_image(color):
    # Kalp: koyu kenar, renk geçişi, sol üstte parlama
    big = canvas(*HEART_SIZE)
    heart_shape(big, shade(color, 0.5), grow=1.2)
    shape = canvas(*HEART_SIZE)
    heart_shape(shape, WHITE)
    fill = gradient(big.get_size(), tint(color, 0.35), color, shade(color, 0.78))
    big.blit(masked(fill, shape), (0, 0))
    pygame.draw.ellipse(big, (255, 255, 255, 190), (4.2 * AA, 4.5 * AA, 5.5 * AA, 3.6 * AA))
    return fast(finish(big, HEART_SIZE))


def star_points(center, outer, inner):
    x, y = center
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((x + radius * math.cos(angle), y + radius * math.sin(angle)))
    return points


def star_image(filled=True, size=None):
    # Kazanılan (sarı) ya da kazanılmayan (gri) yıldız; size = boyu (piksel, verilmezse 36) — doğrudan o boyda çizilir
    size = size or 36
    color = STAR_COLOR if filled else STAR_EMPTY_COLOR
    big = canvas(size, size)
    s = size * AA
    center = (s / 2, s * 0.54)
    outer = s * 0.47
    pygame.draw.polygon(big, shade(color, 0.55), star_points(center, outer, outer * 0.5))
    shape = canvas(size, size)
    edge = s * 0.07
    pygame.draw.polygon(shape, WHITE, star_points(center, outer - edge, (outer - edge) * 0.5))
    fill = gradient((s, s), tint(color, 0.5), color, shade(color, 0.82))
    big.blit(masked(fill, shape), (0, 0))
    if filled:
        sparkle(big, (s * 0.38, s * 0.4), s * 0.09, 220)
    return fast(finish(big, (size, size)))


# --- Bölüm sonu bayrağı ---
def flag_frames(count=4):
    # Direk (tepesinde altın top), dalgalanan yeşil-beyaz damalı bez, taş ayak. Resim 40 x 80 (Nostalji ile aynı)
    width, height = 40, 80
    frames = []
    for frame in range(count):
        big = canvas(width, height)
        pygame.draw.rect(big, (70, 70, 90), (0, 73 * AA, 13 * AA, 7 * AA), border_radius=2 * AA)
        pygame.draw.rect(big, (110, 110, 135), (AA, 74 * AA, 11 * AA, 2 * AA), border_radius=AA)
        pygame.draw.rect(big, (95, 95, 115), (4 * AA, 6 * AA, 4 * AA, 68 * AA), border_radius=2 * AA)
        pygame.draw.rect(big, (230, 230, 240), (4.8 * AA, 6 * AA, 1.6 * AA, 67 * AA), border_radius=AA)
        pygame.draw.circle(big, COIN_EDGE_COLOR, (6 * AA, 5 * AA), 4.2 * AA)
        pygame.draw.circle(big, COIN_COLOR, (6 * AA, 5 * AA), 3.1 * AA)
        pygame.draw.circle(big, (255, 250, 210), (5 * AA, 4 * AA), 1.2 * AA)

        def wave(u):
            # Bezin direkten u piksel uzaktaki yerinin aşağı-yukarı kayması
            return 4 * min(1.0, u / 10) * math.sin(u / 8.8 - frame * math.pi / 2)

        left, cloth_top, cloth_width, cloth_height, square = 8, 8, 32, 24, 8
        for col in range(cloth_width // square):
            for strip in range(4):  # her kare 4 dilimde çizilir: dalga yumuşak olsun
                u0 = col * square + strip * 2
                u1 = u0 + 2
                slope = math.cos((u0 + 1) / 8.8 - frame * math.pi / 2)
                for row in range(cloth_height // square):
                    color = FLAG_COLOR if (col + row) % 2 else (245, 245, 250)
                    color = shade(color, 0.86 + 0.14 * slope) if u0 > 2 else color
                    v0, v1 = cloth_top + row * square, cloth_top + (row + 1) * square
                    points = [(left + u0, v0 + wave(u0)), (left + u1 + 0.3, v0 + wave(u1)), (left + u1 + 0.3, v1 + wave(u1)), (left + u0, v1 + wave(u0))]
                    pygame.draw.polygon(big, color, [(x * AA, y * AA) for x, y in points])
        edge = [(left + u, cloth_top + wave(u)) for u in range(0, cloth_width + 1, 2)]
        edge += [(left + u, cloth_top + cloth_height + wave(u)) for u in range(cloth_width, -1, -2)]
        pygame.draw.lines(big, shade(FLAG_COLOR, 0.45), True, [(x * AA, y * AA) for x, y in edge], round(1.2 * AA))
        frames.append(finish(big, (width, height)))
    return fast_all(frames)


def fireball_frames():
    # Topçunun ateş topu: kızıl kenarlı, ortası beyaza dönen parlak top; iki resim arasında titreşir
    size = 16
    frames = []
    for core in (1.0, 0.85):
        big = canvas(size, size)
        center = (8 * AA, 8 * AA)
        big.blit(radial(8 * AA, (*FIREBALL_COLOR, 255), (*shade(FIREBALL_COLOR, 0.8), 120)), (0, 0))
        pygame.draw.circle(big, shade(FIREBALL_COLOR, 0.75), center, 7 * AA, round(1.2 * AA))
        hot = radial(5 * AA * core, (255, 252, 230, 255), (*tint(FIREBALL_COLOR, 0.45), 255))
        big.blit(hot, hot.get_rect(center=center))
        frames.append(finish(big, (size, size)))
    return fast_all(frames)


# --- Lav ---
LAVA_WAVE_HEIGHT = 32  # dalga şeridinin yüksekliği (Nostalji ile aynı: 8 kare)


def lava_surface(x, phase):
    # Lavın yüzeyi (x piksel → y piksel, şeridin tepesinden): iki dalga üst üste
    return 6 + 3.2 * math.sin(2 * math.pi * x / 100 + phase) + 1.5 * math.sin(2 * math.pi * x / 43 - 2 * phase)


def lava_frames(count=8):
    # Lavın üst kenarı: yuvarlak dalgalar yana akar, tepeleri parlar, içinde kabarcıklar yükselir. Şeridin altı
    # düz lav rengi (altını lava.py doldurur)
    width, height = SCREEN_WIDTH, LAVA_WAVE_HEIGHT
    w, h = width * AA, height * AA
    fill = gradient((w, h), LAVA_TOP_COLOR, tint(LAVA_COLOR, 0.5), LAVA_COLOR, LAVA_COLOR)
    rng = random.Random(5)
    bubbles = [(rng.uniform(10, width - 10), rng.uniform(0, 1), rng.uniform(1.2, 2.6)) for _ in range(9)]
    frames = []
    for f in range(count):
        phase = 2 * math.pi * f / count
        big = canvas(width, height)
        top = [(x * AA, lava_surface(x, phase) * AA) for x in range(0, width + 4, 4)]
        shape = canvas(width, height)
        pygame.draw.polygon(shape, WHITE, top + [(w, h), (0, h)])
        big.blit(masked(fill, shape), (0, 0))
        for x, start, radius in bubbles:  # kabarcıklar yukarı çıkar, yüzeye varınca baştan
            y = height - ((start + f / count) % 1) * (height - lava_surface(x, phase) - radius)
            pygame.draw.circle(big, (*tint(LAVA_COLOR, 0.55), 255), (x * AA, y * AA), radius * AA)
            pygame.draw.circle(big, (*tint(LAVA_COLOR, 0.85), 255), ((x - radius * 0.3) * AA, (y - radius * 0.3) * AA), radius * 0.4 * AA)
        thick_lines(big, (*tint(LAVA_TOP_COLOR, 0.55), 255), [(x, y + 0.6 * AA) for x, y in top], 1.6 * AA)
        frames.append(finish(big, (width, height)))
    return fast_all(frames)


def lava_body(height):
    # Lavın dalgaların altındaki gövdesi: yüzeye yakın parlak, derine indikçe koyulaşır (lava.py üstüne çizer)
    return gradient((SCREEN_WIDTH, height), LAVA_COLOR, shade(LAVA_COLOR, 0.86), shade(LAVA_COLOR, 0.72), shade(LAVA_COLOR, 0.72)).convert()


def lava_light():
    # Lavın üstüne vuran kızıl ışık (ekrana eklenir: üstündeki her şey hafifçe kızarır)
    return gradient((SCREEN_WIDTH, 50), (0, 0, 0), (12, 4, 0), (42, 15, 2))


def shield_bubble(radius):
    # Kalkan: karakterin etrafında kenarı parlayan, içi hafif mavi baloncuk, sol üstte parlama
    size = 2 * radius
    big = canvas(size, size)
    r = radius * AA
    big.blit(radial(r, (*SHIELD_COLOR, 25), (*SHIELD_COLOR, 120), 30), (0, 0))
    pygame.draw.circle(big, (*tint(SHIELD_COLOR, 0.35), 230), (r, r), r, round(2 * AA))
    pygame.draw.ellipse(big, (255, 255, 255, 140), (r * 0.42, r * 0.32, r * 0.5, r * 0.28))
    return fast(finish(big, (size, size)))


# --- Giriş ekranındaki uçan adacık ---
def island_image(zoom=1):
    # Üstü çimen, altı sivrilen çakıllı toprak (bloklarla aynı renkler). Boyu Nostalji'deki gibi 96 x 48 (x zoom)
    width, height = 96, 48
    big = canvas(width * zoom, height * zoom)
    s = AA * zoom

    def half_width(y):
        # Adacığın y yüksekliğindeki yarı genişliği: aşağı doğru daralır, kenarları biraz dalgalı
        t = max(0.0, (y - 6) / (height - 6))
        return 48 * (1 - t ** 1.7) * (1 + 0.03 * math.sin(y * 0.9))

    outline = [(48 - half_width(y), y) for y in range(0, height + 1, 2)]
    outline += [(48 + half_width(y), y) for y in range(height, -1, -2)]
    pygame.draw.polygon(big, shade(TILE_COLOR, 0.42), [(x * s, y * s) for x, y in outline])
    inner = [(48 - half_width(y) + OUTLINE * 1.4, y) for y in range(OUTLINE, height - 3, 2)]
    inner += [(48 + half_width(y) - OUTLINE * 1.4, y) for y in range(height - 4, OUTLINE - 1, -2)]
    shape = canvas(width * zoom, height * zoom)
    pygame.draw.polygon(shape, WHITE, [(x * s, y * s) for x, y in inner])
    dirt = gradient(big.get_size(), tint(TILE_COLOR, 0.22), TILE_COLOR, shade(TILE_COLOR, 0.6))
    rng = random.Random(11)
    for _ in range(14):
        x, y = rng.uniform(14, 82), rng.uniform(16, 36)
        light = rng.random() < 0.6
        color = tint(TILE_COLOR, 0.25) if light else shade(TILE_COLOR, 0.75)
        pygame.draw.ellipse(dirt, color, (x * s, y * s, rng.uniform(3, 7) * s, rng.uniform(2, 4) * s))
    big.blit(masked(dirt, shape), (0, 0))
    big.blit(masked(grass_layer(width, height, OUTLINE, zoom), shape), (0, 0))
    return fast(finish(big, (width * zoom, height * zoom)))


# --- Gökyüzü: renk geçişi, yumuşak bulutsu ışıklar, kenarları koyu; parlayan yuvarlak yıldızlar, uzakta yavaş
# kayan ışık topları, oyunun başında uzakta tepeler ---
BOKEH_PARALLAX = 0.12  # uzaktaki ışık topları haritaya göre ne kadar yavaş kayar (yıldızlardan da yavaş)
HILLS_PARALLAX = 0.4  # başlangıçtaki tepeler (yükseldikçe aşağıda kalır)


def vignette(size, strength):
    # Ekranın kenarlarını ve köşelerini hafifçe karartan katman (ortası saydam)
    spot = pygame.Surface((64, 64), pygame.SRCALPHA)
    spot.fill((0, 0, 0, 255))
    for i in range(32, 0, -1):
        t = i / 32
        pygame.draw.circle(spot, (0, 0, 0, round(255 * max(0.0, (t - 0.45) / 0.55) ** 2)), (32, 32), 32 * t)
    image = pygame.transform.smoothscale(spot, (round(size[0] * 1.3), round(size[1] * 1.15)))
    image.set_alpha(strength)
    return image


def sky_image(top_color, bottom_color, seed):
    sky = gradient((SCREEN_WIDTH, SCREEN_HEIGHT), top_color, mix(top_color, bottom_color, 0.55), bottom_color)
    rng = random.Random(seed)
    glow = radial(64, (*tint(bottom_color, 0.35), 255), (*tint(bottom_color, 0.35), 0))
    for _ in range(4):  # bulutsu ışıklar (gökyüzüne bir kere işlenir)
        w, h = rng.randint(220, 380), rng.randint(140, 260)
        cloud = pygame.transform.smoothscale(glow, (w, h))
        cloud.set_alpha(rng.randint(28, 52))
        sky.blit(cloud, (rng.randint(-120, SCREEN_WIDTH - 100), rng.randint(-60, SCREEN_HEIGHT - 100)))
    shadow = vignette((SCREEN_WIDTH, SCREEN_HEIGHT), 120)
    sky.blit(shadow, ((SCREEN_WIDTH - shadow.get_width()) // 2, (SCREEN_HEIGHT - shadow.get_height()) // 2))
    return sky.convert() if pygame.display.get_surface() else sky


def hills_image():
    # Oyunun başında uzakta iki sıra tepe (arkadaki açık, öndeki koyu); üst kenarları hafif parlak
    width, height = SCREEN_WIDTH, 230
    big = canvas(width, height)
    w, h = width * AA, height * AA
    layers = (
        ((70, 52, 120), 70, ((0.0055, 30, 0.0), (0.013, 12, 1.3))),
        ((38, 27, 70), 120, ((0.007, 26, 2.1), (0.017, 9, 0.4))),
    )
    for color, base, waves in layers:
        def top(x):
            return base + sum(amp * math.sin(x * freq + phase) for freq, amp, phase in waves)

        points = [(x * AA, top(x) * AA) for x in range(0, width + 4, 4)]
        pygame.draw.polygon(big, color, points + [(w, h), (0, h)])
        thick_lines(big, tint(color, 0.18), [(x, y + 0.6 * AA) for x, y in points], 1.3 * AA)
    return fast(finish(big, (width, height)))


def star_glow(radius, color):
    # Yıldız: parlak ortası olan yumuşak ışık
    size = math.ceil(radius * 4)
    big = canvas(size, size)
    big.blit(radial(size * AA / 2, (*color, 200), (*color, 0)), (0, 0))
    pygame.draw.circle(big, (255, 255, 255, 255), (size * AA / 2, size * AA / 2), radius * AA * 0.7)
    return finish(big, (size, size))


def trail_sparkle(color, radius):
    # Efsanevi izlerinin parıltısı (yıldız tozu, altın, kar): renkli yumuşak ışık + dört kollu parıltı
    size = math.ceil(radius * 2) + 2
    big = canvas(size, size)
    center = size * AA / 2
    big.blit(radial(radius * AA * 0.7, (*color, 150), (*color, 0)), (center - radius * AA * 0.7, center - radius * AA * 0.7))
    x, y = center, center
    r = radius * AA
    for points in (
        [(x, y - r), (x + r * 0.2, y), (x, y + r), (x - r * 0.2, y)],
        [(x - r, y), (x, y - r * 0.2), (x + r, y), (x, y + r * 0.2)],
    ):
        pygame.draw.polygon(big, (*color, 255), points)
    pygame.draw.circle(big, (255, 255, 255, 255), (x, y), max(AA, r * 0.18))
    return finish(big, (size, size))


def twinkle_image():
    # Giriş ekranında parlayıp sönen yıldız: yumuşak ışık + dört kollu parıltı
    size = 22
    big = canvas(size, size)
    center = size * AA / 2
    big.blit(radial(center * 0.6, (255, 250, 210, 120), (255, 250, 210, 0)), (center * 0.4, center * 0.4))
    sparkle(big, (center, center), center * 0.95, 235)
    pygame.draw.circle(big, (255, 255, 255, 255), (center, center), 1.6 * AA)
    return finish(big, (size, size))


class Background:
    def __init__(self):
        self.skies = [sky_image(top, bottom, i) for i, (top, bottom) in enumerate(SKY_THEMES)]
        # Yıldızlar Nostalji'dekiyle aynı yerlerde (aynı sayıyla rastgele); her biri kendi hızında parıldar
        rng = random.Random(7)
        images = {}
        self.stars = []
        for _ in range(STAR_COUNT):
            x, y = rng.randrange(SCREEN_WIDTH), rng.randrange(SCREEN_HEIGHT)
            size = rng.choice((1, 2, 2, 3))
            color = rng.choice(((150, 150, 210), (190, 200, 255), (255, 255, 255)))
            key = (size, color)
            if key not in images:
                images[key] = star_glow(0.5 + size * 0.45, color)
            self.stars.append((x, y, images[key], rng.uniform(0, 6.3), rng.uniform(0.8, 2.2)))
        # Uzakta yavaşça kayan, yumuşak kenarlı ışık topları (iki ekran boyunda bir tekrar eder)
        rng = random.Random(9)
        self.bokeh = []
        for _ in range(5):
            radius = rng.randint(14, 34)
            color = rng.choice(((150, 120, 255), (110, 170, 255), (90, 220, 200), (255, 140, 200)))
            ball = radial(radius, (*color, rng.randint(30, 50)), (*color, 0), 16)
            self.bokeh.append((rng.randrange(-20, SCREEN_WIDTH - 20), rng.randrange(2 * SCREEN_HEIGHT), ball))
        self.hills = hills_image()

    def draw(self, screen, camera_top):
        height = max(0, -camera_top)
        index = int(height // SKY_CHANGE_HEIGHT)
        into = height % SKY_CHANGE_HEIGHT
        blend = (into - (SKY_CHANGE_HEIGHT - SKY_BLEND_HEIGHT)) / SKY_BLEND_HEIGHT
        screen.blit(self.skies[index % len(self.skies)], (0, 0))
        if blend > 0:
            next_sky = self.skies[(index + 1) % len(self.skies)]
            next_sky.set_alpha(round(blend * 255))
            screen.blit(next_sky, (0, 0))
            next_sky.set_alpha(None)
        shift = -camera_top * BOKEH_PARALLAX
        for x, y, ball in self.bokeh:
            y = (y + shift) % (2 * SCREEN_HEIGHT) - ball.get_height()
            if y < SCREEN_HEIGHT:
                screen.blit(ball, (x, y))
        shift = -camera_top * STAR_PARALLAX
        seconds = pygame.time.get_ticks() / 1000
        for x, y, image, phase, speed in self.stars:
            image.set_alpha(round(150 + 105 * math.sin(seconds * speed + phase)))
            half = image.get_width() // 2
            screen.blit(image, (x - half, (y + shift) % SCREEN_HEIGHT - half))
        # Oyunun başında (kamera zemindeyken) uzakta tepeler; yükseldikçe yavaşça aşağıda kalır
        climbed = -SCREEN_HEIGHT - camera_top
        if climbed >= 0:
            top = SCREEN_HEIGHT - self.hills.get_height() + climbed * HILLS_PARALLAX
            if top < SCREEN_HEIGHT:
                screen.blit(self.hills, (0, top))


# --- Logo: kalın, yazı tipiyle; renk geçişli, koyu kenarlı, altında 3B kalınlık ---
LOGO_FONT_SIZE = 84  # harflerin boyu (pygame'in yazı tipi)
LOGO_STRETCH = 1.2  # harfler bu kadar uzun çizilir (daha "logo" gibi)
LOGO_EDGE = 4  # koyu kenarın kalınlığı (piksel)
LOGO_EXTRUDE = 5  # altındaki 3B kalınlık (piksel)
LOGO_TIGHT = 3  # harfler bu kadar sık dizilir (kenarlar üst üste biner, harfler bitişik görünür)


def spread(shape, radius, step=1):
    # Şekli her yana radius piksel kalınlaştır (beyaz şeklin kopyaları daire şeklinde kaydırılıp üst üste konur)
    grown = pygame.Surface(shape.get_size(), pygame.SRCALPHA)
    grown.fill((0, 0, 0, 0))
    for dy in range(-radius, radius + 1, step):
        for dx in range(-radius, radius + 1, step):
            if dx * dx + dy * dy <= radius * radius:
                grown.blit(shape, (dx, dy), special_flags=pygame.BLEND_RGBA_MAX)
    return grown


def logo_letters(text, top_color, bottom_color):
    # art.logo_letters'ın modern hâli: [(resim, parıltı, x)]. Her harf 2 kat büyük hazırlanıp küçültülür
    scale = 2
    font = pygame.font.Font(None, LOGO_FONT_SIZE * scale)
    ascent = font.get_ascent()
    cap = max(font.metrics(char)[0][3] for char in text)  # en uzun harfin taban çizgisinden yüksekliği
    pad = (LOGO_EDGE + 1) * scale
    letters = []
    x = 0
    for char in text:
        glyph = font.render(char, True, WHITE)
        glyph = glyph.subsurface((0, ascent - cap, glyph.get_width(), cap))
        glyph = pygame.transform.smoothscale(glyph, (glyph.get_width(), round(cap * LOGO_STRETCH)))
        width, height = glyph.get_width() + 2 * pad, glyph.get_height() + 2 * pad + LOGO_EXTRUDE * scale
        face = pygame.Surface((width, height), pygame.SRCALPHA)
        face.fill((0, 0, 0, 0))
        face.blit(glyph, (pad, pad))
        edge = spread(face, LOGO_EDGE * scale, 2)
        big = pygame.Surface((width, height), pygame.SRCALPHA)
        big.fill((*LOGO_OUTLINE_COLOR, 0))
        side = pygame.Surface((width, height), pygame.SRCALPHA)
        side.fill((0, 0, 0, 0))
        for d in range(LOGO_EXTRUDE * scale + 1):  # kalınlık: şekil aşağı doğru kopyalanır
            big.blit(masked(LOGO_OUTLINE_COLOR, edge), (0, d))
            if d:
                side.blit(face, (0, d), special_flags=pygame.BLEND_RGBA_MAX)
        big.blit(masked(shade(bottom_color, 0.55), side), (0, 0))
        fill = gradient((width, height), top_color, top_color, bottom_color, shade(bottom_color, 0.8))
        big.blit(masked(fill, face), (0, 0))
        rim = face.copy()  # harfin üst kenarında parlak şerit
        rim.blit(face, (0, 3 * scale), special_flags=pygame.BLEND_RGBA_SUB)
        big.blit(masked((*tint(top_color, 0.6), 200), rim), (0, 0))
        size = (width // scale, height // scale)
        image = finish(big, size)
        shine = pygame.transform.smoothscale(face, size)
        shine.fill((255, 255, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)
        letters.append((fast(image), shine, x))
        x += (glyph.get_width() - 2 * LOGO_TIGHT) // scale
    return letters


# --- Menü kutuları ve düğmeler ---
BOX_SHADOW = 6  # gölge ve ışık için resmin kutudan her yana taşan kısmı (piksel)


def box_image(size, fill, border, border_width, radius, glow=None):
    # Düğme / kutu: altında yumuşak gölge, içi yukarıdan aşağı renk geçişli, üst yarısı hafif parlak, ince kenar.
    # glow = seçiliyse etrafındaki ışığın rengi. Resim kutudan her yana BOX_SHADOW piksel büyük
    width, height = size
    pad = BOX_SHADOW
    full = (width + 2 * pad, height + 2 * pad)
    image = pygame.Surface(full, pygame.SRCALPHA)
    image.fill((0, 0, 0, 0))
    halo = pygame.Surface(full, pygame.SRCALPHA)
    halo.fill((0, 0, 0, 0))
    if glow:
        pygame.draw.rect(halo, (*glow, 150), (pad - 2, pad - 2, width + 4, height + 4), border_radius=radius + 2)
    else:
        pygame.draw.rect(halo, (0, 0, 0, 120), (pad, pad + 3, width, height), border_radius=radius)
    image.blit(pygame.transform.gaussian_blur(halo, 4), (0, 0))
    big = canvas(width, height)
    w, h = width * AA, height * AA
    pygame.draw.rect(big, border, (0, 0, w, h), border_radius=radius * AA)
    edge = border_width * AA
    shape = canvas(width, height)
    pygame.draw.rect(shape, WHITE, (edge, edge, w - 2 * edge, h - 2 * edge), border_radius=max(0, radius - border_width) * AA)
    inside = gradient((w, h), tint(fill, 0.16), fill, shade(fill, 0.78))
    gloss = pygame.Surface((w, h // 2), pygame.SRCALPHA)
    gloss.fill((255, 255, 255, 16))
    inside.blit(gloss, (0, 0))
    big.blit(masked(inside, shape), (0, 0))
    image.blit(finish(big, size), (pad, pad))
    return fast(image)


def knob_image(radius, fill, border):
    # Kaydırma çubuğunun tutulan yuvarlak düğmesi: altında gölge, açık renkli, renk geçişli, ince kenar çizgisi
    size = 2 * radius + 2 * BOX_SHADOW
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    image.fill((0, 0, 0, 0))
    pygame.draw.circle(image, (0, 0, 0, 130), (size / 2, size / 2 + 3), radius)
    image = pygame.transform.gaussian_blur(image, 3)
    big = canvas(2 * radius, 2 * radius)
    r = radius * AA
    pygame.draw.circle(big, border, (r, r), r)
    shape = canvas(2 * radius, 2 * radius)
    pygame.draw.circle(shape, WHITE, (r, r), r - 2.5 * AA)
    light = tint(fill, 0.85)
    big.blit(masked(gradient(big.get_size(), WHITE, light, tint(fill, 0.55)), shape), (0, 0))
    image.blit(finish(big, (2 * radius, 2 * radius)), (BOX_SHADOW, BOX_SHADOW))
    return fast(image)


# --- Oyunda derinlik: platformların altında gölge, toplananların etrafında ışık, ayağın altında gölge ---
SHADOW_DEPTH = 9  # platformun altına düşen gölgenin boyu (piksel)


def drop_shadow(width, ends):
    # Platform / bloğun altına düşen yumuşak gölge (yukarıdan aşağı silinir); sıranın uçlarında yanlara da silinir
    image = gradient((width, SHADOW_DEPTH), (0, 0, 0, 95), (0, 0, 0, 35), (0, 0, 0, 0))
    fade = 10  # uçlarda yana silinme (piksel)
    for side, is_end in zip((0, 1), ends):
        if not is_end:
            continue
        for i in range(fade):
            x = i if side == 0 else width - 1 - i
            image.fill((255, 255, 255, round(255 * (i + 0.5) / fade)), (x, 0, 1, SHADOW_DEPTH), special_flags=pygame.BLEND_RGBA_MULT)
    return image


def glow_image(color, radius):
    # Toplananların (altın, elmas, kalp...) arkasındaki yumuşak ışık
    big = canvas(2 * radius, 2 * radius)
    big.blit(radial(radius * AA, (*tint(color, 0.3), 120), (*color, 0)), (0, 0))
    return finish(big, (2 * radius, 2 * radius))


def foot_shadow(width):
    # Yerde duranın ayağının altındaki yumuşak oval gölge
    height = 8
    image = pygame.Surface((width + 8, height + 8), pygame.SRCALPHA)
    image.fill((0, 0, 0, 0))
    pygame.draw.ellipse(image, (0, 0, 0, 110), (4, 4, width, height))
    return pygame.transform.gaussian_blur(image, 2)


def text_shadow(image):
    # Yazının yumuşak gölgesi: yazının siyah hâli bulanıklaştırılır (resim her yana 4 piksel büyük)
    pad = 4
    shadow = pygame.Surface((image.get_width() + 2 * pad, image.get_height() + 2 * pad), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 0))
    shadow.blit(image, (pad, pad))
    shadow.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)
    soft = pygame.transform.gaussian_blur(shadow, 2)
    soft.blit(shadow, (0, 0), special_flags=pygame.BLEND_RGBA_MAX)
    soft.fill((255, 255, 255, 190), special_flags=pygame.BLEND_RGBA_MULT)
    return soft


# --- Parçacıklar ---
def particle_images(color):
    # Saçılan parçacık: parlak ortalı yuvarlak; ömrü bittikçe küçülür (büyükten küçüğe resimler)
    images = []
    for radius in (3.6, 3.2, 2.8, 2.3, 1.8, 1.3):
        size = math.ceil(radius * 2) + 2
        big = canvas(size, size)
        center = (size * AA / 2, size * AA / 2)
        pygame.draw.circle(big, color, center, radius * AA)
        pygame.draw.circle(big, tint(color, 0.55), (center[0] - radius * AA * 0.25, center[1] - radius * AA * 0.25), radius * AA * 0.45)
        images.append(finish(big, (size, size)))
    return images
