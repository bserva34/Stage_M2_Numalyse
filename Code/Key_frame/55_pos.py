import os
import cv2
import torch
import numpy as np
from tqdm import tqdm
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models
from torchvision.ops import box_area
import matplotlib.pyplot as plt

def compute_sift_score(frame, sift):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kps = sift.detect(gray, None)
    return sum(k.response for k in kps)

def compute_det_score(frame, model, transform,
                      thr_conf, thr_area_min, thr_area_max,
                      w_person, power, sigma, device):
    # Prépare l'image
    pil   = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_t = transform(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(img_t)[0]

    # Scores, labels, boxes bruts
    scores = out["scores"].cpu().numpy()
    labels = out["labels"].cpu().numpy()
    boxes  = out["boxes"]

    # Aires et normalisation
    H, W       = frame.shape[:2]
    total_area = float(H * W)
    areas = box_area(boxes).cpu().numpy()
    a_norm  = areas / total_area

    # Filtrage par confiance et taille
    mask_conf = scores > thr_conf
    mask_min  = a_norm > thr_area_min
    mask_max  = a_norm < thr_area_max
    mask = (
    mask_conf.numpy() if isinstance(mask_conf, torch.Tensor) else mask_conf
    ) & (
        mask_min.numpy() if isinstance(mask_min, torch.Tensor) else mask_min
    ) & (
        mask_max.numpy() if isinstance(mask_max, torch.Tensor) else mask_max
    )


    # Application du masque
    scores         = scores[mask] *10       # [K]
    labels         = labels[mask]        # [K]
    a_norm         = a_norm[mask]        # [K]
    filtered_boxes = boxes[mask]         # [K,4]
    filtered_boxes = filtered_boxes.cpu().numpy()


    # Accentuation selon la surface
    areas_pow = np.power(a_norm, power)

    # Poids COCO=1 (personnes)
    weights_no_pos = np.where(labels == 1, w_person, 1.0)

    # --- Pondération spatiale ---
    # Centre de chaque boîte
    cx = (filtered_boxes[:, 0] + filtered_boxes[:, 2]) / 2
    cy = (filtered_boxes[:, 1] + filtered_boxes[:, 3]) / 2
    cx_img, cy_img = W / 2, H / 2

    # Coordonnées normalisées en [-1,1]
    dx = (cx - cx_img) / cx_img
    dy = (cy - cy_img) / cy_img

    # Distance euclidienne normalisée
    dist = np.sqrt(dx**2 + dy**2)

    # Poids gaussien centré
    w_pos = (np.exp(-0.5 * (dist / sigma)**2))*10  # [K]

    # Combinaison des poids
    weights = weights_no_pos * w_pos
    # --- Fin pondération spatiale ---

    # Score final agrégé
    if isinstance(scores, torch.Tensor):
        scores = scores.numpy()
    if isinstance(areas_pow, torch.Tensor):
        areas_pow = areas_pow.numpy()
    if isinstance(weights, torch.Tensor):
        weights = weights.numpy()

    final = (scores * areas_pow * weights).sum()

    return final, w_pos, weights_no_pos, scores, areas_pow

def main():
    import argparse
    p = argparse.ArgumentParser(
        description="Extrait la keyframe d'une vidéo en combinant score SIFT, "
                    "score détection pondéré par surface et position spatiale"
    )
    p.add_argument("video", help="Chemin vers le fichier vidéo")
    p.add_argument("--out", default="keyframes",
                   help="Dossier de sortie pour la keyframe")
    p.add_argument("--thr", type=float, default=0.7,
                   help="Seuil minimal de confiance pour les détections")
    p.add_argument("--area_min", type=float, default=0.01,
                   help="Seuil minimal de surface normalisée (ex: 0.01 = 1%)")
    p.add_argument("--area_max", type=float, default=0.4,
                   help="Seuil maximal de surface normalisée (ex: 0.4 = 40%)")
    p.add_argument("--weight_person", type=float, default=10.0,
                   help="Poids appliqué aux personnes (label COCO=1)")
    p.add_argument("--power", type=float, default=3.0,
                   help="Exposant appliqué à l'aire normalisée pour accentuer les gros objets")
    p.add_argument("--sigma", type=float, default=0.1,
                   help="Sigma de la gaussienne de pondération spatiale (normalisé)")
    args = p.parse_args()

    # Lecture des frames
    cap    = cv2.VideoCapture(args.video)
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

    txt_path = os.path.splitext(args.video)[0] + ".txt"
    vv_frames = []
    if os.path.exists(txt_path):
        with open(txt_path) as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    vv_frames.append(int(line))

    # Init SIFT et modèle de détection
    device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sift      = cv2.SIFT_create()
    det_model = models.detection.fasterrcnn_resnet50_fpn(
                    weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
                ).to(device).eval()
    det_transform = T.ToTensor()

    sift_scores = []
    det_scores = []
    all_w_pos = []
    all_weights_nopos = []
    all_vs = []
    all_areas = []

    # 1ère passe : calcul des scores
    sift_scores = []
    det_scores  = []
    for frm in tqdm(frames, desc="1ère passe – scores"):
        sift_scores.append(compute_sift_score(frm, sift))
        det_score, w_pos,weights_no_pos, vs,areas = compute_det_score(
            frm, det_model, det_transform,
            thr_conf     = args.thr,
            thr_area_min = args.area_min,
            thr_area_max = args.area_max,
            w_person     = args.weight_person,
            power        = args.power,
            sigma        = args.sigma,
            device       = device
        )
        det_scores.append(det_score)
        all_w_pos.append(w_pos.sum())
        all_weights_nopos.append(weights_no_pos.sum())
        all_vs.append(vs.sum())
        all_areas.append(areas.sum())


    max_sift = max(sift_scores)
    max_det  = max(det_scores) if any(det_scores) else 1.0

    # 2ème passe : sélection de la meilleure frame
    best_idx, best_comb = 0, -1.0
    norm_s_list = []
    norm_d_list = []
    os.makedirs(args.out, exist_ok=True)
    for i, frm in enumerate(frames):
        norm_s = sift_scores[i] / max_sift if max_sift > 0 else 0
        norm_d = det_scores[i]  / max_det  if det_scores[i] > 0 else 0
        comb   = 0.3 * norm_s + 0.7 * norm_d
        norm_s_list.append(norm_s)
        norm_d_list.append(norm_d)
        if comb > best_comb:
            best_comb, best_idx = comb, i

    # Sauvegarde
    out_path = os.path.join(out_dir, f"{base}_keyframe_{best_idx:04d}.jpg")
    cv2.imwrite(out_path, frames[best_idx])

    print(f"Key-frame : {best_idx}, score combiné : {best_comb:.3f}")
    print(f"Enregistrée → {out_path}")

    x = list(range(len(frames)))

    # --- Graphique 1 : w_pos, weights (no pos), vs ---
    plt.figure(figsize=(12, 6))
    plt.plot(x, all_w_pos, linestyle=":", linewidth=1, label="w_pos (somme)")
    plt.plot(x, all_weights_nopos, linestyle=":", linewidth=1, label="weights (sans pos)")
    plt.plot(x, all_vs, linestyle=":", linewidth=1, label="vs (scores détection)")
    plt.plot(x, all_areas, linestyle=":", linewidth=1, label="areas (scores taille)")
    plt.axvline(best_idx, color="red", linestyle="--", label="Keyframe sélectionnée")
    for i, vf in enumerate(vv_frames):
        plt.axvline(vf, linestyle=":", color="gray")
        plt.text(vf + 0.5, max(all_vs), f"VV{i+1}", rotation=90, verticalalignment="top", fontsize=8)
    plt.title(f"Scores de détection – {base}")
    plt.xlabel("Index de frame")
    plt.ylabel("Valeurs")
    plt.legend()
    plt.tight_layout()
    graph1_path = os.path.join(out_dir, f"{base}_graph1_scores_detection.png")
    plt.savefig(graph1_path)
    plt.close()
    print(f"Graphique 1 enregistré → {graph1_path}")

    # --- Graphique 2 : norm_s, norm_d ---
    plt.figure(figsize=(12, 6))
    plt.plot(x, norm_s_list, label="norm_s (SIFT normalisé)")
    plt.plot(x, norm_d_list, label="norm_d (détection normalisée)")
    plt.axvline(best_idx, color="red", linestyle="--", label="Keyframe sélectionnée")
    for i, vf in enumerate(vv_frames):
        plt.axvline(vf, linestyle=":", color="gray")
        plt.text(vf + 0.5, 1.0, f"VV{i+1}", rotation=90, verticalalignment="top", fontsize=8)
    plt.title(f"Scores combinés normalisés – {base}")
    plt.xlabel("Index de frame")
    plt.ylabel("Valeurs normalisées")
    plt.legend()
    plt.tight_layout()
    graph2_path = os.path.join(out_dir, f"{base}_graph2_scores_normes.png")
    plt.savefig(graph2_path)
    plt.close()
    print(f"Graphique 2 enregistré → {graph2_path}")

if __name__ == "__main__":
    main()
