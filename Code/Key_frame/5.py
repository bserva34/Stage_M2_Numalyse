import cv2
import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from tqdm import tqdm

import numpy as np
import argparse

def extract_key_frame_combined_score(video_path, out_dir='keyframes'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(device)

    # Chargement des modèles
    #model_clf = models.alexnet(weights=models.AlexNet_Weights.DEFAULT).to(device).eval()
    model_det = models.detection.fasterrcnn_resnet50_fpn(weights=models.detection.FasterRCNN_ResNet50_FPN_Weights.DEFAULT).to(device).eval()
    transform_clf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    transform_det = transforms.Compose([transforms.ToTensor()])
    sift = cv2.SIFT_create()

    # Lecture de la vidéo
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    best_score = -1.0
    best_idx = 0
    for idx, img in enumerate(tqdm(frames, desc="Processing frames")):
        # Score SIFT
        kps = sift.detect(img, None)
        score_sift = sum(k.response for k in kps)

        # Score de détection d'objets
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        input_det = transform_det(pil_img).unsqueeze(0).to(device)
        with torch.no_grad():
            output = model_det(input_det)[0]
        det_scores = output['scores'].cpu().numpy()   # shape [N]
        det_labels = output['labels'].cpu().numpy()   # shape [N], ID COCO

        # Seuil et poids pour les personnes
        thr = 0.7
        w_person = 100.0   # poids appliqué aux “person”

        # Masque des scores > seuil
        mask_thr = det_scores > thr

        # Poids par détection : w_person si label==1 (person), sinon 1.0
        weights = np.where(det_labels == 1, w_person, 1.0)

        # On ne garde que scores et weights pour les indices au-dessus du seuil
        valid_scores  = det_scores[mask_thr]
        valid_weights = weights[mask_thr]

        # Score de détection pondéré
        score_det = float((valid_scores * valid_weights).sum())

        # Puis tout redevient comme avant
        combined_score = score_sift + score_det
        if combined_score > best_score:
            best_score = combined_score
            best_idx   = idx

    # Sauvegarde de la key-frame
    os.makedirs(out_dir, exist_ok=True)
    best_frame = frames[best_idx]
    fname = os.path.join(out_dir, f"keyframe_{best_idx:04d}.jpg")
    cv2.imwrite(fname, best_frame)
    print(f"Saved keyframe {best_idx} with combined score {best_score:.2f} to {fname}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extraction de la unique meilleure key-frame via SIFT + détection + classification')
    parser.add_argument('video', help='Chemin vers la vidéo')
    parser.add_argument('--out', default='keyframes', help='Répertoire de sortie')
    args = parser.parse_args()

    extract_key_frame_combined_score(args.video, out_dir=args.out)
# import cv2
# import os
# import urllib.request
# import torch
# import torch.nn.functional as F
# import torchvision.models as models
# import torchvision.transforms as transforms
# import torchvision.models.detection as detection_models
# from PIL import Image
# from tqdm import tqdm
# import argparse


# def extract_single_best_frame(video_path, out_dir='keyframes'):
#     """
#     Extrait la frame unique ayant le score SIFT le plus élevé,
#     puis réalise une détection d'objet et une classification AlexNet
#     pour information, sans filtrage par seuil.
#     """
#     # Device setup
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

#     # 1) Chargement du modèle AlexNet pour classification
#     print("Loading AlexNet...")
#     model_clf = models.alexnet(weights=models.AlexNet_Weights.DEFAULT).to(device).eval()
#     transform_clf = transforms.Compose([
#         transforms.Resize((224, 224)),
#         transforms.ToTensor(),
#         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
#     ])
#     labels = [l.strip() for l in urllib.request.urlopen(
#         "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
#     ).read().decode().splitlines()]
#     print(f"Loaded {len(labels)} ImageNet labels.")

#     # 2) Chargement du modèle Faster R-CNN pour détection d'objets
#     print("Loading Faster R-CNN detector...")
#     det_model = detection_models.fasterrcnn_resnet50_fpn(
#         weights=detection_models.FasterRCNN_ResNet50_FPN_Weights.DEFAULT
#     ).to(device).eval()
#     transform_det = transforms.Compose([transforms.ToTensor()])

#     # 3) Initialisation de SIFT
#     print("Initializing SIFT feature detector...")
#     sift = cv2.SIFT_create()

#     # Lecture de la vidéo
#     cap = cv2.VideoCapture(video_path)
#     if not cap.isOpened():
#         raise RuntimeError(f"Cannot open video: {video_path}")

#     frames = []
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
#         frames.append(frame)
#     cap.release()

#     if not frames:
#         raise RuntimeError("Video contains no frames")

#     # Scoring SIFT de chaque frame
#     best_score = -1.0
#     best_idx = 0
#     for idx, img in enumerate(tqdm(frames, desc="Scoring SIFT")):
#         kps = sift.detect(img, None)
#         score = sum(k.response for k in kps)
#         if score > best_score:
#             best_score = score
#             best_idx = idx
#     print(f"Best frame by SIFT: index={best_idx}, score={best_score:.1f}")

#     # Récupération de la frame best
#     best_img = frames[best_idx]
#     pil = Image.fromarray(cv2.cvtColor(best_img, cv2.COLOR_BGR2RGB))

#     # Détection d'objets (pour info)
#     inp_det = transform_det(pil).unsqueeze(0).to(device)
#     with torch.no_grad():
#         det_out = det_model(inp_det)
#     det_scores = det_out[0]['scores'].cpu().numpy()
#     print(f"Object detection scores: {det_scores}")

#     # Classification AlexNet (pour info)
#     inp_clf = transform_clf(pil).unsqueeze(0).to(device)
#     with torch.no_grad():
#         out_clf = model_clf(inp_clf)
#         probs = F.softmax(out_clf, dim=1).cpu().numpy()[0]
#         idx_cl = probs.argmax()
#         p_val = probs[idx_cl]
#     print(f"Classification: {labels[idx_cl]}, confidence={p_val:.3f}")

#     # Sauvegarde de la key-frame
#     os.makedirs(out_dir, exist_ok=True)
#     fname = os.path.join(out_dir, f"keyframe_{best_idx:04d}.jpg")
#     cv2.imwrite(fname, best_img)
#     print(f"Saved best keyframe to {fname}")

#     return best_idx, fname


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(
#         description='Extraction de la unique meilleure key-frame via SIFT + détection + classification')
#     parser.add_argument('video', help='Chemin vers la vidéo')
#     parser.add_argument('--out', default='keyframes', help='Répertoire de sortie')
#     args = parser.parse_args()

#     extract_single_best_frame(args.video, out_dir=args.out)



