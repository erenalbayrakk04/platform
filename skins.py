# Skinler: karakterin görünüşleri. Her skin bir piksel çizim (art.py'deki gibi harf haritası) + renkler + nasıl
# açıldığı. SADECE GÖRÜNÜŞ: çarpışma kutusu, hız ve zıplama her skinde aynı (rekorlar adil kalsın).
# Çizim 10 sütun x 10 satır gövde + 2 satır bacak (bacaklar yürürken değişir; art.PLAYER_LEGS, harfi "L").
# Her harf bir renk ('.' saydam); "W" (göz beyazı) ve "E" (göz bebeği) verilmezse oyunun göz renkleri,
# "L" (bacak) verilmezse "K" (dış çizgi) rengi kullanılır. Resimler sağa bakar, sola bakan aynalanarak yapılır.
#
# Gruplar (Karakterler ekranındaki sekmeler): "colors" Renkler, "characters" Karakterler, "legendary" Efsanevi.
# Açılma: coins = kaç altın, gems = kaç elmas (ikisi de yoksa baştan açık; Renkler altınla, Karakterler elmasla);
# goal = görev (efsaneviler parayla alınmaz, görevle açılır):
#   ("games", N) N oyun oyna · ("climbed", N) toplam N m tırman · ("enemies", N) N düşman yen
#   ("coins", N) toplam N altın topla · ("stars", N) bölümlerden N yıldız · ("height-hard", N) Zor'da N m (Sonsuz)
# trail = efsanevilerin arkasında bıraktığı iz (trail.py): "spark", "fire", "stars", "gold", "snow", "rainbow", "shadow"
from settings import WHITE, PLAYER_COLOR, DIFFICULTY_NAMES, UNLOCK_ALL_SKINS
from storage import load_dict, save_dict
import art
from art import shade, tint

GROUP_NAMES = {"colors": "Renkler", "characters": "Karakterler", "legendary": "Efsanevi"}
CURRENCY_NAMES = {"coins": "altın", "gems": "elmas"}  # paralar (Wardrobe'da aynı adla tutulur)
DEFAULT_SKIN = "classic"


def skin(id, name, group, body, palette, coins=0, gems=0, goal=None, legs=None, trail=None, color=None):
    # color = karakterin ana rengi (can kaybedince saçılan parçacıklar); verilmezse "B".
    # Fiyat: currency = hangi parayla ("coins" / "gems" / None = bedava ya da görevli), price = kaç tane
    return {
        "id": id, "name": name, "group": group, "body": body, "palette": palette, "legs": legs,
        "currency": "gems" if gems else "coins" if coins else None, "price": gems or coins,
        "goal": goal, "trail": trail, "color": color or palette.get("B", PLAYER_COLOR),
    }


def blob_palette(color, legs=None):
    # Klasik karakterin renkleri tek bir renkten: dış çizgi koyu, alt kısım biraz koyu, parlak yer açık.
    # legs = bacakların ne kadar koyu olacağı (verilmezse dış çizgi renginde; açık renklerde koyu gökte kaybolmasın)
    palette = {"K": shade(color, 0.3), "B": color, "b": shade(color, 0.75), "h": tint(color, 0.5)}
    if legs:
        palette["L"] = shade(color, legs)
    return palette


# --- Renkler: klasik karakter, farklı renk ve desenlerle ---
BLOB = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhhBBBK.",
    "KBhBBBBBBK",
    "KBBBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBBBBBK",
    "KbBBBBBBbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

