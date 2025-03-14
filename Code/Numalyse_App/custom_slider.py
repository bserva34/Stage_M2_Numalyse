from PySide6.QtWidgets import QSlider, QStyle
from PySide6.QtCore import Qt

class CustomSlider(QSlider):
    def mousePressEvent(self, event):
        self.setFocusPolicy(Qt.NoFocus)
        """ Permet de cliquer n'importe où sur la barre pour déplacer le curseur immédiatement """
        if self.orientation() == Qt.Horizontal:
            value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width())
        else:
            value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().y(), self.height())

        self.setValue(value)
        self.sliderMoved.emit(value)  # Émet l'événement pour mettre à jour la position

        super().mousePressEvent(event)  # Appelle l'événement original

