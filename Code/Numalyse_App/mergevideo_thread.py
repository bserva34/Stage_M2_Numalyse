from PySide6.QtCore import QThread, Signal

class MergeVideoThread(QThread):
    segmentation_done = Signal()  # Signal émis à la fin

    def __init__(self, vlc_sync,video_paths):
        super().__init__()
        self.vlc_sync = vlc_sync
        self.video_paths=video_paths
        self.running = True  # Flag de contrôle

    def run(self):
        try:
            self.vlc_sync.merge_video(self.video_paths)
        except StopProcessingException as e:
            print("Exportation interrompue :", str(e))

        self.segmentation_done.emit()

    def check_stop(self):
        if not self.running:
            print("Interruption de la segmentation...")
            raise StopProcessingException("Segmentation interrompue par l'utilisateur.")
        return True  

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class StopProcessingException(Exception):
    pass
