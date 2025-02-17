import vlc
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QFrame, QLabel, QSlider, QDialog, QRadioButton, QButtonGroup, QApplication
)
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from vlc_player_widget import VLCPlayerWidget
from PySide6.QtGui import QImage, QPainter, QKeySequence, QShortcut


class SyncWidget(QWidget):
    """ Widget permettant la lecture synchronisée de vidéos. """
    enable_segmentation = Signal(bool)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.layout = QVBoxLayout(self)
        self.player_widgets = []  # Liste pour stocker les lecteurs vidéo
        self.num_windows = 0  # Nombre de sous-fenêtres actives
        self.play=False

        self.cpt_load=0

        self.dialog_result = False

    def configure(self):
        """ Ouvre une fenêtre de configuration pour choisir le mode. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration du mode synchronisé")

        dialog_layout = QVBoxLayout(dialog)

        # Options pour le nombre de fenêtres
        num_label = QLabel("Nombre de sous-fenêtres :", dialog)
        dialog_layout.addWidget(num_label)

        num_group = QButtonGroup(dialog)
        option_2 = QRadioButton("2", dialog)
        option_4 = QRadioButton("4", dialog)
        num_group.addButton(option_2)
        num_group.addButton(option_4)
        option_2.setChecked(True)

        dialog_layout.addWidget(option_2)
        dialog_layout.addWidget(option_4)

        # Boutons OK/Annuler
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)

        def on_ok():
            if option_2.isChecked():
                self.num_windows = 2
            elif option_4.isChecked():
                self.num_windows = 4
            self.create_video_players()  # Crée les lecteurs
            self.dialog_result=True
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        dialog.exec()

    

    def create_video_players(self):
        #print("Création des lecteurs vidéo...")  

        # Vérifier que la référence à VLCMainWindow est valide
        if self.main_window is None:
            print("Erreur : impossible de récupérer VLCMainWindow")
            return
        
        parent_window = self.main_window  # Utiliser la référence correcte
        


        # Créer une disposition en grille
        grid_layout = QGridLayout()
        self.layout.addLayout(grid_layout)

        # Créer et ajouter les nouveaux lecteurs
        self.player_widgets = []
        rows, cols = (1, 2) if self.num_windows == 2 else (2, 2)

        for i in range(self.num_windows):
            player = VLCPlayerWidget(True,True,True,False)
            player.begin=False
            player.enable_load.connect(self.cpt_load_action)
            self.player_widgets.append(player)
            grid_layout.addWidget(player, i // cols, i % cols)
        
        #print(f"{self.num_windows} lecteurs créés.")

        # Remplacer le contenu principal de VLCMainWindow
        parent_window.setCentralWidget(self)
        #print("Fenêtre mise à jour avec les nouveaux lecteurs.")
        self.create_control_buttons()

    def cpt_load_action(self, val):
        if(val):
            self.cpt_load+=1
        else:
            self.cpt_load-=1

        if (self.cpt_load==self.num_windows):
            self.enable_segmentation.emit(True)
        else:
            self.enable_segmentation.emit(False)

        if (self.cpt_load==0):
            self.play_pause_button.setText("⏯️ Lire")
            self.play=False

    def create_control_buttons(self):
        """ Crée et ajoute automatiquement les boutons de contrôle au layout donné. """
        button_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("⏯️ Lire", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_pause_button)

        self.play_pause_shortcut = QShortcut(QKeySequence("Space"), self)
        self.play_pause_shortcut.activated.connect(self.toggle_play_pause)

        self.stop_button = QPushButton("⏹ Arrêter", self)
        self.stop_button.clicked.connect(self.exit_video_players)
        button_layout.addWidget(self.stop_button)

        self.layout.addLayout(button_layout)

    def toggle_play_pause(self):
        cond=True
        for i in self.player_widgets:
            if i.media is not None : cond=False
        if cond:
            self.load_video()
        elif self.play:
            self.stop_all()
            self.play_pause_button.setText("⏯️ Lire")
            self.play=False
        else:
            self.play_all()
            self.play_pause_button.setText("⏯️ Pause")
            self.play=True            


    def exit_video_players(self):
        for i in self.player_widgets:
            i.stop_video()
        self.play_pause_button.setText("⏯️ Lire")
        self.enable_segmentation.emit(False)

    def load_video(self):
        fp=self.player_widgets[0].load_file(False)
        for i in self.player_widgets:
            i.begin=True
            i.load_video(fp)
        self.play_pause_button.setText("⏯️ Pause")
        self.play=True
        self.enable_segmentation.emit(True)


    def play_all(self):
        for i in self.player_widgets:
            if i.media is not None:
                i.play_video()

    def stop_all(self):
        for i in self.player_widgets:
            if i.media is not None:
                i.pause_video()



    #capture d'écran combiné
    def capture_screenshot(self):
        images = []
        capture_dir = os.path.join(str(Path.home()), "Videos", "Capture_SLV")

        # Capture des screenshots et ajout des chemins d'accès
        for i in range(self.num_windows):
            img_path = self.player_widgets[i].capture_screenshot(i)
            if img_path:
                images.append(img_path)

        if not images:
            print("Aucune image n'a été capturée.")
            return None

        # Charger les images capturées
        loaded_images = []
        for img_path in images:
            try:
                loaded_images.append(Image.open(img_path))
            except (IOError, FileNotFoundError):
                return

        separateur = 2  # Espacement entre les images

        # Trouver la plus petite largeur et hauteur parmi les images
        min_width = min(img.width for img in loaded_images)
        min_height = min(img.height for img in loaded_images)

        # Redimensionner toutes les images en conservant le ratio
        resized_images = []
        for img in loaded_images:
            img_ratio = img.width / img.height  # Ratio largeur / hauteur
            if img_ratio > 1:  # Image en mode paysage
                new_width = min_width
                new_height = int(new_width / img_ratio)
            else:  # Image en mode portrait ou carré
                new_height = min_height
                new_width = int(new_height * img_ratio)
            
            resized_images.append(img.resize((new_width, new_height), Image.LANCZOS))

        # Trouver la largeur et la hauteur maximales des images
        max_width = max(img.width for img in resized_images)
        max_height = max(img.height for img in resized_images)

        # Déterminer la disposition en grille
        num_columns = 2
        num_rows = (len(resized_images) + num_columns - 1) // num_columns  # Arrondi vers le haut

        # Taille totale de l'image combinée
        total_width = max_width * num_columns + (num_columns - 1) * separateur
        total_height = max_height * num_rows + (num_rows - 1) * separateur

        # Créer une nouvelle image vierge avec fond noir
        combined_image = Image.new('RGB', (total_width, total_height), (0, 0, 0))
        draw = ImageDraw.Draw(combined_image)  # Outil pour dessiner

        # Positionner les images au centre de chaque cellule
        x_offset, y_offset = 0, 0
        for index, img in enumerate(resized_images):
            # Calculer la position pour centrer l'image dans la cellule
            centered_x = x_offset + (max_width - img.width) // 2
            centered_y = y_offset + (max_height - img.height) // 2

            # Coller l'image à la bonne position
            combined_image.paste(img, (centered_x, centered_y))

            # Mise à jour de l'offset
            x_offset += max_width + separateur
            if (index + 1) % num_columns == 0:  # Nouvelle ligne après num_columns images
                x_offset = 0
                y_offset += max_height + separateur

        # Dessiner les séparateurs blancs
        for col in range(1, num_columns):
            x_sep = col * max_width + (col - 1) * separateur
            draw.line([(x_sep, 0), (x_sep, total_height)], fill="white", width=separateur)

        for row in range(1, num_rows):
            y_sep = row * max_height + (row - 1) * separateur
            draw.line([(0, y_sep), (total_width, y_sep)], fill="white", width=separateur)

        # Suppression des captures individuelles
        for img_path in images:
            os.remove(img_path)

        # Sauvegarder l'image combinée
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_path = os.path.join(capture_dir, f"capture_{timestamp}.png")
        combined_image.save(combined_path)

        return combined_image





