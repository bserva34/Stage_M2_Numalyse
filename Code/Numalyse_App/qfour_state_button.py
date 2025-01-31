from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QFileDialog, QSlider, QLabel, QLineEdit
from PySide6.QtCore import Qt, QTimer

class QFourStateButton(QPushButton):
    STATES = ["x1", "x2", "x0.25", "x0.5"]  # Tu peux modifier les labels
    SPEED = [1,2,0.25,0.5]

    def __init__(self, parent=None):
        super().__init__(self.STATES[0], parent)
        self.state_index = 0
        self.clicked.connect(self.next_state)

    def next_state(self):
        """Change l'état du bouton."""
        self.state_index = (self.state_index + 1) % len(self.STATES)
        self.setText(self.STATES[self.state_index])

    def get_state(self):
        """Retourne l'état actuel du bouton."""
        return self.STATES[self.state_index]

    def get_speed(self):
        return self.SPEED[self.state_index]