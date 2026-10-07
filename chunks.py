# Harita parçaları — oyun bunları rastgele seçip üst üste dizer (sonsuz tırmanma).
#
# Her parça küçük bir harita; işaretler level.py'deki gibi:
#   #  = blok (katı)
#   -  = ince platform (o da katı)
#   .  = boşluk
#   C  = altın (toplanınca puan verir; bir platformun hemen üstüne koy ki alınabilsin)
#   E  = düşman (bir platformun hemen üstüne koy; o platformda sağa-sola yürür,
#        platform en az 3 kare geniş olmalı)
#   P  = karakterin başladığı yer (sadece başlangıç parçasında)
#
# Parçaların birbirine bağlanma kuralları (check_chunk bunları kontrol eder):
#   - Her satır 10 karakter.
#   - En alt satır boş ("..........").
#   - Sondan ikinci satır GİRİŞ: sadece ince platform ('-'), hepsi giriş tarafında.
#     Sol taraf = 0-4. sütunlar ve 4. sütun dolu olmalı; sağ taraf = 5-9. sütunlar ve 5. sütun dolu olmalı.
#   - En üst satır ÇIKIŞ: hepsi çıkış tarafında, aynı kural.
#   - Altın (C) ve düşman (E) giriş, çıkış ve en alt satıra konmaz; altlarında katı bir şey olmalı.
#   - Oyun bir parçanın çıkışı soldaysa üstüne girişi sağda olan bir parça koyar (ya da tersi).
#     Böylece birleşme yerinde platformlar üst üste binmez ve aralarında sadece 2 satır olur.
#   - Parçanın içinde: basılan yüzeyler arası en fazla 3 satır, bir üstteki platform
#     bir alttakinin tam tepesinde olmasın (yana kaydır).
#
# difficulty: 1 = kolay (geniş platformlar), 2 = orta, 3 = zor (tek karelik platformlar).
# Yükseldikçe zor parçalar da gelmeye başlar (settings.py → DIFFICULTY_STEP).

START_CHUNK = {
    "exit": "L",
    "rows": [
        "-----.....",
        "..........",
        "......C...",
        ".....----.",
        "..........",
        "..C.......",
        ".----.....",
        "..........",
        ".P........",
        "##########",
    ],
}

