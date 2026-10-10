# Menü düğmeleri: dokunarak, fareyle veya klavyeyle (yukarı/aşağı + Enter/Boşluk) seçilir.
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    BUTTON_FONT_SIZE,
    BUTTON_COLOR,
    BUTTON_FOCUS_COLOR,
    BUTTON_BORDER_COLOR,
    BUTTON_FOCUS_BORDER_COLOR,
    BUTTON_CLICK_GAP,
    PAUSE_BUTTON_SIZE,
    VOLUME_STEPS,
    SLIDER_HEIGHT,
    SLIDER_KNOB_RADIUS,
    SLIDER_TRACK_COLOR,
    SLIDER_FILL_COLOR,
    SLIDER_MUTED_COLOR,
    LOCKED_COLOR,
    DIFFICULTY_NAMES,
    HINT_COLOR,
    WHITE,
)
from score import draw_text
from lang import mark
import art
import theme

ACTIVATE_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)

# Son tıklamanın zamanı: telefonda bir dokunuş hem "parmak" hem "fare" olayı olarak gelebilir,
# aynı dokunuş iki kez sayılmasın (ör. ses düğmesi açıp hemen geri kapatmasın)
_last_click = [-BUTTON_CLICK_GAP]
_fonts = {}
DISABLED_TEXT_COLOR = HINT_COLOR  # basılamayan düğmenin yazısı


def click_pos(event):
    # Olay bir dokunuş / sol tık ise ekrandaki yerini döndür, değilse None
    if event.type == pygame.FINGERDOWN:
        return (event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT)
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        return event.pos
    return None


def take_click():
    # Bu tıklama sayılsın mı (bir öncekine çok yakınsa aynı dokunuştur)
    now = pygame.time.get_ticks()
    if now - _last_click[0] < BUTTON_CLICK_GAP:
        return False
    _last_click[0] = now
    return True


_boxes = {}


def draw_box(screen, rect, fill, border, border_width=3, radius=12):
    # Düğme / kutu / sekme. Nostalji: düz renk + kenar çizgisi. Modern: altında yumuşak gölge, içi renk geçişli,
    # seçiliyse (altın kenar) etrafı parlar — resmi her boy ve renk için bir kere hazırlanır (modern.box_image)
    if not theme.modern():
        pygame.draw.rect(screen, fill, rect, border_radius=radius)
        pygame.draw.rect(screen, border, rect, border_width, border_radius=radius)
        return
    import modern

    glow = border if border == BUTTON_FOCUS_BORDER_COLOR else None
    key = (rect.size, fill, border, border_width, radius)
    image = theme.cached(_boxes, key, lambda: modern.box_image(rect.size, fill, border, border_width, radius, glow))
    screen.blit(image, (rect.x - modern.BOX_SHADOW, rect.y - modern.BOX_SHADOW))


class Buttons:
    # Alt alta dizilmiş düğmeler. actions = düğmelerin adları (sırayla), top = ilk düğmenin ortası,
    # gap = iki düğmenin ortası arası
    def __init__(self, actions, top, gap=BUTTON_HEIGHT + 12):
        self.actions = list(actions)
        self.rects = [
            pygame.Rect(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT).move(
                (SCREEN_WIDTH - BUTTON_WIDTH) // 2, top + i * gap - BUTTON_HEIGHT // 2
            )
            for i in range(len(self.actions))
        ]
        self.focus = 0  # klavyeyle seçili olan düğme

    def handle_event(self, event):
        # Bir düğme seçildiyse adını döndürür, yoksa None
        if event.type == pygame.KEYDOWN:
            if event.key in UP_KEYS:
                self.focus = (self.focus - 1) % len(self.actions)
            elif event.key in DOWN_KEYS:
                self.focus = (self.focus + 1) % len(self.actions)
            elif event.key in ACTIVATE_KEYS and take_click():
                return self.actions[self.focus]
            return None
        if event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(event.pos):
                    self.focus = i
            return None
        pos = click_pos(event)
        if pos is None:
            return None
        for i, rect in enumerate(self.rects):
            if rect.inflate(0, 8).collidepoint(pos) and take_click():
                self.focus = i
                return self.actions[i]
        return None

    def draw(self, screen, labels, disabled=()):
        # labels: düğme adı → üstünde yazacak yazı; disabled = şu an işe yaramayan düğmeler (gri görünür)
        if BUTTON_FONT_SIZE not in _fonts:
            _fonts[BUTTON_FONT_SIZE] = pygame.font.Font(None, BUTTON_FONT_SIZE)
        font = _fonts[BUTTON_FONT_SIZE]
        for i, (action, rect) in enumerate(zip(self.actions, self.rects)):
            focused = i == self.focus
            off = action in disabled
            fill = LOCKED_COLOR if off else BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR
            border = BUTTON_FOCUS_BORDER_COLOR if focused else BUTTON_BORDER_COLOR
            draw_box(screen, rect, fill, border)
            draw_text(screen, font, labels.get(action, action), DISABLED_TEXT_COLOR if off else WHITE, center=rect.center)


