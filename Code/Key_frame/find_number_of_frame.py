import cv2
import numpy as np

def find_matching_frame(video_path, image_path, method='hist', step=1):
    """
    Trouve le numéro de la frame la plus proche de l'image donnée dans une vidéo.

    :param video_path: chemin de la vidéo
    :param image_path: chemin de l'image de référence
    :param method: méthode de comparaison ('hist' ou 'ssim')
    :param step: sauter des frames pour accélérer (1 = toutes, 5 = 1 sur 5, etc.)
    :return: numéro de la frame la plus proche
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Impossible d'ouvrir la vidéo")

    ref_img = cv2.imread(image_path)
    if ref_img is None:
        raise ValueError("Impossible de lire l'image")

    ref_img = cv2.resize(ref_img, (320, 240))  # standardiser taille
    ref_hist = cv2.calcHist([cv2.cvtColor(ref_img, cv2.COLOR_BGR2HSV)], [0, 1], None, [50, 60], [0, 180, 0, 256])
    ref_hist = cv2.normalize(ref_hist, ref_hist).flatten()

    best_score = -1
    best_frame = -1
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % step == 0:
            frame_resized = cv2.resize(frame, (320, 240))
            frame_hist = cv2.calcHist([cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)], [0, 1], None, [50, 60], [0, 180, 0, 256])
            frame_hist = cv2.normalize(frame_hist, frame_hist).flatten()
            score = cv2.compareHist(ref_hist, frame_hist, cv2.HISTCMP_CORREL)

            if score > best_score:
                best_score = score
                best_frame = frame_idx

        frame_idx += 1

    cap.release()
    return best_frame

# Exemple d'utilisation
video_file = "../../Film/BBD_video_varié/Plan_film/4eme2.mp4"
image_file = "vv/FA/4eme2.png"
#image_file = "vv/4eme2.jpg"
#image_file = "vv/VV_Amandine_D'AZEVEDO/4eme2.png"

frame_number = find_matching_frame(video_file, image_file)
print(f"Frame correspondante : {frame_number}")
