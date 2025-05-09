import cv2
import os
import numpy as np
import matplotlib.pyplot as plt

def calculate_psnr(img1, img2):
    mse = np.mean((img1.astype(np.float32) - img2.astype(np.float32)) ** 2)
    if mse == 0:
        return float('inf')
    PIXEL_MAX = 255.0
    return 20 * np.log10(PIXEL_MAX / np.sqrt(mse))

def compute_psnr_video(reference_image_path, video_path, output_folder):
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
    psnr_values = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Redimensionner la frame à la taille de l'image de référence si nécessaire
        if frame.shape != ref_img.shape:
            frame = cv2.resize(frame, (ref_img.shape[1], ref_img.shape[0]))

        psnr = calculate_psnr(ref_img, frame)
        psnr_values.append(psnr)

        frame_idx += 1

    cap.release()

    # Tracer la courbe PSNR
    plt.figure(figsize=(10, 5))
    plt.plot(psnr_values, label='PSNR')
    plt.xlabel('Numéro de frame')
    plt.ylabel('PSNR (dB)')
    plt.title('Courbe PSNR entre l\'image de référence et chaque frame')
    plt.grid(True)
    plt.legend()

    base = os.path.splitext(os.path.basename(video_path))[0]

    output_path = os.path.join(output_folder, base)
    output_path=output_path+"_psnr.png"
    plt.savefig(output_path)
    plt.close()

    print(f"Courbe PSNR enregistrée dans : {output_path}")

# Exemple d'utilisation
if __name__ == "__main__":
    reference_image = "vv/adele_plan_253.png"
    video = "../../Film/BBD_video_varié/adele_plan.mp4"
    output = "test_psnr_ssim"

    compute_psnr_video(reference_image, video, output)
