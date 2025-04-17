from PySide6.QtCore import QThread, Signal
import cv2
import os

from scenedetect import detect, AdaptiveDetector, ContentDetector, ThresholdDetector, HistogramDetector, HashDetector, open_video, SceneManager, FrameTimecode
from scenedetect.scene_manager import save_images


class SegmentationThread(QThread):
    segmentation_done = Signal(list)  # Signal émis à la fin

    def __init__(self, video_path,color=True):
        super().__init__()
        self.video_path = video_path
        self.running = True  # Flag d'arrêt
        self.color=color

    #calcul de la seg
    def run(self):
        if not os.path.exists(self.video_path):
            print("Impossible d'ouvrir la vidéo.")
            return

        # output_dir = "segmentation"
        # os.makedirs(output_dir, exist_ok=True)

        video = open_video(self.video_path)
        scene_manager = SceneManager()
        scene_manager.auto_downscale = True #pour réduire la qualité et gagner en temps de calcul
        #scene_manager.add_detector(HistogramDetector())
        if self.color:
            #print("AdaptiveDetector")
            scene_manager.add_detector(AdaptiveDetector())
        else:
            #print("HashDetector")
            scene_manager.add_detector(HashDetector())

        try:
            scene_manager.detect_scenes(video, show_progress=False, callback=self.check_stop)
            scene_list = scene_manager.get_scene_list()
            timecodes = [(scene[0].get_seconds() * 1000,scene[1].get_seconds() * 1000,scene[0].get_frames(),scene[1].get_frames()) for scene in scene_list]
            #save_images(scene_list,video,num_images=1,output_dir=output_dir)
            if self.running:
                self.segmentation_done.emit(timecodes)
        except StopProcessingException:
            print("Segmentation interrompue avant la fin.")

    #fonction de callback
    def check_stop(self, frame_number, frame_time: FrameTimecode):
        """Callback appelé à chaque frame pour vérifier si on doit arrêter."""
        if not self.running:
            print("Interruption de la segmentation...")
            raise StopProcessingException("Segmentation interrompue par l'utilisateur.")
        return True  # Continue l'analyse

    #pour stopper l'exécution du calcul de seg
    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class StopProcessingException(Exception):
    pass