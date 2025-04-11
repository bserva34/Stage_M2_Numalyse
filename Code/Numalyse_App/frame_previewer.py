import cv2
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

class FramePreviewer:
    def __init__(self, label, fps, media_path):

        self.label = label
        self.fps = fps
        self.media_path = media_path

    def get_frame(self, time_ms):

        return int((time_ms / 1000) * self.fps)

    def get_img(self, num_frame):
        cap = cv2.VideoCapture(self.media_path)
        if not cap.isOpened():
            print("Impossible d'ouvrir la vidéo.")
            return None

        cap.set(cv2.CAP_PROP_POS_FRAMES, num_frame)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None

        return frame

    def preview_frame(self, time_ms):
        # Calcul de l'indice de la frame correspondant au temps (en ms)
        frame_index = self.get_frame(time_ms)
        # Récupération de l'image associée à la frame
        frame = self.get_img(frame_index)
        if frame is None:
            while frame is None:
                frame = self.get_img(frame_index-1)
                frame_index-=1

        # Conversion de l'image de BGR (OpenCV) à RGB (Qt)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame_rgb.shape
        bytes_per_line = channels * width

        # Création d'un QImage
        q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        # Conversion en QPixmap et affichage dans le QLabel
        pixmap = QPixmap.fromImage(q_img)
        self.label.setPixmap(pixmap.scaled(320, 240, Qt.KeepAspectRatio))
