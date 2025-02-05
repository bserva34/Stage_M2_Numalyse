from PySide6.QtWidgets import QMainWindow, QToolBar, QWidget, QPushButton, QFileDialog, QMessageBox
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import Qt

from vlc_player_widget import VLCPlayerWidget
from vlc_sync_widget import SyncWidget
from overlay_grid_widget import OverlayGridWidget 
from side_menu_widget import SideMenuWidget
from project_manager import ProjectManager

import os
import json



class VLCMainWindow(QMainWindow):
    """ Fenêtre principale contenant le lecteur et les menus. """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SLV")
        self.setGeometry(100, 100, 1400, 1200)

        # Initialisation du widget principal
        self.vlc_widget = VLCPlayerWidget(True)
        self.vlc_widget.enable_load.connect(self.media_load_action)
        self.setCentralWidget(self.vlc_widget)

        self.sync_widget = SyncWidget(self)

        # Ajout du menu
        self.create_menu_bar()

        # Ajout de la barre d'outils
        self.create_toolbar()

        self.create_keyboard()

        self.sync_mode = False  # État du mode de synchronisation

        self.vlc_widget.enable_recording.connect(self.update_capture_video_button)

        self.overlay_grid = OverlayGridWidget(self)
        self.overlay_grid.setGeometry(self.vlc_widget.geometry())  # Même taille que VLC
        self.overlay_grid.hide()
        self.grille_button.toggled.connect(self.overlay_grid.toggle_grid)

        self.side_menu = None

        self.project=None

        self.save_state=False

    def create_keyboard(self):
        # Raccourci Ctrl + S pour Sauvegarde
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_action) 

        self.open_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.open_shortcut.activated.connect(self.open_project_action) 

        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+X"), self)
        self.quit_shortcut.activated.connect(self.close) 

        self.open_video_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.open_video_shortcut.activated.connect(self.load_video_action) 
        

    def create_menu_bar(self):
        """ Crée une barre de menu avec plusieurs menus déroulants. """
        menu_bar = self.menuBar()

        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")

        open_action = QAction("Ouvrir...\tCtrl+O", self)
        open_action.triggered.connect(self.load_video_action)
        self.save_button = QAction("Enregistrer\tCtrl+S", self)
        self.save_button.triggered.connect(self.save_action)
        self.save_button.setEnabled(False)
        self.vlc_widget.enable_segmentation.connect(self.save_button.setEnabled)
        open_project_button = QAction("Ouvrir un project\tCtrl+A", self)
        open_project_button.triggered.connect(self.open_project_action)
        exit_action = QAction("Quitter\tCtrl+X", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_button)
        file_menu.addSeparator()
        file_menu.addAction(open_project_button)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)


        # Menu Mode
        mode_menu = menu_bar.addMenu("Mode")
        sync_mode_action = QAction("Lecture Synchronisée", self)
        sync_mode_action.triggered.connect(self.sync_button_use)
        mode_menu.addAction(sync_mode_action)

        annotation_mode_action = QAction("Annotation", self)
        annotation_mode_action.triggered.connect(self.annotation_button_use)
        annotation_mode_action.setEnabled(False)
        mode_menu.addAction(annotation_mode_action)

        # Menu Outils
        outil_menu = menu_bar.addMenu("Outils")
        self.seg_mode_action = QAction("Segmentation", self)
        self.seg_mode_action.triggered.connect(self.seg_button_use)
        self.seg_mode_action.setEnabled(False)
        self.vlc_widget.enable_segmentation.connect(self.seg_mode_action.setEnabled)
        outil_menu.addAction(self.seg_mode_action)

        self.grille_button = QAction("Affichage Grille", self)
        self.grille_button.setCheckable(True)
        self.grille_button.toggled.connect(self.grille_button_use)
        #outil_menu.addAction(self.grille_button)


        autres_mode_action = QAction("Autres...", self)
        autres_mode_action.triggered.connect(self.seg_button_use)
        autres_mode_action.setEnabled(False)
        outil_menu.addAction(autres_mode_action)


    def save_action(self):
        if self.project==None:
            if os.name == "nt":  # Windows
                default_dir = "C:/"
            else:  # Linux/Mac
                default_dir = "/"
            file_path, _ = QFileDialog.getSaveFileName(self, "Créer un projet", default_dir, "Projet (*.json)")
            if file_path:
                project_dir = os.path.splitext(file_path)[0] 
                project_name = os.path.basename(project_dir)
                os.makedirs(project_dir, exist_ok=True)
                self.project=ProjectManager(self.side_menu,self.vlc_widget,project_dir,project_name)
                self.project.save_project()
        else:
            self.project.write_json()
        self.save_state=False

    def open_project_action(self):
        if(self.auto_save()):
            if(self.sync_mode):
                self.sync_button_use()
            else:
                self.vlc_widget.stop_video()

            if os.name == "nt":  # Windows
                default_dir = "C:/"
            else:  # Linux/Mac
                default_dir = "/"
            project_path = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier du projet",default_dir)
            if project_path :
                self.recreate_window()

                self.side_menu=SideMenuWidget(self.vlc_widget, self,False)
                self.addDockWidget(Qt.RightDockWidgetArea, self.side_menu)
                self.side_menu.setVisible(False)
                self.side_menu.change.connect(self.change)

                self.project=ProjectManager(self.side_menu,self.vlc_widget)
                val=self.project.open_project(project_path)
                if not val :
                    self.project=None


    def load_video_action(self):
        if(self.auto_save()):
            if self.sync_mode:
                self.sync_widget.load_video()
            else:
                self.vlc_widget.load_file()
            
    def create_toolbar(self):
        """ Crée une barre d'outils avec des boutons d'action. """
        self.toolbar = QToolBar("Barre d'outils")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.capture_button = QAction("📸 Capture d'écran", self)
        self.capture_button.setEnabled(False)
        self.capture_button.triggered.connect(self.capture_action)
        self.vlc_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.toolbar.addAction(self.capture_button)

        self.capture_video_button = QPushButton("📽️ Démarrer la capture vidéo", self)
        self.capture_video_button.setEnabled(False)
        self.capture_video_button.clicked.connect(self.capture_video_action)
        self.vlc_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.toolbar.addWidget(self.capture_video_button)

        self.timecode_button = QAction("Affichage timecode", self)
        self.timecode_button.setEnabled(False)
        self.timecode_button.triggered.connect(self.timecode_action)
        self.vlc_widget.enable_segmentation.connect(self.timecode_button.setEnabled)
        self.toolbar.addAction(self.timecode_button)

    def capture_action(self):
        if self.sync_mode:
            self.sync_widget.capture_screenshot()
        else:
            self.vlc_widget.capture_screenshot()

    def capture_video_action(self):
        if self.sync_mode==False:
            self.vlc_widget.capture_video()

    def timecode_action(self):
        if self.sync_mode==False:
            print("Timecode vidéo : ",self.vlc_widget.player.get_time())

    def sync_button_use(self):
        if(self.auto_save()):
            """ Fonction qui gère l'activation et la désactivation du mode synchronisé. """
            if self.sync_mode:
                # Si on est en mode synchronisé, on désactive ce mode
                self.sync_mode = False
                self.remove_quit_button()

                self.sync_widget.exit_video_players()

                self.recreate_window()


            else:
                self.capture_video_button.setEnabled(False)
                self.sync_mode = True

                self.sync_widget = SyncWidget(self)
                self.create_sync_window()
                self.sync_widget.configure()
                if(self.sync_widget.dialog_result):
                    self.add_quit_button()
                    self.vlc_widget.stop_video()
                else:
                    self.sync_mode=False

    def annotation_button_use(self):
        print('annotation mode')

    def seg_button_use(self):
        """Affiche ou cache le menu latéral."""
        if not self.side_menu:
            #self.vlc_widget.pause_video()
            self.side_menu = SideMenuWidget(self.vlc_widget, self)
            self.addDockWidget(Qt.RightDockWidgetArea, self.side_menu)
            if self.project : 
                self.project.seg=self.side_menu
            self.side_menu.change.connect(self.change)
        else:
            self.side_menu.setVisible(not self.side_menu.isVisible())

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

    def update_capture_video_button(self, is_recording):
        """ Met à jour le texte du bouton en fonction de l'état d'enregistrement. """
        if is_recording:
            self.capture_video_button.setText("📽️ Arrêter la capture vidéo")
            self.capture_video_button.setStyleSheet("background-color: red;")
        else:
            self.capture_video_button.setText("📽️ Démarrer la capture vidéo")
            self.capture_video_button.setStyleSheet("")


    def recreate_window(self):
        self.vlc_widget = VLCPlayerWidget(True)
        self.vlc_widget.enable_load.connect(self.media_load_action)
        self.setCentralWidget(self.vlc_widget)
        self.vlc_widget.enable_segmentation.connect(self.seg_mode_action.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.save_button.setEnabled)

        if self.side_menu : self.side_menu.change.connect(self.change)

    def change(self,state:bool):
        self.save_state=state

    def create_sync_window(self):
        self.sync_widget.enable_segmentation.connect(self.capture_button.setEnabled)

    def media_load_action(self):
        self.project=None
        if(self.side_menu):
            self.side_menu.stop_segmentation()
            self.removeDockWidget(self.side_menu)
            self.side_menu.deleteLater()
            self.side_menu=None


    def grille_button_use(self):
        if self.grille_button.isChecked():
            print("Mode Segmentation activé")
            self.overlay_grid.show()
        else:
            print("Mode Segmentation désactivé")
            self.overlay_grid.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_grid.setGeometry(self.vlc_widget.geometry()) 

    def closeEvent(self, event):    
        if self.project and self.save_state:
            reply = QMessageBox.question(
                self, "Quitter", "Voulez-vous enregistrer avant de quitter ?", 
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.save_action()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept() 
            else:
                event.ignore()

    def auto_save(self):
        if self.project and self.save_state:
            reply = QMessageBox.question(
                self, "Quitter", "Voulez-vous enregistrer avant de quitter ?", 
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.save_action()
                return True
            elif reply == QMessageBox.No:
                return True
            else:
                return False
        else :
            return True       
