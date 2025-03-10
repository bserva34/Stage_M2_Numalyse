from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog,
    QScrollArea, QDockWidget, QLabel, QDialog, QLineEdit, QSlider, QHBoxLayout,
    QSpinBox, QTextEdit, QFrame, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsRectItem,QGraphicsItem)
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtCore import Qt, QTimer, Signal, QEvent, QRectF

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


class ClickableRectItem(QGraphicsRectItem):
    def __init__(self, rect, click_callback=None, context_callback=None, parent=None):
        super().__init__(rect, parent)
        self.click_callback = click_callback
        self.context_callback = context_callback
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Appel du callback pour le clic gauche
            if self.click_callback:
                self.click_callback()
        elif event.button() == Qt.RightButton:
            # Appel du callback pour le clic droit, si défini
            if self.context_callback:
                self.context_callback(event)
            else:
                super().contextMenuEvent(event)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        # Intercepte le clic droit et appelle la fonction callback passée
        if self.context_callback:
            self.context_callback(event)
        else:
            super().contextMenuEvent(event)


class SideMenuWidget(QDockWidget):
    change = Signal(bool)
    segmentation_done = Signal(bool)

    def __init__(self, vlc_widget, parent=None,start=True):
        super().__init__("", parent)  # Titre du dock
        self.vlc_widget = vlc_widget

        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        #self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable) 

        self.setAllowedAreas(Qt.BottomDockWidgetArea)  # Zones autorisées
        self.parent=parent

        self.display=SideMenuWidgetDisplay(self.vlc_widget,self)
        self.parent.addDockWidget(Qt.RightDockWidgetArea, self.display)
        #self.display.setVisible(False)

        self.length=self.vlc_widget.get_size_of_slider()

        # Définir la largeur du dock
        self.setFixedHeight(250)

        # Création d'un widget conteneur et d'un layout vertical
        self.container = QWidget(self)
        self.setWidget(self.container)
        self.main_layout = QVBoxLayout(self.container)
        self.container.setLayout(self.main_layout)

        # --- Zone supérieure : boutons ---
        self.timeline_view = QGraphicsView(self)
        self.timeline_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timeline_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.timeline_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.timeline_scene = QGraphicsScene(self.timeline_view)
        self.timeline_view.setScene(self.timeline_scene)
        # Définir la scène (2000 pixels de large sur 200 pixels de haut)
        self.timeline_scene.setSceneRect(0, 0, self.length, 150)
        self.timeline_view.setFixedHeight(150)
        self.main_layout.addWidget(self.timeline_view)

        # Installer un event filter sur le viewport pour capturer la molette
        self.timeline_view.viewport().installEventFilter(self)

        # --- Zone inférieure : Timeline zoomable ---
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(0)
        self.seg_ok = False

        if start:
            self.seg_button = QPushButton("Segmentation Auto", self)
            self.seg_button.setStyleSheet("background-color: green; color: white; padding: 5px; border-radius: 5px;")
            self.seg_button.clicked.connect(self.seg_action)
            self.seg_button.setFixedHeight(40)
            self.buttons_layout.addWidget(self.seg_button)
        else:
            self.seg_ok = True

        self.add_button = QPushButton("Ajouter", self)
        self.add_button.setStyleSheet("background-color: blue; color: white; padding: 5px; border-radius: 5px;")
        self.add_button.clicked.connect(self.add_action)
        self.add_button.setFixedHeight(40)
        self.buttons_layout.addWidget(self.add_button)

        self.buttons_layout.addStretch()
        self.main_layout.addLayout(self.buttons_layout)

        self.fps = None
        self.max_time = self.vlc_widget.player.get_length()
        self.time_manager = TimeManager()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_buttons_color)
        self.timer.start(50)  # actualisation toutes les 50 ms

        self.id_creation=0

    def eventFilter(self, source, event):
        """Gère le zoom horizontal de la timeline avec la molette, sans dézoomer en dessous de l'échelle de base."""
        if source is self.timeline_view.viewport() and event.type() == QEvent.Wheel:
            # Récupère l'échelle horizontale actuelle (facteur X)
            current_scale = self.timeline_view.transform().m11()

            # Détermine le facteur de zoom en fonction de la direction de la molette
            if event.angleDelta().y() > 0:
                factor = 1.15
            else:
                # Si le zoom sortant risquerait de passer en dessous de 1, on le limite
                if current_scale <= 1:
                    return True  # on ne change rien si on est déjà au niveau de base
                factor = 1 / 1.15
                # Vérifie que le nouveau facteur ne descend pas en dessous de 1
                if current_scale * factor < 1:
                    factor = 1 / current_scale

            # Applique le zoom uniquement sur l'axe horizontal
            self.timeline_view.scale(factor, 1)
            return True
        return super().eventFilter(source, event)

        
    def emit_change(self):
        self.change.emit(True)

    #affichage du bouton en rouge
    def update_buttons_color(self):
        if not self.vlc_widget.media:
            return

        current_time = self.vlc_widget.player.get_time()
        self.max_time = self.vlc_widget.player.get_length()

        for seg in self.display.stock_button:
            if seg["time"] <= current_time < seg["end"]:
                seg["rect"].setBrush(QBrush(QColor("red")))
            else:
                seg["rect"].setBrush(QBrush(seg["color"]))


    #fonction d'ajout d'une nouveaux bouton
    def add_new_button(self, name="", time=0, end=0, verif=True, frame1=-1, frame2=-1):
        if verif and time >= self.max_time:
            return

        if name == "":
            cpt = len(self.display.stock_button)
            name = "Plan " + f"{cpt+1}"

        size=self.get_ratio(end-time)

        if size < 50:
            couleur = QColor("blue")
        elif size < 150:
            couleur = QColor("green")
        else:
            couleur = QColor("yellow")


        rect = ClickableRectItem(
            QRectF(self.get_ratio(time), 0, size, 150),
            click_callback=lambda iden=self.id_creation: self.set_position(iden),
            context_callback=lambda event,iden=self.id_creation, t=time, e=end: self.show_context_menu(event,iden, t, e)
        )
        rect.setBrush(QBrush(couleur))
        self.timeline_scene.addItem(rect)

        btn=self.display.add_new_button(btn=self.id_creation,rect=rect,color=couleur,name=name,time=time,end=end,verif=False,frame1=frame1,frame2=frame2) 

        #self.reorganize_buttons()

        if verif:
            self.change.emit(True)

        self.id_creation+=1

        return btn

    def get_ratio(self,time):
        return (time/self.max_time)*self.length

    #menu clique droit du bouton/séquence
    def show_context_menu(self,event, button,time,end):
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

        menu.exec(event.screenPos())


    #fonction 2
    def delate_button(self, button):
        """Supprime un bouton et son cadre associé."""
        time = 0
        end = 0
        frame1 = -1
        frame2 = -1
        for btn_data in self.display.stock_button:
            if btn_data["id"] == button:
                time = btn_data["time"]
                end = btn_data["end"]
                frame1 = btn_data["frame1"]
                frame2 = btn_data["frame2"]

                item = btn_data["rect"]

                self.timeline_scene.removeItem(item)

                # Supprimer les notes associées
                if button in self.display.button_notes:
                    del self.button_notes[button]

                # Supprimer le bouton de la liste
                self.display.stock_button.remove(btn_data)
                break

        self.change.emit(True)
        return time, end, frame1, frame2

    def delate_button_prec(self, button):
        time, end, frame1, frame2 = self.delate_button(button)
        for btn_data in self.display.stock_button:
            if btn_data["end"] == time:
                btn_data["end"] = end
                rect_item = btn_data["rect"]  # C'est le QGraphicsRectItem
                rect_item.prepareGeometryChange()  # Prépare la mise à jour
                newRect = rect_item.rect()         # Récupère le QRectF actuel
                newRect.setWidth(self.get_ratio(end - btn_data["time"]))  # Modifie la largeur
                rect_item.setRect(newRect)         # Applique le nouveau QRectF
                rect_item.update()                 # Demande un rafraîchissement
                btn_data["frame2"] = frame2
                self.display.change_label_time(btn_data["label"], btn_data["time"], btn_data["end"])



    def delate_button_suiv(self, button):
        time, end, frame1, frame2 = self.delate_button(button)
        for btn_data in self.display.stock_button:
            if btn_data["time"] == end:
                btn_data["time"] = time
                rect_item = btn_data["rect"]
                rect_item.prepareGeometryChange()
                newRect = rect_item.rect()
                newRect.setX(self.get_ratio(time))
                newRect.setWidth(self.get_ratio(btn_data["end"] - time))
                rect_item.setRect(newRect)
                rect_item.update()
                btn_data["frame1"] = frame1
                self.display.change_label_time(btn_data["label"], btn_data["time"], btn_data["end"])



    #fonction 4 extraction
    def extract_action(self, button): 
        for btn_data in self.display.stock_button:
            if btn_data["id"] == button:
                time = btn_data["time"]
                end = btn_data["end"]
                duration = end - time
                name=btn_data["button"].text()
                break;

        capture_dir = os.path.join(str(Path.home()), "Vidéos", "Capture_SLV")
        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir,exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y")
        capture_path = os.path.join(capture_dir, f"{name}_{self.time_manager.m_to_hms(time)}_{self.time_manager.m_to_hms(end)}_{timestamp}.mp4")

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

        self.time2 = TimeEditor(dialog, self.vlc_widget.player.get_length() , self.vlc_widget.player.get_time() + 5000)
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
            name = name_input.text().strip()
            new_time = self.time.get_time_in_milliseconds()
            end_time = self.time2.get_time_in_milliseconds()
            frame1 = self.get_frame(new_time)
            frame2 = self.get_frame(end_time)
            if name and 0<new_time<=self.max_time:
                self.add_new_button(name=name, time=new_time, end=end_time,frame1=frame1,frame2=frame2)
                self.display.adjust_neighbors(new_time,end_time)
                dialog.accept()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

    def get_frame(self,time):
        if(self.fps==None):
            video=VideoFileClip(self.vlc_widget.path_of_media)
            self.fps = video.fps
        return int((time/1000)*self.fps)

    #fonction appeler quand on clique sur un bouton
    def set_position(self, button):
        time=-1
        for i,btn_data in enumerate(self.display.stock_button):
            if btn_data["id"] == button:
                time = btn_data["time"]
                self.display.select_plan(i)
                break
        self.vlc_widget.set_position_timecode(int(time))

    def seg_action(self):
        self.seg_button.setText("Calcul Segmentation en cours ⌛")
        self.seg_button.setStyleSheet("background-color: red; color: white; padding: 5px; border-radius: 5px;") 
        self.seg_button.setEnabled(False)
        self.start_segmentation()


    #segmentation appelé automatiquement à la création plus maintenant
    def start_segmentation(self):
        video_path = self.vlc_widget.path_of_media
        self.segmentation_thread = SegmentationThread(video_path)
        
        # Connecte le signal pour recevoir les timecodes
        self.segmentation_thread.segmentation_done.connect(self.on_segmentation_complete)
        
        self.segmentation_thread.start()  # Démarrer le thread

        #self.test()

    def on_segmentation_complete(self, timecodes):
        self.seg_ok=True
        self.buttons_layout.removeWidget(self.seg_button)
        self.seg_button.deleteLater()
        for time in timecodes:
            self.add_new_button(time=time[0],end=time[1],frame1=time[2],frame2=time[3]) 
        print("Segmentation terminée en arrière-plan.")
        self.segmentation_done.emit(True)

    def test(self):
        self.seg_ok=True
        self.layout.removeWidget(self.seg_button)
        self.seg_button.deleteLater()
        self.max_time=10000
        for i in range(10):
            self.add_new_button(time=i*1000,end=(i+1)*1000)
        self.segmentation_done.emit(True)

    def stop_segmentation(self):
        """Arrête la segmentation si elle est en cours."""
        if hasattr(self, 'segmentation_thread') and self.segmentation_thread.isRunning():
            print("Arrêt de la segmentation en cours...")
            self.segmentation_thread.stop()


    def remove_display(self):
        self.parent.removeDockWidget(self.display)
        self.display.deleteLater()
        self.display=None