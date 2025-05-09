import os
import argparse
import subprocess

def is_video_file(filename):
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    return filename.lower().endswith(video_extensions)

def main():
    parser = argparse.ArgumentParser(
        description="Appliquer first_pass.py à toutes les vidéos d'un dossier et enregistrer les résultats dans un fichier texte."
    )
    parser.add_argument("video_folder", help="Chemin vers le dossier contenant les vidéos")
    parser.add_argument("output_txt", help="Fichier texte pour enregistrer les résultats")
    args = parser.parse_args()

    video_folder = args.video_folder
    output_txt = args.output_txt

    if not os.path.isdir(video_folder):
        print(f"Erreur : le dossier « {video_folder} » n'existe pas.")
        return

    video_files = sorted(f for f in os.listdir(video_folder) if is_video_file(f))
    if not video_files:
        print("Aucune vidéo trouvée dans le dossier.")
        return

    for video_file in video_files:
        full_path = os.path.join(video_folder, video_file)
        with open(output_txt, "a") as f:
            subprocess.run(
                ["python3", "first_pass.py", full_path],
                stdout=f,
                stderr=subprocess.STDOUT
            )
            f.write(f"\n")

    print(f"Tous les résultats ont été ajoutés dans : {output_txt}")

if __name__ == "__main__":
    main()