CHUNKS = [
    # --- Kolay ---
    {
        "entry": "L", "exit": "R", "difficulty": 1,
        "rows": [
            ".....-----",
            "..........",
            "..C.E.....",
            ".----.....",
            "..........",
            "......C...",
            ".....----.",
            "..........",
            "..........",
            ".----.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "L", "difficulty": 1,
        "rows": [
            "-----.....",
            "..........",
            "......C...",
            ".....----.",
            "..........",
            "..C.......",
            ".----.....",
            "..........",
            "..........",
            ".....----.",
            "..........",
        ],
    },
    {
        "entry": "L", "exit": "L", "difficulty": 1,
        "rows": [
            "-----.....",
            "..........",
            "......C...",
            ".....----.",
            "..........",
            "..........",
            "..---.....",
            "..........",
            "......C...",
            ".....---..",
            "..........",
            "..---.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "R", "difficulty": 1,
        "rows": [
            ".....-----",
            "..........",
            "..C.......",
            ".----.....",
            "..........",
            "......E...",
            ".....---..",
            "..........",
            "...C......",
            "..---.....",
            "..........",
            ".....---..",
            "..........",
        ],
    },
    {
        "entry": "L", "exit": "R", "difficulty": 1,
        "rows": [
            ".....#####",
            "..........",
            "..C.......",
            ".###......",
            "..........",
            "......CE..",
            ".....###..",
            "..........",
            "..........",
            "-----.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "L", "difficulty": 1,
        "rows": [
            "#####.....",
            "..........",
            ".......C..",
            "......###.",
            "..........",
            "..EC......",
            "..###.....",
            "..........",
            "..........",
            ".....-----",
            "..........",
        ],
    },
    # --- Orta ---
    {
        "entry": "L", "exit": "R", "difficulty": 2,
        "rows": [
            ".....--...",
            "..........",
            "...C......",
            "..--......",
            "..........",
            ".......C..",
            "......--..",
            "..........",
            "..........",
            "...--.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "L", "difficulty": 2,
        "rows": [
            "...--.....",
            "..........",
            ".......C..",
            "......--..",
            "..........",
            "...C......",
            "..--......",
            "..........",
            "..........",
            ".....--...",
            "..........",
        ],
    },
    {
        "entry": "L", "exit": "L", "difficulty": 2,
        "rows": [
            "...--.....",
            "..........",
            "......C...",
            "......#...",
            "..........",
            ".........C",
            "........##",
            "..........",
            "..........",
            ".....--...",
            "..........",
            "...--.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "R", "difficulty": 2,
        "rows": [
            ".....--...",
            "..........",
            "...C......",
            "...#......",
            "..........",
            "C.........",
            "##........",
            "..........",
            "..........",
            "...--.....",
            "..........",
            ".....--...",
            "..........",
        ],
    },
    # --- Zor ---
    {
        "entry": "L", "exit": "R", "difficulty": 3,
        "rows": [
            ".....-....",
            "..........",
            "..C.......",
            "..-.......",
            "..........",
            ".....C....",
            ".....#....",
            "..........",
            ".......C..",
            ".......-..",
            "..........",
            "..........",
            "....-.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "L", "difficulty": 3,
        "rows": [
            "....-.....",
            "..........",
            ".......C..",
            ".......-..",
            "..........",
            "....C.....",
            "....#.....",
            "..........",
            "..C.......",
            "..-.......",
            "..........",
            "..........",
            ".....-....",
            "..........",
        ],
    },
    {
        "entry": "L", "exit": "L", "difficulty": 3,
        "rows": [
            "....-.....",
            "..........",
            ".C........",
            ".-........",
            "..........",
            "....C.....",
            "....#.....",
            "..........",
            ".......C..",
            ".......-..",
            "..........",
            "....-.....",
            "..........",
        ],
    },
    {
        "entry": "R", "exit": "R", "difficulty": 3,
        "rows": [
            ".....-....",
            "..........",
            "........C.",
            "........-.",
            "..........",
            ".....C....",
            ".....#....",
            "..........",
            "..C.......",
            "..-.......",
            "..........",
            ".....-....",
            "..........",
        ],
    },
]

WIDTH = 10
# Her taraf için hangi sütunlar ona ait ve hangi sütun mutlaka dolu olmalı
SIDE_COLUMNS = {"L": range(0, 5), "R": range(5, 10)}
SIDE_EDGE = {"L": 4, "R": 5}
SOLID = "#-"
ENEMY_MIN_PLATFORM = 3  # düşmanın yürüdüğü platform en az kaç kare olmalı


def platform_run(rows, row, col):
    # (row, col) karesinin altındaki platformun soldan ve sağdan ilk/son sütunu.
    # Platform, altı katı ve kendisi boş olan yan yana karelerdir (duvara gelince biter).
    def walkable(c):
        return rows[row + 1][c] in SOLID and rows[row][c] not in SOLID

    left = right = col
    while left > 0 and walkable(left - 1):
        left -= 1
    while right < WIDTH - 1 and walkable(right + 1):
        right += 1
    return left, right


def check_side_row(row, side, allowed):
    # Satırdaki her şey o tarafta olsun ve ortaya yakın sütun dolu olsun
    for col, cell in enumerate(row):
        if cell != ".":
            if cell not in allowed or col not in SIDE_COLUMNS[side]:
                return False
    return row[SIDE_EDGE[side]] != "."


def check_chunk(chunk, is_start=False):
    # Parça kurallara uymuyorsa oyun açılırken hata ver (yanlış parça fark edilmeden kalmasın)
    rows = chunk["rows"]
    allowed = "#-.CE" + ("P" if is_start else "")
    problem = None
    if any(len(row) != WIDTH for row in rows):
        problem = "her satır 10 karakter olmalı"
    elif any(cell not in allowed for row in rows for cell in row):
        problem = f"sadece şu işaretler kullanılabilir: {allowed}"
    elif not check_side_row(rows[0], chunk["exit"], "#-"):
        problem = "en üst satır (çıkış) kurala uymuyor"
    elif not is_start and rows[-1] != "." * WIDTH:
        problem = "en alt satır boş olmalı"
    elif not is_start and not check_side_row(rows[-2], chunk["entry"], "-"):
        problem = "sondan ikinci satır (giriş) kurala uymuyor"
    # Altın ve düşman havada olmasın; düşmanın platformu yeterince geniş olsun
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if problem or cell not in "CE":
                continue
            if r + 1 >= len(rows) or rows[r + 1][c] not in SOLID:
                problem = f"{r}. satır {c}. sütundaki '{cell}' havada (altı katı değil)"
            elif cell == "E":
                left, right = platform_run(rows, r, c)
                if right - left + 1 < ENEMY_MIN_PLATFORM:
                    problem = f"{r}. satırdaki düşmanın platformu {ENEMY_MIN_PLATFORM} kareden kısa"
    if problem:
        raise ValueError(f"Hatalı parça ({problem}):\n" + "\n".join(rows))


check_chunk(START_CHUNK, is_start=True)
for _chunk in CHUNKS:
    check_chunk(_chunk)
# Her iki giriş tarafı için de en az bir kolay parça olmalı, yoksa oyun takılır
for _side in "LR":
    if not any(c["entry"] == _side and c["difficulty"] == 1 for c in CHUNKS):
        raise ValueError(f"Girişi '{_side}' olan kolay parça yok")
