from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog, QScrollArea, QDockWidget, QLabel, QDialog, QLineEdit, QSlider, QPushButton, QHBoxLayout, QSpinBox, QTextEdit, QFrame
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer, Signal

import cv2 
import os
from datetime import datetime
from moviepy.editor import VideoFileClip
from pathlib import Path

from segmentation import SegmentationThread
from time_selector import TimeSelector
from time_editor import TimeEditor
from time_manager import TimeManager
from message_popup import MessagePopUp
from side_menu_widget_display import SideMenuWidgetDisplay

class SideMenuWidget(QDockWidget):
    change = Signal(bool)
    segmentation_done = Signal(bool)

    def __init__(self, vlc_widget, parent=None,start=True):
        super().__init__("", parent)  # Titre du dock
        self.vlc_widget = vlc_widget
        self.setAllowedAreas(Qt.BottomDockWidgetArea)  # Zones autorisées
        self.parent=parent

        # Définir la largeur du dock
        self.setFixedHeight(200)

        # Créer un widget de conteneur pour le contenu
        self.container = QWidget(self)

        # Créer une zone défilante pour les boutons
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.container)

        # Définir le widget pour le dock
        self.setWidget(self.scroll_area)

        # Layout vertical pour stocker les boutons
        self.layout = QHBoxLayout(self.container)
        self.container.setLayout(self.layout)

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

        self.display=SideMenuWidgetDisplay(self.vlc_widget,self)
        self.parent.addDockWidget(Qt.RightDockWidgetArea, self.display)
        
    def emit_change(self):
        self.change.emit(True)

    #affichage du bouton en rouge
    def update_buttons_color(self):
        if not self.vlc_widget.media:
            return

        current_time = self.vlc_widget.player.get_time()
        self.max_time = self.vlc_widget.player.get_length()

        # Appliquer la couleur en fonction du temps actuel
        for btn_data in self.display.stock_button:
            button_time = btn_data["time"]
            button_end = btn_data["end"]

            if button_time < current_time <= button_end:
                btn_data["btn"].setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 5px;")
            else:
                btn_data["btn"].setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")


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
        for btn_data in self.display.stock_button:
            self.layout.addWidget(btn_data["btn"])

        # Réajoute un stretch à la fin
        self.layout.addStretch()

    #fonction d'ajout d'une nouveaux bouton
    def add_new_button(self, name="", time=0, end=0, verif=True, frame1=-1, frame2=-1):
        if verif and time >= self.max_time:
            return

        if name == "":
            cpt = len(self.display.stock_button)
            name = "Plan " + f"{cpt+1}"

        # Création du bouton
        button = QPushButton(name, self)
        button.setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, btn=button,t=time,e=end: self.show_context_menu(pos, btn,t,e))
        button.clicked.connect(lambda *_: self.set_position(button))
        button.setFixedSize(80, 150)

        btn=self.display.add_new_button(btn=button,name=button.text(),time=time,end=end,frame1=frame1,frame2=frame2) 

        self.reorganize_buttons()

        if verif:
            self.change.emit(True)

        return btn

    #menu clique droit du bouton/séquence
    def show_context_menu(self, pos, button,time,end):
        """Affiche un menu contextuel avec options de renommer et modifier valeurs."""
        menu = QMenu(self)

        if(time>0):
            delete_action = QAction("Supprimer et concaténer avec le précedent", self)
            delete_action.triggered.connect(lambda: self.delate_button_prec(button))
            menu.addAction(delete_action)

        if (end<self.max_time):
            delete_action2 = QAction("Supprimer et concaténer avec le suivant", self)
            delete_action2.triggered.connect(lambda: self.delate_button_suiv(button))
            menu.addAction(delete_action2)

        extract_action = QAction("Extraire la séquence")
        extract_action.triggered.connect(lambda: self.extract_action(button))
        menu.addAction(extract_action)

        menu.exec_(button.mapToGlobal(pos))

    #fonction 2
    def delate_button(self, button):
        """Supprime un bouton et son cadre associé."""
        time=0
        end=0
        for btn_data in self.display.stock_button:
            if btn_data["btn"] == button:
                time = btn_data["time"]
                end = btn_data["end"]
                # Supprimer le frame entier
                self.layout.removeWidget(button)

                # Supprimer les notes associées
                if button in self.display.button_notes:
                    del self.button_notes[button]
                button.deleteLater()

                # Supprimer le bouton de la liste
                self.display.stock_button.remove(btn_data)
                break

        self.change.emit(True)
        return time,end

    def delate_button_prec(self,button):
        time,end=self.delate_button(button)
        for btn_data in self.display.stock_button:
            if btn_data["end"]==time:
                btn_data["end"]=end
        self.display.reorganize_buttons()


    def delate_button_suiv(self,button):
        time,end=self.delate_button(button)
        for btn_data in self.display.stock_button:
            if btn_data["time"]==end:
                btn_data["time"]=time
        self.display.reorganize_buttons()


    #fonction 4 extraction
    def extract_action(self, button): 
        for btn_data in self.display.stock_button:
            if btn_data["btn"] == button:
                time = btn_data["time"]
                end = btn_data["end"]
                duration = end - time

        capture_dir = os.path.join(str(Path.home()), "Vidéos", "Capture_SLV")
        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir,exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y")
        capture_path = os.path.join(capture_dir, f"{button.text()}_{self.time_manager.m_to_hms(time)}_{self.time_manager.m_to_hms(end)}_{timestamp}.mp4")

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

        self.time = TimeEditor(dialog, self.vlc_widget.player.get_length(), self.vlc_widget.player.get_time())
        layout.addWidget(self.time)        

        time_label2 = QLabel("Fin :", dialog)
        layout.addWidget(time_label2)

        self.time2 = TimeEditor(dialog, self.vlc_widget.player.get_length() , self.vlc_widget.player.get_time() + 5)
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

    #fonction appeler quand on clique sur un bouton
    def set_position(self, button):
        for i,btn_data in enumerate(self.display.stock_button):
            if btn_data["btn"] == button:
                time = btn_data["time"]
                self.display.select_plan(i)
                break
        
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
            self.add_new_button(time=time[0],end=time[1],frame1=time[2],frame2=time[3]) 
        print("Segmentation terminée en arrière-plan.")
        self.segmentation_done.emit(True)


    def stop_segmentation(self):
        """Arrête la segmentation si elle est en cours."""
        if hasattr(self, 'segmentation_thread') and self.segmentation_thread.isRunning():
            print("Arrêt de la segmentation en cours...")
            self.segmentation_thread.stop()


