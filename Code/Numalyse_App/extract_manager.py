from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QDialog, QHBoxLayout, QMessageBox, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
import os
import cv2

from time_selector import TimeSelector
from time_editor import TimeEditor
from message_popup import MessagePopUp
from no_focus_push_button import NoFocusPushButton
from frame_previewer import FramePreviewer

class ExtractManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vlc = parent
        self.file_path = None
        self.configure()

    def configure(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Extraire une séquence")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Zone de texte pour le nom
        name_label = QLabel("Nom de l'extrait :", dialog)
        layout.addWidget(name_label)
        
        self.folder_button = NoFocusPushButton("Sélectionner l'emplacement du fichier", dialog)
        self.folder_button.setStyleSheet("background-color: red;")
        self.folder_button.clicked.connect(self.save_export)
        layout.addWidget(self.folder_button)

        # Choix du temps de début
        time_label = QLabel("Début :", dialog)
        layout.addWidget(time_label)

        self.start_time = TimeEditor(dialog, (self.vlc.player.get_length()-1000), self.vlc.player.get_time(), fps=self.vlc.fps)
        self.start_time.timechanged.connect(lambda: self.previewer1.preview_frame(self.start_time.get_time_in_milliseconds()))
        layout.addWidget(self.start_time)

        # Label pour afficher l'image d'aperçu
        self.img1 = QLabel("", dialog)
        self.img1.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img1)
        self.previewer1 = FramePreviewer(self.img1, self.vlc.fps, self.vlc.path_of_media)
        self.previewer1.preview_frame(self.start_time.get_time_in_milliseconds())

        # Choix du temps de fin
        time_label2 = QLabel("Fin :", dialog)
        layout.addWidget(time_label2)

        self.end_time = TimeEditor(dialog, self.vlc.player.get_length(), self.vlc.player.get_time() + 10000, fps=self.vlc.fps)
        self.end_time.timechanged.connect(lambda: self.previewer2.preview_frame(self.end_time.get_time_in_milliseconds()))
        layout.addWidget(self.end_time)

        self.img2 = QLabel("", dialog)
        self.img2.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.img2)
        self.previewer2 = FramePreviewer(self.img2, self.vlc.fps, self.vlc.path_of_media)
        self.previewer2.preview_frame(self.end_time.get_time_in_milliseconds())

        dialog_load = QHBoxLayout()
        load = QLabel("")
        load.setStyleSheet("color: blue;")
        load.setAlignment(Qt.AlignCenter)
        dialog_load.addWidget(load)
        layout.addLayout(dialog_load)


        # Boutons OK et Annuler
        button_layout = QHBoxLayout()
        ok_button = NoFocusPushButton("Extraire", dialog)
        cancel_button = NoFocusPushButton("Annuler", dialog)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        def on_ok():
            try:
                deb = self.start_time.get_time_in_milliseconds()
                fin = self.end_time.get_time_in_milliseconds()
                temps = fin - deb

                if self.file_path and temps > 0:
                    if not self.file_path.lower().endswith(".mp4"):
                        self.file_path += ".mp4"
                    load.setText("exportation en cours ⌛")
                    QApplication.processEvents() 
                    self.vlc.extract_segment_with_ffmpeg(self.vlc.path_of_media, deb / 1000, temps / 1000, self.file_path)
                    affichage = MessagePopUp(self)
                    dialog.accept()
            except ValueError:
                print("Erreur : Format de temps invalide. Utiliser MM:SS.")

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec()

    def save_export(self):
        if os.name == "nt":  # Windows
            default_dir = "C:/"
        else:  # Linux/Mac
            default_dir = "/"
        file_path, _ = QFileDialog.getSaveFileName(self, "Nommer le fichier texte", default_dir)
        self.file_path = file_path
        if file_path:
            self.folder_button.setStyleSheet("background-color: green;")


