import os
import cv2
import torch
import numpy as np
from tqdm import tqdm
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models
from torchvision.ops import box_area

def compute_sift_score(frame, sift):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kps = sift.detect(gray, None)
    return sum(k.response for k in kps)

def compute_det_score(frame, model, transform, thr, w_person, power, device):
    # Prépare l'image
    pil    = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_t  = transform(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(img_t)[0]

    # Récupère scores, labels et boxes
    scores = out["scores"]         # Tensor [M]
    labels = out["labels"]         # Tensor [M]
    boxes  = out["boxes"]          # Tensor [M,4]

    # Filtre par seuil de confiance
    mask   = scores > thr          # Tensor bool [M]
    scores = scores[mask]          # [K]
    labels = labels[mask]          # [K]
    boxes  = boxes[mask]           # [K,4]

    # Calcul des aires et normalisation
    areas      = box_area(boxes)   # [K]
    H, W       = frame.shape[:2]
    total_area = float(H * W)
    a_norm     = areas / total_area  # [K], dans [0,1]

    # Accentuation des gros objets
    areas_pow = a_norm.pow(power)   # [K]

    # Poids spécifiques (personnes label=1)
    weights = torch.where(labels == 1, w_person, 1.0)  # [K]

    # Score final
    final = (scores * areas_pow * weights).sum()
    return float(final)

def main():
    import argparse
    p = argparse.ArgumentParser(
        description="Extrait la keyframe d'une vidéo en combinant score SIFT et score détection pondéré par surface normalisée^p"
    )
    p.add_argument("video", help="Chemin vers le fichier vidéo")
    p.add_argument("--out", default="keyframes",
                   help="Dossier de sortie pour la keyframe")
    p.add_argument("--thr", type=float, default=0.7,
                   help="Seuil minimal de confiance pour les détections")
    p.add_argument("--weight_person", type=float, default=10.0,
                   help="Poids appliqué aux personnes (label COCO=1)")
    p.add_argument("--power", type=float, default=1.0,
                   help="Exposant appliqué à l'aire normalisée pour accentuer les gros objets")
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
        print("Erreur : impossible de lire des frames dans la vidéo.")
        return

    # Initialisation des modèles et modules
    device       = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sift         = cv2.SIFT_create()
    det_model    = models.detection.fasterrcnn_resnet50_fpn(
                       weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
                   ).to(device).eval()
    det_transform = T.ToTensor()

    # 1ère passe : calcul des scores
    sift_scores = []
    det_scores  = []
    for frm in tqdm(frames, desc="1ère passe – scores"):
        sift_scores.append(compute_sift_score(frm, sift))
        det_scores.append(compute_det_score(
            frm,
            model=det_model,
            transform=det_transform,
            thr=args.thr,
            w_person=args.weight_person,
            power=args.power,
            device=device
        ))

    max_sift = max(sift_scores)
    max_det  = max(det_scores)

    # 2ème passe : sélection de la meilleure frame
    best_idx, best_comb = 0, -1.0
    os.makedirs(args.out, exist_ok=True)
    for i, frm in enumerate(frames):
        norm_s = sift_scores[i] / max_sift
        norm_d = det_scores[i]  / max_det
        comb   = 0.5 * norm_s + 0.5 * norm_d
        if comb > best_comb:
            best_comb, best_idx = comb, i

    # Sauvegarde de la keyframe
    base     = os.path.splitext(os.path.basename(args.video))[0]
    out_path = os.path.join(args.out, f"{base}_keyframe_{best_idx:04d}.jpg")
    cv2.imwrite(out_path, frames[best_idx])

    print(f"Key-frame : {best_idx}, score combiné : {best_comb:.3f}")
    print(f"Enregistrée → {out_path}")

if __name__ == "__main__":
    main()
