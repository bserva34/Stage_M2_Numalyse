from PySide6.QtWidgets import QMainWindow, QToolBar, QWidget
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from vlc_player_widget import VLCPlayerWidget
from vlc_sync_widget import SyncWidget

class VLCMainWindow(QMainWindow):
    """ Fenêtre principale contenant le lecteur et les menus. """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SLV")
        self.setGeometry(100, 100, 800, 600)

        # Initialisation du widget principal
        self.vlc_widget = VLCPlayerWidget(True)
        self.setCentralWidget(self.vlc_widget)

        self.sync_widget = SyncWidget(self)

        # Ajout du menu
        self.create_menu_bar()

        # Ajout de la barre d'outils
        self.create_toolbar()

        self.sync_mode = False  # État du mode de synchronisation
        

    def create_menu_bar(self):
        """ Crée une barre de menu avec plusieurs menus déroulants. """
        menu_bar = self.menuBar()

        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")

        open_action = QAction("Ouvrir...", self)
        open_action.triggered.connect(self.load_video_action)
        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Menu Mode
        mode_menu = menu_bar.addMenu("Mode")
        sync_mode_action = QAction("Lecture Synchronisée", self)
        sync_mode_action.triggered.connect(self.sync_button_use)
        mode_menu.addAction(sync_mode_action)

        # Menu Outils
        outil_menu = menu_bar.addMenu("Outils")
        self.seg_mode_action = QAction("Segmentation", self)
        self.seg_mode_action.triggered.connect(self.seg_button_use)
        self.seg_mode_action.setEnabled(False)
        outil_menu.addAction(self.seg_mode_action)

        autres_mode_action = QAction("Autres...", self)
        autres_mode_action.triggered.connect(self.seg_button_use)
        autres_mode_action.setEnabled(False)
        outil_menu.addAction(autres_mode_action)

    def load_video_action(self):
        """ Charge une vidéo et ajuste les actions disponibles selon le mode. """
        if self.sync_mode:
            self.sync_widget.load_video()
        else:
            self.vlc_widget.load_file()
            self.seg_mode_action.setEnabled(True)
            
        

    def create_toolbar(self):
        """ Crée une barre d'outils avec des boutons d'action. """
        self.toolbar = QToolBar("Barre d'outils")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        capture_button = QAction("📸 Capture d'écran", self)
        capture_button.triggered.connect(self.capture_action)
        self.toolbar.addAction(capture_button)

    def capture_action(self):
        if self.sync_mode:
            self.sync_widget.capture_screenshot()
        else:
            self.vlc_widget.capture_screenshot()

    def sync_button_use(self):
        """ Fonction qui gère l'activation et la désactivation du mode synchronisé. """
        if self.sync_mode:
            # Si on est en mode synchronisé, on désactive ce mode
            self.sync_mode = False
            self.remove_quit_button()

            self.sync_widget.exit_video_players()

            # Revenir au mode normal avec un seul lecteur
            self.vlc_widget = VLCPlayerWidget(True)
            self.setCentralWidget(self.vlc_widget)

        else:
            # Si on n'est pas en mode synchronisé, on active ce mode
            self.sync_mode = True

            # Créer un nouveau SyncWidget chaque fois que l'on entre en mode synchronisé
            self.sync_widget = SyncWidget(self)  # Re-créer SyncWidget

            self.sync_widget.configure()

            # Ajouter le bouton "Quitter"
            self.add_quit_button()

            self.vlc_widget.stop_video()



    def add_quit_button(self):
        """ Ajoute le bouton 'Quitter' à la barre d'outils. """
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.sync_button_use)  # Ferme l'application
        self.toolbar.addAction(quit_action)

    def remove_quit_button(self):
        """ Retire le bouton 'Quitter' de la barre d'outils. """
        actions = self.toolbar.actions()
        for action in actions:
            if action.text() == "Quitter":
                self.toolbar.removeAction(action)
                break

    def seg_button_use(self):
        print("Segmentation")
