# Kamera: bölüm ekrandan genişse karakteri takip eder.
from settings import SCREEN_WIDTH, CAMERA_SMOOTHNESS


class Camera:
    def __init__(self, level_width):
        self.level_width = level_width
        # Kameranın bölümün ne kadar sağına kaydığı (piksel)
        self.offset_x = 0.0

    def follow(self, target_rect, instant=False):
        # Karakter ekranın ortasında kalsın...
        goal = target_rect.centerx - SCREEN_WIDTH / 2
        # ...ama kamera bölümün kenarlarından dışarı bakmasın
        goal = max(0, min(goal, self.level_width - SCREEN_WIDTH))

        if instant:
            self.offset_x = goal
        else:
            # Hedefe her karede biraz yaklaş — yumuşak takip
            self.offset_x += (goal - self.offset_x) * CAMERA_SMOOTHNESS

    def apply(self, rect):
        # Bölümdeki konumu ekrandaki konuma çevir
        return rect.move(-round(self.offset_x), 0)
