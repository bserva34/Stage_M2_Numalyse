import cv2
import os
import argparse

def extract_middle_frame(video_path, out_dir='keyframes'):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    middle_index = total_frames-10

    os.makedirs(out_dir, exist_ok=True)
    name_of_video=os.path.splitext(os.path.basename(args.video))[0]


    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_index)
    ret, frame = cap.read()
    if ret:
        fname = os.path.join(out_dir, f"{name_of_video}_keyframe_{middle_index}.jpg")
        cv2.imwrite(fname, frame)
    else:
        print("Impossible de lire la frame du milieu.")

    cap.release()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extraction de la frame du milieu')
    parser.add_argument('video', help='Chemin vers la vidéo')
    parser.add_argument('--out', default='keyframes', help='Répertoire de sortie')
    args = parser.parse_args()

    extract_middle_frame(args.video, out_dir=args.out)