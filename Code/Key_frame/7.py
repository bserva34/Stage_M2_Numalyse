import argparse
import os
import cv2
import numpy as np
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(
        description='Key frame extraction based on quaternion Fourier transform with multiple features fusion')
    parser.add_argument('video', help='Path to input video')
    parser.add_argument('--out', '-o', required=True, help='Output directory')
    parser.add_argument('--sigma', type=float, default=20, help='Gaussian filter sigma')
    return parser.parse_args()


def quaternion_fused_map(fm, fb, frg, fby, sigma):
    """
    Compute fused feature map via quaternion Fourier transform approximation.
    """
    f1 = fm.astype(np.float32) + 1j * fb.astype(np.float32)
    f2 = frg.astype(np.float32) + 1j * fby.astype(np.float32)

    F1 = np.fft.fft2(f1)
    F2 = np.fft.fft2(f2)

    M = np.real(F1)
    I = np.imag(F1)
    RG = np.real(F2)
    BY = np.imag(F2)

    eps = 1e-8
    phase = np.arctan(np.sqrt(RG**2 + BY**2 + I**2 + eps) / (M + eps))
    phase_norm = cv2.normalize(phase, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    ksize = int(6 * sigma + 1) | 1
    filtered = cv2.GaussianBlur(phase_norm, (ksize, ksize), sigma)

    inv = np.fft.ifft2(filtered.astype(np.float32))
    fused = np.abs(inv)
    fused_norm = cv2.normalize(fused, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return fused_norm


def extract_best_frame(frames, fused_maps, output_dir):
    """
    Compute MSE curve and save only the single best keyframe (max MSE).
    """
    n = len(fused_maps)
    mse = np.zeros(n)
    for i in range(1, n):
        diff = fused_maps[i].astype(np.float32) - fused_maps[i-1].astype(np.float32)
        mse[i] = np.mean(diff**2)

    best_idx = int(np.argmax(mse))
    frame = frames[best_idx]

    out_path = f"{output_dir}_keyframe_{best_idx:04d}.jpg"
    cv2.imwrite(out_path, frame)
    return best_idx


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)

    cap = cv2.VideoCapture(args.video)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    prev = None
    frames, fused_maps = [], []

    for _ in tqdm(range(total), desc="Processing frames"):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame.copy())
        b, g, r = cv2.split(frame)
        gray = ((r.astype(np.float32) + g + b) / 3).astype(np.uint8)
        fb = gray

        R = r.astype(np.float32) - (g.astype(np.float32) + b) / 2
        G = g.astype(np.float32) - (r.astype(np.float32) + b) / 2
        B = b.astype(np.float32) - (r.astype(np.float32) + g) / 2
        Y = ((r.astype(np.float32) + g) / 2) - (np.abs(r.astype(np.float32) - g) / 2)
        frg = (R - G).astype(np.uint8)
        fby = (B - Y).astype(np.uint8)

        fm = cv2.absdiff(frame, prev) if prev is not None else np.zeros_like(frame)
        prev = frame.copy()

        fused = quaternion_fused_map(fm[...,0], fb, frg, fby, args.sigma)
        fused_maps.append(fused)

    cap.release()

    base = os.path.splitext(os.path.basename(args.video))[0]
    output_path=os.path.join(args.out,base)

    print(output_path)


    best_idx = extract_best_frame(frames, fused_maps, output_path)
    print(f"Saved best keyframe at index: {best_idx}")

if __name__ == '__main__':
    main()



# Lecture et prétraitement des images

# On ouvre la vidéo et on parcourt chaque image (frame).

# Pour chaque image, on extrait quatre « canaux » de caractéristiques :

# FM (motion) : différence absolue entre l’image courante et la précédente (si elle existe).

# FB (brightness) : moyenne des trois canaux R, G, B, restituée en niveaux de gris.

# FRG (red/green opponency) : 

# FBY (blue/yellow opponency) : 


# Fusion par transformée de Fourier quaternion

# On regroupe ces quatre caractéristiques en deux plans complexes :

# Plan 1 : FM + i·FB

# Plan 2 : FRG + i·FBY

# On effectue une FFT 2D sur chacun des deux plans.

# On calcule une carte de phase fusionnée :

# formule

# On normalise cette phase en image 8 bits (0–255).

# Filtrage spatial

# On applique un flou gaussien sur la carte de phase normalisée, afin d’atténuer le bruit (les hautes fréquences).

# Cette étape permet d’isoler les contours et structures globales les plus saillants.

# Reconstruction (inverse FFT)

# On traite la carte floutée comme un signal « réel » et on fait une IFFT 2D.

# Le module du résultat constitue la carte fusionnée finale pour cette frame, qui met en valeur à la fois le mouvement et les variations de couleur/brillance.

# Détection de la frame la plus « saillante »

# On calcule la MSE (Mean Squared Error) entre chaque carte fusionnée et celle de la frame précédente, pour obtenir une courbe MSE tout au long de la vidéo.

# L’indice où cette MSE est maximale correspond à la transformation la plus marquée (changement global + local).