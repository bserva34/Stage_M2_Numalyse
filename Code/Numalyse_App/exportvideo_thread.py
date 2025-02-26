from PySide6.QtCore import QThread, Signal

class ExportVideoThread(QThread):
    segmentation_done = Signal()  # Signal émis à la fin

    def __init__(self, export_manager):
        super().__init__()
        self.export_manager = export_manager
        self.running = True  # Flag de contrôle

    def run(self):
        try:
            self.export_manager.export_video(callback=self.check_stop)
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
