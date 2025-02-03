from PySide6.QtCore import QThread, Signal
import cv2
import numpy as np
import os
from scipy.stats import entropy

from scenedetect import detect, AdaptiveDetector, ContentDetector, ThresholdDetector, HistogramDetector, HashDetector, open_video, SceneManager
from scenedetect.scene_manager import save_images


class SegmentationThread(QThread):
    segmentation_done = Signal(list)  # Signal émis à la fin

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.running = True  # Flag d'arrêt

    def run(self):
        if not os.path.exists(self.video_path):
            print("Impossible d'ouvrir la vidéo.")
            return

        # Création du dossier de sauvegarde
        output_dir = "segmentation"
        os.makedirs(output_dir, exist_ok=True)

        # Utilisation de SceneDetect pour détecter les scènes
        # scene_list = detect(self.video_path, HashDetector(),show_progress=True)
        # timecodes = [scene[0].get_seconds() * 1000 for scene in scene_list]  # Convertir en millisecondes
        # for t in timecodes:
        #     print(t)


        video = open_video(self.video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(HashDetector())
        #on peut ajouter d'autre pour plus de res
        scene_manager.detect_scenes(video,show_progress=True)
        scene_list = scene_manager.get_scene_list()
        timecodes = [scene[0].get_seconds() * 1000 for scene in scene_list]  # Convertir en millisecondes

        #save_images(scene_list,video,num_images=1,output_dir=output_dir)

        if self.running:
            self.segmentation_done.emit(timecodes)
        print("Segmentation arrêtée proprement.")


    def stop(self):
        """Arrête le thread proprement."""
        self.running = False
        self.quit()
        self.wait()

