import os
import argparse
import cv2
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models
from tqdm import tqdm
from scipy.spatial.distance import cdist

import matplotlib.pyplot as plt


def double_gaussian_equal(x, t, epsilon):
    """
    Generates a double Gaussian weight over frame indices.
    x: array-like frame indices
    t: total number of frames
    epsilon: 0.1 * t by default
    """
    sigma = 0.15 * t
    A = 1.0
    g1 = A * np.exp(-((x - t/2)**2) / (2 * sigma**2))
    g2 = A * np.exp(-((x - (t - epsilon))**2) / (2 * sigma**2))
    return g1 + g2


def compute_label_histogram(frame, model, transform, thr, num_classes, device, sigma_pos):
    # Convert BGR to PIL RGB
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_t = transform(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(img_t)[0]

    # Extract detections
    scores = out['scores'].cpu().numpy()
    labels = out['labels'].cpu().numpy()
    boxes = out['boxes'].cpu().numpy()

    # Filter by threshold
    mask = scores > thr
    scores_f = scores[mask]
    labels_f = labels[mask]
    boxes_f = boxes[mask]

    # Image dimensions
    H, W = frame.shape[:2]
    cx_img, cy_img = W / 2.0, H / 2.0

    # Center of boxes
    cx = (boxes_f[:, 0] + boxes_f[:, 2]) / 2.0
    cy = (boxes_f[:, 1] + boxes_f[:, 3]) / 2.0

    # Distance to image center (normalized)
    dx = (cx - cx_img) / cx_img
    dy = (cy - cy_img) / cy_img
    dist = np.sqrt(dx**2 + dy**2)

    # pondération spatial
    w_pos = np.exp(-0.5 * (dist / sigma_pos)**2)

    # Taille (aire) normalisée
    area = (boxes_f[:, 2] - boxes_f[:, 0]) * (boxes_f[:, 3] - boxes_f[:, 1])
    a_norm = area / (H * W)

    # Pondération totale = score * w_pos * a_norm
    weights = scores_f * w_pos

    # Histogramme
    hist = np.zeros(num_classes, dtype=np.float32)
    for label, w in zip(labels_f, weights):
        hist[label] += w

    return hist

def compute_sharpness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def main():
    parser = argparse.ArgumentParser(description="Keyframe selection via spatially & temporally weighted label histograms")
    parser.add_argument('video', help='Path to input video file')
    parser.add_argument('--out', default='output', help='Output directory')
    parser.add_argument('--thr', type=float, default=0.7, help='Detection score threshold')
    parser.add_argument('--metric', default='euclidean', choices=['euclidean', 'cityblock', 'cosine'],
                        help='Distance metric to use')
    parser.add_argument('--topk', type=int, default=1, help='Number of nearest frames to select')
    parser.add_argument('--sigma-pos', type=float, default=0.3,
                        help='Spatial weighting sigma (normalized distance)')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        print("Error: No frames read from video.")
        return

    num_frames = len(frames)
    epsilon = 0.1 * num_frames

    # Prepare detection model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = models.detection.fasterrcnn_resnet50_fpn(
        weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
    ).to(device).eval()
    transform = T.ToTensor()

    # nb classe + background
    num_classes = 91

    # First pass
    histograms = []
    sharpness_scores = []
    print("Computing weighted label histograms for each frame...")
    for frame in tqdm(frames, desc="Histograms"):
        hist = compute_label_histogram(frame, model, transform, args.thr, num_classes, device, args.sigma_pos)
        histograms.append(hist)
        sharpness_scores.append(compute_sharpness(frame))
    histograms = np.stack(histograms, axis=0)

    #normalisation qualité
    sharpness_scores = np.array(sharpness_scores)
    sharpness_scores /= sharpness_scores.max() 

    #pondération qualité
    histograms = np.array(histograms)
    histograms *= sharpness_scores[:, None]  

    # pondération tempo
    x = np.arange(num_frames, dtype=float)
    weights_t = double_gaussian_equal(x, num_frames, epsilon)
    weights_t /= weights_t.sum()
    hist_t = np.average(histograms, axis=0, weights=weights_t)

    # calcul distance entre chaque histo et histo de référence
    dists = cdist(histograms, hist_t[None, :], metric=args.metric).squeeze()

    # Select top-k frames
    topk_idxs = np.argsort(dists)[:args.topk]
    print(f"Selected frame indices: {topk_idxs.tolist()}")

    # Save results
    base = os.path.splitext(os.path.basename(args.video))[0]
    for rank, idx in enumerate(topk_idxs, start=1):
        out_path = os.path.join(args.out, f"{base}_keyframe_rank{rank}_{idx:04d}.jpg")
        cv2.imwrite(out_path, frames[idx])
        print(f"Rank {rank}: frame {idx}, distance {dists[idx]:.4f} -> {out_path}")

    # plt.figure(figsize=(12, 6))
    # x = np.arange(num_classes)

    # # Histogramme moyen (pondéré spatio-temporellement)
    # plt.plot(x, hist_t, label="Histogramme moyen (pondéré)", linewidth=2)

    # # Histogramme de la frame sélectionnée numéro 1
    # idx1 = topk_idxs[0]
    # plt.plot(x, histograms[idx1], label=f"Frame sélectionnée {idx1}", linewidth=2)

    # plt.title(f"Comparaison des histogrammes – {base}")
    # plt.xlabel("Index de classe (COCO)")
    # plt.ylabel("Score pondéré")
    # plt.legend()
    # plt.tight_layout()

    # # Correction du nom de dossier (args.out au lieu de out_dir)
    # graph2_path = os.path.join(args.out, f"{base}_graph2_histogram_comparison.png")
    # plt.savefig(graph2_path)
    # plt.close()


if __name__ == '__main__':
    main()
