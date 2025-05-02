import cv2
import os
import argparse

def extract_10th_frame(video_path, out_dir='keyframes'):
    cap = cv2.VideoCapture(video_path)
    os.makedirs(out_dir, exist_ok=True)
    name_of_video=os.path.splitext(os.path.basename(args.video))[0]

    frame_idx = 0
    target_idx = 9  # 10e frame (index 9 car indexation commence à 0)
    saved = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx == target_idx:
            fname = os.path.join(out_dir, f"{name_of_video}_keyframe_10.jpg")
            cv2.imwrite(fname, frame)
            saved = True
            break
        frame_idx += 1

    cap.release()
    if not saved:
        print("La vidéo contient moins de 10 frames.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extraction de la 10ème frame')
    parser.add_argument('video', help='Chemin vers la vidéo')
    parser.add_argument('--out', default='keyframes', help='Répertoire de sortie')
    args = parser.parse_args()

    extract_10th_frame(args.video, out_dir=args.out)