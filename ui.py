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
    WHITE,
)
from score import draw_text

ACTIVATE_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
UP_KEYS = (pygame.K_UP, pygame.K_w)
DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)

# Son tıklamanın zamanı: telefonda bir dokunuş hem "parmak" hem "fare" olayı olarak gelebilir,
# aynı dokunuş iki kez sayılmasın (ör. ses düğmesi açıp hemen geri kapatmasın)
_last_click = [-BUTTON_CLICK_GAP]
_fonts = {}


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

    def draw(self, screen, labels):
        # labels: düğme adı → üstünde yazacak yazı
        if BUTTON_FONT_SIZE not in _fonts:
            _fonts[BUTTON_FONT_SIZE] = pygame.font.Font(None, BUTTON_FONT_SIZE)
        font = _fonts[BUTTON_FONT_SIZE]
        for i, (action, rect) in enumerate(zip(self.actions, self.rects)):
            focused = i == self.focus
            pygame.draw.rect(screen, BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR, rect, border_radius=12)
            border = BUTTON_FOCUS_BORDER_COLOR if focused else BUTTON_BORDER_COLOR
            pygame.draw.rect(screen, border, rect, 3, border_radius=12)
            draw_text(screen, font, labels.get(action, action), center=rect.center)


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
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, self.rect, border_radius=radius)
        knob_x = self.rect.left + self.rect.width * self.value // VOLUME_STEPS
        fill = self.rect.copy()
        fill.width = knob_x - self.rect.left
        if fill.width > 0:
            color = SLIDER_MUTED_COLOR if muted else SLIDER_FILL_COLOR
            pygame.draw.rect(screen, color, fill, border_radius=radius)
        border = BUTTON_FOCUS_BORDER_COLOR if focused else BUTTON_BORDER_COLOR
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=radius)
        knob = (knob_x, self.rect.centery)
        pygame.draw.circle(screen, BUTTON_FOCUS_COLOR if focused else BUTTON_COLOR, knob, SLIDER_KNOB_RADIUS)
        pygame.draw.circle(screen, border if focused else WHITE, knob, SLIDER_KNOB_RADIUS, 3)
