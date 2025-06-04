import numpy as np
import matplotlib.pyplot as plt

def double_gaussian_equal(x, t, epsilon):
    """
    Deux gaussiennes de même hauteur (=1) et même largeur (=20% de t),
    centrées en t/2 et t - epsilon.
    """
    sigma = 0.15 * t
    A = 1.0

    g1 = A * np.exp(-((x - t/2)**2) / (2 * sigma**2))
    g2 = A * np.exp(-((x - (t - epsilon))**2) / (2 * sigma**2))
    return g1 + g2

# Exemple de tracé
t = 1000
epsilon = 0.1*t
x = np.linspace(0, t, 500)
y = double_gaussian_equal(x, t, epsilon)

plt.plot(x, y)
plt.title("Double gaussienne")
plt.xlabel("num frame")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()
