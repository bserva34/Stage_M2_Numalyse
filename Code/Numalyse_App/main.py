import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtCore import Qt
from main_window import VLCMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName("SLV")
    app.setWindowIcon(QIcon("icon/icon3.ico"))

    # app.setStyle("Fusion")

    # palette = QPalette()
    # palette.setColor(QPalette.Window, Qt.black)
    # palette.setColor(QPalette.WindowText, Qt.white)
    # palette.setColor(QPalette.Base, Qt.black)
    # palette.setColor(QPalette.AlternateBase, Qt.gray)
    # palette.setColor(QPalette.ToolTipBase, Qt.black)
    # palette.setColor(QPalette.ToolTipText, Qt.white)
    # palette.setColor(QPalette.Text, Qt.white)
    # palette.setColor(QPalette.Button, Qt.darkGray)
    # palette.setColor(QPalette.ButtonText, Qt.white)
    # palette.setColor(QPalette.BrightText, Qt.red)
    # palette.setColor(QPalette.Highlight, Qt.blue)
    # palette.setColor(QPalette.HighlightedText, Qt.black)

    # app.setPalette(palette)

    window = VLCMainWindow()
    window.show()
    sys.exit(app.exec())



# pyinstaller --name "SLV" --windowed --icon=icon/icon3.ico --exclude PyQt5 --exclude PyQt6 --onefile \
# --add-binary "/usr/lib/x86_64-linux-gnu/libvlc.so:." \
# --add-binary "/usr/lib/x86_64-linux-gnu/libvlccore.so.9:." main.py


#pyinstaller -w --add-binary "C:\Program Files\VideoLAN\VLC\libvlc.dll;." main.py

#penser à intégrer le plugin vlc dans le dossier
#--add-binary "C:\\Program Files\\VideoLAN\\VLC\\libvlccore.dll;." à tester avec
#-w pour normalement enlever le terminal

#windows slv_installeur inno_setup
#pyinstaller --name "SLV" --icon=icon/icon3.ico -w --add-data "icon;icon" --add-binary "C:\ffmpeg\bin\ffmpeg.exe;." --add-binary "C:\Program Files\VideoLAN\VLC\libvlc.dll;." main.py
#--add-binary "C:\ffmpeg\bin\ffmpeg.exe;."
#--add-binary "C:\Users\33652\AppData\Local\Programs\Python\Python310\python310.dll;."


#linux ne fonctionne pas
#pyinstaller --name "SLV" --icon=icon/icon3.ico -w --exclude PyQt5 --exclude PyQt6 --add-binary "/usr/lib/x86_64-linux-gnu/libvlc.so:." main.py

