# Sesler ve müzik: dosya yok, hepsi oyun açılırken kodla üretilir (eski atari sesleri gibi).
# Ses kartı yoksa veya bir sorun çıkarsa oyun sessiz çalışır, çökmez.
import array
import functools
import operator
import random

import pygame

from settings import SOUND_VOLUME, MUSIC_VOLUME, WEB, WEB_AUDIO_BUFFER

SAMPLE_RATE = 22050  # saniyedeki ses örneği sayısı (düşük = daha "retro" ve hızlı üretilir)
FULL = 32000  # en yüksek ses örneği (16 bit: en fazla 32767)
MUSIC_TEMPO = 140  # oyun müziğinin hızı (dakikadaki vuruş)
TITLE_TEMPO = 120  # açılış müziğinin hızı


def pre_init():
    # pygame.init()'ten ÖNCE çağrılmalı: sesi tek kanal (mono), 16 bit kur.
    # Tarayıcıda ses, oyunla aynı yerde doldurulur; küçük tamponda yetişemez ve cızırdar
    buffer = WEB_AUDIO_BUFFER if WEB else 512
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, buffer)


def freq(midi):
    # Nota numarasından frekans (69 = La = 440 Hz, her +12 bir oktav yukarı)
    return 440 * 2 ** ((midi - 69) / 12)


def wave(kind, phase):
    # Dalga şekli: phase 0-1 arası (bir titreşimin neresindeyiz)
    if kind == "square":  # kare dalga: klasik "bip" sesi
        return 1.0 if phase < 0.5 else -1.0
    if kind == "pulse":  # dar kare dalga: daha ince, müzikte melodi için
        return 1.0 if phase < 0.25 else -1.0
    if kind == "triangle":  # üçgen dalga: yumuşak, bas için
        return 4 * abs(phase - 0.5) - 1
    return random.uniform(-1, 1)  # "noise": hışırtı (çarpma sesi)


def wave_samples(kind, step, length):
    # wave() ile aynı dalga, ama bir notanın bütün örnekleri tek seferde (müzik için; çok daha hızlı üretilir).
    # step = her örnekte titreşimin ne kadar ilerlediği
    if kind == "triangle":
        return [4 * abs((i * step) % 1.0 - 0.5) - 1 for i in range(length)]
    duty = 0.25 if kind == "pulse" else 0.5
    return [1.0 if (i * step) % 1.0 < duty else -1.0 for i in range(length)]


# --- Oyun müziği: 8 ölçü, her ölçü 8 sekizlik nota; None = sus ---
MELODY = [
    72, 76, 79, 76, 84, 79, 76, 79,  # Do
    69, 72, 76, 72, 81, 76, 72, 76,  # La minör
    77, 81, 84, 81, 77, 72, 77, 81,  # Fa
    79, 83, 86, 83, 79, 74, 71, 74,  # Sol
    84, None, 83, 84, 79, None, 76, None,
    81, None, 79, 81, 76, None, 72, None,
    77, 79, 81, 84, 81, 79, 77, 76,
    74, 76, 77, 79, 83, None, 79, None,
]
# Bas: her ölçüde 4 vuruş (kök ve beşli sesler)
BASS = [48, 55, 48, 55, 45, 52, 45, 52, 41, 48, 41, 48, 43, 50, 43, 50] * 2

# --- Açılış müziği (giriş ekranı ve menüler): daha yavaş ve maceralı, La minör. 8 ölçü:
# Lam - Fa - Do - Sol | Lam - Fa - Rem - Mi. İkinci yarıda melodi daha yükseğe tırmanır, sondaki Mi başa bağlanır.
# Melodi: (nota, kaç sekizlik) — her ölçü 8 sekizlik
TITLE_MELODY = [
    (76, 2), (81, 3), (79, 1), (76, 2),  # Lam
    (77, 2), (76, 1), (74, 1), (72, 4),  # Fa
    (76, 2), (79, 3), (77, 1), (76, 2),  # Do
    (74, 1), (76, 1), (74, 2), (71, 4),  # Sol
    (76, 2), (81, 3), (83, 1), (84, 2),  # Lam
    (84, 3), (81, 1), (77, 2), (81, 2),  # Fa
    (81, 3), (79, 1), (77, 2), (74, 2),  # Rem
    (76, 2), (80, 2), (83, 2), (80, 2),  # Mi
]
# Her ölçünün akoru: (bas notası, akorun dört notası: kök, üçlü, beşli, oktav). Arpej (akorun notaları tek tek)
# ve bas bunlardan üretilir
TITLE_CHORDS = [
    (45, (57, 60, 64, 69)),  # Lam
    (41, (53, 57, 60, 65)),  # Fa
    (48, (60, 64, 67, 72)),  # Do
    (43, (55, 59, 62, 67)),  # Sol
    (45, (57, 60, 64, 69)),  # Lam
    (41, (53, 57, 60, 65)),  # Fa
    (38, (50, 53, 57, 62)),  # Rem
    (40, (52, 56, 59, 64)),  # Mi
]
ARPEGGIO = (0, 1, 2, 3, 2, 1, 0, 1)  # her ölçüde akorun notaları bu sırayla, sekizlik sekizlik çalınır


