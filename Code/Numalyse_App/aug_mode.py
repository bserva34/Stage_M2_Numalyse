from PySide6.QtCore import QObject, QTimer

class AugMode(QObject):
    def __init__(self, vlc_player, seg, path):
        super().__init__()  # Important pour initialiser QObject
        self.vlc_widget = vlc_player
        self.seg = seg
        self.path_of_super = path

        self.path_of_video = self.vlc_widget.path_of_media
        self.timecodes = [btn_data["time"] for btn_data in self.seg.stock_button]

        self.start()

        self.timer = QTimer(self)  # Maintenant, self est un QObject valide
        self.timer.timeout.connect(self.update)
        self.timer.start(10)  # Mise à jour toutes les 10 ms

    def start(self):
        #self.vlc_widget.stop_video(False)
        self.vlc_widget.load_video(self.path_of_super, False)

    def update(self):
        acc = self.vlc_widget.player.get_time()
        for val in self.timecodes:  # Correction : ajouter self.
            if abs(val - acc) < 10:
                self.vlc_widget.pause_video()

    def exit_aug(self):
        self.vlc_widget.load_video(self.path_of_video, False)
