# Harita parçaları — oyun bunları rastgele seçip üst üste dizer (sonsuz tırmanma).
#
# Her parça küçük bir harita; işaretler level.py'deki gibi:
#   #  = blok (katı)
#   -  = ince platform (o da katı)
#   K  = kırılan platform (ince; üstüne basınca yarım saniye sonra kırılır, birkaç saniye sonra geri gelir)
#   .  = boşluk
#   C  = altın (toplanınca puan verir; bir platformun hemen üstüne koy ki alınabilsin)
#   M  = hareketli platform (yan yana M'ler tek platform; satırında duvara/kenara kadar gidip gelir)
#   S  = yay (bir platformun hemen üstüne koy; üstüne basınca ~9 blok yükseğe fırlatır)
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
#   - Altın (C), yay (S) ve düşman (E) giriş, çıkış ve en alt satıra konmaz; altlarında katı bir şey olmalı.
#     Yay ve düşman kırılan platformun (K) üstüne konmaz; altın konabilir.
#   - Kırılan platform (K) giriş ve çıkış satırında olmaz.
#   - Yaylı parçalarda "en fazla 3 satır" kuralı yay için geçerli değil (yay ~8 satır çıkarır).
#   - Hareketli platform: satırda tek grup; gittiği yolun hemen üstü ve altı boş olmalı
#     (iki üstünde '#' olmasın) ki üstünde giderken kafa çarpmasın, alttakini ezmesin.
#     Altın/yay/düşman hareketli platformun üstüne konmaz.
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



def mirror(chunk):
    # Parçanın sağ-sol aynası: her satır ters çevrilir, giriş/çıkış tarafları yer değiştirir
    swap = {"L": "R", "R": "L"}
    return {
        "entry": swap[chunk["entry"]],
        "exit": swap[chunk["exit"]],
        "difficulty": chunk["difficulty"],
        "rows": [row[::-1] for row in chunk["rows"]],
    }


# Bu parçalar oyuna iki kere girer: bir olduğu gibi, bir de aynalanmış haliyle (mirror).
# Böylece her biri için iki giriş tarafı da olur.
MIRRORED_CHUNKS = [
    # Kolay: blok merdiven, ortadaki blokta bir düşman
    {
        "entry": "L", "exit": "R", "difficulty": 1,
        "rows": [
            ".....----.",
            "..........",
            ".C........",
            ".###......",
            "..........",
            ".....E....",
            "....###...",
            "..........",
            "........C.",
            ".......###",
            "..........",
            "..---.....",
            "..........",
        ],
    },
    # Orta: geniş platformlar ama iki düşman
    {
        "entry": "L", "exit": "L", "difficulty": 2,
        "rows": [
            "-----.....",
            "..........",
            "........C.",
            ".....-----",
            "..........",
            "..E.......",
            ".----.....",
            "..........",
            "......E...",
            ".....----.",
            "..........",
            "..---.....",
            "..........",
        ],
    },
    # Orta: dar platformlar, düşmanın yanındaki altın riskli
    {
        "entry": "L", "exit": "L", "difficulty": 2,
        "rows": [
            "..---.....",
            "..........",
            "C.........",
            "##........",
            "..........",
            "..........",
            "...--.....",
            "..........",
            ".....CE...",
            ".....---..",
            "..........",
            "..........",
            "...--.....",
            "..........",
        ],
    },
    # Orta: ortada düşmanlı blok, sağa sola zikzak
    {
        "entry": "L", "exit": "R", "difficulty": 2,
        "rows": [
            ".....--...",
            "..........",
            "........C.",
            "........--",
            "..........",
            ".....E....",
            "....###...",
            "..........",
            ".C........",
            ".--.......",
            "..........",
            "...--.....",
            "..........",
        ],
    },
    # Zor: tek karelik platformlar, düşman tam inilecek yerde bekliyor
    {
        "entry": "L", "exit": "R", "difficulty": 3,
        "rows": [
            ".....-....",
            "..........",
            "...C......",
            "...-......",
            "..........",
            "......C...",
            "......-...",
            "..........",
            "..E.......",
            ".###......",
            "..........",
            "..........",
            "....-.....",
            "..........",
        ],
    },
    # Kolay: yay seni yukarıdaki platforma fırlatır (yaysız çıkılamaz)
    {
        "entry": "L", "exit": "L", "difficulty": 1,
        "rows": [
            "-----.....",
            "..........",
            "......C...",
            ".....---..",
            "..........",
            "..........",
            "..........",
            "..........",
            "..........",
            "..........",
            ".S........",
            "-----.....",
            "..........",
        ],
    },
    # Zor: tek karelik yay platformu, havada sağa uzun bir uçuş
    {
        "entry": "L", "exit": "R", "difficulty": 3,
        "rows": [
            ".....-....",
            "..........",
            "........C.",
            "........-.",
            "..........",
            "..........",
            "..........",
            "..........",
            "..........",
            "..........",
            "...S......",
            "...-......",
            "....-.....",
            "..........",
        ],
    },
    # Orta: hareketli platformla sağa geçip yukarı zıpla (platformsuz çıkılamaz)
    {
        "entry": "L", "exit": "R", "difficulty": 2,
        "rows": [
            ".....----.",
            "..C.......",
            ".---......",
            "..........",
            "......C...",
            "......--..",
            "..........",
            "C.........",
            "-MM.......",
            "..........",
            "..........",
            "..---.....",
            "..........",
        ],
    },
    # Zor: tek karelik hareketli platform bütün satırı boydan boya geçer
    {
        "entry": "L", "exit": "L", "difficulty": 3,
        "rows": [
            "....-.....",
            "..........",
            ".......C..",
            ".......-..",
            "..........",
            "..........",
            "M.........",
            "..........",
            "..C.......",
            "..-.......",
            "..........",
            "..........",
            "....-.....",
            "..........",
        ],
    },
    # Kolay: geniş ama kırılan platform — üstünde oyalanma
    {
        "entry": "L", "exit": "R", "difficulty": 1,
        "rows": [
            ".....----.",
            "..........",
            "..C.......",
            ".KKKK.....",
            "..........",
            "..........",
            ".....---..",
            "..........",
            "..........",
            "..---.....",
            "..........",
        ],
    },
    # Orta: kırılan basamaklarla zikzak
    {
        "entry": "L", "exit": "L", "difficulty": 2,
        "rows": [
            "..---.....",
            "..........",
            "......C...",
            ".....KK...",
            "..........",
            "..C.......",
            ".KK.......",
            "..........",
            "..........",
            "...--.....",
            "..........",
        ],
    },
    # Zor: tek karelik kırılan taşlar, durmadan zıpla
    {
        "entry": "L", "exit": "R", "difficulty": 3,
        "rows": [
            ".....-....",
            "..........",
            "..C.......",
            "..K.......",
            "..........",
            "......C...",
            "......K...",
            "..........",
            "..........",
            "..K.......",
            "..........",
            "..........",
            "....-.....",
            "..........",
        ],
    },
]
CHUNKS += MIRRORED_CHUNKS + [mirror(chunk) for chunk in MIRRORED_CHUNKS]

