import sys
import vlc
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QMenuBar, QToolBar
from PySide6.QtGui import QAction  # Import correct pour QAction

from PySide6.QtCore import Qt


class VLCPlayerWidget(QWidget):
    """ Widget contenant les lecteurs VLC et les boutons de lecture. """

    def __init__(self):
        super().__init__()

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Layout principal
        main_layout = QVBoxLayout(self)

        # Cadre vidéo
        self.video_frame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_frame)

        # Bouton de lecture
        self.play_button = QPushButton("Lire", self)
        self.play_button.clicked.connect(self.play_video)
        main_layout.addWidget(self.play_button)

        # Définir la sortie vidéo en fonction de l'OS
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winId())

    def play_video(self):
        """ Charge et joue une vidéo. """
        media = self.instance.media_new("../Film/Alfred Hitchcock - Notorious -1946.mp4")
        self.player.set_media(media)
        self.player.play()


class VLCMainWindow(QMainWindow):
    """ Fenêtre principale contenant le lecteur et les menus. """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SLV")
        self.setGeometry(100, 100, 800, 600)

        # Initialisation du widget principal
        self.vlc_widget = VLCPlayerWidget()
        self.setCentralWidget(self.vlc_widget)

        # Ajout du menu
        self.create_menu_bar()

        # Ajout de la barre d'outils
        self.create_toolbar()

    def create_menu_bar(self):
        """ Crée une barre de menu avec plusieurs menus déroulants. """
        menu_bar = self.menuBar()

        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")

        open_action = QAction("Ouvrir...", self)
        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Menu Lecture
        play_menu = menu_bar.addMenu("Lecture")

        play_action = QAction("Lire", self)
        pause_action = QAction("Pause", self)
        stop_action = QAction("Arrêter", self)

        play_action.triggered.connect(self.vlc_widget.play_video)
        play_menu.addAction(play_action)
        play_menu.addAction(pause_action)
        play_menu.addAction(stop_action)

        # Menu Aide
        help_menu = menu_bar.addMenu("Aide")

        about_action = QAction("À propos", self)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """ Crée une barre d'outils avec des boutons d'action. """
        toolbar = QToolBar("Barre d'outils")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        play_button = QAction("▶ Lire", self)
        pause_button = QAction("⏸ Pause", self)
        stop_button = QAction("⏹ Arrêter", self)

        play_button.triggered.connect(self.vlc_widget.play_video)

        toolbar.addAction(play_button)
        toolbar.addAction(pause_button)
        toolbar.addAction(stop_button)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VLCMainWindow()
    window.show()
    sys.exit(app.exec())
