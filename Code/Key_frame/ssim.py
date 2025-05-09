import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim

def calculate_ssim(img1, img2):
    # Conversion en niveaux de gris pour le SSIM
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(img1_gray, img2_gray, full=True)
    return score

def compute_ssim_video(reference_image_path, video_path, output_folder):
    # Chargement de l'image de référence
    ref_img = cv2.imread(reference_image_path)
    if ref_img is None:
        raise ValueError(f"Impossible de charger l'image: {reference_image_path}")

    # Ouverture de la vidéo
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo: {video_path}")

    # Création du dossier de sortie
    os.makedirs(output_folder, exist_ok=True)

    frame_idx = 0
    ssim_values = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionner la frame à la taille de l'image de référence si nécessaire
        if frame.shape != ref_img.shape:
            frame = cv2.resize(frame, (ref_img.shape[1], ref_img.shape[0]))

        score = calculate_ssim(ref_img, frame)
        ssim_values.append(score)

        frame_idx += 1

    cap.release()

    # Tracer la courbe SSIM
    plt.figure(figsize=(10, 5))
    plt.plot(ssim_values, label='SSIM', color='green')
    plt.xlabel('Numéro de frame')
    plt.ylabel('SSIM')
    plt.title('Courbe SSIM entre l\'image de référence et chaque frame')
    plt.grid(True)
    plt.legend()

    base = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_folder, base + "_ssim.png")
    plt.savefig(output_path)
    plt.close()

    print(f"Courbe SSIM enregistrée dans : {output_path}")

# Exemple d'utilisation
if __name__ == "__main__":
    reference_image = "vv/adele_plan_253.png"
    video = "../../Film/BBD_video_varié/adele_plan.mp4"
    output = "test_psnr_ssim"

    compute_ssim_video(reference_image, video, output)
