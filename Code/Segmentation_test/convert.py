import cv2
import os

# Répertoire contenant les vidéos
input_dir = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/Autoshot/videos"

print("Fichiers trouvés :", os.listdir(input_dir))


output_dir = os.path.join(input_dir, "AutoShot_gray")

# Créer le répertoire de sortie s'il n'existe pas
os.makedirs(output_dir, exist_ok=True)

# Extensions de fichiers vidéo que tu veux traiter
video_extensions = ('.mp4', '.avi', '.mov', '.mkv')

# Parcourir tous les fichiers du dossier
for filename in os.listdir(input_dir):
    if filename.lower().endswith(video_extensions):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_gray.mp4")

        cap = cv2.VideoCapture(input_path)

        # Vérifier si la vidéo s'ouvre bien
        if not cap.isOpened():
            print(f"Erreur lors de l'ouverture de la vidéo : {filename}")
            continue

        # Obtenir les propriétés de la vidéo
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec pour .mp4

        # Création du writer pour la vidéo en niveaux de gris
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height), isColor=False)

        print(f"Conversion de {filename} en niveaux de gris...")

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            out.write(gray_frame)

        cap.release()
        out.release()
        print(f"Vidéo convertie : {output_path}")

print("✅ Conversion terminée.")
