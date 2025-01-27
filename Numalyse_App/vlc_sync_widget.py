import vlc
import sys
import os
from PIL import Image
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QFrame, QLabel, QSlider, QDialog, QRadioButton, QButtonGroup, QApplication
)
from PySide6.QtCore import Qt, QTimer, QRect
from vlc_player_widget import VLCPlayerWidget
from PySide6.QtGui import QImage, QPainter





class SyncWidget(QWidget):
    """ Widget permettant la lecture synchronisée de vidéos. """

    def __init__(self,parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.layout = QVBoxLayout(self)
        self.player_widgets = []  # Liste pour stocker les lecteurs vidéo
        self.num_windows = 0  # Nombre de sous-fenêtres actives
        self.play=False

        self.setup_initial_ui()

    def setup_initial_ui(self):
        """ Configure l'interface initiale. """
        #label = QLabel("Cliquez sur le bouton 'Configurer' pour démarrer.", self)
        #label.setAlignment(Qt.AlignCenter)
        #self.layout.addWidget(label)

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
        
        # Supprimer l'ancien lecteur
        if hasattr(parent_window, 'vlc_widget'):
            parent_window.vlc_widget.setParent(None)
            parent_window.vlc_widget.deleteLater()
            #print("Ancien lecteur supprimé.")

        # Créer une disposition en grille
        grid_layout = QGridLayout()
        self.layout.addLayout(grid_layout)

        # Créer et ajouter les nouveaux lecteurs
        self.player_widgets = []
        rows, cols = (1, 2) if self.num_windows == 2 else (2, 2)

        for i in range(self.num_windows):
            player = VLCPlayerWidget(True,True,True)
            player.begin=False
            self.player_widgets.append(player)
            grid_layout.addWidget(player, i // cols, i % cols)
        
        #print(f"{self.num_windows} lecteurs créés.")

        # Remplacer le contenu principal de VLCMainWindow
        parent_window.setCentralWidget(self)
        #print("Fenêtre mise à jour avec les nouveaux lecteurs.")
        self.create_control_buttons()


    def create_control_buttons(self):
        """ Crée et ajoute automatiquement les boutons de contrôle au layout donné. """
        button_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("⏯️ Lire", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_pause_button)

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

    def load_video(self):
        fp=self.player_widgets[0].load_file(False)
        for i in self.player_widgets:
            i.load_video(fp)

    def play_all(self):
        for i in self.player_widgets:
            i.play_video()

    def stop_all(self):
        for i in self.player_widgets:
            i.pause_video()


    def capture_screenshot(self):
        images = []
        capture_dir = "captures"
        
        # Capture des screenshots et ajout des chemins d'accès
        for i in range(0, self.num_windows):
            img_path = self.player_widgets[i].capture_screenshot(i)
            if img_path:
                images.append(img_path)

        if not images:
            print(" Aucune image n'a été capturée.")
            return None

        # Charger les images capturées
        loaded_images = [Image.open(img_path) for img_path in images]
        
        # Calculer le nombre de lignes nécessaires (2 images par ligne)
        num_columns = 2
        num_rows = (len(loaded_images) + num_columns - 1) // num_columns  # Division entière pour obtenir le nombre de lignes nécessaires

        # Trouver la largeur et la hauteur de l'image combinée
        max_width = max(img.width for img in loaded_images) * num_columns  # Largeur pour deux images côte à côte
        max_height = max(img.height for img in loaded_images) * num_rows + (num_rows - 1) * 1  # Hauteur pour toutes les lignes + espaces entre les lignes

        # Créer une nouvelle image pour l'assemblage
        combined_image = Image.new('RGB', (max_width, max_height), (255, 255, 255))  # Fond blanc

        # Coller les images deux par deux
        x_offset = 0
        y_offset = 0
        for i, img in enumerate(loaded_images):
            combined_image.paste(img, (x_offset, y_offset))
            
            # Changer l'offset en x pour la prochaine image dans la même ligne
            x_offset += img.width + 5  # 5 px d'espace blanc entre les images

            # Si deux images ont été collées, passer à la ligne suivante
            if (i + 1) % num_columns == 0:
                x_offset = 0
                y_offset += img.height + 5  # 5 px d'espace blanc entre les lignes

        #suppresion des captures individuel
        for img_path in images:
            os.remove(img_path)
        # Sauvegarder l'image combinée
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_path = os.path.join(capture_dir, f"capture_{timestamp}.png")
        combined_image.save(combined_path)

        #print(f" Capture combinée enregistrée : {combined_path}")
        return combined_image







