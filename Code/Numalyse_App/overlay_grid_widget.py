from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt

class OverlayGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Laisse passer les événements de la souris
        self.setAttribute(Qt.WA_NoSystemBackground)  # Pas d'arrière-plan
        self.setStyleSheet("background: transparent;")  # Fond transparent
        self.grid_enabled = False  # Grille désactivée par défaut

    def paintEvent(self, event):
        if not self.grid_enabled:
            return  # Ne dessine rien si la grille est désactivée

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Définition du style de la grille
        pen = QPen(QColor(255, 0, 0, 150))  # Rouge semi-transparent
        pen.setWidth(2)
        painter.setPen(pen)

        # Récupérer la taille actuelle de la fenêtre
        width = self.width()
        height = self.height()
        rows, cols = 20, 20  # 3x3 grilles

        # Dessiner les lignes horizontales
        for i in range(1, rows):
            y = i * height // rows
            painter.drawLine(0, y, width, y)

        # Dessiner les lignes verticales
        for j in range(1, cols):
            x = j * width // cols
            painter.drawLine(x, 0, x, height)

    def toggle_grid(self):
        """ Active/Désactive la grille """
        self.grid_enabled = not self.grid_enabled
        self.update()  # Rafraîchir l'affichage


