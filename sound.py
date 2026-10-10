# Sesler ve müzik: dosya yok, hepsi oyun açılırken kodla üretilir (eski atari sesleri gibi).
# Ses kartı yoksa veya bir sorun çıkarsa oyun sessiz çalışır, çökmez.
import array
import random

import pygame

from settings import SOUND_VOLUME, MUSIC_VOLUME, WEB, WEB_AUDIO_BUFFER

SAMPLE_RATE = 22050  # saniyedeki ses örneği sayısı (düşük = daha "retro" ve hızlı üretilir)
MUSIC_TEMPO = 140  # müziğin hızı (dakikadaki vuruş)


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


# --- Müzik: 8 ölçü, her ölçü 8 sekizlik nota; None = sus ---
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


class Sounds:
    def __init__(self):
        self.muted = False
        # Ses seviyeleri (0-1): ses ekranındaki çubuklar. 1 = settings'teki SOUND_VOLUME / MUSIC_VOLUME
        self.music_level = 1.0
        self.effects_level = 1.0
        self.effects = {}
        self.music = None
        self.channels = 0
        try:
            settings = pygame.mixer.get_init()
            # Beklediğimiz biçimde değilse (16 bit değil) sessiz kal
            if settings and settings[1] == -16:
                self.rate, _, self.channels = settings
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

    def note(self, midi, length, kind):
        # Müzik notası: hafif sönerek çalar, sonunda yumuşakça kesilir
        f = freq(midi) / self.rate
        release = length * 0.15
        samples = []
        for i in range(length):
            envelope = 1 - 0.6 * i / length
            if i > length - release:
                envelope *= (length - i) / release
            samples.append(wave(kind, (i * f) % 1.0) * envelope * min(1.0, i / 40))
        return samples

    def to_sound(self, samples, volume):
        # Sayı listesini pygame sesine çevir (16 bit; stereo ise her örnek iki kere)
        data = array.array("h")
        for s in samples:
            value = int(max(-1.0, min(1.0, s)) * 32000)
            data.extend([value] * self.channels)
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
        win = []  # bölüm bitti: kısa zafer melodisi
        for midi, length in ((72, 0.1), (76, 0.1), (79, 0.1), (84, 0.22), (79, 0.1), (84, 0.45)):
            win += t(freq(midi), freq(midi), length, "pulse", 0.45)
        buy = []  # skin satın alındı: yükselen üç "çın"
        for midi, length in ((83, 0.06), (88, 0.06), (95, 0.2)):
            buy += t(freq(midi), freq(midi), length, "pulse", 0.4)
        gem = []  # elmas: parlak, hızlı yükselen çınlama
        for midi in (88, 91, 95, 100):
            gem += t(freq(midi), freq(midi), 0.05, "pulse", 0.35)
        game_over = []
        for midi, length in ((67, 0.2), (64, 0.2), (60, 0.2), (55, 0.6)):
            game_over += t(freq(midi), freq(midi) * 0.98, length, "triangle", 0.8)
        # Boss (Lav Golemi): yere çakılınca gümbürtü, uyanınca kükreme, kafasına basılınca kalın "tank" sesi
        slam = [a + b for a, b in zip(t(0, 0, 0.35, "noise", 0.55), t(110, 35, 0.35, "triangle", 0.9))]
        roar = [a + b for a, b in zip(t(0, 0, 0.7, "noise", 0.3), t(95, 55, 0.7, "square", 0.35))]
        boss_hit = t(330, 90, 0.12, "square", 0.5) + t(520, 160, 0.2, "square", 0.45)
        sounds = {
            "jump": jump,
            "coin": coin,
            "stomp": stomp,
            "hurt": hurt,
            "start": start,
            "game_over": game_over,
            "win": win,
            "life": life,
            "spring": spring,
            "crumble": crumble,
            "shoot": shoot,
            "powerup": powerup,
            "powerdown": powerdown,
            "buy": buy,
            "gem": gem,
            "slam": slam,
            "roar": roar,
            "boss_hit": boss_hit,
        }
        self.effects = {name: self.to_sound(s, SOUND_VOLUME) for name, s in sounds.items()}

    def make_music(self):
        step = int(self.rate * 60 / MUSIC_TEMPO / 2)  # bir sekizlik notanın uzunluğu (örnek sayısı)
        mix = [0.0] * (step * len(MELODY))
        cache = {}  # aynı notayı tekrar tekrar üretmeyelim

        def add(start, midi, length, kind, volume):
            key = (midi, length, kind)
            if key not in cache:
                cache[key] = self.note(midi, length, kind)
            for i, value in enumerate(cache[key]):
                mix[start + i] += value * volume

        for i, midi in enumerate(MELODY):
            if midi is not None:
                add(i * step, midi, step, "pulse", 0.35)
        for i, midi in enumerate(BASS):
            add(i * 2 * step, midi, 2 * step, "triangle", 0.6)
        self.music = self.to_sound(mix, MUSIC_VOLUME)
        # Müzik kendi kanalında çalsın, efektler onu kesmesin
        pygame.mixer.set_reserved(1)
        self.music_channel = pygame.mixer.Channel(0)

    def set_levels(self, music, effects):
        # Müzik ve efekt seviyesini değiştir (0-1); çalan müzik de hemen kısılır/açılır
        self.music_level = music
        self.effects_level = effects
        if self.enabled:
            self.music.set_volume(MUSIC_VOLUME * music)
            for effect in self.effects.values():
                effect.set_volume(SOUND_VOLUME * effects)

    # --- Çalma ---
    def play(self, name):
        if self.enabled and not self.muted:
            self.effects[name].play()

    def start_music(self):
        if self.enabled:
            self.music_channel.play(self.music, loops=-1)  # -1 = sonsuza kadar tekrar
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
