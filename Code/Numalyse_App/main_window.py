from PySide6.QtWidgets import QMainWindow, QToolBar, QWidget, QPushButton, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QTimer

from vlc_player_widget import VLCPlayerWidget
from vlc_sync_widget import SyncWidget
from overlay_grid_widget import OverlayGridWidget 
from side_menu_widget import SideMenuWidget
from project_manager import ProjectManager
from export_manager import ExportManager
from extract_manager import ExtractManager
from message_popup import MessagePopUp
from aug_mode import AugMode

import os
import json

class VLCMainWindow(QMainWindow):
    """ Fenêtre principale contenant le lecteur et les menus. """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SLV")
        self.setGeometry(100, 100, 1400, 1200)
        self.showMaximized()
        #self.showFullScreen() #enlève la barre menu etc

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

        self.extract_manager=None      

        self.aug_mode=None


    #création interface
    def create_menu_bar(self):
        """ Crée une barre de menu avec plusieurs menus déroulants. """
        self.menu_bar = self.menuBar()

        # Menu Fichier
        file_menu = self.menu_bar.addMenu("Fichier")

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
        mode_menu = self.menu_bar.addMenu("Mode")
        sync_mode_action = QAction("Lecture Synchronisée", self)
        sync_mode_action.triggered.connect(self.sync_button_use)
        mode_menu.addAction(sync_mode_action)

        self.aug_mode_action = QAction("Lecture Augmentée", self)
        self.aug_mode_action.triggered.connect(self.aug_button_use)
        self.aug_mode_action.setEnabled(False)
        mode_menu.addAction(self.aug_mode_action)

        # Menu Outils
        outil_menu = self.menu_bar.addMenu("Outils")
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

    def create_toolbar(self):
        """ Crée une barre d'outils avec des boutons d'action. """
        self.toolbar = QToolBar("Barre d'outils")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.capture_button = QPushButton("📸 Capture d'écran", self)
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_action)
        self.vlc_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.toolbar.addWidget(self.capture_button)

        self.capture_video_button = QPushButton("📽️ Démarrer la capture vidéo", self)
        self.capture_video_button.setEnabled(False)
        self.capture_video_button.clicked.connect(self.capture_video_action)
        self.vlc_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.toolbar.addWidget(self.capture_video_button)

        # self.timecode_button = QPushButton("Affichage timecode", self)
        # self.timecode_button.setEnabled(False)
        # self.timecode_button.clicked.connect(self.timecode_action)
        # self.vlc_widget.enable_segmentation.connect(self.timecode_button.setEnabled)
        # self.toolbar.addWidget(self.timecode_button)

        self.export_button = QPushButton("Exporter",self)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_action)
        self.toolbar.addWidget(self.export_button)

        self.extraction_button = QPushButton("Extraire une séquence",self)
        self.extraction_button.setEnabled(False)
        self.extraction_button.clicked.connect(self.extraction_action)
        self.vlc_widget.enable_segmentation.connect(self.extraction_button.setEnabled)
        self.toolbar.addWidget(self.extraction_button)

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

        self.echap_aug_mode = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.echap_aug_mode.activated.connect(self.echap_button_use)


    #gestion du projet 
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
        self.save_button.setEnabled(False)

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
            project_path = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier du projet à ouvrir",default_dir)
            if project_path :
                self.recreate_window()

                self.side_menu=SideMenuWidget(self.vlc_widget, self,start=False)
                self.addDockWidget(Qt.RightDockWidgetArea, self.side_menu)
                self.side_menu.setVisible(False)
                self.side_menu.change.connect(self.change)
                self.export_button.setEnabled(True) 
                self.aug_mode_action.setEnabled(True)     

                self.project=ProjectManager(self.side_menu,self.vlc_widget)
                val=self.project.open_project(project_path)
                if not val :
                    self.project=None
                    self.side_menu=None
                self.save_state=False


    #load de vidéo
    def load_video_action(self):
        if(self.auto_save()):
            if self.sync_mode:
                self.sync_widget.load_video()
            else:
                self.vlc_widget.load_file()

    def media_load_action(self):
        self.project=None
        if(self.side_menu):
            self.side_menu.stop_segmentation()
            self.removeDockWidget(self.side_menu)
            self.side_menu.deleteLater()
            self.side_menu=None
        self.export_button.setEnabled(False)
        self.aug_mode_action.setEnabled(False) 
            
    #capture image et vidéo
    def capture_action(self):
        if self.sync_mode:
            self.sync_widget.capture_screenshot()
        else:
            self.vlc_widget.capture_screenshot()

    def capture_video_action(self):
        if self.sync_mode==False:
            self.vlc_widget.capture_video()

    def update_capture_video_button(self, is_recording):
        """ Met à jour le texte du bouton en fonction de l'état d'enregistrement. """
        if is_recording:
            self.capture_video_button.setText("📽️ Arrêter la capture vidéo")
            self.capture_video_button.setStyleSheet("background-color: red;")
        else:
            self.capture_video_button.setText("📽️ Démarrer la capture vidéo")
            self.capture_video_button.setStyleSheet("")

    #extraction de séquence vidéo
    def extraction_action(self):
        self.extract_manager=ExtractManager(self.vlc_widget)



    #fonction qui sera à supprimer et qui permet d'afficher le timecode
    def timecode_action(self):
        if self.sync_mode==False:
            print("Timecode vidéo : ",self.vlc_widget.player.get_time())


    #quand on revient en mode classique
    def recreate_window(self):
        self.vlc_widget = VLCPlayerWidget(True)
        self.vlc_widget.enable_load.connect(self.media_load_action)
        self.setCentralWidget(self.vlc_widget)
        self.vlc_widget.enable_segmentation.connect(self.seg_mode_action.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.save_button.setEnabled)

        self.vlc_widget.enable_recording.connect(self.update_capture_video_button)

        self.vlc_widget.enable_segmentation.connect(self.extraction_button.setEnabled)

        if self.side_menu : self.side_menu.change.connect(self.change)

    #lecture sync
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

    def create_sync_window(self):
        self.sync_widget.enable_segmentation.connect(self.capture_button.setEnabled)

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



    #segmentation
    def seg_button_use(self):
        """Affiche ou cache le menu latéral."""
        if not self.side_menu:
            #self.vlc_widget.pause_video()
            self.side_menu = SideMenuWidget(self.vlc_widget, self,start=True)
            self.addDockWidget(Qt.RightDockWidgetArea, self.side_menu)
            if self.project : 
                self.project.seg=self.side_menu
            self.side_menu.change.connect(self.change)
            #self.export_button.setEnabled(True)
            self.side_menu.segmentation_done.connect(self.export_button.setEnabled)
            self.side_menu.segmentation_done.connect(self.aug_mode_action.setEnabled)
        else:
            self.side_menu.setVisible(not self.side_menu.isVisible())



    #exportation du travail
    def export_action(self):
        if self.project:
            self.export=ExportManager(self.side_menu,self.vlc_widget,self.project)
            self.save_state=True
        else:
            msg=MessagePopUp(self,titre="Attention",txt="Vous devez d'abord créer un projet",type="error")


    def echap_button_use(self):
        if self.aug_mode:
            self.aug_button_use()

    #lecture augmentée
    def aug_button_use(self):
        if self.aug_mode : 
            self.toolbar.setVisible(True)
            self.menu_bar.setVisible(True)
            if self.side_menu:
                self.side_menu.setVisible(True)
            self.aug_mode.exit_aug()
            self.aug_mode=None
            self.showMaximized()
            self.vlc_widget.display(True)
            self.msg.hide_message_2()
        else :
            if self.project:
                if self.project.path_of_super: 
                    self.showFullScreen()
                    self.aug_mode=AugMode(self.vlc_widget,self.side_menu,self.project.path_of_super, callback=self.aug_button_use)
                    self.toolbar.setVisible(False)
                    self.side_menu.setVisible(False)    
                    self.menu_bar.setVisible(False) 
                    self.vlc_widget.display(False)  
                    self.msg=MessagePopUp(self,False)  
                else :
                    msg=MessagePopUp(self,titre="Erreur",txt="Exporter d'abord une super vidéo",type="warning")
            else:
                msg=MessagePopUp(self,titre="Attention",txt="Vous devez d'abord créer un projet",type="error")


    #gestion de la sauvegarde automatique
    def closeEvent(self, event):    
        if(self.auto_save()):
            if(self.side_menu):
                self.side_menu.stop_segmentation()
            event.accept()
        else:
            event.ignore()

    def auto_save(self):
        if (self.project and self.save_state) or (not self.project and self.side_menu):
            reply = QMessageBox.question(
                self, "Quitter", "Voulez-vous enregistrer ce projet avant de quitter ?", 
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

    def change(self,state:bool):
        self.save_state=state
        if(self.project):
            self.save_button.setEnabled(not state)

    # grille mais ne fonctionne pas pour l'instant
    def grille_button_use(self):
        if self.grille_button.isChecked():
            print("Mode Segmentation activé")
            self.overlay_grid.show()
        else:
            print("Mode Segmentation désactivé")
            self.overlay_grid.hide()

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     self.overlay_grid.setGeometry(self.vlc_widget.geometry()) 