# Kamera: bölüm ekrandan uzunsa karakteri yukarı-aşağı takip eder.
from settings import SCREEN_HEIGHT, CAMERA_SMOOTHNESS, CAMERA_PLAYER_Y


class Camera:
    def __init__(self, level_height):
        self.level_height = level_height
        # Kameranın bölümün tepesinden ne kadar aşağıya kaydığı (piksel)
        self.offset_y = 0.0

    def follow(self, target_rect, instant=False):
        # Karakter ekranın biraz alt tarafında kalsın, yukarısı daha çok görünsün...
        goal = target_rect.centery - SCREEN_HEIGHT * CAMERA_PLAYER_Y
        # ...ama kamera bölümün üstünden/altından dışarı bakmasın
        goal = max(0, min(goal, self.level_height - SCREEN_HEIGHT))

        if instant:
            self.offset_y = goal
        else:
            # Hedefe her karede biraz yaklaş — yumuşak takip
            self.offset_y += (goal - self.offset_y) * CAMERA_SMOOTHNESS

    def apply(self, rect):
        # Bölümdeki konumu ekrandaki konuma çevir
        return rect.move(0, -round(self.offset_y))
