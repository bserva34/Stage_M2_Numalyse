from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt

from no_focus_push_button import NoFocusPushButton

class TimeSelector(QWidget):
    def __init__(self, parent=None, max_time=3600, time=-1):
        super().__init__(parent)
        self.max_time = max_time
        self.time= 0  

        # Layout principal vertical
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        # Layout horizontal pour centrer le contenu
        self.center_layout = QHBoxLayout()
        self.center_layout.setAlignment(Qt.AlignCenter)

        # GridLayout pour aligner les boutons et les labels
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)

        # Boutons +
        self.plus_minutes_button = NoFocusPushButton("+", self)
        self.plus_seconds_button = NoFocusPushButton("+", self)
        self.plus_minutes_button.setFixedSize(30, 30)
        self.plus_seconds_button.setFixedSize(30, 30)

        # Labels pour afficher le temps
        self.minutes_label = QLabel("00", self)
        self.minutes_label.setAlignment(Qt.AlignCenter)
        self.minutes_label.setStyleSheet("font-size: 16px;")

        self.separator_label = QLabel(":", self)
        self.separator_label.setAlignment(Qt.AlignCenter)
        self.separator_label.setStyleSheet("font-size: 16px;")

        self.seconds_label = QLabel("00", self)
        self.seconds_label.setAlignment(Qt.AlignCenter)
        self.seconds_label.setStyleSheet("font-size: 16px;")

        # Boutons -
        self.minus_minutes_button = NoFocusPushButton("-", self)
        self.minus_seconds_button = NoFocusPushButton("-", self)
        self.minus_minutes_button.setFixedSize(30, 30)
        self.minus_seconds_button.setFixedSize(30, 30)

        # Ajout des éléments au GridLayout
        self.grid_layout.addWidget(self.plus_minutes_button, 0, 0)
        self.grid_layout.addWidget(self.plus_seconds_button, 0, 2)

        self.grid_layout.addWidget(self.minutes_label, 1, 0)
        self.grid_layout.addWidget(self.separator_label, 1, 1)
        self.grid_layout.addWidget(self.seconds_label, 1, 2)

        self.grid_layout.addWidget(self.minus_minutes_button, 2, 0)
        self.grid_layout.addWidget(self.minus_seconds_button, 2, 2)

        # Ajout d'un SpacerItem pour centrer le contenu
        self.center_layout.addStretch()
        self.center_layout.addLayout(self.grid_layout)
        self.center_layout.addStretch()

        # Ajout du layout centré au layout principal
        self.main_layout.addLayout(self.center_layout)

        # Connexion des boutons aux fonctions
        self.plus_minutes_button.clicked.connect(self.increment_minutes)
        self.plus_seconds_button.clicked.connect(self.increment_seconds)
        self.minus_minutes_button.clicked.connect(self.decrement_minutes)
        self.minus_seconds_button.clicked.connect(self.decrement_seconds)

        if time>-1 :
            self.set_time(time)

        # Mise à jour de l'état des boutons
        self.update_buttons()

    def get_time_in_milliseconds(self):
        return self.time


    def set_time(self, milliseconds):
        """Met à jour l'affichage du temps en MM:SS."""
        self.time = max(0, min(milliseconds, self.max_time))  # Assure que le temps reste dans les limites
        minutes = int(self.time // 60000)
        seconds = int((self.time % 60000) // 1000)  # Diviser par 1000 pour obtenir les secondes
        self.minutes_label.setText(f"{minutes:02}")
        self.seconds_label.setText(f"{seconds:02}")
        self.update_buttons()


    def increment_minutes(self):
        """Incrémente les minutes de 1."""
        self.set_time(self.time + 60000)

    def decrement_minutes(self):
        """Décrémente les minutes de 1."""
        self.set_time(self.time - 60000)

    def increment_seconds(self):
        """Incrémente les secondes de 1."""
        self.set_time(self.time + 1000)

    def decrement_seconds(self):
        """Décrémente les secondes de 1."""
        self.set_time(self.time - 1000)

    def update_buttons(self):
        """Désactive les boutons en fonction des limites."""
        current_time = self.time

        # Désactiver le bouton - si on est déjà à 00:00
        self.minus_minutes_button.setEnabled(current_time > 0)
        self.minus_seconds_button.setEnabled(current_time > 0)

        # Désactiver le bouton + si on atteint le max
        self.plus_minutes_button.setEnabled(current_time < self.max_time)
        self.plus_seconds_button.setEnabled(current_time < self.max_time)
