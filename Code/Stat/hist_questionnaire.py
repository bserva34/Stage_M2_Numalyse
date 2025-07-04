import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Charger les données : deux colonnes (x, fréquences)
data = np.loadtxt("hist++.dat")
x = data[:, 0]
frequences = data[:, 1]

# Reconstituer les données selon les fréquences
reconstruit = np.repeat(x, frequences.astype(int))

# Calculs statistiques
moyenne = np.mean(reconstruit)
variance = np.var(reconstruit)
mediane = np.median(reconstruit)

# Affichage console
print(f"Moyenne : {moyenne}")
print(f"Variance : {variance}")
print(f"Médiane : {mediane}")

# Tracer l'histogramme
plt.bar(x, frequences, width=0.05, edgecolor='black', align='center')
plt.title("Histogramme Méthode Histogramme Final")
plt.xlabel("Pourcentage de vote")
plt.ylabel("Fréquence")

# Forcer l'affichage des ticks Y en entiers
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

# Ajouter texte des statistiques
# text_str = f"Moyenne = {moyenne:.3f}\nVariance = {variance:.3f}\nMédiane = {mediane:.3f}"
# plt.text(0.95, 0.95, text_str, transform=plt.gca().transAxes,
#          fontsize=10, verticalalignment='top', horizontalalignment='right',
#          bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'))

# Supprimer le quadrillage
# plt.grid(True)  <-- cette ligne est supprimée

# Sauvegarder l'image
plt.savefig("histogramme.png", dpi=300, bbox_inches='tight')

# Afficher
plt.show()
