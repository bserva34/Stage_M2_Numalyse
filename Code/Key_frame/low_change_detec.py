import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim

def compute_ssim_changes(video_path, output_folder, threshold=0.98):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")

    ret, prev_frame = cap.read()
    if not ret:
        raise ValueError("Impossible de lire la première frame.")

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    ssim_scores = []
    frame_idx = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(prev_gray, gray, full=True)
        ssim_scores.append(score)

        prev_gray = gray
        frame_idx += 1

    cap.release()

    mean_ssim = np.mean(ssim_scores)
    print(f"Moyenne SSIM entre frames successives : {mean_ssim:.4f}")

    if mean_ssim > threshold:
        print("🔍 La vidéo semble comporter très peu de changements (quasiment statique).")
    else:
        print("✅ La vidéo présente des changements visibles entre les frames.")

    # Enregistrement de la courbe SSIM
    import os
    os.makedirs(output_folder, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_folder, base + "_ssim_variation.png")

    plt.figure(figsize=(10, 4))
    plt.plot(ssim_scores, color='orange', label='SSIM entre frames')
    plt.axhline(y=threshold, color='red', linestyle='--', label=f'Seuil {threshold}')
    plt.title("Variation SSIM entre frames successives")
    plt.xlabel("Index de frame")
    plt.ylabel("SSIM")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f"Courbe SSIM enregistrée dans : {output_path}")

if __name__ == "__main__":
    video = "../../Film/BBD_video_varié/velo1.mp4"
    output = "test_psnr_ssim"
    compute_ssim_changes(video, output)
