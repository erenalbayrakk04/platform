# Kamera: karakteri yukarı-aşağı takip eder. Yukarısı sonsuz, aşağıda bölümün dibinde durur.
from settings import SCREEN_HEIGHT, CAMERA_SMOOTHNESS, CAMERA_PLAYER_Y


class Camera:
    def __init__(self):
        # Ekranın tepesinin bölümdeki y konumu (yukarı çıktıkça eksiye iner)
        self.offset_y = 0.0

    @property
    def top(self):
        return self.offset_y

    @property
    def bottom(self):
        return self.offset_y + SCREEN_HEIGHT

    def follow(self, target_rect, level_bottom, instant=False):
        # Karakter ekranın biraz alt tarafında kalsın, yukarısı daha çok görünsün...
        goal = target_rect.centery - SCREEN_HEIGHT * CAMERA_PLAYER_Y
        # ...ama kamera bölümün altından dışarı bakmasın
        goal = min(goal, level_bottom - SCREEN_HEIGHT)

        if instant:
            self.offset_y = goal
        else:
            # Hedefe her karede biraz yaklaş — yumuşak takip
            self.offset_y += (goal - self.offset_y) * CAMERA_SMOOTHNESS

    def apply(self, rect):
        # Bölümdeki konumu ekrandaki konuma çevir
        return rect.move(0, -round(self.offset_y))
