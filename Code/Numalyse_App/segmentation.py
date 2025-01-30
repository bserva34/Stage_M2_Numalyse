from PySide6.QtCore import QThread, Signal
import cv2
import numpy as np
from scipy.stats import entropy

class SegmentationThread(QThread):
    segmentation_done = Signal(list)  # Signal émis à la fin

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.running = True  # Flag d'arrêt

    def kullback_leibler_divergence(self, p, q):
        epsilon = 1e-10  # Ajout pour éviter les divisions par zéro
        p = np.array(p) + epsilon
        q = np.array(q) + epsilon
        return entropy(p, q)

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print("Impossible d'ouvrir la vidéo.")
            return

        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        timecodes = []
        prev_hist = None
        frame_count = 0
        threshold = 0.1
        min_time_between_cuts = 500  # 500 ms entre deux cuts (pour éviter doublons)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            current_time = (frame_count / frame_rate) * 1000  # Temps en ms

            # Calcul de l'histogramme
            hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                kl_div = self.kullback_leibler_divergence(prev_hist, hist)
                if kl_div > threshold:
                    if not timecodes or (current_time - timecodes[-1]) > min_time_between_cuts:
                        timecodes.append(current_time)
                        print(f"Cut détecté à {current_time:.2f} ms avec KL divergence = {kl_div:.4f}")

            prev_hist = hist

        cap.release()
        if self.running:
            self.segmentation_done.emit(timecodes)
        print("Segmentation arrêtée proprement.")

    def stop(self):
        """Arrête le thread proprement."""
        self.running = False
        self.quit()  # Quitte proprement le thread
        self.wait()  # Attend la fin du thread
