from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QKeySequence, QShortcut

class AugMode(QObject):
    def __init__(self, vlc_player, seg, path, callback=None):
        super().__init__()
        self.vlc_widget = vlc_player
        self.seg = seg
        self.path_of_super = path

        self.path_of_video = self.vlc_widget.path_of_media
        self.timecodes = sorted([btn_data["time"] for btn_data in self.seg.display.stock_button])  # Tri pour éviter les erreurs

        self.paused = False  # Évite les pauses répétées

        self.callback = callback

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)  # Exécution toutes les 5 ms

        self.start()

    def start(self):
        self.vlc_widget.load_video(self.path_of_super, False)


    def update(self):
        if self.vlc_widget.player.get_state() == 6:  # Détection de la fin de la vidéo
            self.end()
            return

        acc = self.vlc_widget.player.get_time()  
        if self.timecodes and acc >= self.timecodes[0]:
            if not self.paused:
                if abs(acc-self.timecodes[0])<200:
                    self.vlc_widget.pause_video()
                    self.paused = True
                self.timecodes.pop(0)  # Supprime le timecode détecté

        if(self.paused and self.vlc_widget.player.is_playing()):
            self.paused=False
                
    def exit_aug(self):
        self.vlc_widget.load_video(self.path_of_video, False)
        self.paused = False

    def end(self):
        if self.callback:
            self.callback()
