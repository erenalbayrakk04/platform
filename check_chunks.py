# Parça testi: her harita parçasının ve her iki parçanın birleşme yerinin gerçekten çıkılabilir
# olduğunu GERÇEK karakter fiziğiyle dener (Player sınıfı sahte tuşlarla binlerce kez zıplatılır).
# Yeni parça ekledikten veya zıplama/hız ayarlarını değiştirdikten sonra çalıştır:
#   python check_chunks.py
# Not: düşmanlar hesaba katılmaz (üstlerine basılabilir veya beklenip geçilebilir).
# Hareketli platformlar iki durumla düşünülür: yolunun sol ucunda veya sağ ucunda. Üstünde duran
# karakter onunla öbür uca gider; üstünde değilse platformun öbür uca gitmesini bekleyebilir.
# Kırılan platformun üstünde beklenemez ve yürünemez: karakter oraya inince hemen zıplamak zorunda.
import itertools
import os
import sys
import time
from collections import deque
from multiprocessing import Pool

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # pencere açmadan çalışsın
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from chunks import START_CHUNK, CHUNKS, FINISH_CHUNKS, WIDTH, SOLID, moving_platforms
from controls import Controls
from level import Tile, Platform, Spring, MovingPlatform, CrumblingPlatform
from player import Player
from settings import TILE_SIZE

# Denenen hareketler: (zıpla mı, ilk yön, ilk yön kaç kare, sonraki yön); yön -1 sol, 0 yok, 1 sağ
SWITCH_FRAMES = (1, 2, 4, 6, 8, 11, 14, 18, 22, 27, 33, 40)
ACTIONS = [(False, d1, 1, d2) for d1 in (-1, 1) for d2 in (-1, 0, 1)]
for d1 in (-1, 0, 1):
    for d2 in (-1, 0, 1):
        for t1 in SWITCH_FRAMES if d1 != d2 else (999,):
            ACTIONS.append((True, d1, t1, d2))
JUMP_ACTIONS = [action for action in ACTIONS if action[0]]  # kırılan platformun üstünden yapılabilenler
MAX_FRAMES = 150
# Denenen parçalar: oyundakiler + bölüm modunun bitiş parçaları (tepesinde bayrak; üstlerine parça gelmez)
TESTED = CHUNKS + list(FINISH_CHUNKS.values())


def build(rows):
    # Harf satırlarından sabit bloklar, yaylar ve hareketli platformların iki ucu (en üst satır y = 0)
    tiles = []
    springs = pygame.sprite.Group()
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell == "#":
                tiles.append(Tile(c * TILE_SIZE, r * TILE_SIZE))
            elif cell == "-":
                tiles.append(Platform(c * TILE_SIZE, r * TILE_SIZE))
            elif cell == "K":
                tiles.append(CrumblingPlatform(c * TILE_SIZE, r * TILE_SIZE))
            elif cell == "S":
                springs.add(Spring(c * TILE_SIZE, r * TILE_SIZE))
    movers = []
    for r, left, width, span_left, span_right in moving_platforms(rows):
        ends = (span_left, span_right + 1 - width)  # sol uçtaki ve sağ uçtaki ilk sütun
        movers.append([MovingPlatform(c * TILE_SIZE, r * TILE_SIZE, width, 0, 0) for c in ends])
    # Her durum (hangi platform hangi uçta) için ayrı bir çarpışma grubu
    groups = {}
    for phase in itertools.product((0, 1), repeat=len(movers)):
        groups[phase] = pygame.sprite.Group(tiles, [pair[p] for pair, p in zip(movers, phase)])
    return groups, springs, movers


def simulate(player, tiles, springs, x, bottom, action, limit):
    # Karakteri (x, bottom)'da yerde dururken koy, hareketi uygula; yere indiği yeri döndür
    jump, d1, t1, d2 = action
    player.rect.x, player.rect.bottom = x, bottom
    player.pos_y, player.velocity_y, player.on_ground = float(bottom), 0.0, True
    for frame in range(MAX_FRAMES):
        d = d1 if frame < t1 else d2
        player.update(tiles, Controls(d < 0, d > 0, jump and frame == 0))
        player.check_springs(springs)
        if player.on_ground and (frame > 0 or not jump):
            return player.rect.x, player.rect.bottom
        if player.rect.top > limit:
            return None  # aşağı düştü
    return None


def mover_moves(player, groups, movers, x, bottom, phase):
    # Hareketli platformlarla yapılabilecekler: üstündeyse binip öbür uca git, değilse bekle
    body = player.rect.copy()
    body.x, body.bottom = x, body.bottom - player.rect.bottom + bottom
    for i, pair in enumerate(movers):
        here, there = pair[phase[i]], pair[1 - phase[i]]
        other = phase[:i] + (1 - phase[i],) + phase[i + 1 :]
        on_it = bottom == here.rect.top and body.right > here.rect.left and body.left < here.rect.right
        if on_it:
            moved = body.move(there.rect.x - here.rect.x, 0)
            walls = [t for t in groups[other] if t is not there]
            inside = 0 <= moved.left and moved.right <= WIDTH * TILE_SIZE
            if inside and not any(moved.colliderect(t.rect) for t in walls):
                yield moved.x, bottom, other
        elif not body.colliderect(there.rect):
            yield x, bottom, other


