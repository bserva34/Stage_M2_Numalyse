from PySide6.QtWidgets import QWidget, QMessageBox, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

class MessagePopUp(QWidget):  
    def __init__(self, parent, msg1=True,titre="Succès",txt="L'action a été effectuée avec succès !",type="info",time=2000):
        super().__init__(parent)
        
        self.affichage = QLabel("Appuyez sur Échap pour quitter le plein écran", parent)
        self.affichage.setFixedSize(600, 80)  # Taille plus petite et fixe
        self.affichage.move(
            (parent.width() - self.affichage.width()) // 2, 
            (parent.height() - self.affichage.height()) // 2
        )  # Centre le label dans la fenêtre
        
        self.affichage.setAlignment(Qt.AlignCenter)  # Centre le texte
        self.affichage.setStyleSheet("""
            color: white; 
            background-color: rgba(0, 0, 0, 150);  /* Fond semi-transparent réduit */
            font-size: 24px;  
            padding: 10px;
            border-radius: 10px;
        """)
        self.affichage.setFont(QFont("Arial", 20, QFont.Bold))  # Police plus grande
        self.affichage.hide()

        self.parent = parent

        if msg1:
            self.show_message(titre,txt,type,time)
        else:
            self.show_message_2()

    def show_message(self, title, message, message_type="info", timeout=2000):
        msg_box = QMessageBox(self.parent)  

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
        msg_box.setStandardButtons(QMessageBox.NoButton)

        QTimer.singleShot(timeout, msg_box.accept)
        msg_box.show()

    def show_message_2(self, timeout=1000):
        """ Affiche le message en transparence pendant `timeout` ms """
        self.affichage.show()
        QTimer.singleShot(timeout, self.affichage.hide)  # Cache le message après le timeout
    
    def hide_message_2(self):
        self.affichage.hide()