from PySide6.QtCore import QThread, Signal

class ExportTextThread(QThread):
    segmentation_done = Signal()  # Signal émis à la fin

    def __init__(self, export_manager,option=3):
        super().__init__()
        self.export_manager = export_manager
        self.option=option
        self.running = True  # Flag de contrôle

    def run(self):
        try:
            if self.option==1:                
                self.export_manager.export_docx(callback=self.check_stop)
            elif self.option==2:
                self.export_manager.export_odt(callback=self.check_stop)
            elif self.option==3:
                self.export_manager.export_pdf(callback=self.check_stop)
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
