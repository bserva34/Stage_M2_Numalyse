from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog, QScrollArea, QDockWidget, QLabel, QDialog, QLineEdit, QSlider, QHBoxLayout, QSpinBox, QTextEdit, QFrame, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer, Signal, QEvent

import cv2 
import os
from datetime import datetime
from moviepy import VideoFileClip
from pathlib import Path

from segmentation import SegmentationThread
from time_selector import TimeSelector
from time_editor import TimeEditor
from time_manager import TimeManager
from message_popup import MessagePopUp
from no_focus_push_button import NoFocusPushButton

class MyTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.FocusOut and source is self:
            new_focus = QApplication.focusWidget()
            # Ne pas redonner le focus si le nouveau widget est une note
            if not isinstance(new_focus, MyTextEdit):
                QTimer.singleShot(0, self.setFocus)
        return super().eventFilter(source, event)


class SideMenuWidgetDisplay(QDockWidget):
    change = Signal(bool)
    segmentation_done = Signal(bool)

    def __init__(self, vlc_widget, parent=None):
        super().__init__("Segmentation", parent)  # Titre du dock
        self.vlc_widget = vlc_widget

        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        #self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable) 

        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)  # Zones autorisées

        self.parent=parent
        # Définir la largeur du dock
        self.setFixedWidth(340)

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

        self.id_affichage = -1

        self.fps=None

        self.max_time=self.vlc_widget.player.get_length()

        self.time_manager=TimeManager()


    def select_plan(self,i):
        self.id_affichage=i
        self.reorganize_buttons()


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

        # Réinsère les frames triés
        for i,btn_data in enumerate(self.stock_button):
            if self.id_affichage==i:
                self.layout.addWidget(btn_data["frame"])
                btn_data["frame"].setVisible(True)
            else:
                btn_data["frame"].setVisible(False)

        # Réajoute un stretch à la fin
        self.layout.addStretch()




    #fonction d'ajout d'une nouveaux bouton
    def add_new_button(self, btn,rect,color,name="", time=0, end=0, verif=True, frame1=-1, frame2=-1):
        if verif and time >= self.max_time:
            return

        if name == "":
            cpt = len(self.stock_button)
            name = "Plan " + f"{cpt+1}"

        # Création du cadre pour regrouper le bouton et ses éléments associés
        frame = QFrame(self)
        frame.setStyleSheet("border: 1px solid gray; padding: 5px; border-radius: 5px;")
        frame_layout = QVBoxLayout(frame)

        # Création du bouton
        button = NoFocusPushButton(name, self)
        button.setStyleSheet("background-color: #666; color: white; padding: 5px; border-radius: 5px;")
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))
        button.setFocusPolicy(Qt.NoFocus)
        #button.setFixedSize(180, 25)

        frame.setVisible(False)

        # Création du label pour afficher le timecode
        if end == 0:
            time_label = QLabel("Début : " + self.time_manager.m_to_hmsf(time), self)
        else:
            time_label = QLabel(f"Début : {self.time_manager.m_to_hmsf(time)} / Fin : {self.time_manager.m_to_hmsf(end)}", self)

        time_label.setFixedHeight(30)

        frame_layout.addWidget(button)
        frame_layout.addWidget(time_label)


        # Ajouter le frame à la liste des boutons stockés
        self.stock_button.append({"id":btn,"rect":rect,"color":color,"frame": frame, "button": button, "time": time, "end": end, "label": time_label, "frame1": frame1, "frame2":frame2})

        # Trier les boutons
        self.stock_button.sort(key=lambda btn_data: btn_data["time"])

        # Réorganiser les boutons dans l'affichage
        self.reorganize_buttons()

        self.button_notes[button] = []  # Associer une liste vide de notes au bouton

        if verif:
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
                    btn_data["btn"].setText(new_name)
        self.parent.emit_change()



    #fonction 3
    def add_note_menu(self, button):
        self.add_note(button, "")  # Ajoute une note vide directement
        self.parent.emit_change()

    def add_note(self, button, text=""):
        note_widget = MyTextEdit(self)
        note_widget.setPlainText(text)
        note_widget.setReadOnly(False)
        note_widget.setStyleSheet("color: gray; font-style: italic;")
        note_widget.setFixedSize(285, 200)
        note_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        note_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        note_widget.customContextMenuRequested.connect(lambda pos: self.show_note_context_menu(note_widget, pos))

        if button not in self.button_notes:
            self.button_notes[button] = []

        self.button_notes[button].append(note_widget)

        note_widget.setFocus()

        # Trouver le `frame` associé au bouton et ajouter la note dedans
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                frame_layout = btn_data["frame"].layout()
                frame_layout.addWidget(note_widget)
                break  # On sort de la boucle une fois trouvé

        # Détecte si du texte est ajouté
        note_widget.textChanged.connect(lambda: self.on_text_changed(note_widget))



    def on_text_changed(self, note_widget):
        text = note_widget.toPlainText().strip()
        if text:
            note_widget.setStyleSheet("")  # Normal
        else:
            note_widget.setStyleSheet("color: gray; font-style: italic;")
        self.parent.emit_change()

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
        self.parent.emit_change()

    #fonction 4 extraction
    def extract_action(self, button): 
        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                time = btn_data["time"]
                end = btn_data["end"]
                duration = end - time


        capture_dir = os.path.join(str(Path.home()), "Capture_SLV","Vidéos")

        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir,exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y")
        capture_path = os.path.join(capture_dir, f"{button.text()}_{self.time_manager.m_to_hms(time)}_{self.time_manager.m_to_hms(end)}_{timestamp}.mp4")

        self.vlc_widget.extract_segment_with_ffmpeg(self.vlc_widget.path_of_media,time//1000,duration//1000,capture_path)
        affichage=MessagePopUp(self)


    #modif temps non utilisé
    def modify_time(self, button):

        for btn_data in self.stock_button:
            if btn_data["button"] == button:
                start = btn_data["time"]
                end = btn_data["end"]

        dialog = QDialog(self)
        dialog.setWindowTitle("Modification TimeCode")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        # Slider pour choisir le temps
        time_label = QLabel("Début :", dialog)
        layout.addWidget(time_label)

        self.time = TimeEditor(dialog, self.vlc_widget.player.get_length(), start)
        layout.addWidget(self.time)        

        time_label2 = QLabel("Fin :", dialog)
        layout.addWidget(time_label2)

        self.time2 = TimeEditor(dialog, self.vlc_widget.player.get_length(), end )
        layout.addWidget(self.time2)        

        # Boutons OK et Annuler
        button_layout = QHBoxLayout()
        ok_button = NoFocusPushButton("OK", dialog)
        cancel_button = NoFocusPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Action du bouton OK
        def on_ok():
            new_time = self.time.get_time_in_milliseconds()
            end_time = self.time2.get_time_in_milliseconds()
            for btn_data in self.stock_button:
                if btn_data["button"] == button:
                    btn_data["time"] = new_time
                    btn_data["end"] = end_time
                    self.change_label_time(btn_data["label"],new_time,end_time)
                    self.parent.change_rect(btn_data["rect"],new_time,end_time)
            self.adjust_neighbors(new_time,end_time)
            self.reorganize_buttons()
            self.parent.emit_change()
            dialog.accept()


        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()


    def change_label_time(self,label,new_time,end_time):
        new_label ="Début : "+self.time_manager.m_to_hmsf(new_time)+" / Fin : "+self.time_manager.m_to_hmsf(end_time)
        label.setText(new_label)

    def adjust_neighbors(self, new_time, new_end_time):
        frame1=self.parent.get_frame(new_time)
        frame2=self.parent.get_frame(new_end_time)
        tab_suppr = []
        for btn_data in self.stock_button:
            if btn_data["time"] == new_end_time or (btn_data["time"] <= new_end_time and btn_data["time"] > new_time):
                if new_end_time < btn_data["end"]:
                    btn_data["time"] = new_end_time
                    btn_data["frame1"]=frame2

                    self.parent.change_rect(btn_data["rect"],new_end_time,btn_data["end"])

                    self.change_label_time(btn_data["label"], new_end_time, btn_data["end"])
                else:
                    tab_suppr.append(btn_data["id"])
            if btn_data["end"] == new_time or (btn_data["end"] >= new_time and btn_data["end"] < new_end_time):
                if new_time > btn_data["time"]:
                    btn_data["end"] = new_time
                    btn_data["frame2"]=frame1

                    self.parent.change_rect(btn_data["rect"],btn_data["time"],new_time)

                    self.change_label_time(btn_data["label"], btn_data["time"], new_time)
                else:
                    tab_suppr.append(btn_data["id"])
        for btn in tab_suppr:
            self.parent.delate_button(btn)

