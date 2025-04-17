import os
from scenedetect import open_video, SceneManager, FrameTimecode
from scenedetect.detectors import AdaptiveDetector, ContentDetector, ThresholdDetector, HistogramDetector, HashDetector

def process_video_with_detector(video_path, detector_class, output_dir):
    print(f"Traitement de {video_path} avec {detector_class.__name__}...")
    
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.auto_downscale = True
    detector = detector_class()
    scene_manager.add_detector(detector)
    
    try:
        scene_manager.detect_scenes(video, show_progress=False)
    except Exception as e:
        print(f"Erreur lors du traitement de {video_path} avec {detector_class.__name__} : {e}")
        return
    
    scene_list = scene_manager.get_scene_list()
    video_basename = os.path.splitext(os.path.basename(video_path))[0]
    output_file = os.path.join(output_dir, f"{video_basename}_{detector_class.__name__}.txt")
    
    with open(output_file, "w") as f:
        for scene in scene_list:
            start, end = scene
            f.write(f"{start.get_frames()}\t{end.get_frames()}\n")
    
    print(f"Résultats enregistrés dans {output_file}")

def process_videos_in_directory(directory, output_dir):
    # Utilisez exist_ok=True pour éviter une exception si le dossier existe déjà
    os.makedirs(output_dir, exist_ok=True)
    
    video_files = [f for f in os.listdir(directory) if f.lower().endswith(('.mp4', '.avi', '.mkv'))]
    detector_classes = [AdaptiveDetector, ContentDetector, ThresholdDetector, HistogramDetector, HashDetector]
    
    for video in video_files:
        video_path = os.path.join(directory, video)
        for detector_class in detector_classes:
            process_video_with_detector(video_path, detector_class, output_dir)

if __name__ == "__main__":
    # Utilisation de chaînes brutes pour éviter les problèmes d'échappement
    # input_directory = r"../../../../../../media/bserva34/Extreme SSD/Transition"  # Dossier source de vos vidéos
    # output_directory = r"../../../../../../media/bserva34/Extreme SSD/Transition/Res"  # Dossier de sortie
    input_directory = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/AutoShot/videos/AutoShot_gray"  # Dossier source de vos vidéos
    output_directory = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/AutoShot_gray_res"  # Dossier de sortie
    
    process_videos_in_directory(input_directory, output_directory)
