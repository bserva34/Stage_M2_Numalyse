from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog, QScrollArea, QDockWidget, QLabel
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer

import cv2 
import numpy as np

from segmentation import SegmentationThread

class SideMenuWidget(QDockWidget):

    def __init__(self, vlc_widget, parent=None):
        super().__init__("Segmentation", parent)  # Titre du dock
        self.vlc_widget = vlc_widget
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)  # Zones autorisées

        # Définir la largeur du dock
        self.setFixedWidth(200)

        # Créer un widget de conteneur pour le contenu
        self.container = QWidget(self)

        # Créer une zone défilante pour les boutons
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.container)

        # Définir le widget pour le dock
        self.setWidget(self.scroll_area)

        # Layout vertical pour stocker les boutons
        self.layout = QVBoxLayout(self.container)
        self.container.setLayout(self.layout)

        self.affichage = QLabel("Calcul Segmentation ...", self)
        self.affichage.setStyleSheet("color: blue;")
        self.layout.addWidget(self.affichage)

        # Liste pour stocker les boutons et leurs informations
        self.stock_button = []
        self.start_segmentation()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_buttons_color)
        self.timer.start(200) #actu en ms

        self.max_time=self.vlc_widget.player.get_length()


    def update_buttons_color(self):
        """ Met à jour la couleur des boutons en fonction de la progression de la vidéo. """
        if not self.vlc_widget.media:
            return

        current_time = self.vlc_widget.player.get_time()

        # Trouver le bouton qui correspond au temps actuel
        active_button = None
        for btn_data in self.stock_button:
            button_time = btn_data["time"]
            
            if button_time <= current_time:
                active_button = btn_data  # Dernier bouton trouvé avant ou égal au temps actuel
            else:
                break

        # Appliquer la couleur uniquement au bon bouton
        for btn_data in self.stock_button:
            if btn_data == active_button:
                btn_data["button"].setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 5px;")
            else:
                btn_data["button"].setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")


    def add_new_button(self, name="Séquence", time=0):
        """Ajoute un bouton avec un nom, une valeur en secondes et un texte."""
        if(time>=self.max_time):
            return
        cpt = len(self.stock_button)
        name = name + f" {cpt+1}"

        button = QPushButton(name, self)
        button.setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

        button.clicked.connect(lambda *_: self.set_position(button))
        button.setFixedSize(180, 25)

        # Stocker le bouton avec ses infos associées
        self.stock_button.append({"button": button, "time": time})

        # Ajouter le bouton à l'interface
        self.layout.addWidget(button)  # Ajoute avant le bouton d'ajout

    def show_context_menu(self, pos, button):
        """Affiche un menu contextuel avec options de renommer et modifier valeurs."""
        menu = QMenu(self)

        rename_action = QAction("Renommer", self)
        rename_action.triggered.connect(lambda: self.rename_button(button))
        menu.addAction(rename_action)

        delete_action = QAction("Supprimer", self)
        delete_action.triggered.connect(lambda: self.delate_button(button))
        menu.addAction(delete_action)

        mod_action = QAction("Modif TimeCode", self)
        mod_action.triggered.connect(lambda: self.modify_time(button))
        #menu.addAction(mod_action)

        menu.exec_(button.mapToGlobal(pos))

    def rename_button(self, button):
        """Ouvre une boîte de dialogue pour renommer le bouton."""
        new_name, ok = QInputDialog.getText(self, "Renommer le bouton", "Nouveau nom :", text=button.text())
        if ok and new_name.strip():
            button.setText(new_name)
            # Mettre à jour dans stock_button
            for btn_data in self.stock_button:
                if btn_data["button"] == button:
                    btn_data["button"].setText(new_name)

    def delate_button(self, button):
        self.layout.removeWidget(button)
        for i, btn_data in enumerate(self.stock_button):
            if btn_data["button"] == button:
                del self.stock_button[i] 
        
        button.deleteLater()


    def modify_time(self, button):
        """Modifie la valeur de temps associée à un bouton."""
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                val = btn_data["time"]
        new_time, ok = QInputDialog.getInt(self, "Modifier le temps", "Temps en secondes :", value=val, minValue=0)
        if ok:
            for btn_data in self.stock_button:
                if btn_data["button"] == button:
                    btn_data["time"] = new_time
                    print(f"Temps mis à jour pour {button.text()} : {new_time} secondes")

    def set_position(self, button):
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                time = btn_data["time"]
            
        # Passer le temps au VLCWidget
        self.vlc_widget.set_position_timecode(int(time))


    def start_segmentation(self):
        """Démarre la segmentation dans un thread séparé."""
        video_path = self.vlc_widget.path_of_media
        self.segmentation_thread = SegmentationThread(video_path)
        
        # Connecte le signal pour recevoir les timecodes
        self.segmentation_thread.segmentation_done.connect(self.on_segmentation_complete)
        
        self.segmentation_thread.start()  # Démarrer le thread

    def on_segmentation_complete(self, timecodes):
        """Callback exécuté une fois la segmentation terminée."""
        self.layout.removeWidget(self.affichage)
        self.affichage.deleteLater()
        for time in timecodes:
            self.add_new_button(time=time)  # Crée un bouton pour chaque changement de plan
        print("Segmentation terminée en arrière-plan.")


    def stop_segmentation(self):
        """Arrête la segmentation si elle est en cours."""
        if hasattr(self, 'segmentation_thread') and self.segmentation_thread.isRunning():
            print("Arrêt de la segmentation en cours...")
            self.segmentation_thread.stop()


