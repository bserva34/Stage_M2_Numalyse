import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from main_window import VLCMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName("SLV")
    app.setWindowIcon(QIcon("icon2.png"))

    window = VLCMainWindow()
    window.show()
    sys.exit(app.exec())



#pyinstaller --name "MonLogiciel" --windowed --icon=icon.ico main.py
