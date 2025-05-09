#!/usr/bin/env python3
import os
import fnmatch
from PIL import Image, ImageDraw, ImageFont
import math

def create_composite(image_paths, save_path, folder_names, extra_labels=None,
                     font_size=20, per_row=3, target_h=256):
    """
    Crée une image composite :
    - toutes les images ont la même hauteur (target_h), largeur proportionnelle,
    - le texte est centré avec nom de dossier + suffixe,
    - les images sont centrées horizontalement dans chaque cellule.
    """
    from PIL import ImageOps

    imgs = []
    resized_sizes = []

    # 1. Charger et redimensionner les images tout en conservant le ratio
    for path in image_paths:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        ratio = target_h / h
        new_w = int(w * ratio)
        img_resized = img.resize((new_w, target_h), Image.LANCZOS)
        imgs.append(img_resized)
        resized_sizes.append((new_w, target_h))

    max_w = max(w for w, _ in resized_sizes)
    img_w = max_w
    img_h = target_h

    text_padding = font_size + 10
    cell_h = img_h + text_padding

    n = len(imgs)
    rows = math.ceil(n / per_row)

    composite_w = per_row * img_w
    composite_h = rows * cell_h

    composite = Image.new('RGB', (composite_w, composite_h), (255, 255, 255))
    draw = ImageDraw.Draw(composite)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    for idx, (img, folder_name) in enumerate(zip(imgs, folder_names)):
        label = folder_name
        if extra_labels:
            label += f" - {extra_labels[idx]}"

        row = idx // per_row
        col = idx % per_row
        x = col * img_w
        y = row * cell_h

        # Centrage horizontal de l’image dans la cellule
        img_w_resized, _ = img.size
        paste_x = x + (img_w - img_w_resized) // 2

        # Centrer le texte
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = x + (img_w - text_w) // 2
        draw.text((text_x, y + 5), label, fill=(0, 0, 0), font=font)

        # Coller l’image redimensionnée
        composite.paste(img, (paste_x, y + text_padding))

    composite.save(save_path)
    print(f"→ Enregistré : {save_path}")




def collect_prefixes(root_dir, marker='_keyframe'):
    """
    Parcourt tous les sous-dossiers de root_dir et renvoie :
    - un ensemble de tous les préfixes trouvés (avant marker),
    - la liste des chemins de sous-dossiers.
    """
    subdirs = [
        os.path.join(root_dir, d) for d in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, d))
    ]
    prefixes = set()

    for d in subdirs:
        for fname in os.listdir(d):
            if marker in fname:
                prefix = fname.split(marker, 1)[0]
                prefixes.add(prefix)
    return prefixes, subdirs


def main(root_dir, output_dir, marker='_keyframe'):
    os.makedirs(output_dir, exist_ok=True)

    prefixes, subdirs = collect_prefixes(root_dir, marker)
    if not prefixes:
        print("Aucun préfixe « ..._keyframe » trouvé dans les sous-dossiers.")
        return

    for prefix in sorted(prefixes):
        # Pour chaque dossier, cherche le fichier commençant par prefix + marker*
        paths = []
        folders = []
        missing = False
        for d in subdirs:
            pattern = f"{prefix}{marker}*"
            matches = fnmatch.filter(os.listdir(d), pattern)
            if not matches:
                print(f"⚠️  Dans «{d}», aucun fichier ne correspond à '{pattern}'")
                missing = True
                break
            paths.append(os.path.join(d, matches[0]))
            folders.append(os.path.basename(d))  # nom du dossier


        if missing:
            continue

        # Déterminer l'extension d'origine
        ext = os.path.splitext(paths[0])[1]
        save_name = f"{prefix}{ext}"
        save_path = os.path.join(output_dir, save_name)

        folder_vals = []
        for d, p in zip(folders, paths):
            try:
                val = float(d.split('_')[1])
            except (IndexError, ValueError):
                val = float('inf')  # met à la fin si le format est incorrect
            folder_vals.append((val, d, p))

        # Tri par valeur numérique extraite
        folder_vals.sort()

        # On remet dans l’ordre trié
        folders = [d for _, d, _ in folder_vals]
        paths = [p for _, _, p in folder_vals]


        extra_labels = [os.path.splitext(os.path.basename(p))[0].rsplit('_', 1)[-1] for p in paths]
        create_composite(paths, save_path, folders, extra_labels=extra_labels)





if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Pour chaque préfixe avant '_keyframe', crée une image composite horizontale."
    )
    parser.add_argument("root_dir",
                        help="Répertoire racine contenant vos sous-dossiers (p.ex. '7_frame/').")
    parser.add_argument("output_dir",
                        help="Répertoire où stocker les composites (p.ex. '7_frame/res/').")
    parser.add_argument("-m", "--marker", default="_keyframe",
                        help="Marqueur séparant le préfixe (défaut '_keyframe').")
    args = parser.parse_args()

    main(args.root_dir, args.output_dir, args.marker)
