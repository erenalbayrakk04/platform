# Harita parçaları — oyun bunları rastgele seçip üst üste dizer (sonsuz tırmanma).
#
# Her parça küçük bir harita; işaretler level.py'deki gibi:
#   #  = blok (katı)
#   -  = ince platform (o da katı)
#   .  = boşluk
#   P  = karakterin başladığı yer (sadece başlangıç parçasında)
#
# Parçaların birbirine bağlanma kuralları (check_chunk bunları kontrol eder):
#   - Her satır 10 karakter.
#   - En alt satır boş ("..........").
#   - Sondan ikinci satır GİRİŞ: sadece ince platform ('-'), hepsi giriş tarafında.
#     Sol taraf = 0-4. sütunlar ve 4. sütun dolu olmalı; sağ taraf = 5-9. sütunlar ve 5. sütun dolu olmalı.
#   - En üst satır ÇIKIŞ: hepsi çıkış tarafında, aynı kural.
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
        "..........",
        ".....----.",
        "..........",
        "..........",
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
            "..........",
            ".----.....",
            "..........",
            "..........",
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
            "..........",
            ".....----.",
            "..........",
            "..........",
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
            "..........",
            ".....----.",
            "..........",
            "..........",
            "..---.....",
            "..........",
            "..........",
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
            "..........",
            ".----.....",
            "..........",
            "..........",
            ".....---..",
            "..........",
            "..........",
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
            "..........",
            ".###......",
            "..........",
            "..........",
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
            "..........",
            "......###.",
            "..........",
            "..........",
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
            "..........",
            "..--......",
            "..........",
            "..........",
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
            "..........",
            "......--..",
            "..........",
            "..........",
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
            "..........",
            "......#...",
            "..........",
            "..........",
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
            "..........",
            "...#......",
            "..........",
            "..........",
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
            "..........",
            "..-.......",
            "..........",
            "..........",
            ".....#....",
            "..........",
            "..........",
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
            "..........",
            ".......-..",
            "..........",
            "..........",
            "....#.....",
            "..........",
            "..........",
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
            "..........",
            ".-........",
            "..........",
            "..........",
            "....#.....",
            "..........",
            "..........",
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
            "..........",
            "........-.",
            "..........",
            "..........",
            ".....#....",
            "..........",
            "..........",
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
    problem = None
    if any(len(row) != WIDTH for row in rows):
        problem = "her satır 10 karakter olmalı"
    elif not check_side_row(rows[0], chunk["exit"], "#-"):
        problem = "en üst satır (çıkış) kurala uymuyor"
    elif not is_start and rows[-1] != "." * WIDTH:
        problem = "en alt satır boş olmalı"
    elif not is_start and not check_side_row(rows[-2], chunk["entry"], "-"):
        problem = "sondan ikinci satır (giriş) kurala uymuyor"
    if problem:
        raise ValueError(f"Hatalı parça ({problem}):\n" + "\n".join(rows))


check_chunk(START_CHUNK, is_start=True)
for _chunk in CHUNKS:
    check_chunk(_chunk)
# Her iki giriş tarafı için de en az bir kolay parça olmalı, yoksa oyun takılır
for _side in "LR":
    if not any(c["entry"] == _side and c["difficulty"] == 1 for c in CHUNKS):
        raise ValueError(f"Girişi '{_side}' olan kolay parça yok")
