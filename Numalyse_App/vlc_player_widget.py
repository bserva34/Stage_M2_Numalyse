import sys
import os
import vlc
import time
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QFileDialog, QSlider, QLabel, QLineEdit
from PySide6.QtCore import Qt, QTimer

class VLCPlayerWidget(QWidget):
    """ Widget contenant le lecteur VLC et les boutons de contrôle. """

    def __init__(self,add_controls=False,add_window_time=True,m=False):
        super().__init__()

        self.instance = vlc.Instance("--quiet")
        self.player = self.instance.media_player_new()
        self.media = None  # Pour suivre le fichier chargé
        self.ac = add_controls
        self.mute = m
        if self.mute :
            self.player.audio_set_mute(True)
        else : 
            self.player.audio_set_mute(False)
        

        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Cadre vidéo
        self.video_frame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_frame)

        if add_window_time:
            self.create_window_time(main_layout)

        if add_controls : 
            self.create_control_buttons(main_layout)


        # Définir la sortie vidéo en fonction de l'OS
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(self.video_frame.winId())

        # Timer pour mettre à jour le slider et l'affichage du temps
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)

        self.begin=True

    def create_control_buttons(self, parent_layout):
        """ Crée et ajoute automatiquement les boutons de contrôle au layout donné. """
        button_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("⏯️ Lire", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_pause_button)

        self.stop_button = QPushButton("⏹ Arrêter", self)
        self.stop_button.clicked.connect(self.stop_video)
        button_layout.addWidget(self.stop_button)

        parent_layout.addLayout(button_layout)


    def create_window_time(self, parent_layout):
        # Layout pour le temps + bouton mute
        time_layout = QHBoxLayout()

        self.line_edit=QLineEdit()
        self.line_edit.setText("00:00")
        self.line_edit.setAlignment(Qt.AlignCenter)
        self.line_edit.setFixedWidth(50)

        # Affichage du temps
        self.time_label = QLabel("00:00 / 00:00", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.line_edit.textChanged.connect(self.on_value_changed)
        self.time_label.setFixedHeight(15)

        self.mute_button = QPushButton("🔇" if self.mute else "🔊", self)
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(self.mute)  # Définit l'état initial du bouton

        self.mute_button.setFixedSize(30, 30)
        self.mute_button.setCheckable(True)
        self.mute_button.clicked.connect(self.toggle_mute)  

        # Ajouter les éléments au layout
        time_layout.addWidget(self.line_edit)
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.mute_button)
        parent_layout.addLayout(time_layout)

        # Slider pour la progression
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.setEnabled(False)
        parent_layout.addWidget(self.progress_slider)





    def toggle_play_pause(self):
        """ Joue ou met en pause la vidéo, ou demande un fichier si aucune vidéo chargée. """
        if self.media is None:
            self.load_file()
        elif self.player.is_playing():
            self.pause_video()
        else:
            self.play_video()

    def toggle_mute(self):
        if self.mute_button.isChecked():
            self.mute_button.setText("🔇")  # Emoji "Son coupé"
            self.player.audio_set_mute(True)
        else:
            self.mute_button.setText("🔊")  # Emoji "Son activé"
            self.player.audio_set_mute(False)


    def load_file(self,auto=True):
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir une vidéo", "", "Fichiers vidéo (*.mp4 *.avi *.mkv *.mov)")
        if auto : self.load_video(file_path)
        return file_path


    def load_video(self,file_path):
        if file_path:
            self.media = self.instance.media_new(file_path)
            self.player.set_media(self.media)
            if(self.begin):
                self.player.play()
                self.play_pause_button.setText("⏯️ Pause")
            self.timer.start()
            self.progress_slider.setEnabled(True)
            self.time_label.setStyleSheet("color: red;")
            # self.media.parse_with_options(vlc.MediaParseFlag.local, 0)
            # time.sleep(1)
            # print(self. media.get_duration() // 1000)
    
    def play_video(self):
        self.player.play()
        self.play_pause_button.setText("⏯️ Pause")
        self.timer.start()

    def pause_video(self):
        self.player.set_pause(1)
        self.play_pause_button.setText("⏯️ Lire")
        self.timer.stop()

    def stop_video(self):
        """ Arrête et décharge la vidéo. """
        self.player.stop()
        self.media = None
        if self.ac : 
            self.play_pause_button.setText("⏯️ Lire")
        self.timer.stop()
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.time_label.setText("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white;")

    def capture_screenshot(self, name=""):
        """ Capture un screenshot de la vidéo. """
        capture_dir = "captures"
        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Si un nom est fourni, il est ajouté après un underscore
        if name:
            capture_path = os.path.join(capture_dir, f"capture_{timestamp}_{name}.png")
        else:
            capture_path = os.path.join(capture_dir, f"capture_{timestamp}.png")

        if self.player.video_take_snapshot(0, capture_path, 0, 0):
            print(f" Capture enregistrée : {capture_path}")
        return capture_path


    def update_ui(self):
        """ Met à jour le slider et l'affichage du temps. """
        if self.media is None:
            return

        # Position actuelle et durée totale
        current_time = self.player.get_time() // 1000  # en secondes
        total_time = self.player.get_length() // 1000  # en secondes

        if current_time >= 0 and total_time > 0:
            self.progress_slider.setValue(int((current_time / total_time) * 1000))
            current_time_str = self.format_time(current_time)
            #self.line_edit.setText(current_time_str)
            total_time_str = self.format_time(total_time)
            self.time_label.setText(f"{current_time_str} / {total_time_str}")

    def set_position(self, position):
        """ Définit la position de lecture en fonction du slider. """
        if self.media is not None:
            total_time = self.player.get_length() // 1000  # en secondes
            new_time = position / 1000 * total_time
            self.player.set_time(int(new_time * 1000))

    @staticmethod
    def format_time(seconds):
        """ Formate un temps donné en secondes en mm:ss. """
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def on_value_changed(self):
        """ Change la position de la vidéo lorsqu'on modifie le timecode dans le QLineEdit. """
        time_str = self.line_edit.text()
        
        # Vérifier si le format est valide (mm:ss)
        try:
            minutes, seconds = map(int, time_str.split(":"))
            new_time = (minutes * 60 + seconds) * 1000  # Convertir en millisecondes
        except ValueError:
            return  # Si la conversion échoue, on ignore l'entrée

        # Vérifier si le temps est valide par rapport à la durée totale
        total_time = self.player.get_length()
        if total_time > 0 and 0 <= new_time <= total_time:
            self.player.set_time(new_time)
            self.update_ui()

