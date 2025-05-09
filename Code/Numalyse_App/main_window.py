from PySide6.QtWidgets import QDockWidget, QMainWindow, QToolBar, QWidget, QPushButton, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit,QMenu, QHBoxLayout, QButtonGroup, QRadioButton, QToolButton, QSlider
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QActionGroup, QImage, QPixmap
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
from preference_manager import PreferenceManager
from no_focus_push_button import NoFocusPushButton
#from color_img import ColorImage

import os
import json
import cv2
import time

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

        #option capture
        self.format_capture=False
        self.post_traitement=False
        self.gamma=1.4
        self.format_export_text=[False,False,True]

        self.pref_manager = PreferenceManager(self)

        self.quit_button=None

        self.image_display_label = QLabel("image post traité", self)
        self.image_display_label.setAlignment(Qt.AlignCenter)

        self.image_dock = QDockWidget("Aperçu de l'image corrigée", self)
        self.image_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.image_dock.setWidget(self.image_display_label)
        self.addDockWidget(Qt.RightDockWidgetArea, self.image_dock)
        self.image_dock.setVisible(False)


    def display_size(self):
        # Obtenir la taille actuelle du vlc_widget
        taille = self.vlc_widget.size()
        largeur = taille.width()
        hauteur = taille.height()
        print(f"Largeur : {largeur}, Hauteur : {hauteur}")

        return largeur,hauteur



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
        mode_menu.addSeparator()

        self.aug_mode_action = QAction("Lecture Augmentée", self)
        self.aug_mode_action.triggered.connect(self.aug_button_use)
        self.aug_mode_action.setEnabled(False)
        self.aug_mode_action.setVisible(False)
        mode_menu.addAction(self.aug_mode_action)

        # Menu Outils
        outil_menu = self.menu_bar.addMenu("Outils")
        self.seg_mode_action = QAction("Segmentation", self)
        self.seg_mode_action.triggered.connect(self.seg_button_use)
        self.seg_mode_action.setEnabled(False)
        self.vlc_widget.enable_segmentation.connect(self.seg_mode_action.setEnabled)
        outil_menu.addAction(self.seg_mode_action)
        outil_menu.addSeparator()

        self.subtitle_button = QAction("Sous Titres", self)
        self.subtitle_button.setEnabled(False)
        self.vlc_widget.enable_segmentation.connect(self.subtitle_button.setEnabled)
        self.subtitle_create=False
        self.subtitle_menu = QMenu(self)
        self.subtitle_button.setMenu(self.subtitle_menu)
        self.subtitle_menu.aboutToShow.connect(self.update_subtitle_menu)
        outil_menu.addAction(self.subtitle_button)
        outil_menu.addSeparator()

        self.colormap_button = QAction("ColorMap", self)
        self.colormap_button.setVisible(False)
        self.colormap_button.setEnabled(False)
        self.vlc_widget.enable_segmentation.connect(self.colormap_button.setEnabled)
        self.colormap_button.triggered.connect(self.colormap_action)
        outil_menu.addAction(self.colormap_button)

        self.grille_button = QAction("Affichage Grille", self)
        self.grille_button.setCheckable(True)
        self.grille_button.toggled.connect(self.grille_button_use)
        #outil_menu.addAction(self.grille_button)

        option_menu= self.menu_bar.addMenu("Options")
        self.capture_menu = QAction("Options de captures",self)
        self.capture_menu.triggered.connect(self.capture_option)
        option_menu.addAction(self.capture_menu)
        option_menu.addSeparator()

        self.export_menu = QAction("Option d'exportation",self)
        self.export_menu.triggered.connect(self.export_option)
        option_menu.addAction(self.export_menu)


    def create_toolbar(self):
        """ Crée une barre d'outils avec des boutons d'action. """
        self.toolbar = QToolBar("Barre d'outils")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.capture_button = NoFocusPushButton("Capture d'écran", self)
        self.capture_button.setEnabled(False)
        self.capture_button.setFocusPolicy(Qt.NoFocus)
        self.capture_button.clicked.connect(self.capture_action)
        self.vlc_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.toolbar.addWidget(self.capture_button)

        self.capture_video_button = NoFocusPushButton("Démarrer la capture vidéo", self)
        self.capture_video_button.setEnabled(False)
        self.capture_video_button.setFocusPolicy(Qt.NoFocus)
        self.capture_video_button.clicked.connect(self.capture_video_action)
        self.vlc_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.toolbar.addWidget(self.capture_video_button)

        self.export_button = NoFocusPushButton("Exporter",self)
        self.export_button.setEnabled(False)
        self.export_button.setFocusPolicy(Qt.NoFocus)
        self.export_button.clicked.connect(self.export_action)
        self.toolbar.addWidget(self.export_button)

        self.extraction_button = NoFocusPushButton("Extraire une séquence",self)
        self.extraction_button.setEnabled(False)
        self.extraction_button.setFocusPolicy(Qt.NoFocus)
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
                #self.recreate_window()

                self.side_menu=SideMenuWidget(self.vlc_widget, self,start=False)
                self.addDockWidget(Qt.BottomDockWidgetArea, self.side_menu)
                self.side_menu.display.setVisible(True)
                self.add_quit_button(sync=False)
                self.side_menu.length=self.vlc_widget.get_size_of_slider()
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
        self.remove_quit_button()
        if(self.side_menu):
            self.side_menu.stop_segmentation()
            self.side_menu.remove_display()
            self.removeDockWidget(self.side_menu)
            self.side_menu.deleteLater()
            self.side_menu=None
        self.export_button.setEnabled(False)
        self.aug_mode_action.setEnabled(False) 
        self.subtitle_create=False
            
    #capture image et vidéo
    def capture_action(self):
        if self.sync_mode:
            self.sync_widget.capture_screenshot(post_traitement=self.post_traitement,format_capture=self.format_capture)
        else:
            if self.post_traitement:
                if self.side_menu:
                    if self.side_menu.isVisible():
                        self.display_side_menu=True
                        self.side_menu.setVisible(False)
                        self.side_menu.display.setVisible(False)
                else:
                    self.display_side_menu=False

                self.toolbar.addWidget(QLabel("         ",self))

                self.slider = QSlider(Qt.Horizontal, self)
                self.slider.setRange(49,201)
                self.slider.sliderMoved.connect(self.display_capture)
                self.slider.setValue(self.gamma*100)
                self.toolbar.addWidget(self.slider)

                self.affichage_slider = QLabel(str(self.gamma),self)
                self.toolbar.addWidget(self.affichage_slider)

                self.validate_pt = NoFocusPushButton("Valider",self)
                self.validate_pt.clicked.connect(self.capture_action_with_post_traitement)
                self.validate_pt.setStyleSheet("background-color: green;")
                self.toolbar.addWidget(self.validate_pt)

                self.annule_pt = NoFocusPushButton("Annuler",self)
                self.annule_pt.clicked.connect(self.annule_capture)
                self.annule_pt.setStyleSheet("background-color: red;")
                self.toolbar.addWidget(self.annule_pt)

                self.capture_button.setEnabled(False)
                self.vlc_widget.pause_video()
                self.path_post,_=self.vlc_widget.capture_screenshot(post_traitement=True)
                self.image_post=cv2.imread(self.path_post)
                self.image_corrige=self.vlc_widget.adjust_gamma(self.image_post,gamma=self.gamma)
                self.display_corrected_image()
                self.image_dock.setVisible(True)
            else:
                self.vlc_widget.capture_screenshot(post_traitement=self.post_traitement,format_capture=self.format_capture)

    def display_capture(self):
        self.gamma=self.slider.value()/100
        self.affichage_slider.setText(str(self.gamma))   

        self.image_corrige=self.vlc_widget.adjust_gamma(self.image_post,gamma=self.gamma)
        self.display_corrected_image()

    def display_corrected_image(self):
        fixed_width = 1000  # Définir une largeur fixe (ajustez selon vos besoins)
    
        original_height, original_width, channels = self.image_corrige.shape
        aspect_ratio = original_height / original_width  # Calcul du ratio

        new_height = int(fixed_width * aspect_ratio)

        resized_image = cv2.resize(self.image_corrige, (fixed_width, new_height), interpolation=cv2.INTER_AREA)

        image_rgb = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
        
        bytesPerLine = channels * fixed_width
        qImg = QImage(image_rgb.data, fixed_width, new_height, bytesPerLine, QImage.Format_RGB888)
        
        self.image_display_label.setPixmap(QPixmap.fromImage(qImg))

    
    def suppr_pt(self):
        self.slider.deleteLater()
        self.affichage_slider.deleteLater()
        self.validate_pt.deleteLater()
        self.annule_pt.deleteLater()

        self.slider=None
        self.affichage_slider=None
        self.validate_pt=None
        self.annule_pt=None

        self.capture_button.setEnabled(True)

    def capture_action_with_post_traitement(self):
        self.suppr_pt()

        cv2.imwrite(self.path_post,self.image_corrige)
        if self.format_capture:
            self.vlc_widget.png_to_jpeg(self.path_post)
        self.image_dock.setVisible(False)

        if self.display_side_menu:
            self.side_menu.setVisible(True)
            self.side_menu.display.setVisible(True)

        self.pref_manager.save_preferences()

    def annule_capture(self):
        self.suppr_pt()
        os.remove(self.path_post)
        self.image_dock.setVisible(False)
        if self.display_side_menu:
            self.side_menu.setVisible(True)
            self.side_menu.display.setVisible(True)

    def capture_video_action(self):
        if self.sync_mode:
            self.sync_widget.capture_video()
        else:
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

    #quand on revient en mode classique
    def recreate_window(self):
        self.vlc_widget = VLCPlayerWidget(True)
        self.vlc_widget.enable_load.connect(self.media_load_action)
        self.setCentralWidget(self.vlc_widget)
        self.vlc_widget.enable_segmentation.connect(self.seg_mode_action.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.save_button.setEnabled)
        self.vlc_widget.enable_segmentation.connect(self.subtitle_button.setEnabled)

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
                self.remove_quit_button()
                self.capture_video_button.setEnabled(False)
                self.sync_mode = True

                self.sync_widget = SyncWidget(self)
                self.create_sync_window()
                self.sync_widget.configure()
                if(self.sync_widget.dialog_result):
                    self.vlc_widget.stop_video()
                    self.add_quit_button()                    
                else:
                    self.sync_mode=False

    def create_sync_window(self):
        self.sync_widget.enable_segmentation.connect(self.capture_button.setEnabled)
        self.sync_widget.enable_segmentation.connect(self.subtitle_button.setEnabled)
        self.sync_widget.enable_segmentation.connect(self.capture_video_button.setEnabled)
        self.sync_widget.enable_segmentation.connect(self.subtitles_load)
        self.sync_widget.enable_recording.connect(self.update_capture_video_button)

    def add_quit_button(self,sync=True):
        self.quit_action = QAction("Quitter", self)
        if sync:
            self.quit_action.triggered.connect(self.sync_button_use)
        else:
            self.quit_action.triggered.connect(self.seg_button_use)

        # Créer un QToolButton et lui associer l'action
        self.quit_button = QToolButton()
        self.quit_button.setDefaultAction(self.quit_action)
        
        # Appliquer une feuille de style pour changer la couleur du texte en rouge
        self.quit_button.setStyleSheet("QToolButton { color: red; }")
        
        # Ajouter le bouton personnalisé à la barre d'outils
        self.toolbar.addWidget(self.quit_button)


    def remove_quit_button(self):
        if self.quit_button:
            action = self.quit_button.defaultAction()
            if action:
                # Retirer l'action de la barre d'outils
                self.toolbar.removeAction(action)
            # Supprimer le QToolButton
            self.quit_button.deleteLater()
            self.quit_button = None



    #segmentation
    def seg_button_use(self):
        """Affiche ou cache le menu latéral."""
        if not self.side_menu:
            #self.vlc_widget.pause_video()
            self.side_menu = SideMenuWidget(self.vlc_widget, self,start=True)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.side_menu)
            self.side_menu.display.setVisible(True)
            self.side_menu.length=self.vlc_widget.get_size_of_slider()
            if self.project : 
                self.project.seg=self.side_menu
            self.side_menu.change.connect(self.change)
            #self.export_button.setEnabled(True)
            self.side_menu.segmentation_done.connect(self.export_button.setEnabled)
            self.side_menu.segmentation_done.connect(self.aug_mode_action.setEnabled)
            self.add_quit_button(sync=False)
        else:
            val=not self.side_menu.isVisible()
            self.side_menu.setVisible(val)
            self.side_menu.display.setVisible(val)
            if val:
                self.add_quit_button(sync=False)
            else:
                self.remove_quit_button()





    #exportation du travail
    def export_action(self):
        if self.project:
            self.export=ExportManager(self.side_menu,self.vlc_widget,self.project,self.format_export_text)
            self.save_state=True
        else:
            msg=MessagePopUp(self,titre="Attention",txt="Vous devez d'abord créer un projet",type="error")


    def echap_button_use(self):
        if self.aug_mode:
            self.aug_button_use()

    #lecture augmentée
    def aug_button_use(self):
        if self.aug_mode : 
            self.aug_mode.exit_aug()
            self.aug_mode=None
            self.display(True)
            self.vlc_widget.display(True)
            self.msg.hide_message_2()
        else :
            if self.project:
                if self.project.path_of_super: 
                    self.aug_mode=AugMode(self.vlc_widget,self.side_menu,self.project.path_of_super, callback=self.aug_button_use)
                    self.display(False)
                    self.vlc_widget.display(False)  
                    self.msg=MessagePopUp(self,False)  
                else :
                    msg=MessagePopUp(self,titre="Erreur",txt="Exporter d'abord une super vidéo",type="warning")
            else:
                msg=MessagePopUp(self,titre="Attention",txt="Vous devez d'abord créer un projet",type="error")

    def display(self,visible):
        self.toolbar.setVisible(visible)
        self.menu_bar.setVisible(visible)
        if self.side_menu:
            self.side_menu.setVisible(visible)
        if(visible):
            self.showMaximized()
        else:
            self.showFullScreen()

    #gestion de la sauvegarde automatique
    def closeEvent(self, event):    
        if(self.auto_save()):
            if(self.side_menu):
                self.side_menu.stop_segmentation()
            self.pref_manager.save_preferences()
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

    def capture_option(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Option des captures")

        dialog_layout = QVBoxLayout(dialog)

        # Options pour le nombre de fenêtres
        num_label = QLabel("Format :", dialog)
        dialog_layout.addWidget(num_label)

        num_group = QButtonGroup(dialog)
        option_2 = QRadioButton(".png", dialog)
        option_4 = QRadioButton(".jpeg", dialog)
        num_group.addButton(option_2)
        num_group.addButton(option_4)
        option_2.setChecked(not self.format_capture)
        option_4.setChecked(self.format_capture)

        dialog_layout.addWidget(option_2)
        dialog_layout.addWidget(option_4)

        contraste = QLabel("Post Traitement:", dialog)
        dialog_layout.addWidget(contraste)

        c = QButtonGroup(dialog)
        none = QRadioButton("aucun", dialog)
        yes = QRadioButton("réhaussement de contraste", dialog)
        c.addButton(none)
        c.addButton(yes)
        none.setChecked(not self.post_traitement)
        yes.setChecked(self.post_traitement)

        dialog_layout.addWidget(none)
        dialog_layout.addWidget(yes)

        # Boutons OK/Annuler
        button_layout = QHBoxLayout()
        ok_button = NoFocusPushButton("OK", dialog)
        cancel_button = NoFocusPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)

        def on_ok():
            if option_2.isChecked():
                self.format_capture=False
            elif option_4.isChecked():
                self.format_capture=True

            if(none.isChecked()):
                self.post_traitement=False
            elif yes.isChecked():
                self.post_traitement=True
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        dialog.exec()

    def export_option(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Option d'exportation")

        dialog_layout = QVBoxLayout(dialog)

        # Options pour le nombre de fenêtres
        num_label = QLabel("Format :", dialog)
        dialog_layout.addWidget(num_label)

        format_option = QButtonGroup(dialog)
        option1 = QRadioButton(".docx", dialog)
        option2 = QRadioButton(".odt", dialog)
        option3=  QRadioButton(".pdf",dialog)
        format_option.addButton(option1)
        format_option.addButton(option2)
        format_option.addButton(option3)

        option1.setChecked(self.format_export_text[0])
        option2.setChecked(self.format_export_text[1])
        option3.setChecked(self.format_export_text[2])

        dialog_layout.addWidget(option1)
        dialog_layout.addWidget(option2)
        dialog_layout.addWidget(option3)

        # Boutons OK/Annuler
        button_layout = QHBoxLayout()
        ok_button = NoFocusPushButton("OK", dialog)
        cancel_button = NoFocusPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)

        def on_ok():
            self.format_export_text[:] = [False, False, False] 
            if option1.isChecked():
                self.format_export_text[0]=True
            elif option2.isChecked():
                self.format_export_text[1]=True
            elif option3.isChecked():
                self.format_export_text[2]=True
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        dialog.exec()


    def update_subtitle_menu(self):
        if not self.subtitle_create:
            if self.sync_mode :
                self.subtitle_menu.clear()
                action_group = QActionGroup(self)
                action_group.setExclusive(True)

                if self.sync_widget.get_subtitles():
                    action1 = QAction("Désactivé", self)
                    action1.setCheckable(True)
                    action_group.addAction(action1)
                    action1.triggered.connect(lambda *args, id=-1: self.sync_widget.set_subtitles(id))
                    self.subtitle_menu.addAction(action1)

                    action2 = QAction("Activé", self)
                    action2.setCheckable(True)
                    action_group.addAction(action2)
                    action2.triggered.connect(lambda *args, id=3: self.sync_widget.set_subtitles(id))
                    self.subtitle_menu.addAction(action2)
                    action2.setChecked(True)
                else:
                    action=QAction("Aucun Sous-Titres",self)
                    action.setEnabled(False)
                    action_group.addAction(action)
                    self.subtitle_menu.addAction(action)   
                    

            else:
                self.subtitle_menu.clear()

                action_group = QActionGroup(self)
                action_group.setExclusive(True)

                liste = self.vlc_widget.get_subtitles()
                if len(liste)==0:
                    action=QAction("Aucun Sous-Titres",self)
                    action.setEnabled(False)
                    action_group.addAction(action)
                    self.subtitle_menu.addAction(action)
                else :
                    track=self.vlc_widget.get_track()
                    for subtitle in liste:
                        nom = subtitle["nom"]
                        if isinstance(nom, bytes):
                            nom = nom.decode('utf-8', errors='ignore')
                        action = QAction(nom, self)
                        action.setCheckable(True)
                        if(subtitle["id"]==track):
                            action.setChecked(True)
                        action_group.addAction(action)
                        action.triggered.connect(lambda *args, id=subtitle["id"]: self.vlc_widget.set_subtitles(id))
                        self.subtitle_menu.addAction(action)
            self.subtitle_create=True


    def subtitles_load(self,state:bool):
        self.subtitle_create=False

    def colormap_action(self):
        self.cm=ColorImage(self,self.vlc_widget)



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