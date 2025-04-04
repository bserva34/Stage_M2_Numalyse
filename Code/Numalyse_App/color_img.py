import cv2
import numpy as np
from skimage.segmentation import slic
from scipy.cluster.hierarchy import linkage, fcluster
from PIL import Image

from message_popup import MessagePopUp

class ColorImage(): 
    def __init__(self, parent=None, vlc_widget=None):
        super().__init__()
        self.parent=parent
        self.vlc = vlc_widget
        self.affichage_temp=MessagePopUp(self.parent,titre="",txt="Calcul en cours",type="warning",time=0)

        self.generate_color_bar_from_video(self.vlc.path_of_media)



    def get_palette_superpixels(self, image, num_superpixels=100, num_clusters=10):
        """Segmente l'image en superpixels, applique un clustering hiérarchique et extrait les couleurs dominantes"""
        
        # Convertir en espace Lab (mieux pour l'analyse des couleurs)
        image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2Lab)
        
        # Appliquer SEEDS / SLIC pour créer des superpixels
        superpixels = slic(image_lab, n_segments=num_superpixels, compactness=10, start_label=0)
        
        # Moyenne des couleurs par superpixel
        avg_colors = []
        for label in np.unique(superpixels):
            mask = (superpixels == label)
            avg_color = np.mean(image_lab[mask], axis=0)  # Moyenne par superpixel
            avg_colors.append(avg_color)

        avg_colors = np.array(avg_colors)  # Convertir en numpy array
        
        # Clustering agglomératif (bottom-up) sur ces couleurs
        clusters = linkage(avg_colors, method='ward')  # Création de la hiérarchie
        cluster_labels = fcluster(clusters, num_clusters, criterion='maxclust')  # Regroupement en k couleurs

        # Moyenne des couleurs par cluster obtenu
        final_palette = []
        for i in range(1, num_clusters + 1):
            mask = (cluster_labels == i)
            if np.any(mask):  
                cluster_color = np.mean(avg_colors[mask], axis=0)
                final_palette.append(cluster_color)

        # Convertir en RGB pour affichage
        final_palette = np.array(final_palette, dtype=np.uint8)
        final_palette = cv2.cvtColor(final_palette.reshape(1, -1, 3), cv2.COLOR_Lab2RGB)
        return final_palette[0]  # Retourne une liste de couleurs dominantes

    def generate_color_bar_from_video(self, video_path, frame_step=10, num_superpixels=100, num_clusters=10):
        """Génère un barcode de couleurs basé sur la palette de chaque frame"""

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Erreur : Impossible d'ouvrir la vidéo")
            return
        
        # Récupérer la hauteur de la vidéo
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_colors = []
        cpt=1
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            print(f"Frame {cpt}/{total_frames}")

            # Traiter une frame sur 'frame_step' pour accélérer
            if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % frame_step == 0:
                palette = self.get_palette_superpixels(frame, num_superpixels, num_clusters)
                frames_colors.append(palette)
            cpt+=1
        
        cap.release()

        # Nombre total de frames traitées
        num_frames = len(frames_colors)

        # Création du barcode final avec la bonne hauteur et largeur
        barcode_img = np.zeros((video_height, num_frames, 3), dtype=np.uint8)

        for i, palette in enumerate(frames_colors):
            for j, color in enumerate(palette):
                barcode_img[j * (video_height // num_clusters):(j + 1) * (video_height // num_clusters), i] = color

        # current_width = barcode_img.shape[1]
        # min_width = 1000
        # if current_width < min_width:
        #     scale = min_width / current_width
        #     barcode_img = cv2.resize(barcode_img, (min_width, video_height), interpolation=cv2.INTER_NEAREST)

        # Sauvegarde et affichage de l'image
        barcode_img = Image.fromarray(barcode_img)
        # barcode_img.show()
        barcode_img.save("vian_color_barcode.png")
        self.affichage_temp.hide_message()