def reachable(rows, starts, goal_bottom):
    # Başlangıç noktalarından (x, ayak hizası) hedef yüksekliğe basılabiliyor mu? (genişlik öncelikli arama)
    groups, springs, movers = build(rows)
    player = Player(0, 0, WIDTH * TILE_SIZE)
    limit = len(rows) * TILE_SIZE + 100
    # Durum: (x, ayak hizası, hareketli platformların hangi uçta olduğu)
    seen = {(x, bottom, phase) for x, bottom in starts for phase in groups}
    queue = deque(seen)
    while queue:
        x, bottom, phase = queue.popleft()
        if bottom == goal_bottom:
            return True
        # Sadece kırılan platformun üstündeyse: beklemek ve yürümek yok, hemen zıpla
        feet = pygame.Rect(x, bottom, player.rect.width, 1)
        ground = [t for t in groups[phase] if feet.colliderect(t.rect)]
        crumbling = ground and all(isinstance(t, CrumblingPlatform) for t in ground)
        results = [
            (*landed, phase)
            for action in (JUMP_ACTIONS if crumbling else ACTIONS)
            if (landed := simulate(player, groups[phase], springs, x, bottom, action, limit))
        ]
        if not crumbling:
            results += mover_moves(player, groups, movers, x, bottom, phase)
        for state in results:
            if state not in seen:
                seen.add(state)
                queue.append(state)
    return False


def row_starts(rows, r):
    # r. satırdaki her katı karenin ortasında dururken başlangıç noktaları
    width = Player(0, 0, 1).rect.width
    return [
        (c * TILE_SIZE + (TILE_SIZE - width) // 2, r * TILE_SIZE)
        for c, cell in enumerate(rows[r])
        if cell in SOLID
    ]


def chunk_name(chunk):
    return chunk.get("name") or f"{chunk.get('entry', 'başlangıç')}->{chunk['exit']} zorluk {chunk.get('difficulty', '-')}"


def test_inside(index):
    # Parçanın girişinden (başlangıç parçasında P'den) en üst satıra (bitiş parçasında zirveye) çıkılabiliyor mu?
    chunk = START_CHUNK if index < 0 else TESTED[index]
    rows = chunk["rows"]
    if index < 0:
        r = next(i for i, row in enumerate(rows) if "P" in row)
        starts = [(rows[r].index("P") * TILE_SIZE, (r + 1) * TILE_SIZE)]
    else:
        starts = row_starts(rows, len(rows) - 2)
    return reachable(rows, starts, chunk.get("goal_row", 0) * TILE_SIZE)


def test_join(pair):
    # Alttaki parçanın çıkışından üstteki parçanın girişine geçilebiliyor mu?
    lower, upper = pair
    lower_rows = (START_CHUNK if lower < 0 else CHUNKS[lower])["rows"]
    upper_rows = TESTED[upper]["rows"]
    # Üst parçanın alt 5 satırı + alt parçanın üst 4 satırı yeter (zıplama 3 satırdan fazla ulaşmaz)
    rows = upper_rows[-5:] + lower_rows[:4]
    return reachable(rows, row_starts(rows, 5), 3 * TILE_SIZE)


def main():
    start = time.time()
    indexes = [-1] + list(range(len(TESTED)))
    pairs = []
    for lower in indexes[: len(CHUNKS) + 1]:  # bitiş parçasının üstüne parça gelmez
        exit_side = (START_CHUNK if lower < 0 else CHUNKS[lower])["exit"]
        for upper, chunk in enumerate(TESTED):
            if chunk["entry"] != exit_side:  # oyun sadece böyle dizer (level.pick_chunk)
                pairs.append((lower, upper))

    with Pool() as pool:
        inside = pool.map(test_inside, indexes)
        joins = pool.map(test_join, pairs)

    def describe(i):
        if i < 0:
            return "başlangıç parçası"
        if i >= len(CHUNKS):
            return f"bitiş parçası (giriş {TESTED[i]['entry']})"
        return f"CHUNKS[{i}] (" + chunk_name(CHUNKS[i]) + ")"

    problems = [f"İçinden çıkılamıyor: {describe(i)}" for i, ok in zip(indexes, inside) if not ok]
    problems += [
        f"Birleşme geçilemiyor: {describe(a)} üstüne {describe(b)}"
        for (a, b), ok in zip(pairs, joins)
        if not ok
    ]
    print(f"{len(indexes)} parça ve {len(pairs)} birleşme denendi ({time.time() - start:.0f} sn).")
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print("Hepsi çıkılabilir.")


if __name__ == "__main__":
    main()
