from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QMenu, QInputDialog,
    QScrollArea, QDockWidget, QLabel, QDialog, QLineEdit, QSlider, QHBoxLayout,
    QSpinBox, QTextEdit, QFrame, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsRectItem,QGraphicsItem)
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtCore import Qt, QTimer, Signal, QEvent, QRectF

import os
import json
import shutil

class ProjectManager:
    def __init__(self, sidemenu,vlc_player, file_path=None, project_name=None):
        self.seg = sidemenu
        self.vlc = vlc_player
        self.project_path = file_path
        self.project_name = project_name

        self.save_file_path=None

        self.destination_path=None

        self.video_name=None

        self.path_of_super=None


    #création du projet dossier + copie de la vidéo + fichier json
    def save_project(self):
        #copie vidéo dans le project
        pof = self.vlc.path_of_media  
        
        if not pof or not os.path.isfile(pof):
            print("Erreur : Fichier vidéo introuvable !")
            return

        self.video_name = os.path.basename(pof)
        self.destination_path = os.path.join(self.project_path, self.video_name)
        try:
            shutil.copy2(pof, self.destination_path)
            print(f"Vidéo copiée avec succès dans : {self.destination_path}")
        except Exception as e:
            print(f"Erreur lors de la copie de la vidéo : {e}")

        srt_path = os.path.splitext(pof)[0]
        srt_path = srt_path+".srt"
        if os.path.isfile(srt_path):
            srt_name=os.path.basename(srt_path)
            srt_destination = os.path.join(self.project_path,srt_name)
            try:
                shutil.copy2(srt_path, srt_destination)
            except Exception as e:
                print(f"Erreur lors de la copie du srt : {e}")


        #création fichier sauvegarde
        self.save_file_path = os.path.join(self.project_path, f"{self.project_name}.json")

        self.write_json()

    #écriture dans le fichier json
    def write_json(self):
        self.destination_path = os.path.join(self.project_path, self.video_name)
        
        if self.seg is not None:
            button_data = []
            for btn_data in self.seg.display.stock_button:
                button = btn_data["button"]
                button_info = {
                    "name": button.text(),
                    "color1": btn_data["color"].red(),
                    "color2": btn_data["color"].green(),
                    "color3": btn_data["color"].blue(),
                    "time": btn_data["time"],
                    "end": btn_data["end"],
                    "frame": btn_data["frame1"],
                    "frame_end": btn_data["frame2"],
                    "notes": [note_widget.toPlainText() for note_widget in self.seg.display.button_notes.get(button, [])]  
                }
                button_data.append(button_info)

            project_data = {
                "nom": self.project_name,
                "video": self.video_name,
                "duration": self.seg.max_time,
                "super": self.path_of_super,
                "segmentation": button_data  # Liste des boutons avec notes
            }
        else:
            project_data = {
                "nom": self.project_name,
                "video": self.video_name
            }

        try: 
            with open(self.save_file_path, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=4, ensure_ascii=False)  # UTF-8 pour éviter les problèmes d'accents
            print(f"Fichier de sauvegarde créé : {self.save_file_path}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier JSON : {e}")

    #ouverture du projet et chargement de la vidéo et séquence+annotation
    def open_project(self, project_path):
        self.project_path = project_path

        project_dir = os.path.splitext(project_path)[0] 
        self.project_name = os.path.basename(project_dir)
        
        self.save_file_path = os.path.join(project_path, f"{self.project_name}.json")

        if not os.path.isfile(self.save_file_path):
            print("Erreur : Fichier de projet introuvable !")
            return False

        try:
            with open(self.save_file_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)
            self.path_of_super=project_data.get("super")
            video_path = os.path.join(project_path,project_data.get("video"))
            self.seg.max_time = project_data.get("duration")
            self.seg.display.max_time = project_data.get("duration")
            if video_path and os.path.isfile(video_path):
                # Charger la vidéo dans VLC
                self.vlc.load_video(video_path, False)
                self.video_name = os.path.basename(video_path)
                print(f"Vidéo chargée : {video_path}")
            else:
                return False
            self.load_buttons(project_data.get("segmentation", []))

        except Exception as e:
            print(f"Erreur lors de l'ouverture du projet : {e}")
            return False
        
        return True

    #création des séquences et des annotations
    def load_buttons(self, buttons_data):
        self.seg.length=self.vlc.get_size_of_slider()
        for button_info in buttons_data:
            name = button_info.get("name", "")
            c1 = button_info.get("color1", 100)
            c2 = button_info.get("color2", 100)
            c3 = button_info.get("color3", 100)
            couleur=QColor(c1,c2,c3)
            time = button_info.get("time", 0)
            end = button_info.get("end",0)
            frame1 = button_info.get("frame",0)
            frame2 = button_info.get("frame_end",0)
            notes = button_info.get("notes", [])  # Récupérer les notes

            # Créer le bouton
            button = self.seg.add_new_button(name=name, time=time,end=end, verif=False, frame1=frame1, frame2=frame2,color=couleur)

            # Ajouter les notes associées
            for note_text in notes:
                self.seg.display.add_note(button, note_text)

