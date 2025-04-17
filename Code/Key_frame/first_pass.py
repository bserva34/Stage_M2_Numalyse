import os
import torch
import cv2                                    # OpenCV pour la lecture vidéo
from lavis.models import load_model_and_preprocess
from PIL import Image

def main(video_path: str):
    # 2.1. Configuration du device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # GPU si disponible :contentReference[oaicite:1]{index=1}

    # 2.2. Chargement du modèle pré-entraîné
    # Ici, 'blip_video_caption' est un modèle BLIP adapté à la description vidéo :contentReference[oaicite:2]{index=2}
    model, vis_processors, txt_processors = load_model_and_preprocess(
        name="blip_video_caption", 
        model_type="default",
        is_eval=True,
        device=device
    )  # load_model_and_preprocess fournit à la fois le modèle et ses transformateurs :contentReference[oaicite:3]{index=3}

    # 2.3. Lecture et extraction des frames
    cap = cv2.VideoCapture(video_path)           # Création de l'objet VideoCapture :contentReference[oaicite:4]{index=4}
    frames = []
    success, frame = cap.read()
    count = 0
    while success and count < 16:                # On extrait par exemple 16 frames uniformément
        # Conversion BGR→RGB et en PIL.Image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        frames.append(pil_img)
        # Lecture de la frame suivante
        success, frame = cap.read()
        count += 1
    cap.release()

    # 2.4. Prétraitement des frames pour le modèle
    # Le processor 'eval' convertit chaque PIL.Image en Tensor [3×H×W]
    video_tensor = torch.stack([vis_processors["eval"](img) for img in frames], dim=1)  
    # On ajoute la dimension batch
    inputs = {"video": video_tensor.unsqueeze(0).to(device)}

    # 2.5. Génération de la caption
    captions = model.generate(inputs)            # Appel à generate() pour produire la description :contentReference[oaicite:5]{index=5}

    # 2.6. Affichage du résultat
    print("Description générée :", captions[0])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Video Captioning avec LAVIS")
    parser.add_argument("video", type=str, help="Chemin vers le fichier vidéo")
    args = parser.parse_args()
    assert os.path.isfile(args.video), "Le fichier vidéo n'existe pas"
    main(args.video)
