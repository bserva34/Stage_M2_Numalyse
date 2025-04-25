import os
import cv2
import torch
import numpy as np
from tqdm import tqdm
from PIL import Image
import torchvision.transforms as T
import torchvision.models as models

def compute_sift_score(frame, sift):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    kps = sift.detect(gray, None)
    return sum(k.response for k in kps)

def compute_det_score(frame, model, transform, thr, w_person, device):
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    img_t = transform(pil).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(img_t)[0]
    scores = out["scores"].cpu().numpy()
    labels = out["labels"].cpu().numpy()
    mask   = scores > thr
    vs     = scores[mask]
    vl     = labels[mask]
    weights = np.where(vl == 1, w_person, 1.0)
    return float((vs * weights).sum())

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--out", default="keyframes")
    p.add_argument("--thr", type=float, default=0.7)
    p.add_argument("--weight_person", type=float, default=10.0)
    args = p.parse_args()

    # Lire toutes les frames
    cap = cv2.VideoCapture(args.video)
    frames = []
    while True:
        ret, frm = cap.read()
        if not ret: break
        frames.append(frm)
    cap.release()
    if not frames:
        print("Erreur de lecture")
        return

    # Init SIFT + Faster-RCNN
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sift = cv2.SIFT_create()
    det_model = models.detection.fasterrcnn_resnet50_fpn(
        weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
    ).to(device).eval()
    det_transform = T.ToTensor()

    # 1ère passe : calculer tous les scores
    sift_scores = []
    det_scores  = []
    for frm in tqdm(frames, desc="1ère passe scores"):
        sift_scores.append(compute_sift_score(frm, sift))
        det_scores.append(compute_det_score(
            frm, det_model, det_transform,
            thr=args.thr, w_person=args.weight_person,
            device=device
        ))
    max_sift = max(sift_scores)
    max_det  = max(det_scores)

    # 2ème passe : normaliser et combiner 50/50
    best_idx   = 0
    best_comb  = -1
    os.makedirs(args.out, exist_ok=True)
    for i, frm in enumerate(frames):
        norm_s = sift_scores[i] / max_sift
        norm_d = det_scores[i]  / max_det
        comb   = 0.5 * norm_s + 0.5 * norm_d
        if comb > best_comb:
            best_comb = comb
            best_idx  = i

    # Sauvegarde
    out_path = os.path.join(args.out, f"keyframe_{best_idx:04d}.jpg")
    cv2.imwrite(out_path, frames[best_idx])
    print(f"Key-frame: {best_idx}, score combiné normalisé {best_comb:.3f}")
    print(f"Saved → {out_path}")

if __name__ == "__main__":
    main()
