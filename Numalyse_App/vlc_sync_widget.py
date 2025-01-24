from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QFrame, QLabel, QSlider, QDialog, QRadioButton, QButtonGroup, QApplication
)
from PySide6.QtCore import Qt, QTimer
import vlc
import sys
from vlc_player_widget import VLCPlayerWidget




class SyncWidget(QWidget):
    """ Widget permettant la lecture synchronisée de vidéos. """

    def __init__(self,parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.layout = QVBoxLayout(self)
        self.player_widgets = []  # Liste pour stocker les lecteurs vidéo
        self.num_windows = 0  # Nombre de sous-fenêtres actives

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
        print("Création des lecteurs vidéo...")  

        # Vérifier que la référence à VLCMainWindow est valide
        if self.main_window is None:
            print("Erreur : impossible de récupérer VLCMainWindow")
            return
        
        parent_window = self.main_window  # Utiliser la référence correcte
        
        # Supprimer l'ancien lecteur
        if hasattr(parent_window, 'vlc_widget'):
            parent_window.vlc_widget.setParent(None)
            parent_window.vlc_widget.deleteLater()
            print("Ancien lecteur supprimé.")

        # Créer une disposition en grille
        grid_layout = QGridLayout()
        self.layout.addLayout(grid_layout)

        # Créer et ajouter les nouveaux lecteurs
        self.player_widgets = []
        rows, cols = (1, 2) if self.num_windows == 2 else (2, 2)

        for i in range(self.num_windows):
            player = VLCPlayerWidget()
            player.begin=False
            self.player_widgets.append(player)
            grid_layout.addWidget(player, i // cols, i % cols)
        
        print(f"{self.num_windows} lecteurs créés.")

        # Remplacer le contenu principal de VLCMainWindow
        parent_window.setCentralWidget(self)
        print("Fenêtre mise à jour avec les nouveaux lecteurs.")

    def exit_video_players(self):
        for i in self.player_widgets:
            i.stop_video()







