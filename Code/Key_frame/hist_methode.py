import os
import argparse
import cv2
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models
from tqdm import tqdm

def compute_label_histogram(frame, model, transform, thr, num_classes, device):
    # Convert BGR to PIL RGB
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_t = transform(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(img_t)[0]

    scores = out['scores'].cpu().numpy()
    labels = out['labels'].cpu().numpy()

    # Initialize histogram
    hist = np.zeros(num_classes, dtype=np.float32)
    # Sum confidences per label above threshold
    for score, label in zip(scores, labels):
        if score >= thr:
            hist[label] += score
    return hist


def main():
    parser = argparse.ArgumentParser(description="Keyframe selection via label histograms")
    parser.add_argument('video', help='Path to input video file')
    parser.add_argument('--out', default='output', help='Output directory')
    parser.add_argument('--thr', type=float, default=0.7, help='Detection score threshold')
    parser.add_argument("--metric", default="euclidean", choices=["euclidean", "cityblock", "cosine"],
                   help="Distance metric à utiliser (euclidean=L2, cityblock=L1, cosine=cosinus)")

    parser.add_argument('--topk', type=int, default=3, help='Number of nearest frames to select')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Load video frames
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

    # Prepare detection model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = models.detection.fasterrcnn_resnet50_fpn(
        weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
    ).to(device).eval()
    transform = T.ToTensor()

    # Determine number of classes (including background)
    num_classes = 91  # COCO has 80 classes, but model outputs 91 labels including background

    # First pass: compute histograms per frame
    histograms = []
    print("Computing label histograms for each frame...")
    for frame in tqdm(frames, desc="Computing label histograms"):
        hist = compute_label_histogram(frame, model, transform, args.thr, num_classes, device)
        histograms.append(hist)

    histograms = np.stack(histograms, axis=0)  # shape: (N_frames, num_classes)
    # Compute average histogram
    avg_hist = histograms.mean(axis=0)

    # Compute distances to average
    from scipy.spatial.distance import cdist
    # Use pairwise distance between each histogram and avg_hist
    dists = cdist(histograms, avg_hist[None, :], metric=args.metric).squeeze()

    # Find top-k closest frames
    topk_idxs = np.argsort(dists)[:args.topk]
    print(f"Selected frame indices (closest to mean histogram): {topk_idxs.tolist()}")

    # Save selected frames and distance info
    base = os.path.splitext(os.path.basename(args.video))[0]
    for rank, idx in enumerate(topk_idxs, start=1):
        out_path = os.path.join(args.out, f"{base}_histkeyframe_rank{rank}_{idx:04d}.jpg")
        cv2.imwrite(out_path, frames[idx])
        print(f"Rank {rank}: frame {idx}, distance {dists[idx]:.4f} -> {out_path}")

    # Optionally, save histogram data
    # np.savez(os.path.join(args.out, f"{base}_histograms.npz"),
    #          histograms=histograms, avg_hist=avg_hist, dists=dists)
    # print(f"Saved histograms and distances to {args.out}/{base}_histograms.npz")

if __name__ == '__main__':
    main()
