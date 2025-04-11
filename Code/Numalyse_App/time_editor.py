from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel, QGridLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator

from no_focus_push_button import NoFocusPushButton

class TimeEditor(QWidget):
    timechanged = Signal()
    def __init__(self, parent=None, max_time=3600000, time=-1,fps=25):
        super().__init__(parent)
        self.fps=fps
        self.tf=1000/self.fps
        self.max_time = max_time
        self.time = 0  # Temps en millisecondes
        self.frame = 0  # Compteur de frames

        # Layout principal horizontal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)

        # Création des zones de texte pour les heures, minutes et secondes
        self.hours_edit = QLineEdit(self)
        self.minutes_edit = QLineEdit(self)
        self.seconds_edit = QLineEdit(self)

        # Limiter les saisies numériques avec des validators
        self.hours_edit.setValidator(QIntValidator(0, 99, self))
        self.minutes_edit.setValidator(QIntValidator(0, 59, self))
        self.seconds_edit.setValidator(QIntValidator(0, 59, self))

        # Alignement centré et taille fixe pour un affichage uniforme
        self.hours_edit.setAlignment(Qt.AlignCenter)
        self.minutes_edit.setAlignment(Qt.AlignCenter)
        self.seconds_edit.setAlignment(Qt.AlignCenter)
        self.hours_edit.setFixedWidth(40)
        self.minutes_edit.setFixedWidth(40)
        self.seconds_edit.setFixedWidth(40)

        # Labels de séparation pour l'affichage "HH:MM:SS:FF"
        self.colon1 = QLabel(":", self)
        self.colon1.setAlignment(Qt.AlignCenter)
        self.colon2 = QLabel(":", self)
        self.colon2.setAlignment(Qt.AlignCenter)
        self.colon3 = QLabel(":", self)
        self.colon3.setAlignment(Qt.AlignCenter)

        # Layout pour la gestion des frames
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(3)

        self.plus_frames_button = NoFocusPushButton("+", self)
        self.plus_frames_button.setFixedSize(30, 30)

        self.frames_label = QLabel("00", self)
        self.frames_label.setAlignment(Qt.AlignCenter)
        self.frames_label.setStyleSheet("font-size: 16px;")

        self.minus_frames_button = NoFocusPushButton("-", self)
        self.minus_frames_button.setFixedSize(30, 30)

        self.grid_layout.addWidget(self.plus_frames_button)
        self.grid_layout.addWidget(self.frames_label)
        self.grid_layout.addWidget(self.minus_frames_button)

        # Ajout des widgets au layout principal
        self.main_layout.addWidget(self.hours_edit)
        self.main_layout.addWidget(self.colon1)
        self.main_layout.addWidget(self.minutes_edit)
        self.main_layout.addWidget(self.colon2)
        self.main_layout.addWidget(self.seconds_edit)
        self.main_layout.addWidget(self.colon3)
        self.main_layout.addLayout(self.grid_layout)

        # Connexion des signaux pour mettre à jour le temps lors de l'édition
        self.hours_edit.textChanged.connect(self.on_time_edited)
        self.minutes_edit.textChanged.connect(self.on_time_edited)
        self.seconds_edit.textChanged.connect(self.on_time_edited)

        # Connexion des boutons pour gérer les frames
        self.plus_frames_button.clicked.connect(self.on_plus_frame)
        self.minus_frames_button.clicked.connect(self.on_minus_frame)

        # Initialisation de l'affichage du temps
        if time > -1:
            self.set_time(time)
        else:
            self.set_time(self.time)

    def set_fps(self,new_fps):
        self.fps=new_fps
        self.tf=1000/self.fps

    def get_time_in_milliseconds(self):
        return self.time

    def set_time(self, milliseconds):
        self.hours_edit.blockSignals(True)
        self.minutes_edit.blockSignals(True)
        self.seconds_edit.blockSignals(True)
        """
        Met à jour le temps interne et l'affichage des zones de texte.
        """
        # S'assurer que le temps reste dans les limites autorisées
        self.time = max(0, min(milliseconds, self.max_time))
        total_seconds = self.time // 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frames = int((self.time % 1000) // self.tf)

        # Mise à jour des zones de texte avec un format à deux chiffres
        self.hours_edit.setText(f"{hours:02}")
        self.minutes_edit.setText(f"{minutes:02}")
        self.seconds_edit.setText(f"{seconds:02}")
        self.frames_label.setText(f"{frames:02}")

        self.frame = frames

        self.hours_edit.blockSignals(False)
        self.minutes_edit.blockSignals(False)
        self.seconds_edit.blockSignals(False)

    def on_time_edited(self):
        try:
            hours = int(self.hours_edit.text())
        except ValueError:
            hours = 0
        try:
            minutes = int(self.minutes_edit.text())
        except ValueError:
            minutes = 0
        try:
            seconds = int(self.seconds_edit.text())
        except ValueError:
            seconds = 0


        new_time = (hours * 3600 + minutes * 60 + seconds) * 1000 + self.frame * self.tf
        new_time = min(new_time, self.max_time)
        self.set_time(new_time)

        self.timechanged.emit()

    def on_plus_frame(self):
        """
        Incrémente le nombre de frames de 1. Si l'incrémentation dépasse 24 frames, la seconde est augmentée.
        """
        new_time = self.time + self.tf 
        if new_time > self.max_time:
            new_time = self.max_time
        self.set_time(new_time)

        self.timechanged.emit()

    def on_minus_frame(self):
        """
        Décrémente le nombre de frames de 1. Si aucune frame n'est présente, la seconde est diminuée.
        """
        new_time = self.time - self.tf 
        if new_time < 0:
            new_time = 0
        self.set_time(new_time)

        self.timechanged.emit()
