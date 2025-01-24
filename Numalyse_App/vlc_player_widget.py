import sys
import os
import vlc
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QFileDialog, QSlider, QLabel
from PySide6.QtCore import Qt, QTimer


class VLCPlayerWidget(QWidget):
    """ Widget contenant le lecteur VLC et les boutons de contrôle. """

    def __init__(self):
        super().__init__()

        self.instance = vlc.Instance("--quiet")
        self.player = self.instance.media_player_new()
        self.media = None  # Pour suivre le fichier chargé

        # Layout principal
        main_layout = QVBoxLayout(self)

        # Cadre vidéo
        self.video_frame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_frame)

        # Affichage du temps
        self.time_label = QLabel("00:00 / 00:00", self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFixedHeight(20)
        main_layout.addWidget(self.time_label)

        # Slider pour la progression
        self.progress_slider = QSlider(Qt.Horizontal, self)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.setEnabled(False)
        main_layout.addWidget(self.progress_slider)

        # Layout pour les boutons de contrôle
        button_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("▶ Lire", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_pause_button)

        self.stop_button = QPushButton("⏹ Arrêter", self)
        self.stop_button.clicked.connect(self.stop_video)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)

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

    def toggle_play_pause(self):
        """ Joue ou met en pause la vidéo, ou demande un fichier si aucune vidéo chargée. """
        if self.media is None:
            self.load_video()
        elif self.player.is_playing():
            self.player.pause()
            self.play_pause_button.setText("▶️ Lire")
        else:
            self.player.play()
            self.play_pause_button.setText("⏸ Pause")
            self.timer.start()

    def load_video(self):
        """ Ouvre un explorateur de fichiers et charge une vidéo. """
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir une vidéo", "", "Fichiers vidéo (*.mp4 *.avi *.mkv *.mov)")
        if file_path:
            self.media = self.instance.media_new(file_path)
            self.player.set_media(self.media)
            if(self.begin):
                self.player.play()
                self.play_pause_button.setText("⏸ Pause")
            self.timer.start()
            self.progress_slider.setEnabled(True)

    def stop_video(self):
        """ Arrête et décharge la vidéo. """
        self.player.stop()
        self.media = None
        self.play_pause_button.setText("▶️ Lire")
        self.timer.stop()
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.time_label.setText("00:00 / 00:00")

    def capture_screenshot(self):
        """ Capture un screenshot de la vidéo. """
        capture_dir = "captures"
        if not os.path.exists(capture_dir):
            os.makedirs(capture_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_path = os.path.join(capture_dir, f"capture_{timestamp}.png")

        if self.player.video_take_snapshot(0, capture_path, 0, 0):
            print(f" Capture enregistrée : {capture_path}")
        else:
            print(" Erreur lors de la capture d'écran")

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