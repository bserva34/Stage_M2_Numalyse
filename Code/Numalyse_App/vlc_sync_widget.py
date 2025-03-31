import vlc
import sys
import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QFrame, QLabel, QSlider, QDialog, QRadioButton, QButtonGroup, QApplication
)
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QImage, QPainter, QKeySequence, QShortcut


from vlc_player_widget import VLCPlayerWidget
from message_popup import MessagePopUp
from mergevideo_thread import MergeVideoThread
from no_focus_push_button import NoFocusPushButton

class SyncWidget(QWidget):
    """ Widget permettant la lecture synchronisée de vidéos. """
    enable_segmentation = Signal(bool)
    enable_recording = Signal(bool)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.layout = QVBoxLayout(self)
        self.player_widgets = []  # Liste pour stocker les lecteurs vidéo
        self.num_windows = 0  # Nombre de sous-fenêtres actives
        self.play=False

        self.cpt_load=0

        self.dialog_result = False

        self.full_screen=False

        self.is_recording=False

    def configure(self):
        """ Ouvre une fenêtre de configuration pour choisir le mode. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration du mode synchronisé")

        dialog_layout = QVBoxLayout(dialog)

        # Options pour le nombre de fenêtres
        num_label = QLabel("Nombre de sous-fenêtres :", dialog)
        dialog_layout.addWidget(num_label)

        num_group = QButtonGroup(dialog)
        option_2 = QRadioButton("2", dialog)
        option_4 = QRadioButton("4", dialog)
        num_group.addButton(option_2)
        num_group.addButton(option_4)
        option_2.setChecked(True)

        dialog_layout.addWidget(option_2)
        dialog_layout.addWidget(option_4)

        # Boutons OK/Annuler
        button_layout = QHBoxLayout()
        ok_button = NoFocusPushButton("OK", dialog)
        cancel_button = NoFocusPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)

        def on_ok():
            if option_2.isChecked():
                self.num_windows = 2
            elif option_4.isChecked():
                self.num_windows = 4
            self.create_video_players()  # Crée les lecteurs
            self.dialog_result=True
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        dialog.exec()

    

    def create_video_players(self):
        #print("Création des lecteurs vidéo...")  

        # Vérifier que la référence à VLCMainWindow est valide
        if self.main_window is None:
            print("Erreur : impossible de récupérer VLCMainWindow")
            return
        
        parent_window = self.main_window  # Utiliser la référence correcte
        


        # Créer une disposition en grille
        grid_layout = QGridLayout()
        self.layout.addLayout(grid_layout)

        # Créer et ajouter les nouveaux lecteurs
        self.player_widgets = []
        rows, cols = (1, 2) if self.num_windows == 2 else (2, 2)

        for i in range(self.num_windows):
            player = VLCPlayerWidget(True,True,True,False)
            player.begin=False
            player.enable_load.connect(self.cpt_load_action)
            self.player_widgets.append(player)
            grid_layout.addWidget(player, i // cols, i % cols)
        
        #print(f"{self.num_windows} lecteurs créés.")

        # Remplacer le contenu principal de VLCMainWindow
        parent_window.setCentralWidget(self)
        #print("Fenêtre mise à jour avec les nouveaux lecteurs.")
        self.create_control_buttons()

    def cpt_load_action(self, val):
        if(val):
            self.cpt_load+=1
        else:
            self.cpt_load-=1

        if (self.cpt_load==self.num_windows):
            self.enable_segmentation.emit(True)
        else:
            self.enable_segmentation.emit(False)

        if (self.cpt_load==0):
            self.play_pause_button.setText("⏯️ Lire")
            self.play=False

    def create_control_buttons(self):
        """ Crée et ajoute automatiquement les boutons de contrôle au layout donné. """
        button_layout = QHBoxLayout()

        self.play_pause_button = NoFocusPushButton("⏯️ Lire", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_pause_button)

        self.play_pause_shortcut = QShortcut(QKeySequence("Space"), self)
        self.play_pause_shortcut.activated.connect(self.toggle_play_pause)

        self.stop_button = NoFocusPushButton("⏹ Arrêter", self)
        self.stop_button.clicked.connect(self.exit_video_players)
        button_layout.addWidget(self.stop_button)

        self.full_screen_button = NoFocusPushButton("◻",self)
        self.full_screen_button.setFixedSize(30, 30)
        self.full_screen_button.clicked.connect(self.full_screen_action)
        button_layout.addWidget(self.full_screen_button)

        self.full_screen_shortcut = QShortcut(QKeySequence("F"), self)
        self.full_screen_shortcut.activated.connect(self.full_screen_action)

        self.layout.addLayout(button_layout)


    def full_screen_action(self):
        for i in self.player_widgets:
            i.display(self.full_screen)
        self.main_window.display(self.full_screen)
        self.play_pause_button.setVisible(self.full_screen)
        self.stop_button.setVisible(self.full_screen)
        self.full_screen_button.setVisible(self.full_screen)

        self.full_screen=not self.full_screen

    def toggle_play_pause(self):
        cond=True
        for i in self.player_widgets:
            if i.media is not None : cond=False
        if cond:
            self.load_video()
        elif self.play:
            self.stop_all()
            self.play_pause_button.setText("⏯️ Lire")
            self.play=False
        else:
            self.play_all()
            self.play_pause_button.setText("⏯️ Pause")
            self.play=True            


    def exit_video_players(self):
        for i in self.player_widgets:
            i.stop_video()
        self.play_pause_button.setText("⏯️ Lire")
        self.enable_segmentation.emit(False)

    def load_video(self):
        fp=self.player_widgets[0].load_file(False)
        if fp:
            for i in self.player_widgets:
                i.begin=True
                i.load_video(fp)
            self.play_pause_button.setText("⏯️ Pause")
            self.play=True
            self.enable_segmentation.emit(True)


    def play_all(self):
        for i in self.player_widgets:
            if i.media is not None:
                i.play_video()

    def stop_all(self):
        for i in self.player_widgets:
            if i.media is not None:
                i.pause_video()



    #capture d'écran combiné
    def capture_screenshot(self,post_traitement=False,format_capture=False):
        images = []
        timestamps = []
        capture_dir = os.path.join(str(Path.home()),"Capture_SLV", "Images")

        # Capture des screenshots et ajout des chemins d'accès
        for i in range(self.num_windows):
            img_path,ts = self.player_widgets[i].capture_screenshot(i,post_traitement,format_capture)
            if img_path:
                images.append(img_path)
            if ts:
                timestamps.append(ts)

        if not images:
            print("Aucune image n'a été capturée.")
            return None

        # Charger les images capturées
        loaded_images = []
        for img_path in images:
            try:
                loaded_images.append(Image.open(img_path))
            except (IOError, FileNotFoundError):
                return

        combined_image=self.merge_image(loaded_images)

        # Suppression des captures individuelles
        for img_path in images:
            os.remove(img_path)

        name = "_".join(f"{i.name_of_video()[:5]}_{ts}" for i, ts in zip(self.player_widgets, timestamps))


        if format_capture:
            combined_path = os.path.join(capture_dir, f"{name}.jpg")
            combined_image.save(combined_path,format="JPEG")
        else:
            combined_path = os.path.join(capture_dir, f"{name}.png")
            combined_image.save(combined_path)


        return combined_image


    def merge_image(self,loaded_images):
        separateur = 2  # Espacement entre les images

        # Trouver la plus petite largeur et hauteur parmi les images
        min_width = min(img.width for img in loaded_images)
        min_height = min(img.height for img in loaded_images)

        # Redimensionner toutes les images en conservant le ratio
        resized_images = []
        for img in loaded_images:
            img_ratio = img.width / img.height  # Ratio largeur / hauteur
            if img_ratio > 1:  # Image en mode paysage
                new_width = min_width
                new_height = int(new_width / img_ratio)
            else:  # Image en mode portrait ou carré
                new_height = min_height
                new_width = int(new_height * img_ratio)
            
            resized_images.append(img.resize((new_width, new_height), Image.LANCZOS))

        # Trouver la largeur et la hauteur maximales des images
        max_width = max(img.width for img in resized_images)
        max_height = max(img.height for img in resized_images)

        # Déterminer la disposition en grille
        num_columns = 2
        num_rows = (len(resized_images) + num_columns - 1) // num_columns  # Arrondi vers le haut

        # Taille totale de l'image combinée
        total_width = max_width * num_columns + (num_columns - 1) * separateur
        total_height = max_height * num_rows + (num_rows - 1) * separateur

        # Créer une nouvelle image vierge avec fond noir
        combined_image = Image.new('RGB', (total_width, total_height), (0, 0, 0))
        draw = ImageDraw.Draw(combined_image)  # Outil pour dessiner

        # Positionner les images au centre de chaque cellule
        x_offset, y_offset = 0, 0
        for index, img in enumerate(resized_images):
            # Calculer la position pour centrer l'image dans la cellule
            centered_x = x_offset + (max_width - img.width) // 2
            centered_y = y_offset + (max_height - img.height) // 2

            # Coller l'image à la bonne position
            combined_image.paste(img, (centered_x, centered_y))

            # Mise à jour de l'offset
            x_offset += max_width + separateur
            if (index + 1) % num_columns == 0:  # Nouvelle ligne après num_columns images
                x_offset = 0
                y_offset += max_height + separateur

        # Dessiner les séparateurs blancs
        for col in range(1, num_columns):
            x_sep = col * max_width + (col - 1) * separateur
            draw.line([(x_sep, 0), (x_sep, total_height)], fill="white", width=separateur)

        for row in range(1, num_rows):
            y_sep = row * max_height + (row - 1) * separateur
            draw.line([(0, y_sep), (total_width, y_sep)], fill="white", width=separateur)

        return combined_image

    def capture_video(self):
        if self.is_recording:
            video_path=[]
            for i in self.player_widgets:
                video_path.append(i.capture_video())
            self.is_recording=not self.is_recording
            self.enable_recording.emit(self.is_recording)
            self.merge_thread=MergeVideoThread(self,video_path)
            self.merge_thread.segmentation_done.connect(self.merge_video_end)
            self.merge_thread.start()
            self.affichage_temp=MessagePopUp(self,titre="",txt="Exportation en cours",type="warning",time=0)
        else:
            for i in self.player_widgets:
                i.capture_video()
            self.is_recording=not self.is_recording  
            self.enable_recording.emit(self.is_recording) 

    def merge_video_end(self):
        self.affichage_temp.hide_message()
        msg=MessagePopUp(self,txt="Capture vidéo combiné enregistré dans Capture_SLV/Vidéo")


    def merge_video(self, video_paths):
        # Ouvrir chaque vidéo avec cv2.VideoCapture
        captures = []
        for path in video_paths:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                print(f"Erreur : impossible d'ouvrir la vidéo {path}")
                return
            captures.append(cap)

        # Récupérer le FPS de la première vidéo (on suppose que tous ont le même FPS)
        fps = captures[0].get(cv2.CAP_PROP_FPS)

        out_writer = None
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        name = "_".join(i.name_of_video()[:5] for i in self.player_widgets)
        output_path = os.path.join(os.path.dirname(video_paths[0]), f"{name}.mp4")

        while True:
            frames_pil = []
            # Lire une frame de chaque vidéo
            for cap in captures:
                ret, frame = cap.read()
                if not ret:
                    # Si l'une des vidéos est terminée, on arrête la fusion
                    break
                # Convertir la frame (BGR) en RGB puis en image PIL
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames_pil.append(pil_image)

            # Si on n'a pas pu lire une frame de chaque vidéo, sortir de la boucle
            if len(frames_pil) != len(captures):
                break

            # Combiner les images avec la méthode merge_image existante
            combined_pil = self.merge_image(frames_pil)

            # Convertir l'image combinée (PIL) en numpy array pour cv2 (et repasser en BGR)
            combined_np = np.array(combined_pil)
            combined_bgr = cv2.cvtColor(combined_np, cv2.COLOR_RGB2BGR)

            # Initialiser le VideoWriter dès la première frame fusionnée
            if out_writer is None:
                height, width, _ = combined_bgr.shape
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # Écrire la frame fusionnée dans le fichier de sortie
            out_writer.write(combined_bgr)

        # Libérer les captures et le writer
        for cap in captures:
            cap.release()
        if out_writer is not None:
            out_writer.release()

        print(f"Vidéo fusionnée enregistrée : {output_path}")

    def set_subtitles(self,id=-1):
        for i in self.player_widgets:
            i.set_subtitles(id)

    def get_subtitles(self):
        acc=0
        for i in self.player_widgets:
            acc+=len(i.get_subtitles())
        if acc>0:
            return True

        return False

        





