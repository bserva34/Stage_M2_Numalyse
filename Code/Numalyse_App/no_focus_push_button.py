from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class NoFocusPushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.ClickFocus)
