import ctypes
import vlc

lib = ctypes.util.find_library("vlc")
print("Bibliothèque VLC trouvée :", lib)

try:
    instance = vlc.Instance()
    print("VLC Instance chargée avec succès :", instance)
except Exception as e:
    print("Erreur lors du chargement de VLC :", e)
