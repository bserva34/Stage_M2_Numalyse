from PySide6.QtCore import QThread, Signal
import cv2
import numpy as np
import os
from scipy.stats import entropy

class SegmentationThread(QThread):
    segmentation_done = Signal(list)  # Signal émis à la fin

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.running = True  # Flag d'arrêt

    def kullback_leibler_divergence(self, p, q):
        epsilon = 1e-10  # Pour éviter division par zéro
        p = np.array(p) + epsilon
        q = np.array(q) + epsilon
        return entropy(p, q)

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print("Impossible d'ouvrir la vidéo.")
            return

        # Création du dossier de sauvegarde
        output_dir = "segmentation"
        os.makedirs(output_dir, exist_ok=True)

        timecodes = []
        prev_hist = None
        prev_image = None
        threshold = 0.7

        # Variables pour stocker le cut en attente
        pending_cut_time = None
        pending_cut_image = None
        pending_prev_image = None
        cpt_cut = 0

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # Utiliser le temps exact fourni par OpenCV
            current_time = cap.get(cv2.CAP_PROP_POS_MSEC)  # Temps en millisecondes

            # Calcul de l'histogramme
            hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                kl_div = self.kullback_leibler_divergence(prev_hist, hist)

                if kl_div > threshold:
                    if pending_cut_time is None:
                        # Premier cut détecté, on le garde en mémoire
                        pending_cut_time = current_time
                        pending_cut_image = frame.copy()
                        pending_prev_image = prev_image.copy() if prev_image is not None else None
                    else:
                        # Un autre cut est détecté juste après → on remplace l'ancien
                        pending_cut_time = current_time
                        pending_cut_image = frame.copy()
                        pending_prev_image = prev_image.copy() if prev_image is not None else None
                else:
                    if pending_cut_time is not None:
                        cpt_cut += 1
                        timecodes.append(pending_cut_time)
                        print(f"Cut validé à {pending_cut_time:.2f} ms")

                        # Sauvegarde des images
                        if pending_prev_image is not None:
                            cv2.imwrite(os.path.join(output_dir, f"s_{cpt_cut}_prev.jpg"), pending_prev_image)
                        cv2.imwrite(os.path.join(output_dir, f"s_{cpt_cut}_current.jpg"), pending_cut_image)

                        # Réinitialiser le cut en attente
                        pending_cut_time = None
                        pending_cut_image = None
                        pending_prev_image = None

            prev_hist = hist
            prev_image = frame.copy()

        # Vérifier s'il reste un cut en attente à la fin
        if pending_cut_time is not None:
            cpt_cut += 1
            timecodes.append(pending_cut_time)
            print(f"Cut final validé à {pending_cut_time:.2f} ms")

            if pending_prev_image is not None:
                cv2.imwrite(os.path.join(output_dir, f"s_{cpt_cut}_prev.jpg"), pending_prev_image)
            cv2.imwrite(os.path.join(output_dir, f"s_{cpt_cut}_current.jpg"), pending_cut_image)

        cap.release()
        if self.running:
            self.segmentation_done.emit(timecodes)
        print("Segmentation arrêtée proprement.")

    def stop(self):
        """Arrête le thread proprement."""
        self.running = False
        self.quit()
        self.wait()

