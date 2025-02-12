from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import QTimer

class MessagePopUp(QWidget):  # Hérite maintenant de QWidget
    def __init__(self,parent):
        super().__init__()

        self.parent=parent
        self.show_message("Succès", "L'action a été effectuée avec succès !", "info")

    def show_message(self, title, message, message_type="info", timeout=1000):
        msg_box = QMessageBox(self.parent)  # self est maintenant un QWidget

        # Définir l'icône du message
        if message_type == "info":
            msg_box.setIcon(QMessageBox.Information)
        elif message_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif message_type == "error":
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.NoIcon)

        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Supprimer les boutons
        msg_box.setStandardButtons(QMessageBox.NoButton)

        # Fermer automatiquement après un délai
        QTimer.singleShot(timeout, msg_box.accept)

        # Affichage du message
        msg_box.show()
