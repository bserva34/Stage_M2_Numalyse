import os
import cv2
import numpy as np
import argparse
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(description='One-class SVM: extract top-N keyframes from a single shot')
    parser.add_argument("video")
    parser.add_argument('--out', '-o', required=True, help='Output directory for keyframes')
    parser.add_argument('--nu', type=float, default=0.05,
                        help='Nu parameter for OneClassSVM (upper bound on outliers fraction)')
    parser.add_argument('--gamma', type=str, default='scale',
                        help="Gamma parameter for RBF kernel ('scale', 'auto', or float)")
    parser.add_argument('--top_n', type=int, default=1,
                        help='Number of top anomalous frames to extract')
    return parser.parse_args()


def extract_features(video_path):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    histograms = []
    frames = []

    # Read frames and compute HSV histograms
    for _ in tqdm(range(total), desc="Reading frames", unit="frame"):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0,1,2], None, [8,3,3], [0,180,0,256,0,256])
        histograms.append(cv2.normalize(hist, hist).flatten())
    cap.release()

    # Compute PD and GD between consecutive frames
    PDs, GDs = [], []
    for i in tqdm(range(len(frames)-1), desc="Computing temporal features", unit="pair"):
        h1, h2 = histograms[i], histograms[i+1]
        pd = np.linalg.norm(h1 - h2, ord=1)

        gray1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frames[i+1], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(gray1, gray2, None,
                                            pyr_scale=0.5, levels=3, winsize=15,
                                            iterations=3, poly_n=5, poly_sigma=1.2, flags=0)
        mag, _ = cv2.cartToPolar(flow[...,0], flow[...,1])
        gd = mag.mean()

        PDs.append(pd)
        GDs.append(gd)

    # Prepare feature matrix and corresponding frame indices
    X = np.vstack([PDs, GDs]).T  # shape (N-1, 2)
    frame_indices = list(range(1, len(frames)))  # feature i corresponds to frame index i
    return frames, X, frame_indices


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)

    # 1) Extract features
    frames, X, frame_indices = extract_features(args.video)

    # 2) Scale features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # 3) Train OneClassSVM
    model = OneClassSVM(kernel='rbf', nu=args.nu, gamma=args.gamma)
    model.fit(X_scaled)

    # 4) Score: negative decision_function means more anomalous
    scores = model.decision_function(X_scaled)
    # Pair each frame index with score
    idx_scores = list(zip(frame_indices, scores))
    # Sort by score ascending (most negative = most anomalous)
    idx_scores.sort(key=lambda pair: pair[1])
    # Select top N
    top_n = min(args.top_n, len(idx_scores))
    selected = [idx for idx, _ in idx_scores[:top_n]]

    # 5) Save selected frames
    for idx in tqdm(selected, desc="Saving keyframes", unit="frame"):
        frame = frames[idx]
        out_path = os.path.join(args.out, f'frame_{idx}.jpg')
        cv2.imwrite(out_path, frame)

    print(f"Extracted {len(selected)} keyframe(s) to '{args.out}'")

if __name__ == '__main__':
    main()