WIDTH = 10
# Her taraf için hangi sütunlar ona ait ve hangi sütun mutlaka dolu olmalı
SIDE_COLUMNS = {"L": range(0, 5), "R": range(5, 10)}
SIDE_EDGE = {"L": 4, "R": 5}
SOLID = "#-K"  # karakterin çarptığı kareler
STEADY = "#-"  # bunların üstüne yay ve düşman konabilir (kırılmazlar)
ENEMY_MIN_PLATFORM = 3  # düşmanın yürüdüğü platform en az kaç kare olmalı


def platform_run(rows, row, col):
    # (row, col) karesinin altındaki platformun soldan ve sağdan ilk/son sütunu.
    # Platform, altı katı ve kendisi boş olan yan yana karelerdir (duvara gelince biter).
    def walkable(c):
        return rows[row + 1][c] in STEADY and rows[row][c] not in SOLID

    left = right = col
    while left > 0 and walkable(left - 1):
        left -= 1
    while right < WIDTH - 1 and walkable(right + 1):
        right += 1
    return left, right


def moving_platforms(rows):
    # Her satırdaki M grubu bir hareketli platform:
    # (satır, ilk sütun, genişlik, gidebildiği en sol sütun, en sağ sütun)
    found = []
    for r, row in enumerate(rows):
        if "M" not in row:
            continue
        left, width = row.index("M"), row.count("M")
        span_left, span_right = left, left + width - 1
        while span_left > 0 and row[span_left - 1] not in SOLID:
            span_left -= 1
        while span_right < WIDTH - 1 and row[span_right + 1] not in SOLID:
            span_right += 1
        found.append((r, left, width, span_left, span_right))
    return found


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
    allowed = "#-.CESMK" + ("P" if is_start else "")
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
    # Altın, yay ve düşman havada olmasın; düşmanın platformu yeterince geniş olsun
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if problem or cell not in "CES":
                continue
            if r + 1 >= len(rows) or rows[r + 1][c] not in SOLID:
                problem = f"{r}. satır {c}. sütundaki '{cell}' havada (altı katı değil)"
            elif cell in "ES" and rows[r + 1][c] not in STEADY:
                problem = f"{r}. satır {c}. sütundaki '{cell}' kırılan platformun üstünde"
            elif cell == "E":
                left, right = platform_run(rows, r, c)
                if right - left + 1 < ENEMY_MIN_PLATFORM:
                    problem = f"{r}. satırdaki düşmanın platformu {ENEMY_MIN_PLATFORM} kareden kısa"
    # Hareketli platformlar: tek parça, gidecek yeri olsun, yolunun üstü/altı boş olsun
    for r, left, width, span_left, span_right in moving_platforms(rows) if not problem else []:
        span = range(span_left, span_right + 1)
        if rows[r][left : left + width] != "M" * width:
            problem = f"{r}. satırdaki M'ler yan yana olmalı (satırda tek hareketli platform)"
        elif span_right - span_left + 1 <= width:
            problem = f"{r}. satırdaki hareketli platformun gidecek yeri yok"
        elif any(rows[r + d][c] in SOLID + "S" for d in (-1, 1) for c in span):
            problem = f"{r}. satırdaki hareketli platformun yolunun hemen üstü ve altı boş olmalı"
        elif r >= 2 and any(rows[r - 2][c] == "#" for c in span):
            problem = f"{r}. satırdaki hareketli platformun iki üstünde blok var (kafa çarpar)"
    if problem:
        raise ValueError(f"Hatalı parça ({problem}):\n" + "\n".join(rows))


check_chunk(START_CHUNK, is_start=True)
for _chunk in CHUNKS:
    check_chunk(_chunk)
# Her iki giriş tarafı için de en az bir kolay parça olmalı, yoksa oyun takılır
for _side in "LR":
    if not any(c["entry"] == _side and c["difficulty"] == 1 for c in CHUNKS):
        raise ValueError(f"Girişi '{_side}' olan kolay parça yok")
