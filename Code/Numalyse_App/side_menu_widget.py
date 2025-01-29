from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog, QScrollArea, QDockWidget
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

import cv2 
import numpy as np

class SideMenuWidget(QDockWidget):
    """Menu latéral sous forme de DockWidget."""

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

        # Liste pour stocker les boutons et leurs informations
        self.stock_button = []
        self.calcul_segmentation()


    def add_new_button(self, name="Séquence", time=0):
        """Ajoute un bouton avec un nom, une valeur en secondes et un texte."""
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
        
        # Convertir le temps en secondes en millisecondes
        time_in_ms = int(time * 1000)  # Conversion en millisecondes
        
        # Passer le temps au VLCWidget
        self.vlc_widget.set_position_timecode(time_in_ms)


    
    def calcul_segmentation(self):
        """Analyse la vidéo et détecte les changements de scène pour créer des boutons."""
        
        video_path = self.vlc_widget.path_of_media

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("Impossible d'ouvrir la vidéo.")
            return

        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        prev_frame = None
        change_threshold = 0.99  # Seuil pour détecter un changement de plan
        timecodes = []  # Liste des temps où les changements de plan se produisent

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Fin de la vidéo

            frame_count += 1
            current_time = frame_count / frame_rate  # Temps en secondes de la frame actuelle

            # Convertir l'image en niveau de gris pour simplifier la comparaison
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_frame is not None:
                # Calculer la différence entre les images successives
                diff = cv2.absdiff(gray_frame, prev_frame)
                non_zero_count = np.count_nonzero(diff)  # Compter les pixels différents

                # Si la différence dépasse le seuil, on considère qu'il y a un changement de plan
                if non_zero_count / diff.size > change_threshold:
                    print(f"Changement de plan détecté à {current_time} secondes.")
                    timecodes.append(current_time)

            prev_frame = gray_frame

        cap.release()

        # Créer un bouton pour chaque changement de plan
        for idx, time in enumerate(timecodes):
            self.add_new_button(time=time)

        print("Segmentation terminée.")
