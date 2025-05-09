'''
Prérequis:
    pip install ultralytics opencv-python

Usage:
    python3 first_pass.py -s chemin/vers/video.mp4
'''
import argparse
import cv2
import os
from collections import Counter
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Détection d'objets dans une vidéo avec YOLO et OpenCV"
    )
    parser.add_argument('video', help='Path to input video')
    parser.add_argument(
        '--conf', '-c',
        type=float,
        default=0.9,
        help='Seuil de confiance minimal pour les détections'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Charger le modèle YOLO (taille nano par défaut)
    model = YOLO('yolov8n.pt')

    # Ouvrir la vidéo
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Erreur: impossible d'ouvrir la vidéo {args.video}")
        return

    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Compteur des occurrences de chaque label
    label_counter = Counter()
    label_counter_per_frame = Counter()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Exécuter la détection
        results = model(frame, conf=args.conf,verbose=False,show=False)

        # Compter chaque détection de label
        for r in results:
            for cls_id in r.boxes.cls.cpu().numpy().tolist():
                label = model.names[int(cls_id)]
                label_counter[label] += 1
            # Extraire les classes détectées dans cette frame (une seule fois par classe)
            cls_ids = set(r.boxes.cls.cpu().numpy().tolist())
            for cls_id in cls_ids:
                label = model.names[int(cls_id)]
                label_counter_per_frame[label] += 1


    cap.release()

    base = os.path.splitext(os.path.basename(args.video))[0]

    print(f"Occurrences des objets détectés dans la vidéo : {base}")
    print(f"Nombre de frames : {length}")
    for label, frame_count in label_counter_per_frame.most_common():
        total_count = label_counter[label]
        ratio = (frame_count / length) * 100
        print(f"{label} détecté {total_count} fois -> présent dans {ratio:.4f}% des frames")
    print("\n")

if __name__ == '__main__':
    main()
