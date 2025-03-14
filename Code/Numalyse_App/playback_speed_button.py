from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMenu, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

class PlaybackSpeedButton(QPushButton):
    speedChanged = Signal(float)
    
    def __init__(self, speeds=[1,0.25,0.5,0.75,1.25,1.5,1.75,2,4], labels=None, parent=None):
        self.parent = parent
        if labels is None:
            labels = [f"x{speed}" for speed in speeds]
        super().__init__(labels[0], parent)
        self.speeds = speeds
        self.labels = labels
        self.current_speed = speeds[0]

        self.setFixedWidth(70)
        # Empêche ce bouton de prendre le focus
        self.setFocusPolicy(Qt.NoFocus)

        # Création du menu déroulant
        self.menu = QMenu(self)
        self.menu.setFixedWidth(70)
        self.menu.setStyleSheet(
            "QMenu::item {text-align: left;padding: 2px 10px;}"
        )

        for speed, label in zip(speeds, labels):
            action = QAction(label, self)
            action.setData(speed)
            action.triggered.connect(lambda *args, s=speed, l=label: self.setSpeed(s, l))
            self.menu.addAction(action)

        self.setMenu(self.menu)

    def setSpeed(self, speed, label):
        self.current_speed = speed
        self.setText(label)
        self.parent.toggle_speed()

    def getSpeed(self):
        return self.current_speed