class PauseButton:
    # Oyun sırasında sağ üstteki durdur (⏸) düğmesi
    def __init__(self):
        size = PAUSE_BUTTON_SIZE
        self.rect = pygame.Rect(SCREEN_WIDTH - 12 - size, 10, size, size)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (0, 0, 0, 110), self.image.get_rect(), border_radius=8)
        pygame.draw.rect(self.image, (*WHITE, 200), self.image.get_rect(), 2, border_radius=8)
        bar_w, bar_h = size // 6, size // 2
        for x in (size // 2 - bar_w - 3, size // 2 + 3):
            self.image.fill((*WHITE, 230), (x, (size - bar_h) // 2, bar_w, bar_h))

    def clicked(self, event):
        # Dokunma alanı biraz büyük olsun (küçük düğme)
        pos = click_pos(event)
        return pos is not None and self.rect.inflate(16, 16).collidepoint(pos) and take_click()

    def draw(self, screen):
        screen.blit(self.image, self.rect)


def finger_pos(event):
    # Parmak / fare olayının ekrandaki yeri (parmakta x, y 0-1 arası gelir)
    return (event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT)


class Slider:
    # Kaydırma çubuğu (ses seviyesi): parmakla / fareyle sürüklenir veya çubuğa dokunulur,
    # klavyede seçiliyken sol/sağ ok ile ayarlanır. value = 0..VOLUME_STEPS
    def __init__(self, center_y, value=VOLUME_STEPS):
        self.rect = pygame.Rect(0, 0, BUTTON_WIDTH, SLIDER_HEIGHT)
        self.rect.center = (SCREEN_WIDTH // 2, center_y)
        self.value = value
        self.dragging = False

    def touch_area(self):
        # Çubuk ince; dokunulacak alan daha büyük olsun
        return self.rect.inflate(2 * SLIDER_KNOB_RADIUS, 40)

    def set_from_x(self, x):
        # Ekrandaki x'e en yakın basamağı seç. Değer değiştiyse True
        fraction = (x - self.rect.left) / self.rect.width
        value = max(0, min(VOLUME_STEPS, round(fraction * VOLUME_STEPS)))
        changed = value != self.value
        self.value = value
        return changed

    def nudge(self, step):
        # Bir basamak aç (+1) / kıs (-1). Değer değiştiyse True
        value = max(0, min(VOLUME_STEPS, self.value + step))
        changed = value != self.value
        self.value = value
        return changed

    def handle_event(self, event):
        # Değer değiştiyse True. Telefonda aynı dokunuş hem parmak hem fare olayı olarak gelebilir;
        # ikisi de aynı yeri gösterdiği için zararı yok
        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            pos = click_pos(event)
            if pos is not None and self.touch_area().collidepoint(pos):
                self.dragging = True
                return self.set_from_x(pos[0])
        elif event.type in (pygame.FINGERUP, pygame.MOUSEBUTTONUP):
            self.dragging = False
        elif self.dragging and event.type == pygame.FINGERMOTION:
            return self.set_from_x(finger_pos(event)[0])
        elif self.dragging and event.type == pygame.MOUSEMOTION and event.buttons[0]:
            return self.set_from_x(event.pos[0])
        return False

    def draw(self, screen, focused=False, muted=False):
        radius = SLIDER_HEIGHT // 2
        knob_x = self.rect.left + self.rect.width * self.value // VOLUME_STEPS
        border = BUTTON_FOCUS_BORDER_COLOR if focused else BUTTON_BORDER_COLOR
        fill = self.rect.copy()
        fill.width = knob_x - self.rect.left
        color = SLIDER_MUTED_COLOR if muted else SLIDER_FILL_COLOR
        if theme.modern():  # gölgeli çubuk, dolu kısmı içinde; yuvarlak düğme resmi (modern.knob_image)
            import modern

            draw_box(screen, self.rect, SLIDER_TRACK_COLOR, border, 2, radius)
            if fill.width > 4:
                pygame.draw.rect(screen, color, fill.inflate(-4, -4).move(2, 0), border_radius=radius - 2)
            knob = theme.cached(_boxes, ("knob", focused), lambda: modern.knob_image(
                SLIDER_KNOB_RADIUS, BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR, border if focused else WHITE
            ))
            screen.blit(knob, knob.get_rect(center=(knob_x, self.rect.centery + 1)))
            return
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, self.rect, border_radius=radius)
        if fill.width > 0:
            pygame.draw.rect(screen, color, fill, border_radius=radius)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=radius)
        knob = (knob_x, self.rect.centery)
        pygame.draw.circle(screen, BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR, knob, SLIDER_KNOB_RADIUS)
        pygame.draw.circle(screen, border if focused else WHITE, knob, SLIDER_KNOB_RADIUS, 3)


class StageGrid:
    # Bölüm seçme: üstte zorluk sekmeleri, numaralı kutular (COLUMNS sütun), altlarında kazanılan yıldızlar;
    # en altta Geri düğmesi. Kilitli bölümün kutusu gri ve asma kilitli. Dokunma/fare veya klavye (oklar +
    # Enter) ile seçilir; focus = -1 → sekmeler (sağ/sol zorluğu değiştirir), count → Geri düğmesi
    COLUMNS = 4
    SIZE = 72  # kutunun kenarı (piksel)
    GAP = 12  # kutular arası
    TOP = 150  # ilk satırın üst kenarı
    STAR_SIZE = 16
    TAB_Y = 88  # sekmelerin ortası
    TAB_HEIGHT = 36
    TAB_GAP = 8
    TAB_FONT_SIZE = 22

    def __init__(self, count, modes, back_top):
        self.count = count
        self.modes = modes  # sekmelerdeki zorluk modları (soldan sağa)
        width = self.COLUMNS * self.SIZE + (self.COLUMNS - 1) * self.GAP
        left = (SCREEN_WIDTH - width) // 2
        step = self.SIZE + self.GAP
        self.rects = [
            pygame.Rect(left + (i % self.COLUMNS) * step, self.TOP + (i // self.COLUMNS) * step, self.SIZE, self.SIZE)
            for i in range(count)
        ]
        tabs_width = SCREEN_WIDTH - 40
        tab_width = (tabs_width - (len(modes) - 1) * self.TAB_GAP) // len(modes)
        self.tabs = [
            pygame.Rect(20 + i * (tab_width + self.TAB_GAP), self.TAB_Y - self.TAB_HEIGHT // 2, tab_width, self.TAB_HEIGHT)
            for i in range(len(modes))
        ]
        self.back = Buttons(["back"], top=back_top)
        self.set_focus(0)

    def set_focus(self, index):
        self.focus = index
        self.back.focus = 0 if index == self.count else -1

    def move(self, step):
        # Klavyeyle seçimi kaydır (sağ-sol 1, yukarı-aşağı bir satır); sekmeler en üstte, Geri en altta
        if self.focus == self.count:
            if step < 0:  # Geri'den yukarı/sola → son bölüm
                self.set_focus(self.count - 1)
            return
        if self.focus < 0:
            if step == self.COLUMNS:
                self.set_focus(0)
            return
        target = self.focus + step
        if target >= self.count:
            target = self.count  # en alt satırdan aşağı → Geri
        elif target < 0:
            target = -1 if step == -self.COLUMNS else 0  # ilk satırdan yukarı → sekmeler
        self.set_focus(target)

    def handle_event(self, event, unlocked, mode):
        # Seçilen bölümün sırası, kilitliyse "locked", Geri'ye basıldıysa "back", sekmeden zorluk seçildiyse
        # o zorluk ("easy"...), yoksa None. unlocked(i) = i. bölüm açık mı, mode = şu anki zorluk
        if event.type == pygame.KEYDOWN:
            if self.focus < 0 and event.key in LEFT_KEYS + RIGHT_KEYS:
                index = self.modes.index(mode) + (-1 if event.key in LEFT_KEYS else 1)
                return self.modes[index] if 0 <= index < len(self.modes) else None
            steps = {LEFT_KEYS: -1, RIGHT_KEYS: 1, UP_KEYS: -self.COLUMNS, DOWN_KEYS: self.COLUMNS}
            for keys, step in steps.items():
                if event.key in keys:
                    self.move(step)
            if event.key in ACTIVATE_KEYS and self.focus >= 0 and take_click():
                if self.focus == self.count:
                    return "back"
                return self.focus if unlocked(self.focus) else "locked"
            return None
        if event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(event.pos):
                    self.set_focus(i)
            if self.back.rects[0].collidepoint(event.pos):
                self.set_focus(self.count)
            return None
        pos = click_pos(event)
        if pos is None:
            return None
        for i, rect in enumerate(self.tabs):
            if rect.inflate(0, 8).collidepoint(pos) and take_click():
                return self.modes[i]
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos) and take_click():
                self.set_focus(i)
                return i if unlocked(i) else "locked"
        if self.back.handle_event(event) == "back":
            return "back"
        return None

    def draw(self, screen, stars, unlocked, mode):
        # stars[i] = i. bölümün en iyi yıldızı (0-3), mode = seçili zorluk (sekmesi yanar)
        for size in (BUTTON_FONT_SIZE + 8, self.TAB_FONT_SIZE):
            if size not in _fonts:
                _fonts[size] = pygame.font.Font(None, size)
        images = theme.cached(_boxes, "stage_grid", lambda: {
            "lock": art.lock_image(),
            True: art.star_image(True, self.STAR_SIZE),
            False: art.star_image(False, self.STAR_SIZE),
        })
        # Zorluk sekmeleri
        for name, rect in zip(self.modes, self.tabs):
            selected = name == mode
            border = BUTTON_FOCUS_BORDER_COLOR if selected and self.focus < 0 else BUTTON_BORDER_COLOR
            draw_box(screen, rect, BUTTON_FOCUS_COLOR if selected else BUTTON_COLOR, border, 3 if selected else 2, 10)
            color = BUTTON_FOCUS_BORDER_COLOR if selected else WHITE
            draw_text(screen, _fonts[self.TAB_FONT_SIZE], DIFFICULTY_NAMES[name], color, center=rect.center)
        font = _fonts[BUTTON_FONT_SIZE + 8]
        for i, rect in enumerate(self.rects):
            focused = i == self.focus
            is_open = unlocked(i)
            fill = (BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR) if is_open else LOCKED_COLOR
            border = BUTTON_FOCUS_BORDER_COLOR if focused else BUTTON_BORDER_COLOR
            draw_box(screen, rect, fill, border)
            if not is_open:
                lock = images["lock"]
                screen.blit(lock, lock.get_rect(center=rect.center))
                continue
            draw_text(screen, font, str(i + 1), center=(rect.centerx, rect.centery - 9))
            # Altta 3 yıldız: kazanılanlar sarı
            for k in range(3):
                star = images[k < stars[i]]
                x = rect.centerx + (k - 1) * (self.STAR_SIZE + 3)
                screen.blit(star, star.get_rect(center=(x, rect.bottom - 14)))
        self.back.draw(screen, {"back": mark("Geri")})
