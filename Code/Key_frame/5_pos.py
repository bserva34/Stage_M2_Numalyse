import os
import cv2
import torch
import numpy as np
from tqdm import tqdm
from PIL import Image
import matplotlib.pyplot as plt
import torchvision.transforms as T
import torchvision.models as models
from torchvision.ops import box_area

def compute_sift_score(frame, sift):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kps = sift.detect(gray, None)
    return float(sum(k.response for k in kps))

def compute_det_score(frame, model, transform, thr, w_person, sigma, device,store_weights=False):
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_t = transform(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(img_t)[0]

    scores = out["scores"].cpu().numpy()
    labels = out["labels"].cpu().numpy()
    boxes = out["boxes"].cpu().numpy()
    
    # b2 = out["boxes"]

    # # Aires et normalisation
    # H, W       = frame.shape[:2]
    # total_area = float(H * W)
    # areas = box_area(b2).cpu().numpy()
    # a_norm  = areas / total_area

    mask = scores > thr
    vs = scores[mask] * 10
    vl = labels[mask]
    bxs = boxes[mask]
    # a_norm = a_norm[mask]  

    weights_no_pos = np.where(vl == 1, w_person, 1.0)

    H, W = frame.shape[:2]
    cx_img, cy_img = W / 2.0, H / 2.0
    cx = (bxs[:, 0] + bxs[:, 2]) / 2.0
    cy = (bxs[:, 1] + bxs[:, 3]) / 2.0

    dx = (cx - cx_img) / cx_img
    dy = (cy - cy_img) / cy_img
    dist = np.sqrt(dx**2 + dy**2)
    w_pos = (np.exp(-0.5 * (dist / sigma)**2)) * 10

    weights = weights_no_pos * w_pos #* (np.sqrt(a_norm))
    score = float((vs * weights).sum())

    if store_weights:
        return score, w_pos, weights_no_pos, vs
    else:
        return score

def double_gaussian_equal(x, t, epsilon):
    sigma = 0.15 * t
    A = 1.0
    g1 = A * np.exp(-((x - t/2)**2) / (2 * sigma**2))
    g2 = A * np.exp(-((x - (t - epsilon))**2) / (2 * sigma**2))
    return g1 + g2

def compute_sharpness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def main():
    import argparse
    p = argparse.ArgumentParser(description="Extraction de keyframes avec graphique de scores")
    p.add_argument("video", help="Chemin vers le fichier vidéo")
    p.add_argument("--out", default="keyframes", help="Dossier de sortie pour les keyframes")
    p.add_argument("--thr", type=float, default=0.7, help="Seuil minimal de confiance pour les détections")
    p.add_argument("--weight_person", type=float, default=10.0, help="Poids pour les personnes (COCO=1)")
    p.add_argument("--sigma", type=float, default=0.5, help="Sigma de la gaussienne spatiale (normalisé)")
    p.add_argument("--num", type=int, default=1, help="Nombre de keyframes à extraire sur le score combiné")
    p.add_argument("--final", type=int, default=0,
               help="Nombre de keyframes à garder après pondération temporelle (0 = désactivé)")
    args = p.parse_args()

    cap = cv2.VideoCapture(args.video)
    frames = []
    while True:
        ret, frm = cap.read()
        if not ret:
            break
        frames.append(frm)
    cap.release()

    if not frames:
        print("Erreur : aucune frame lue.")
        return

    base = os.path.splitext(os.path.basename(args.video))[0]
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    # Load optional vv_frames annotations
    txt_path = os.path.splitext(args.video)[0] + ".txt"
    vv_frames = []
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    vv_frames.append(int(line))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sift = cv2.SIFT_create()
    det_model = models.detection.fasterrcnn_resnet50_fpn(
        weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
    ).to(device).eval()
    det_transform = T.ToTensor()

    sift_scores = []
    det_scores = []
    all_w_pos = []
    all_weights_nopos = []
    all_vs = []
    gaussienne = []
    sharpness_scores = []

    cpt=0
    for frm in tqdm(frames, desc="Calcul des scores"):
        sift_scores.append(compute_sift_score(frm, sift))
        det_score, w_pos, weights_no_pos, vs = compute_det_score(
            frm, det_model, det_transform, args.thr,
            args.weight_person, args.sigma, device,store_weights=True
        )
        det_scores.append(det_score)
        all_w_pos.append(w_pos.sum())
        all_weights_nopos.append(weights_no_pos.sum())
        all_vs.append(vs.sum())
        acc=double_gaussian_equal(cpt,len(frames),0.1*len(frames))
        gaussienne.append(acc)
        sharpness_scores.append(compute_sharpness(frm))

        cpt+=1


    # Normalisation
    max_sift = max(sift_scores) if sift_scores else 1.0
    max_det = max(det_scores) if det_scores else 1.0
    max_sharp = max(sharpness_scores) if sharpness_scores else 1.0


    comb_scores = []
    for i in range(len(frames)):
        norm_s = sift_scores[i] / max_sift if max_sift > 0 else 0.0
        norm_d = det_scores[i] / max_det if max_det > 0 else 0.0
        norm_sh = sharpness_scores[i] / max_sharp if max_sharp > 0 else 0.0
        comb = (
            0.2 * norm_s +
            0.6 * norm_d +
            0.1 * gaussienne[i] +
            0.1 * (norm_sh)
        )
        # comb = norm_d * gaussienne[i] * norm_sh
        comb_scores.append(comb)

    # Étape 1 : top-N frames par score combiné brut
    num = min(args.num, len(frames))
    initial_top_idxs = sorted(range(len(frames)), key=lambda i: comb_scores[i], reverse=True)[:num]
    final_top_idxs = initial_top_idxs
    # # Étape 2 : pondération tempo
    # if args.final > 0:
    #     t = len(frames)
    #     epsilon = 0.1 * t
    #     temporal_weights = double_gaussian_equal(np.arange(t), t, epsilon)
    #     temporal_weights /= temporal_weights.max()

    #     # Pondérer seulement les top `num` frames
    #     weighted = [(i, comb_scores[i] * temporal_weights[i]) for i in initial_top_idxs]
    #     weighted_sorted = sorted(weighted, key=lambda x: x[1], reverse=True)
    #     final_top_idxs = [i for i, _ in weighted_sorted[:min(args.final, len(weighted_sorted))]]
    # else:
    #     final_top_idxs = initial_top_idxs


    # Sauvegarde keyframes
    for rank, idx in enumerate(final_top_idxs, start=1):
        out_path = os.path.join(out_dir, f"{base}_keyframe_rank{rank}_{idx:04d}.jpg")
        cv2.imwrite(out_path, frames[idx])
        print(f"Rank {rank}: frame {idx}, score {comb_scores[idx]:.3f} -> {out_path}")



    # x = list(range(len(frames)))

    # # Graphique 1 : w_pos, weights (no pos), vs
    # plt.figure(figsize=(12,6))
    # plt.plot(x, all_w_pos,linewidth=1, label="w_pos (somme)")
    # plt.plot(x, all_weights_nopos, linewidth=1, label="weights (sans pos)")
    # plt.plot(x, all_vs,linewidth=1, label="vs (scores détection)")
    # # Couleur pour les initiales
    # for i, idx in enumerate(initial_top_idxs):
    #     plt.axvline(idx, color="grey", linestyle="--", linewidth=1.5, label=("Initial" if i == 0 else None))

    # # Couleur + flèche pour les finales
    # for i, idx in enumerate(final_top_idxs):
    #     plt.axvline(idx, color="red", linestyle="--", linewidth=1.5, label=("Final" if i == 0 else None))

    # for i, vf in enumerate(vv_frames):
    #     plt.axvline(vf, color="green")
    #     plt.text(vf + 0.5, max(all_vs), f"VV{i+1}", rotation=90, verticalalignment="top", fontsize=8)
    # plt.title(f"Scores de détection – {base}")
    # plt.xlabel("Index de frame")
    # plt.ylabel("Valeurs")
    # plt.legend()
    # plt.tight_layout()
    # graph1_path = os.path.join(out_dir, f"{base}_graph1_scores_detection.png")
    # plt.savefig(graph1_path)
    # plt.close()
    # print(f"Graphique 1 enregistré → {graph1_path}")

    # # Graphique 2 : norm_s, norm_d
    # norm_s_list = [s / max_sift if max_sift>0 else 0 for s in sift_scores]
    # norm_d_list = [d / max_det if max_det>0 else 0 for d in det_scores]
    # plt.figure(figsize=(12,6))
    # plt.plot(x, norm_s_list, label="norm_s (SIFT normalisé)")
    # plt.plot(x, norm_d_list, label="norm_d (détection normalisée)")
    # plt.plot(x,gaussienne, label="gaussienne")
    # # Couleur pour les initiales
    # for i, idx in enumerate(initial_top_idxs):
    #     plt.axvline(idx, color="grey", linestyle="--", linewidth=1.5, label=("Initial" if i == 0 else None))

    # # Couleur + flèche pour les finales
    # for i, idx in enumerate(final_top_idxs):
    #     plt.axvline(idx, color="red", linestyle="--", linewidth=1.5, label=("Final" if i == 0 else None))

    # for i, vf in enumerate(vv_frames):
    #     plt.axvline(vf, color="green")
    #     plt.text(vf + 0.5, 1.0, f"VV{i+1}", rotation=90, verticalalignment="top", fontsize=8)
    # plt.title(f"Scores combinés normalisés – {base}")
    # plt.xlabel("Index de frame")
    # plt.ylabel("Valeurs normalisées")
    # plt.legend()
    # plt.tight_layout()
    # graph2_path = os.path.join(out_dir, f"{base}_graph2_scores_normes.png")
    # plt.savefig(graph2_path)
    # plt.close()
    # print(f"Graphique 2 enregistré → {graph2_path}")

if __name__ == "__main__":
    main()