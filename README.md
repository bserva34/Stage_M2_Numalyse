# Stage_M2_Numalyse

Ce projet utilise plusieurs bibliothèques pour assurer la gestion des vidéos, des images, des PDF et des analyses de scènes.

## Bibliothèques utilisées

### Bibliothèques standard de Python
- **sys** : Gestion des arguments en ligne de commande et interaction avec l'interpréteur Python.
- **os** : Manipulation des fichiers et des chemins d'accès.
- **json** : Gestion des fichiers JSON pour la sauvegarde et l'ouverture de projets.
- **shutil** : Copie et déplacement de fichiers, y compris les vidéos.
- **time** : Gestion des temps d'exécution et des pauses.
- **datetime** : Manipulation des dates et heures, utile pour les horodatages.

### Bibliothèques tierces
- **PySide6** : Interface graphique basée sur Qt pour la création d'une application interactive.
- **cv2** (OpenCV) : Gestion et traitement des fichiers vidéo et image.
- **reportlab** : Génération de fichiers PDF, utile pour exporter des rapports.
- **scenedetect** : Détection automatique des coupes dans une vidéo.
- **vlc-python** : Utilisation de VLC pour la lecture et le contrôle des vidéos dans l'application.
- **ffmpeg-python** : Interface Python pour FFmpeg, permettant l'édition et la conversion de vidéos.
- **PIL** (Pillow) : Gestion avancée des images, y compris l'ouverture, la modification et la sauvegarde.

## Installation des dépendances
Pour installer toutes les bibliothèques nécessaires, utilisez la commande suivante :

```sh
pip install PySide6 opencv-python reportlab scenedetect python-vlc ffmpeg-python pillow
