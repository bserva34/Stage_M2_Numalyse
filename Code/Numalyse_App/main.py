import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from main_window import VLCMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName("SLV")
    app.setWindowIcon(QIcon("icon/icon3.ico"))

    window = VLCMainWindow()
    window.show()
    sys.exit(app.exec())



# pyinstaller --name "SLV" --windowed --icon=icon/icon3.ico --exclude PyQt5 --exclude PyQt6 --onefile \
# --add-binary "/usr/lib/x86_64-linux-gnu/libvlc.so:." \
# --add-binary "/usr/lib/x86_64-linux-gnu/libvlccore.so.9:." main.py


