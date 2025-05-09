import cv2
import os

def get_frame_count(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Impossible d'ouvrir la vidéo : {video_path}")
        return None
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return frame_count

def process_videos_in_folder(folder_path):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv') 
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(video_extensions):
            video_path = os.path.join(folder_path, filename)
            frame_count = get_frame_count(video_path)
            if frame_count is not None:
                print(f"{filename} : {frame_count} frames")

# Exemple d'utilisation :
if __name__ == "__main__":
    dossier_videos = "../../Film/BBD_video_varié"  
    process_videos_in_folder(dossier_videos)