TIGER = [
    "...KKKK...",
    ".KKBsBsKK.",
    ".KBhsBsBK.",
    "KssBBBBBBK",
    "KBBBWEBWEK",
    "KssBWEBWEK",
    "KBBBBmmmmK",
    "KbssBmmmbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

STRAWBERRY = [
    "...GGGG...",
    ".GGgGGgGG.",
    ".KGBGGBGK.",
    "KBhBByBBBK",
    "KByBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBByBBK",
    "KbyBBBBBbK",
    ".KbbbbybK.",
    "..KKKKKK..",
]

RAINBOW = [
    "...KKKK...",
    ".KK1111KK.",
    ".K222222K.",
    "K33333333K",
    "K444WE4WEK",
    "K555WE5WEK",
    "K66666666K",
    "K77777777K",
    ".K888888K.",
    "..KKKKKK..",
]

GOLD = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBwhBBBK.",
    "KBhwBBBBBK",
    "KBhBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBBBBhK",
    "KbBBBBBhbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

# --- Karakterler ---
CAT = [
    ".K......K.",
    "KpK....KpK",
    "KBBKKKKBBK",
    "KBsBsBBBBK",
    "KBBBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBBnBBK",
    "KbBBBmmmbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

FROG = [
    ".KKK..KKK.",
    "KWWEKKWWEK",
    "KWWEBBWWEK",
    "KBBBBBBBBK",
    "KhBBBBBBBK",
    "KBBRRRRRRK",
    "KBBYYYYYBK",
    "KbYYYYYYbK",
    ".KbYYYYbK.",
    "..KKKKKK..",
]

PENGUIN = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhBBBBK.",
    "KBBBWWWWWK",
    "KBBWWEWWEK",
    "KBBWWWOOOK",
    "KBWWWWWWWK",
    "KBWWWWWWBK",
    ".KBWWWWBK.",
    "..KKKKKK..",
]

PANDA = [
    ".KKK..KKK.",
    ".KKKKKKKK.",
    ".KBBBBBBK.",
    "KBBBBBBBBK",
    "KBBPhBBPhK",
    "KBPPPBPPPK",
    "KBBBBNBBBK",
    "KbBpBBBpbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

BUNNY = [
    "...K...K..",
    "..KpK.KpK.",
    "..KpK.KpK.",
    ".KBBBBBBK.",
    "KBBBBBBBBK",
    "KBBBWEBWEK",
    "KBBBWEBWEK",
    "KhBBBBnBhK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

MUSHROOM = [
    "..KKKKKK..",
    ".KRRWWRRK.",
    "KRWWRRRWRK",
    "KRRRRRRRRK",
    "KKKKKKKKKK",
    ".KSSSSSSK.",
    ".KSWESWEK.",
    ".KSWESWEK.",
    ".KsSSSSsK.",
    "..KKKKKK..",
]

SNOWMAN = [
    "...KKKK...",
    "...KHHK...",
    "..KKKKKK..",
    ".KWWWWWWK.",
    ".KWWEWWEK.",
    ".KWWWWOOOK",
    ".KRRRRRRK.",
    "KWWWWWWWWK",
    "KwWWWWWWwK",
    ".KKKKKKKK.",
]

OCTOPUS = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhhBBBK.",
    "KBhBBBBBBK",
    "KBBBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBBBBBK",
    "KBpBBpBBpK",
    ".KBBBBBBK.",
    "KBKBKKBKBK",
]
OCTOPUS_LEGS = {
    "idle": ["KBKBKKBKBK", "BK.BKKB.KB"],
    "walk1": ["KBKBKKBKBK", "KB.KBBK.BK"],
    "walk2": ["KBKBKKBKBK", "BK.BKKB.KB"],
    "jump": ["BK.BKKB.KB", "K..K..K..K"],
}

GHOST = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhhBBBK.",
    "KBhBBBBBBK",
    "KBBBEEBEEK",
    "KBBBEEBEEK",
    "KBBBBBBBBK",
    "KBBBBBpBBK",
    "KBBBBBBBBK",
    "KBBBBBBBBK",
]
GHOST_LEGS = {
    "idle": ["KBBKBBKBBK", ".KK.KK.KK."],
    "walk1": ["BKBBKBBKBK", "K.KK.KK.K."],
    "walk2": ["KBBKBBKBBK", ".KK.KK.KK."],
    "jump": ["KBKBBKBBKK", ".K.KK.KK.."],
}

ALIEN = [
    ".Y......Y.",
    "..K....K..",
    "..KKKKKK..",
    ".KBBBBBBK.",
    "KBhBBBBBBK",
    "KBBBEwBEwK",
    "KBBBEEBEEK",
    "KBBBBBBBBK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

PIRATE = [
    "...KKKK...",
    ".KKRRRRKK.",
    ".KRWRRWRK.",
    "KRRRRRRRRK",
    "RRSSWESKKK",
    "RKSSWESKKK",
    "KSSSSSSSSK",
    "KSSSSbbbSK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

ROBOT = [
    "....RR....",
    ".KKKKKKKK.",
    ".KMhhMMMK.",
    "KMVVVVVVMK",
    "KMVVCVVCMK",
    "KMVVVVVVMK",
    "KMMMMMMMMK",
    "KMoMMMMoMK",
    "KmmmmmmmmK",
    ".KKKKKKKK.",
]

NINJA = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhBBBBK.",
    "RRRRRRRRRK",
    "RBBSWESWEK",
    "KBBBBBBBBK",
    "KBBBBBBBBK",
    "KbBBBBBBbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

KNIGHT = [
    "...RR.....",
    "..RRKKKK..",
    ".KKMMMMKK.",
    ".KMhMMMMK.",
    "KMMMMMMMMK",
    "KMMKKKKKKK",
    "KMMMKWKWKK",
    "KMMMMMMMMK",
    ".KmmmmmmK.",
    "..KKKKKK..",
]

ASTRONAUT = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBVVVVVK.",
    "KBVhVVVVVK",
    "KBVVWEVWEK",
    "KBBVVVVVVK",
    "KBBBBBBBBK",
    "KBBRBBCBBK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

# --- Efsaneviler (görevle açılır, arkalarında iz bırakır) ---
LIGHTNING = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBBzBBBK.",
    "KBBzzBBBBK",
    "KBzzBWEWEK",
    "KBBzzWEWEK",
    "KBBBzBBBBK",
    "KbBzBBBBbK",
    ".KbzbbbbK.",
    "..KKKKKK..",
]

DRAGON = [
    "..H....H..",
    ".HHKKKKHK.",
    ".KBBBBBBK.",
    "sBhBBBBBBK",
    "KBBBYEBYEK",
    "sBBBYEBYEK",
    "KBBBBBBBBK",
    "sbBBYYYYbK",
    ".KbbYYYbK.",
    "..KKKKKK..",
]

COSMIC = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBsBBnBK.",
    "KBBBBnnBBK",
    "KBsBWEBWEK",
    "KBBnWEBWEK",
    "KBBBBBsBBK",
    "KbBsBBBBbK",
    ".KbbnbbsK.",
    "..KKKKKK..",
]

KING = [
    "..Y.YY.Y..",
    "..YYYYYY..",
    ".KYRYCYRK.",
    "KSSSSSSSSK",
    "KSSSWESWEK",
    "KSSSWESWEK",
    "KSSSffffSK",
    "KrrffffffK",
    ".KrrrfffK.",
    "..KKKKKK..",
]

ICE = [
    "...K..K...",
    "..KwKKwK..",
    ".KBBwBBBK.",
    "KBwBBBBBBK",
    "KwBBWEBWEK",
    "KBBBWEBWEK",
    "KBBBBBBwBK",
    "KbBBBBwBbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

UNICORN = [
    "........Y.",
    ".......Yy.",
    "..1KKKYK..",
    ".12BBBBBK.",
    "123BBBBBBK",
    "K34BWEBWEK",
    "K45BWEBWEK",
    "K5BBBBBBBK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

SHADOW = [
    "...KKKK...",
    ".KKBBBBKK.",
    ".KBhBBBBK.",
    "KBhBBBBBBK",
    "KBBBRrBRrK",
    "KBBBBBBBBK",
    "KBBBBBBBBK",
    "KbBBBBBBbK",
    ".KbbbbbbK.",
    "..KKKKKK..",
]

RAINBOW_COLORS = [
    (235, 60, 70), (250, 140, 40), (250, 215, 50), (90, 200, 80),
    (60, 190, 210), (70, 120, 230), (130, 90, 220), (200, 90, 200),
]

SKINS = [
    # --- Renkler ---
    skin("classic", "Klasik", "colors", BLOB, blob_palette(PLAYER_COLOR)),
    skin("ocean", "Okyanus", "colors", BLOB, blob_palette((70, 150, 240)), coins=50),
    skin("mint", "Nane", "colors", BLOB, blob_palette((60, 205, 170)), coins=50),
    skin("candy", "Şeker", "colors", BLOB, blob_palette((245, 120, 175)), coins=50),
    skin("lavender", "Lavanta", "colors", BLOB, blob_palette((180, 145, 245), legs=0.5), coins=100),
    skin("snow", "Kar", "colors", BLOB, blob_palette((235, 240, 250)), coins=100),
    skin("night", "Gece", "colors", BLOB, {
        **blob_palette((60, 70, 130)), "K": (130, 150, 220), "b": (45, 52, 100), "h": (95, 110, 175),
    }, coins=150),
    skin("tiger", "Kaplan", "colors", TIGER, {
        **blob_palette((245, 145, 40)), "s": (60, 35, 20), "m": (250, 240, 225),
    }, coins=250),
    skin("strawberry", "Çilek", "colors", STRAWBERRY, {
        **blob_palette((230, 55, 75)), "G": (80, 180, 70), "g": (50, 120, 50), "y": (255, 225, 120),
    }, coins=250),
    skin("rainbow", "Gökkuşağı", "colors", RAINBOW, {
        "K": (45, 35, 70), "L": (110, 95, 150), **{str(i + 1): color for i, color in enumerate(RAINBOW_COLORS)},
    }, coins=600, color=RAINBOW_COLORS[2]),
    skin("gold", "Altın", "colors", GOLD, {
        "K": (115, 70, 10), "B": (250, 200, 50), "b": (205, 145, 25), "h": (255, 240, 160), "w": WHITE,
    }, coins=1200),
    # --- Karakterler ---
    skin("cat", "Kedi", "characters", CAT, {
        **blob_palette((165, 165, 180)), "K": (55, 55, 70), "s": (110, 110, 128), "p": (245, 160, 180),
        "n": (240, 110, 150), "m": (245, 245, 250),
    }, gems=10),
    skin("frog", "Kurbağa", "characters", FROG, {
        "K": (30, 70, 30), "B": (120, 205, 70), "b": (85, 160, 50), "h": (190, 240, 140),
        "R": (200, 60, 80), "Y": (235, 240, 170), "L": (70, 140, 50),
    }, gems=10),
    skin("penguin", "Penguen", "characters", PENGUIN, {
        "K": (15, 15, 25), "B": (50, 55, 75), "h": (90, 95, 120), "W": (240, 240, 250), "O": (250, 160, 40),
        "L": (250, 160, 40),
    }, gems=15),
    skin("panda", "Panda", "characters", PANDA, {
        "K": (30, 30, 35), "B": (240, 240, 240), "b": (195, 195, 205), "h": WHITE, "P": (30, 30, 35),
        "N": (30, 30, 35), "p": (250, 170, 190),
    }, gems=15),
    skin("bunny", "Tavşan", "characters", BUNNY, {
        "K": (90, 80, 100), "B": (245, 240, 245), "b": (215, 205, 220), "p": (250, 170, 190),
        "h": (250, 190, 205), "n": (240, 120, 150),
    }, gems=25),
    skin("mushroom", "Mantar", "characters", MUSHROOM, {
        "K": (70, 30, 30), "R": (225, 50, 50), "S": (245, 225, 190), "s": (210, 185, 150),
    }, gems=25, color=(225, 50, 50)),
    skin("snowman", "Kardan Adam", "characters", SNOWMAN, {
        "K": (40, 45, 60), "H": (60, 60, 80), "W": (245, 248, 255), "w": (200, 210, 230), "E": (25, 25, 40),
        "O": (250, 140, 40), "R": (220, 50, 60), "L": (120, 80, 50),
    }, gems=35, color=(245, 248, 255)),
    skin("octopus", "Ahtapot", "characters", OCTOPUS, {
        **blob_palette((240, 110, 150)), "K": (90, 30, 60), "p": (200, 80, 120),
    }, gems=35, legs=OCTOPUS_LEGS),
    skin("ghost", "Hayalet", "characters", GHOST, {
        "K": (110, 120, 170, 230), "B": (230, 235, 255, 215), "h": (255, 255, 255, 235), "E": (40, 40, 70),
        "p": (255, 170, 190, 220),
    }, gems=50, legs=GHOST_LEGS, color=(230, 235, 255)),
    skin("alien", "Uzaylı", "characters", ALIEN, {
        **blob_palette((150, 225, 90)), "K": (30, 80, 30), "E": (20, 20, 30), "w": WHITE, "Y": (255, 230, 80),
    }, gems=50),
    skin("pirate", "Korsan", "characters", PIRATE, {
        "K": (40, 30, 30), "R": (210, 40, 50), "W": (250, 250, 250), "S": (240, 190, 150), "b": (200, 150, 115),
    }, gems=70, color=(210, 40, 50)),
    skin("robot", "Robot", "characters", ROBOT, {
        "K": (40, 45, 60), "M": (175, 180, 195), "m": (130, 135, 150), "h": (225, 230, 240),
        "V": (35, 40, 60), "C": (80, 240, 255), "o": (100, 105, 120), "R": (255, 60, 60), "L": (130, 135, 150),
    }, gems=70, color=(175, 180, 195)),
    skin("ninja", "Ninja", "characters", NINJA, {
        "K": (15, 15, 25), "B": (45, 45, 65), "b": (30, 30, 45), "h": (80, 80, 105), "R": (220, 40, 50),
        "S": (240, 200, 160),
    }, gems=100),
    skin("knight", "Şövalye", "characters", KNIGHT, {
        "K": (40, 40, 55), "M": (190, 195, 210), "m": (140, 145, 160), "h": (240, 240, 250),
        "R": (220, 40, 50),
    }, gems=150, color=(190, 195, 210)),
    skin("astronaut", "Astronot", "characters", ASTRONAUT, {
        "K": (60, 65, 85), "B": (235, 235, 245), "b": (190, 190, 210), "V": (40, 60, 120), "h": (150, 200, 255),
        "R": (220, 60, 60), "C": (70, 130, 230), "L": (200, 200, 215),
    }, gems=200),
    # --- Efsaneviler ---
    skin("lightning", "Şimşek", "legendary", LIGHTNING, {
        **blob_palette((255, 215, 50)), "K": (40, 40, 100), "z": (90, 200, 255), "E": (40, 120, 220),
    }, goal=("games", 40), trail="spark"),
    skin("dragon", "Ejderha", "legendary", DRAGON, {
        **blob_palette((215, 60, 45)), "K": (70, 15, 15), "H": (250, 235, 190), "Y": (255, 200, 90),
        "s": (255, 170, 60),
    }, goal=("enemies", 150), trail="fire"),
    skin("cosmic", "Kozmik", "legendary", COSMIC, {
        "K": (160, 140, 255), "B": (45, 35, 110), "b": (30, 22, 80), "s": WHITE, "n": (190, 90, 210),
        "W": (220, 240, 255), "E": (40, 30, 90),
    }, goal=("climbed", 2500), trail="stars", color=(160, 140, 255)),
    skin("unicorn", "Tekboynuz", "legendary", UNICORN, {
        "K": (110, 90, 130), "B": (250, 245, 255), "b": (215, 205, 230), "Y": (255, 215, 80),
        "y": (220, 170, 40), "1": (235, 90, 120), "2": (250, 170, 60), "3": (250, 225, 80),
        "4": (100, 210, 150), "5": (110, 160, 240), "E": (90, 50, 130),
    }, goal=("coins", 1000), trail="rainbow"),
    skin("king", "Kral", "legendary", KING, {
        "K": (60, 30, 30), "Y": (255, 205, 50), "R": (230, 40, 60), "C": (70, 140, 255), "S": (245, 200, 160),
        "f": (250, 250, 250), "r": (190, 30, 60), "L": (110, 40, 60),
    }, goal=("stars", 75), trail="gold", color=(255, 205, 50)),
    skin("ice", "Buz", "legendary", ICE, {
        "K": (40, 90, 160), "B": (160, 220, 250), "b": (110, 170, 225), "w": (240, 252, 255),
        "E": (20, 50, 110),
    }, goal=("height-hard", 150), trail="snow"),
    skin("shadow", "Gölge", "legendary", SHADOW, {
        "K": (170, 40, 70), "B": (35, 28, 45), "b": (22, 18, 30), "h": (60, 50, 75), "R": (255, 70, 90),
        "r": (255, 170, 180),
    }, goal=("height-ultra", 75), trail="shadow", color=(170, 40, 70)),
]
SKIN_BY_ID = {skin["id"]: skin for skin in SKINS}
GROUP_SIZE = 15  # bir sekmede en fazla kaç skin olabilir (Karakterler ekranında 5 sütun x 3 satır)
TRAILS = ("spark", "fire", "stars", "gold", "snow", "rainbow", "shadow")


def get(skin_id):
    # Skin (bilinmeyen ad gelirse klasik)
    return SKIN_BY_ID.get(skin_id, SKIN_BY_ID[DEFAULT_SKIN])


def in_group(group):
    return [skin for skin in SKINS if skin["group"] == group]


_frames = {}


def frames(skin_id):
    # Skinin resimleri (art.player_frames) — her skin için bir kere hazırlanır
    skin = get(skin_id)
    if skin["id"] not in _frames:
        _frames[skin["id"]] = art.player_frames(skin)
    return _frames[skin["id"]]


def goal_text(goal):
    # Görevin ekrandaki yazısı, ör. "150 düşman yen"
    kind, target = goal
    if kind.startswith("height-"):
        return f"Sonsuz Oyun'da {target} m tırman ({DIFFICULTY_NAMES[kind[7:]]})"
    texts = {
        "games": "{} oyun oyna",
        "climbed": "Toplam {} m tırman",
        "enemies": "{} düşman yen",
        "coins": "Toplam {} altın topla",
        "stars": "Bölümlerden {} yıldız topla",
    }
    return texts[kind].format(target)


class Wardrobe:
    # Oyuncunun skinleri (storage.py "skins" kaydı): cüzdandaki altın ve elmas, satın alınanlar, seçili skin ve
    # görevi tamamlandığı söylenmiş efsaneviler ("known"). progress = görev sayıları (main.py Game.progress()):
    # {"games", "climbed", "enemies", "coins", "stars", "height-easy", ...}
    DEFAULTS = {"coins": -1, "gems": 0, "owned": [], "selected": DEFAULT_SKIN, "known": []}

    def __init__(self, lifetime_coins):
        data = load_dict("skins", self.DEFAULTS)
        # İlk açılışta cüzdan şimdiye kadar toplanan altınlarla başlar (eski oyunların altınları da sayılsın)
        self.coins = data["coins"] if data["coins"] >= 0 else lifetime_coins
        self.gems = max(0, data["gems"])
        self.owned = [i for i in data["owned"] if i in SKIN_BY_ID]
        self.selected = data["selected"] if data["selected"] in SKIN_BY_ID else DEFAULT_SKIN
        self.known = [i for i in data["known"] if i in SKIN_BY_ID]
        if data["coins"] < 0:
            self.save()

    def save(self):
        save_dict("skins", {
            "coins": self.coins, "gems": self.gems, "owned": self.owned, "selected": self.selected,
            "known": self.known,
        })

    def balance(self, currency):
        # Cüzdanda o paradan kaç tane var ("coins" / "gems")
        return getattr(self, currency)

    def can_afford(self, skin):
        return skin["currency"] is not None and self.balance(skin["currency"]) >= skin["price"]

    def goal_met(self, skin, progress):
        return skin["goal"] is not None and progress[skin["goal"][0]] >= skin["goal"][1]

    def owns(self, skin, progress):
        # Kullanılabilir mi: bedava, satın alınmış ya da görevi tamamlanmış (deneme için hepsi: UNLOCK_ALL_SKINS)
        if UNLOCK_ALL_SKINS or skin["id"] in self.owned:
            return True
        if skin["goal"]:
            return self.goal_met(skin, progress)
        return skin["currency"] is None

    def buy(self, skin):
        # Parası (altın ya da elmas) yetiyorsa satın al ve hemen giy. Alındıysa True
        if skin["goal"] or skin["id"] in self.owned or not self.can_afford(skin):
            return False
        setattr(self, skin["currency"], self.balance(skin["currency"]) - skin["price"])
        self.owned.append(skin["id"])
        self.selected = skin["id"]
        self.save()
        return True

    def select(self, skin_id):
        self.selected = skin_id
        self.save()

    def add_money(self, coins=0, gems=0):
        # Oyun bitince toplanan altın ve kazanılan elmas cüzdana
        if coins or gems:
            self.coins += coins
            self.gems += gems
            self.save()

    def new_unlocks(self, progress):
        # Görevi yeni tamamlanan (daha önce söylenmemiş) efsaneviler — oyun sonu ekranında "Yeni karakter" yazar
        new = [skin for skin in SKINS if self.goal_met(skin, progress) and skin["id"] not in self.known]
        if new:
            self.known += [skin["id"] for skin in new]
            self.save()
        return new


def check_skins():
    # Skin listesinde yanlış bir şey varsa oyun açılırken hemen söyle (çizim boyu, renk harfleri, fiyat, görev)
    ids = [skin["id"] for skin in SKINS]
    if len(ids) != len(set(ids)):
        raise ValueError("skins.py: aynı ada sahip iki skin var")
    if DEFAULT_SKIN not in ids:
        raise ValueError("skins.py: klasik skin yok")
    for group in GROUP_NAMES:
        if not 0 < len(in_group(group)) <= GROUP_SIZE:
            raise ValueError(f"skins.py: '{group}' grubunda 1-{GROUP_SIZE} skin olmalı")
    progress_keys = {"games", "climbed", "enemies", "coins", "stars"} | {f"height-{m}" for m in DIFFICULTY_NAMES}
    for skin in SKINS:
        name = skin["id"]
        legs = skin["legs"] or art.PLAYER_LEGS
        rows = skin["body"] + [row for pair in legs.values() for row in pair]
        if len(skin["body"]) != 10 or set(legs) != set(art.PLAYER_LEGS) or any(len(p) != 2 for p in legs.values()):
            raise ValueError(f"skins.py '{name}': gövde 10 satır, bacaklar 4 resim x 2 satır olmalı")
        if any(len(row) != 10 for row in rows):
            raise ValueError(f"skins.py '{name}': her satır 10 harf olmalı")
        letters = {cell for row in rows for cell in row} - {"."} - {"W", "E", "L"}
        missing = letters - set(skin["palette"])
        if missing or "K" not in skin["palette"]:
            raise ValueError(f"skins.py '{name}': rengi olmayan harf: {sorted(missing) or 'K'}")
        if skin["group"] not in GROUP_NAMES or skin["trail"] not in (None, *TRAILS):
            raise ValueError(f"skins.py '{name}': grup ya da iz yanlış")
        if skin["goal"] and (skin["goal"][0] not in progress_keys or skin["currency"]):
            raise ValueError(f"skins.py '{name}': görev yanlış (görevli skinin fiyatı olmaz)")
        if skin["price"] < 0 or (skin["currency"] is None and not skin["goal"] and name != DEFAULT_SKIN):
            raise ValueError(f"skins.py '{name}': fiyat yanlış (coins= ya da gems= verilmeli)")


check_skins()