class Sounds:
    def __init__(self):
        self.muted = False
        # Ses seviyeleri (0-1): ses ekranındaki çubuklar. 1 = settings'teki SOUND_VOLUME / MUSIC_VOLUME
        self.music_level = 1.0
        self.effects_level = 1.0
        self.effects = {}
        self.musics = {}  # "title" (açılış: giriş ekranı ve menüler), "game" (oyun)
        self.track = None  # şu an çalan müzik
        self.channels = 0
        try:
            settings = pygame.mixer.get_init()
            # Beklediğimiz biçimde değilse (16 bit değil) sessiz kal
            if settings and settings[1] == -16:
                rate, _, self.channels = settings
                # Tarayıcı sesi kendi hızında çalar (çoğunlukla 48000): orada sesler yarı hızda üretilip her örnek
                # iki kez yazılır — iki kat çabuk hazırlanır, kulağa bilgisayardaki (22050) gibi gelir
                self.repeat = 2 if rate > 32000 else 1
                self.rate = rate // self.repeat
                self.make_effects()
                self.make_music()
        except pygame.error:
            self.channels = 0

    @property
    def enabled(self):
        return self.channels > 0

    # --- Ses üretme ---
    def tone(self, f_start, f_end, duration, kind="square", volume=1.0):
        # f_start'tan f_end'e kayan, giderek sönen bir ses (sayı listesi, -1..1 arası)
        n = int(self.rate * duration)
        samples = []
        phase = 0.0
        for i in range(n):
            t = i / n
            phase = (phase + (f_start + (f_end - f_start) * t) / self.rate) % 1.0
            fade_in = min(1.0, i / 40)  # başta "çıt" sesi olmasın
            samples.append(wave(kind, phase) * volume * fade_in * (1 - t))
        return samples

    def note(self, midi, length, kind, volume, cache):
        # Müzik notası: hafif sönerek çalar, sonunda yumuşakça kesilir. Doğrudan 16 bit ölçeğinde (en fazla
        # FULL × volume). Notanın yüksekliğinin zamanla değişimi (zarf) aynı uzunluktaki notalarda aynı: bir kere
        # hesaplanır (cache)
        key = ("zarf", length, volume)
        if key not in cache:
            release = length * 0.15
            top = FULL * volume
            # Başta yumuşak giriş ("çıt" olmasın), giderek söner, sonda yumuşakça kesilir
            cache[key] = [
                top * (1 - 0.6 * i / length) * min(1.0, i / 40, (length - i) / release) for i in range(length)
            ]
        samples = wave_samples(kind, freq(midi) / self.rate, length)
        return array.array("d", [value * level for value, level in zip(samples, cache[key])])

    def to_sound(self, samples, volume):
        # Sayıları (-1..1, dışına taşan kırpılır) pygame sesine çevir
        return self.make_sound(
            array.array("h", [int(FULL * (1.0 if s > 1.0 else -1.0 if s < -1.0 else s)) for s in samples]), volume
        )

    def make_sound(self, mono, volume):
        # 16 bitlik örneklerden pygame sesi: her örnek "repeat" kez (bkz. __init__) ve stereo ise iki kanala yazılır
        copies = self.repeat * self.channels
        if copies > 1:
            data = array.array("h", [0]) * (len(mono) * copies)
            for i in range(copies):
                data[i::copies] = mono
        else:
            data = mono
        sound = pygame.mixer.Sound(buffer=data.tobytes())
        sound.set_volume(volume)
        return sound

    def make_effects(self):
        t = self.tone
        jump = t(280, 560, 0.13, volume=0.5)
        coin = t(988, 988, 0.06, volume=0.4) + t(1319, 1319, 0.22, volume=0.4)
        stomp = t(600, 120, 0.16, volume=0.6)
        hurt = [a + b for a, b in zip(t(0, 0, 0.3, "noise", 0.4), t(220, 70, 0.3, volume=0.5))]
        start = []
        for midi in (72, 76, 79, 84):
            start += t(freq(midi), freq(midi), 0.08, volume=0.4)
        spring = t(150, 750, 0.3, "triangle", 0.9)
        crumble = [
            a + b for a, b in zip(t(0, 0, 0.25, "noise", 0.5), t(180, 60, 0.25, "triangle", 0.5))
        ]
        shoot = [a + b for a, b in zip(t(0, 0, 0.14, "noise", 0.35), t(420, 140, 0.14, volume=0.3))]
        life = []
        for midi in (72, 76, 79, 84, 88):
            life += t(freq(midi), freq(midi), 0.06, "pulse", 0.4)
        powerup = []
        for midi in (60, 64, 67, 72, 76, 79, 84):
            powerup += t(freq(midi), freq(midi + 1), 0.04, "square", 0.35)
        powerdown = []
        for midi in (79, 72, 67, 60):
            powerdown += t(freq(midi), freq(midi), 0.06, "triangle", 0.6)
        game_over = []
        for midi, length in ((67, 0.2), (64, 0.2), (60, 0.2), (55, 0.6)):
            game_over += t(freq(midi), freq(midi) * 0.98, length, "triangle", 0.8)
        sounds = {
            "jump": jump,
            "coin": coin,
            "stomp": stomp,
            "hurt": hurt,
            "start": start,
            "game_over": game_over,
            "life": life,
            "spring": spring,
            "crumble": crumble,
            "shoot": shoot,
            "powerup": powerup,
            "powerdown": powerdown,
        }
        self.effects = {name: self.to_sound(s, SOUND_VOLUME) for name, s in sounds.items()}

    def make_music(self):
        # Her müzik birkaç sesten (dalga şekli, yükseklik) oluşur; notalar (nota numarası, kaç sekizlik)
        game = [
            ([(midi, 1) for midi in MELODY], "pulse", 0.35),
            ([(midi, 2) for midi in BASS], "triangle", 0.6),
        ]
        title = [
            (TITLE_MELODY, "pulse", 0.3),
            ([(chord[i], 1) for _, chord in TITLE_CHORDS for i in ARPEGGIO], "square", 0.1),
            # Bas her ölçüde: kök (uzun), kök (kısa), beşli (7 yarım ses yukarı)
            ([note for bass, _ in TITLE_CHORDS for note in ((bass, 3), (bass, 1), (bass + 7, 4))], "triangle", 0.5),
        ]
        cache = {}  # aynı nota iki müzikte de bir kere üretilsin
        self.musics = {"title": self.song(title, TITLE_TEMPO, cache), "game": self.song(game, MUSIC_TEMPO, cache)}
        # Müzik kendi kanalında çalsın, efektler onu kesmesin
        pygame.mixer.set_reserved(1)
        self.music_channel = pygame.mixer.Channel(0)

    def song(self, voices, tempo, cache):
        # Sesleri (melodi, arpej, bas) üst üste koyup döngü müziği yap. voices = [(notalar, dalga şekli, yükseklik)].
        # Her sesin notaları art arda eklenir, sonra sesler örnek örnek toplanır
        step = int(self.rate * 60 / tempo / 2)  # bir sekizlik notanın uzunluğu (örnek sayısı)
        tracks = []
        for notes, kind, volume in voices:
            track = array.array("d")
            for midi, eighths in notes:
                length = eighths * step
                key = (midi, length, kind, volume)
                if key not in cache:
                    silence = midi is None
                    cache[key] = array.array("d", [0.0]) * length if silence else self.note(*key, cache)
                track += cache[key]
            tracks.append(track)
        if len({len(track) for track in tracks}) > 1:
            raise ValueError("Müziğin sesleri aynı uzunlukta olmalı (sound.py: her ölçü 8 sekizlik)")
        if sum(volume for _, _, volume in voices) > 1:
            raise ValueError("Müziğin seslerinin yükseklikleri toplamı 1'i geçmemeli (sound.py)")
        # Sesler örnek örnek toplanır (yükseklikler toplamı 1'i geçmediği için taşma olmaz)
        mix = functools.reduce(lambda total, track: map(operator.add, total, track), tracks)
        return self.make_sound(array.array("h", map(int, mix)), MUSIC_VOLUME)

    def set_levels(self, music, effects):
        # Müzik ve efekt seviyesini değiştir (0-1); çalan müzik de hemen kısılır/açılır
        self.music_level = music
        self.effects_level = effects
        if self.enabled:
            for song in self.musics.values():
                song.set_volume(MUSIC_VOLUME * music)
            for effect in self.effects.values():
                effect.set_volume(SOUND_VOLUME * effects)

    # --- Çalma ---
    def play(self, name):
        if self.enabled and not self.muted:
            self.effects[name].play()

    def play_music(self, name):
        # "title" (açılış müziği: giriş ekranı ve menüler) veya "game" (oyun). O müzik zaten çalıyorsa baştan başlamaz
        if not self.enabled or (name == self.track and self.music_channel.get_busy()):
            return
        self.track = name
        self.music_channel.play(self.musics[name], loops=-1)  # -1 = sonsuza kadar tekrar
        if self.muted:
            self.music_channel.pause()

    def stop_music(self):
        if self.enabled:
            self.music_channel.stop()

    def toggle_mute(self):
        self.muted = not self.muted
        if self.enabled:
            if self.muted:
                self.music_channel.pause()
            else:
                self.music_channel.unpause()
