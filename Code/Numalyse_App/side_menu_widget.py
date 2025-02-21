from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog, QScrollArea, QDockWidget, QLabel, QDialog, QLineEdit, QSlider, QPushButton, QHBoxLayout, QSpinBox, QTextEdit, QFrame
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer, Signal

import cv2 
import os
from datetime import datetime
from moviepy.editor import VideoFileClip

from segmentation import SegmentationThread
from time_selector import TimeSelector
from time_manager import TimeManager
from message_popup import MessagePopUp

class SideMenuWidget(QDockWidget):
    change = Signal(bool)
    segmentation_done = Signal(bool)

    def __init__(self, vlc_widget, parent=None,start=True):
        super().__init__("Segmentation", parent)  # Titre du dock
        self.vlc_widget = vlc_widget
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)  # Zones autorisées

        # Définir la largeur du dock
        self.setFixedWidth(300)

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
        self.button_notes = {}

        self.seg_ok=False

        if(start):
            self.seg_button = QPushButton("Segmentation Auto",self)
            self.seg_button.setStyleSheet("background-color: green; color: white; padding: 5px; border-radius: 5px;") 
            self.seg_button.clicked.connect(self.seg_action)
            self.layout.addWidget(self.seg_button)
        else:
            self.seg_ok=True

        self.add_button = QPushButton("Ajouter",self)
        self.add_button.setStyleSheet("background-color: blue; color: white; padding: 5px; border-radius: 5px;") 
        self.add_button.clicked.connect(self.add_action)
        self.layout.addWidget(self.add_button)

        self.layout.addStretch()

        self.fps=None

        self.max_time=self.vlc_widget.player.get_length()

        self.time_manager=TimeManager()


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_buttons_color)
        self.timer.start(50) #actu en ms

        

    #affichage du bouton en rouge
    def update_buttons_color(self):
        if not self.vlc_widget.media:
            return

        current_time = self.vlc_widget.player.get_time()
        self.max_time = self.vlc_widget.player.get_length()

        # Appliquer la couleur en fonction du temps actuel
        for btn_data in self.stock_button:
            button_time = btn_data["time"]
            button_end = btn_data["end"]

            if button_time <= current_time <= button_end:
                btn_data["button"].setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 5px;")
            else:
                btn_data["button"].setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")


    #fonction de tri appeler après ajout de bouton pour un affichage logique
    def reorganize_buttons(self):
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget:
                    self.layout.removeWidget(widget)
                    widget.setParent(None)
                else: 
                    self.layout.removeItem(item)

        # Réajoute les boutons fixes
        if(not self.seg_ok):
            self.layout.addWidget(self.seg_button)
        self.layout.addWidget(self.add_button)

        # Réinsère les frames triés
        for btn_data in self.stock_button:
            self.layout.addWidget(btn_data["frame"])

        # Réajoute un stretch à la fin
        self.layout.addStretch()




    #fonction d'ajout d'une nouveaux bouton
    def add_new_button(self, name="", time=0, end=0, verif=True, frame1=-1, frame2=-1):
        if verif and time >= self.max_time:
            return

        if name == "":
            cpt = len(self.stock_button)
            name = "Sequence " + f"{cpt+1}"

        # Création du cadre pour regrouper le bouton et ses éléments associés
        frame = QFrame(self)
        frame.setStyleSheet("border: 1px solid gray; padding: 5px; border-radius: 5px;")
        frame_layout = QVBoxLayout(frame)

        # Création du bouton
        button = QPushButton(name, self)
        button.setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))
        button.clicked.connect(lambda *_: self.set_position(button))
        #button.setFixedSize(180, 25)

        # Création du label pour afficher le timecode
        if end == 0:
            time_label = QLabel("Début : " + self.time_manager.m_to_mst(time), self)
        else:
            time_label = QLabel(f"Début : {self.time_manager.m_to_mst(time)} / Fin : {self.time_manager.m_to_mst(end)}", self)

        time_label.setFixedHeight(25)

        frame_layout.addWidget(button)
        frame_layout.addWidget(time_label)

        # Ajouter le frame à la liste des boutons stockés
        self.stock_button.append({"frame": frame, "button": button, "time": time, "end": end, "label": time_label, "frame1": frame1, "frame2":frame2})

        # Trier les boutons
        self.stock_button.sort(key=lambda btn_data: btn_data["time"])

        # Réorganiser les boutons dans l'affichage
        self.reorganize_buttons()

        self.button_notes[button] = []  # Associer une liste vide de notes au bouton

        if verif:
            self.change.emit(True)
            self.segmentation_done.emit(True)

        return button



    #menu clique droit du bouton/séquence
    def show_context_menu(self, pos, button):
        """Affiche un menu contextuel avec options de renommer et modifier valeurs."""
        menu = QMenu(self)

        rename_action = QAction("Renommer", self)
        rename_action.triggered.connect(lambda: self.rename_button(button))
        menu.addAction(rename_action)

        mod_action = QAction("Modifier TimeCode", self)
        mod_action.triggered.connect(lambda: self.modify_time(button))
        menu.addAction(mod_action)

        delete_action = QAction("Supprimer", self)
        delete_action.triggered.connect(lambda: self.delate_button(button))
        menu.addAction(delete_action)

        add_note_action = QAction("Ajouter une note")
        add_note_action.triggered.connect(lambda: self.add_note_menu(button))
        menu.addAction(add_note_action)

        extract_action = QAction("Extraire la séquence")
        extract_action.triggered.connect(lambda: self.extract_action(button))
        menu.addAction(extract_action)

        menu.exec_(button.mapToGlobal(pos))

    #fonction 1
    def rename_button(self, button):
        """Ouvre une boîte de dialogue pour renommer le bouton."""
        new_name, ok = QInputDialog.getText(self, "Renommer le bouton", "Nouveau nom :", text=button.text())
        if ok and new_name.strip():
            button.setText(new_name)
            # Mettre à jour dans stock_button
            for btn_data in self.stock_button:
                if btn_data["button"] == button:
                    btn_data["button"].setText(new_name)
        self.change.emit(True)

    #fonction 2
    def delate_button(self, button):
        """Supprime un bouton et son cadre associé."""
        cpt=0
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                frame = btn_data["frame"]
                
                # Supprimer le frame entier
                self.layout.removeWidget(frame)
                frame.deleteLater()

                # Supprimer les notes associées
                if button in self.button_notes:
                    del self.button_notes[button]


                # Supprimer le bouton de la liste
                self.stock_button.remove(btn_data)
                break
            cpt+=1

        self.change.emit(True)


    #fonction 3
    def add_note_menu(self, button):
        self.add_note(button, "")  # Ajoute une note vide directement
        self.change.emit(True)

    def add_note(self, button, text=""):
        note_widget = QTextEdit(self)
        note_widget.setPlainText(text)
        note_widget.setReadOnly(False)
        note_widget.setStyleSheet("color: gray; font-style: italic;")
        #note_widget.setFixedSize(180, 50)
        note_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        note_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        note_widget.customContextMenuRequested.connect(lambda pos: self.show_note_context_menu(note_widget, pos))

        if button not in self.button_notes:
            self.button_notes[button] = []

        self.button_notes[button].append(note_widget)

        # Trouver le `frame` associé au bouton et ajouter la note dedans
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                frame_layout = btn_data["frame"].layout()
                frame_layout.addWidget(note_widget)
                break  # On sort de la boucle une fois trouvé

        # Détecte si du texte est ajouté
        note_widget.textChanged.connect(lambda: self.on_text_changed(note_widget))

        self.change.emit(True)


    def on_text_changed(self, note_widget):
        text = note_widget.toPlainText().strip()
        if text:
            note_widget.setStyleSheet("")  # Normal
        else:
            note_widget.setStyleSheet("color: gray; font-style: italic;")
        self.change.emit(True)

    #menu clique droit note
    def show_note_context_menu(self, note_widget, pos):
        """ Affiche un menu contextuel sur un clic droit. """
        menu = QMenu(self)

        delete_action = QAction("Supprimer la note", self)
        delete_action.triggered.connect(lambda: self.remove_note(note_widget))

        menu.addAction(delete_action)
        
        menu.exec_(note_widget.mapToGlobal(pos))

    #fonction 1 clique droit note
    def remove_note(self, note_widget):
        """ Supprime la note de l'interface et de la liste. """
        for button, notes in self.button_notes.items():
            if note_widget in notes:
                notes.remove(note_widget)
                self.layout.removeWidget(note_widget)
                note_widget.deleteLater()
                break
        self.change.emit(True)

    #fonction 4 extraction
    def extract_action(self, button): 
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                time = btn_data["time"]
                end = btn_data["end"]
                duration = end - time

        if not os.path.exists(self.vlc_widget.capture_dir):
            os.makedirs(self.vlc_widget.capture_dir,exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_path = os.path.join(self.vlc_widget.capture_dir, f"{button.text()}_{timestamp}.mp4")

        self.vlc_widget.extract_segment_with_ffmpeg(self.vlc_widget.path_of_media,time//1000,duration//1000,capture_path)
        affichage=MessagePopUp(self)

    #ajout d'une séquence
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

        time_label = QLabel("Début :", dialog)
        layout.addWidget(time_label)

        self.time = TimeSelector(dialog, self.vlc_widget.player.get_length(), self.vlc_widget.player.get_time())
        layout.addWidget(self.time)        

        time_label2 = QLabel("Fin :", dialog)
        layout.addWidget(time_label2)

        self.time2 = TimeSelector(dialog, self.vlc_widget.player.get_length() , self.vlc_widget.player.get_time() + 5)
        layout.addWidget(self.time2)        



        # Boutons OK et Annuler
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Action du bouton OK
        def on_ok():
            if(self.fps==None):
                video=VideoFileClip(self.vlc_widget.path_of_media)
                self.fps = video.fps
            name = name_input.text().strip()
            new_time = self.time.get_time_in_milliseconds()
            end_time = self.time2.get_time_in_milliseconds()
            frame1 = int((new_time/1000)*self.fps)
            frame2 = int((end_time/1000)*self.fps)
            if name and 0<new_time<=self.max_time:
                self.add_new_button(name=name, time=new_time, end=end_time,frame1=frame1,frame2=frame2)
                dialog.accept()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

    #modif temps non utilisé
    def modify_time(self, button):

        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                start = btn_data["time"]
                end = btn_data["end"]

        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter une séquence")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        # Slider pour choisir le temps
        time_label = QLabel("Début :", dialog)
        layout.addWidget(time_label)

        self.time = TimeSelector(dialog, self.vlc_widget.player.get_length(), start)
        layout.addWidget(self.time)        

        time_label2 = QLabel("Fin :", dialog)
        layout.addWidget(time_label2)

        self.time2 = TimeSelector(dialog, self.vlc_widget.player.get_length(), end )
        layout.addWidget(self.time2)        

        # Boutons OK et Annuler
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Action du bouton OK
        def on_ok():
            new_time = self.time.get_time_in_milliseconds()
            end_time = self.time2.get_time_in_milliseconds()
            new_label ="Début : "+self.time_manager.m_to_mst(new_time)+" / Fin : "+self.time_manager.m_to_mst(end_time)
            for btn_data in self.stock_button:
                if btn_data["button"] == button:
                    btn_data["time"] = new_time
                    btn_data["end"] = end_time

                    btn_data["label"].setText(new_label)

            dialog.accept()
            self.reorganize_buttons()
            self.change.emit(True)


        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()


    #fonction appeler quand on clique sur un bouton
    def set_position(self, button):
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                time = btn_data["time"]
            
        # Passer le temps au VLCWidget
        self.vlc_widget.set_position_timecode(int(time))


    def seg_action(self):
        self.seg_button.setText("Calcul Segmentation en cours ⌛")
        self.seg_button.setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 5px;") 
        self.start_segmentation()


    #segmentation appelé automatiquement à la création plus maintenant
    def start_segmentation(self):
        video_path = self.vlc_widget.path_of_media
        self.segmentation_thread = SegmentationThread(video_path)
        
        # Connecte le signal pour recevoir les timecodes
        self.segmentation_thread.segmentation_done.connect(self.on_segmentation_complete)
        
        self.segmentation_thread.start()  # Démarrer le thread

    def on_segmentation_complete(self, timecodes):
        self.seg_ok=True
        self.layout.removeWidget(self.seg_button)
        self.seg_button.deleteLater()
        for time in timecodes:
            self.add_new_button(time=time[0],end=time[1],frame1=time[2],frame2=time[3])  # Crée un bouton pour chaque changement de plan
        print("Segmentation terminée en arrière-plan.")
        self.segmentation_done.emit(True)


    def stop_segmentation(self):
        """Arrête la segmentation si elle est en cours."""
        if hasattr(self, 'segmentation_thread') and self.segmentation_thread.isRunning():
            print("Arrêt de la segmentation en cours...")
            self.segmentation_thread.stop()


