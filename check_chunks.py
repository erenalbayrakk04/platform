# Parça testi: her harita parçasının ve her iki parçanın birleşme yerinin gerçekten çıkılabilir
# olduğunu GERÇEK karakter fiziğiyle dener (Player sınıfı sahte tuşlarla binlerce kez zıplatılır).
# Yeni parça ekledikten veya zıplama/hız ayarlarını değiştirdikten sonra çalıştır:
#   python check_chunks.py
# Not: düşmanlar hesaba katılmaz (üstlerine basılabilir veya beklenip geçilebilir).
import os
import sys
import time
from collections import deque
from multiprocessing import Pool

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # pencere açmadan çalışsın
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from chunks import START_CHUNK, CHUNKS, WIDTH, SOLID
from controls import Controls
from level import Tile, Platform
from player import Player
from settings import TILE_SIZE

# Denenen hareketler: (zıpla mı, ilk yön, ilk yön kaç kare, sonraki yön); yön -1 sol, 0 yok, 1 sağ
SWITCH_FRAMES = (1, 2, 4, 6, 8, 11, 14, 18, 22, 27, 33, 40)
ACTIONS = [(False, d1, 1, d2) for d1 in (-1, 1) for d2 in (-1, 0, 1)]
for d1 in (-1, 0, 1):
    for d2 in (-1, 0, 1):
        for t1 in SWITCH_FRAMES if d1 != d2 else (999,):
            ACTIONS.append((True, d1, t1, d2))
MAX_FRAMES = 150


def build(rows):
    # Harf satırlarından çarpılabilir bloklar (en üst satır y = 0)
    tiles = pygame.sprite.Group()
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell == "#":
                tiles.add(Tile(c * TILE_SIZE, r * TILE_SIZE))
            elif cell == "-":
                tiles.add(Platform(c * TILE_SIZE, r * TILE_SIZE))
    return tiles


def simulate(player, tiles, x, bottom, action, limit):
    # Karakteri (x, bottom)'da yerde dururken koy, hareketi uygula; yere indiği yeri döndür
    jump, d1, t1, d2 = action
    player.rect.x, player.rect.bottom = x, bottom
    player.pos_y, player.velocity_y, player.on_ground = float(bottom), 0.0, True
    for frame in range(MAX_FRAMES):
        d = d1 if frame < t1 else d2
        player.update(tiles, Controls(d < 0, d > 0, jump and frame == 0))
        if player.on_ground and (frame > 0 or not jump):
            return player.rect.x, player.rect.bottom
        if player.rect.top > limit:
            return None  # aşağı düştü
    return None


def reachable(rows, starts, goal_bottom):
    # Başlangıç noktalarından (x, ayak hizası) hedef yüksekliğe basılabiliyor mu? (genişlik öncelikli arama)
    tiles = build(rows)
    player = Player(0, 0, WIDTH * TILE_SIZE)
    limit = len(rows) * TILE_SIZE + 100
    seen = set(starts)
    queue = deque(starts)
    while queue:
        x, bottom = queue.popleft()
        if bottom == goal_bottom:
            return True
        for action in ACTIONS:
            result = simulate(player, tiles, x, bottom, action, limit)
            if result and result not in seen:
                seen.add(result)
                queue.append(result)
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
    # Parçanın girişinden (başlangıç parçasında P'den) en üst satıra çıkılabiliyor mu?
    chunk = START_CHUNK if index < 0 else CHUNKS[index]
    rows = chunk["rows"]
    if index < 0:
        r = next(i for i, row in enumerate(rows) if "P" in row)
        starts = [(rows[r].index("P") * TILE_SIZE, (r + 1) * TILE_SIZE)]
    else:
        starts = row_starts(rows, len(rows) - 2)
    return reachable(rows, starts, 0)


def test_join(pair):
    # Alttaki parçanın çıkışından üstteki parçanın girişine geçilebiliyor mu?
    lower, upper = pair
    lower_rows = (START_CHUNK if lower < 0 else CHUNKS[lower])["rows"]
    upper_rows = CHUNKS[upper]["rows"]
    # Üst parçanın alt 5 satırı + alt parçanın üst 4 satırı yeter (zıplama 3 satırdan fazla ulaşmaz)
    rows = upper_rows[-5:] + lower_rows[:4]
    return reachable(rows, row_starts(rows, 5), 3 * TILE_SIZE)


def main():
    start = time.time()
    indexes = [-1] + list(range(len(CHUNKS)))
    pairs = []
    for lower in indexes:
        exit_side = (START_CHUNK if lower < 0 else CHUNKS[lower])["exit"]
        for upper, chunk in enumerate(CHUNKS):
            if chunk["entry"] != exit_side:  # oyun sadece böyle dizer (level.pick_chunk)
                pairs.append((lower, upper))

    with Pool() as pool:
        inside = pool.map(test_inside, indexes)
        joins = pool.map(test_join, pairs)

    def describe(i):
        chunk = START_CHUNK if i < 0 else CHUNKS[i]
        return ("başlangıç parçası" if i < 0 else f"CHUNKS[{i}]") + " (" + chunk_name(chunk) + ")"

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
