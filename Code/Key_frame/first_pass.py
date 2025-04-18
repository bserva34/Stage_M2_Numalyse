'''
Prérequis:
    pip install ultralytics opencv-python

Usage:
    python3 first_pass.py -s chemin/vers/video.mp4
'''
import argparse
import cv2
from collections import Counter
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(
        description="Détection d'objets dans une vidéo avec YOLO et OpenCV"
    )
    parser.add_argument(
        '--source', '-s',
        type=str,
        required=True,
        help='Chemin vers le fichier vidéo à analyser'
    )
    parser.add_argument(
        '--conf', '-c',
        type=float,
        default=0.5,
        help='Seuil de confiance minimal pour les détections'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Charger le modèle YOLO (taille nano par défaut)
    model = YOLO('yolov8n.pt')

    # Ouvrir la vidéo
    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        print(f"Erreur: impossible d'ouvrir la vidéo {args.source}")
        return

    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Compteur des occurrences de chaque label
    label_counter = Counter()

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

    cap.release()

    # Afficher le décompte des objets détectés
    print("Occurrences des objets détectés dans la vidéo :")
    for label, count in label_counter.most_common():
        print(f"{label}: {count} -> {count/length:.4f}%")

if __name__ == '__main__':
    main()
