from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator

class TimeEditor(QWidget):
    def __init__(self, parent=None, max_time=3600000, time=-1):
        super().__init__(parent)
        self.max_time = max_time
        self.time = 0  # Temps en millisecondes

        # Layout principal horizontal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

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

        # Labels de séparation pour l'affichage "HH:MM:SS"
        self.colon1 = QLabel(":", self)
        self.colon1.setAlignment(Qt.AlignCenter)
        self.colon2 = QLabel(":", self)
        self.colon2.setAlignment(Qt.AlignCenter)

        # Ajout des widgets au layout
        self.main_layout.addWidget(self.hours_edit)
        self.main_layout.addWidget(self.colon1)
        self.main_layout.addWidget(self.minutes_edit)
        self.main_layout.addWidget(self.colon2)
        self.main_layout.addWidget(self.seconds_edit)

        # Connexion des signaux pour mettre à jour le temps lors de l'édition
        self.hours_edit.editingFinished.connect(self.on_time_edited)
        self.minutes_edit.editingFinished.connect(self.on_time_edited)
        self.seconds_edit.editingFinished.connect(self.on_time_edited)

        # Initialisation de l'affichage du temps
        if time > -1:
            self.set_time(time)
        else:
            self.set_time(self.time)

    def get_time_in_milliseconds(self):
        return self.time

    def set_time(self, milliseconds):
        """
        Met à jour le temps interne et l'affichage des zones de texte.
        """
        # On s'assure que le temps reste dans les limites autorisées
        self.time = max(0, min(milliseconds, self.max_time))
        total_seconds = self.time / 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        # Mise à jour des zones de texte avec un format à deux chiffres
        self.hours_edit.setText(f"{hours:02}")
        self.minutes_edit.setText(f"{minutes:02}")
        self.seconds_edit.setText(f"{seconds:02}")

    def on_time_edited(self):
        """
        Récupère les valeurs saisies par l'utilisateur et met à jour le temps interne.
        """
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

        # Calcul du temps total en millisecondes
        new_time = (hours * 3600 + minutes * 60 + seconds) * 1000
        # On s'assure que le temps ne dépasse pas le maximum autorisé
        new_time = min(new_time, self.max_time)
        self.set_time(new_time)
