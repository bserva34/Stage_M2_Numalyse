import os
import cv2
import numpy as np
import argparse
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import KFold
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(
        description='One-class SVM keyframe extraction with ISPMDE hyperparameter optimization')
    parser.add_argument('video', help='Path to input video')
    parser.add_argument('--out', '-o', required=True, help='Output directory')
    parser.add_argument('--window', type=int, default=5,
                        help='Sliding window length for feature aggregation')
    parser.add_argument('--kfold', type=int, default=5,
                        help='Number of folds for cross-validation')
    parser.add_argument('--pop', type=int, default=20, help='Population size for DE')
    parser.add_argument('--gens', type=int, default=50, help='Generations for DE')
    parser.add_argument('--F', type=float, default=0.5, help='Scaling factor for DE')
    parser.add_argument('--cr', type=float, default=0.8, help='Crossover rate for DE')
    parser.add_argument('--top_n', type=int, default=1, help='Number of keyframes to extract')
    return parser.parse_args()


def extract_features(video_path, window):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames, hists = [], []
    for _ in tqdm(range(total_frames), desc="Reading frames", unit="frame"):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 3, 3], [0, 180, 0, 256, 0, 256])
        hists.append(cv2.normalize(hist, None).flatten())
    cap.release()

    PD, GD = [], []
    for i in tqdm(range(len(frames) - 1), desc="Computing raw features", unit="pair"):
        pd = np.linalg.norm(hists[i] - hists[i + 1], ord=1)
        gray1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(gray1, gray2, None,
                                            0.5, 3, 15, 3, 5, 1.2, 0)
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        gd = mag.mean()
        PD.append(pd)
        GD.append(gd)
    PD, GD = np.array(PD), np.array(GD)

    X, idxs = [], []
    n_pairs = len(PD)
    for i in tqdm(range(n_pairs - window + 1), desc="Aggregating features", unit="win"):
        win_pd = PD[i: i + window]
        win_gd = GD[i: i + window]
        r1, r2 = win_pd.mean(), np.abs(win_pd - win_pd.mean()).mean()
        s1, s2 = win_gd.mean(), np.abs(win_gd - win_gd.mean()).mean()
        X.append([r1, r2, s1, s2])
        idxs.append(i + window)
    return np.array(X), frames, idxs


def ispmde_optimize(X, kfold, pop_size, gens, F, cr):
    bounds = np.array([[1e-3, 0.5], [np.log(1e-4), np.log(1e1)]])
    pop = np.random.rand(pop_size, 2)
    pop = pop * (bounds[:, 1] - bounds[:, 0]) + bounds[:, 0]
    fitness = np.full(pop_size, np.inf)
    kf = KFold(n_splits=kfold, shuffle=True, random_state=42)

    def eval_ind(ind):
        nu, gamma = ind[0], np.exp(ind[1])
        scores = []
        for tr, va in kf.split(X):
            X_tr, X_va = X[tr], X[va]
            scaler = MinMaxScaler().fit(X_tr)
            X_tr_s, X_va_s = scaler.transform(X_tr), scaler.transform(X_va)
            model = OneClassSVM(kernel='rbf', nu=nu, gamma=gamma)
            model.fit(X_tr_s)
            scores.append(-model.decision_function(X_va_s).mean())
        return np.mean(scores)

    for i in tqdm(range(pop_size), desc="Init DE fitness", unit="ind"):
        fitness[i] = eval_ind(pop[i])

    for _ in tqdm(range(gens), desc="DE generations", unit="gen"):
        for i in range(pop_size):
            idxs_ = [j for j in range(pop_size) if j != i]
            r1, r2, r3 = np.random.choice(idxs_, 3, replace=False)
            trio = sorted([(r1, fitness[r1]), (r2, fitness[r2]), (r3, fitness[r3])], key=lambda x: x[1])
            br, mr, wr = trio[0][0], trio[1][0], trio[2][0]
            vi = pop[i] + F * (pop[br] - pop[mr] + pop[wr] - pop[i])
            xi = pop[i].copy()
            mask = np.random.rand(2) < cr
            xi[mask] = vi[mask]
            xi = np.clip(xi, bounds[:, 0], bounds[:, 1])
            fi = eval_ind(xi)
            if fi <= fitness[i]:
                pop[i], fitness[i] = xi, fi
    best_idx = np.argmin(fitness)
    best = pop[best_idx]
    return best[0], np.exp(best[1])


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)

    # Extraction des features
    X, frames, idxs = extract_features(args.video, args.window)

    # Optimisation des hyperparamètres
    nu_opt, gamma_opt = ispmde_optimize(X, args.kfold, args.pop, args.gens, args.F, args.cr)
    print(f"Optimized nu={nu_opt:.4f}, gamma={gamma_opt:.4g}")

    # Entraînement final et scoring
    scaler = MinMaxScaler().fit(X)
    X_s = scaler.transform(X)
    model = OneClassSVM(kernel='rbf', nu=nu_opt, gamma=gamma_opt)
    model.fit(X_s)
    scores = model.decision_function(X_s)
    order = np.argsort(scores)
    #selected = order[:args.top_n]
    selected = order[-args.top_n:]


    # Nom de base du fichier vidéo
    base = os.path.splitext(os.path.basename(args.video))[0]

    # Sauvegarde avec nom [base]_keyframe_[frame_idx].jpg
    for sel in tqdm(selected, desc="Saving keyframes", unit="kf"):
        frame_idx = idxs[sel]
        out_name = f"{base}_keyframe_{frame_idx:06d}.jpg"
        out_path = os.path.join(args.out, out_name)
        cv2.imwrite(out_path, frames[frame_idx])
    print(f"Saved {len(selected)} keyframe(s) to {args.out}")

if __name__ == '__main__':
    main()
