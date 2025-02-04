from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog, QScrollArea, QDockWidget, QLabel, QDialog, QVBoxLayout, QLabel, QLineEdit, QSlider, QPushButton, QHBoxLayout, QSpinBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer

import cv2 
import numpy as np

from segmentation import SegmentationThread

class SideMenuWidget(QDockWidget):

    def __init__(self, vlc_widget, parent=None,start=True):
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

        if(start):
            self.affichage = QLabel("Calcul Segmentation ...", self)
            self.affichage.setStyleSheet("color: blue;")
            self.layout.addWidget(self.affichage)

            self.start_segmentation()
        else:
            self.add_button = QPushButton("Ajouter",self)
            self.add_button.setStyleSheet("background-color: blue; color: white; padding: 5px; border-radius: 5px;")
            self.add_button.clicked.connect(self.add_action)
            self.layout.addWidget(self.add_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_buttons_color)
        self.timer.start(50) #actu en ms

        self.max_time=self.vlc_widget.player.get_length()


    def update_buttons_color(self):
        if not self.vlc_widget.media:
            return

        current_time = self.vlc_widget.player.get_time()
        self.max_time=self.vlc_widget.player.get_length()

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


    def add_new_button(self, name="", time=0, verif=True):
        """Ajoute un bouton avec un nom et l'insère à la bonne position dans le layout."""
        if verif:
            if time >= self.max_time:
                return

        if name == "":
            cpt = len(self.stock_button)
            name = "Séquence " + f"{cpt+1}"

        button = QPushButton(name, self)
        button.setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))

        button.clicked.connect(lambda *_: self.set_position(button))
        button.setFixedSize(180, 25)

        # Ajouter le bouton dans la liste
        self.stock_button.append({"button": button, "time": time})

        # Trier les boutons immédiatement après l'ajout
        self.stock_button.sort(key=lambda btn_data: btn_data["time"])

        # Réorganiser les boutons dans le layout
        self.reorganize_buttons()

    def reorganize_buttons(self):
        """Réorganise les boutons dans le layout après un tri."""
        # Supprime tous les boutons du layout
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget and widget != self.add_button:
                self.layout.removeWidget(widget)

        # Réinsère les boutons triés
        for btn_data in self.stock_button:
            self.layout.addWidget(btn_data["button"])



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

    def add_action(self):
        """ Ouvre une boîte de dialogue pour entrer un nom et un temps avec un slider. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter une séquence")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Zone de texte pour le nom
        name_label = QLabel("Nom de la séquence :", dialog)
        layout.addWidget(name_label)
        name_input = QLineEdit(dialog)
        layout.addWidget(name_input)

        # Slider pour choisir le temps
        time_label = QLabel("Position :", dialog)
        layout.addWidget(time_label)

        time_layout = QHBoxLayout()
        time_slider = QSlider(Qt.Horizontal, dialog)
        time_slider.setMinimum(0)
        time_slider.setMaximum(self.max_time - 1)  # Définir la valeur maximale à self.max_time
        time_slider.setTickInterval(1000)

        time_spinbox = QSpinBox(dialog)
        time_spinbox.setMinimum(0)
        time_spinbox.setMaximum(self.max_time - 1)

        # Affichage du temps en minutes:secondes
        time_display = QLabel(dialog)

        # Fonction pour mettre à jour l'affichage en mm:ss
        def update_time_display(value):
            minutes = value // 60000  # Conversion ms → min
            seconds = (value // 1000) % 60  # Conversion ms → sec
            time_display.setText(f"{minutes:02}:{seconds:02}")

        # Valeur initiale = position actuelle de la vidéo
        val = self.vlc_widget.player.get_time()
        time_slider.setValue(val)
        time_spinbox.setValue(val)
        update_time_display(val)  # Affichage initial

        # Synchronisation slider, spinbox et affichage
        #time_slider.valueChanged.connect(time_spinbox.setValue)
        time_spinbox.valueChanged.connect(time_slider.setValue)
        time_slider.valueChanged.connect(update_time_display)

        time_layout.addWidget(time_slider)
        time_layout.addWidget(time_spinbox)
        time_layout.addWidget(time_display)
        layout.addLayout(time_layout)

        # Boutons OK et Annuler
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Action du bouton OK
        def on_ok():
            name = name_input.text().strip()
            time = time_slider.value()
            if name:
                self.add_new_button(name=name, time=time)
                dialog.accept()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()




    def modify_time(self, button):
        """Modifie la valeur de temps associée à un bouton."""
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                val = btn_data["time"]
        new_time, ok = QInputDialog.getInt(self, "Modifier le temps", "Temps en secondes :", value=val, minValue=0, maxValue=self.max_time-1)
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
        self.add_button = QPushButton("Ajouter",self)
        self.add_button.setStyleSheet("background-color: blue; color: white; padding: 5px; border-radius: 5px;")
        self.add_button.clicked.connect(self.add_action)
        self.layout.addWidget(self.add_button)
        for time in timecodes:
            self.add_new_button(time=time)  # Crée un bouton pour chaque changement de plan
        print("Segmentation terminée en arrière-plan.")


    def stop_segmentation(self):
        """Arrête la segmentation si elle est en cours."""
        if hasattr(self, 'segmentation_thread') and self.segmentation_thread.isRunning():
            print("Arrêt de la segmentation en cours...")
            self.segmentation_thread.stop()


