import os
import sys
import subprocess

def batch_process(script_name, video_dir, out_dir="keyframes"):
    if not os.path.exists(video_dir):
        print(f"Le dossier {video_dir} n'existe pas.")
        return

    os.makedirs(out_dir, exist_ok=True)

    video_files = [f for f in os.listdir(video_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]

    if not video_files:
        print(f"Aucune vidéo trouvée dans {video_dir}")
        return

    for video_file in video_files:
        video_path = os.path.join(video_dir, video_file)
        print(f"Traitement de : {video_path}")

        cmd = ["python3", script_name, video_path, "--out", out_dir]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors du traitement de {video_file} : {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage : python3 batch_process.py nom_de_fonction.py dossier_videos [dossier_sortie]")
    else:
        script = sys.argv[1]
        folder = sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else "keyframes"
        batch_process(script, folder, out)
