# Kontroller: klavye + ekrandaki dokunmatik butonlar tek bir yerde birleşir.
# Karakter sadece "sola mı, sağa mı, zıplıyor mu" bilgisini alır; nereden geldiğini bilmez.
from collections import namedtuple

import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SHOW_TOUCH_BUTTONS,
    TOUCH_BUTTON_SIZE,
    TOUCH_BUTTON_MARGIN,
    TOUCH_BUTTON_ALPHA,
    WHITE,
)

Controls = namedtuple("Controls", "left right jump")


class TouchButtons:
    def __init__(self):
        size = TOUCH_BUTTON_SIZE
        y = SCREEN_HEIGHT - TOUCH_BUTTON_MARGIN - size
        # Sol altta ← →, sağ altta zıplama
        self.buttons = {
            "left": pygame.Rect(TOUCH_BUTTON_MARGIN, y, size, size),
            "right": pygame.Rect(TOUCH_BUTTON_MARGIN * 2 + size, y, size, size),
            "jump": pygame.Rect(SCREEN_WIDTH - TOUCH_BUTTON_MARGIN - size, y, size, size),
        }
        # Ekrana değen parmaklar: parmak numarası → (x, y) — aynı anda yürüyüp zıplayabilmek için
        self.fingers = {}
        self.pressed = set()
        self.images = {
            (name, down): self.make_image(name, down) for name in self.buttons for down in (False, True)
        }

    def handle_event(self, event):
        # Parmak konumları 0-1 arası gelir, ekran pikseline çeviriyoruz
        if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION):
            self.fingers[event.finger_id] = (event.x * SCREEN_WIDTH, event.y * SCREEN_HEIGHT)
        elif event.type == pygame.FINGERUP:
            self.fingers.pop(event.finger_id, None)

    def update(self):
        # Hangi butonlara basılıyor? Parmak yoksa farenin sol tuşu da parmak gibi sayılır
        points = list(self.fingers.values())
        if not points and pygame.mouse.get_pressed()[0]:
            points.append(pygame.mouse.get_pos())
        # Kolay basılsın diye dokunma alanı butondan biraz büyük
        self.pressed = {
            name
            for name, rect in self.buttons.items()
            if any(rect.inflate(16, 16).collidepoint(p) for p in points)
        }

    def make_image(self, name, down):
        size = TOUCH_BUTTON_SIZE
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        alpha = min(255, TOUCH_BUTTON_ALPHA * (3 if down else 1))
        r = size // 2
        pygame.draw.circle(image, (*WHITE, alpha), (r, r), r)
        pygame.draw.circle(image, (*WHITE, min(255, alpha * 2)), (r, r), r, 3)
        # Ok işareti: sol, sağ veya yukarı
        arrow_color = (*WHITE, min(255, 90 + alpha * 2))
        a = size // 5
        if name == "left":
            points = [(r - a, r), (r + a // 2, r - a), (r + a // 2, r + a)]
        elif name == "right":
            points = [(r + a, r), (r - a // 2, r - a), (r - a // 2, r + a)]
        else:
            points = [(r, r - a), (r - a, r + a // 2), (r + a, r + a // 2)]
        pygame.draw.polygon(image, arrow_color, points)
        return image

    def draw(self, screen):
        if SHOW_TOUCH_BUTTONS:
            for name, rect in self.buttons.items():
                screen.blit(self.images[(name, name in self.pressed)], rect)


def read_controls(touch):
    # Klavye: ok tuşları / A-D yürür, Boşluk / Yukarı / W zıplar. Dokunmatik butonlar da eklenir.
    keys = pygame.key.get_pressed()
    touch_on = touch.pressed if SHOW_TOUCH_BUTTONS else set()
    return Controls(
        left=keys[pygame.K_LEFT] or keys[pygame.K_a] or "left" in touch_on,
        right=keys[pygame.K_RIGHT] or keys[pygame.K_d] or "right" in touch_on,
        jump=keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w] or "jump" in touch_on,
    )
