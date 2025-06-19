import numpy as np
import matplotlib.pyplot as plt

# Taille de l'image
H, W = 480, 640

# Coordonnées du centre
cx, cy = W / 2.0, H / 2.0

# Création d'une grille de coordonnées
x = np.linspace(0, W - 1, W)
y = np.linspace(0, H - 1, H)
X, Y = np.meshgrid(x, y)

# Calcul des distances normalisées
dx = (X - cx) / cx
dy = (Y - cy) / cy
dist = np.sqrt(dx**2 + dy**2)

# Paramètre de la gaussienne
sigma = 0.5

# Calcul de la pondération spatiale
w_pos = np.exp(-0.5 * (dist / sigma)**2)

# Affichage en heatmap
plt.figure(figsize=(8, 6))
plt.imshow(w_pos, cmap='jet')
plt.title("Pondération spatiale centrée")
plt.colorbar(label='w_pos')
plt.axis('off')
plt.show()
