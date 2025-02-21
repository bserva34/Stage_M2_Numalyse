from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QRadioButton, QLabel, QLineEdit, QDialog, QButtonGroup, QHBoxLayout, QApplication
from PySide6.QtCore import Qt

import json
import os
import cv2
import numpy as np
import tempfile

from moviepy.editor import VideoFileClip

from PIL import Image, ImageDraw, ImageFont

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate

from message_popup import MessagePopUp
from time_manager import TimeManager

class ExportManager(QWidget):
    # Définition des styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.red,
        spaceAfter=20
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.blue,
        spaceAfter=10
    )

    note_style = ParagraphStyle(
        'NoteStyle',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.black,
        leftIndent=20
    )


    def __init__(self,parent=None,vlc=None,projectmanager=None):
        super().__init__(parent)
        self.seg=parent
        self.vlc=vlc
        self.project_manager=projectmanager

        self.file_path=self.project_manager.project_path

        self.title=self.project_manager.project_name

        self.time_manager=TimeManager()

        self.configure()

    def configure(self):
        """ Ouvre une fenêtre de configuration pour choisir le mode. """
        dialog = QDialog(self)
        dialog.setWindowTitle("Exportation du Travail")

        dialog_layout = QVBoxLayout(dialog)

        # Options pour le nombre de fenêtres
        num_label = QLabel("Type d'exportation :", dialog)
        dialog_layout.addWidget(num_label)

        num_group = QButtonGroup(dialog)
        option_1 = QRadioButton("Fichier texte", dialog)
        option_2 = QRadioButton("Vidéo annoté", dialog)
        num_group.addButton(option_1)
        num_group.addButton(option_2)
        option_1.setChecked(True)

        dialog_layout.addWidget(option_1)
        dialog_layout.addWidget(option_2)

        dialog_load=QHBoxLayout()
        load=QLabel("")
        load.setStyleSheet("color: blue;")
        load.setAlignment(Qt.AlignCenter)
        dialog_load.addWidget(load)
        dialog_layout.addLayout(dialog_load)


        # Boutons OK/Annuler
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)


        def on_ok():
            if(self.file_path):
                load.setText("exportation en cours ⌛")
                QApplication.processEvents() 
                self.export_pdf() if option_1.isChecked() else self.export_video()
                affichage=MessagePopUp(self)
                dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        dialog.setLayout(dialog_layout)
        dialog.exec()

    #exporte dans la segmentation et annotations dans un fichier pdf
    def export_pdf(self):
        self.file_path = os.path.join(self.file_path, f"{self.title}.pdf")
        try:
            # Création du document PDF
            doc = SimpleDocTemplate(self.file_path, pagesize=A4)
            elements = []

            # Titre principal
            elements.append(Paragraph("Étude cinématographique", self.title_style))

            # Ajout des boutons et notes
            for btn_data in self.seg.stock_button:
                button = btn_data["button"]
                time_str = self.time_manager.m_to_mst(btn_data["time"])
                end_str = self.time_manager.m_to_mst(btn_data["end"] - btn_data["time"])

                # Titre pour chaque bouton
                elements.append(Paragraph(f"- {button.text()} -> Début : {time_str} / Durée : {end_str}", self.subtitle_style))

                # Notes associées
                for note_widget in self.seg.button_notes.get(button, []):
                    note_text = note_widget.toPlainText()
                    self.put_multiline_text(elements, note_text)

            # Génération du fichier PDF
            doc.build(elements)
            print(f"Fichier PDF enregistré : {self.file_path}")

        except Exception as e:
            print(f"Erreur lors de l'exportation PDF : {e}")


    def put_multiline_text(self, elements, text):
        lines = text.split("\n")  # Découpe par retour à la ligne
        for line in lines: 
            line = line.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")  
            elements.append(Paragraph(line, self.note_style))


    #exporte la seg dans une super vidéo sans son  
    def export_video(self):
        self.file_path = os.path.join(self.file_path, f"{self.title}.mp4")
        self.project_manager.path_of_super = self.file_path

        temp_dir = tempfile.gettempdir()
        temp_video_path = os.path.join(temp_dir, "temp_video.mp4")

        # Création de la vidéo sans audio avec OpenCV
        cap = cv2.VideoCapture(self.vlc.path_of_media)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(temp_video_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

        cpt = 0
        active_texts = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            active_texts = [btn_data for btn_data in self.seg.stock_button if btn_data["frame1"] <= cpt < btn_data["frame2"]]
            decalage = 0
            for btn_data in active_texts:
                button = btn_data["button"]
                time_str = self.time_manager.m_to_mst(btn_data["time"])
                end_str = self.time_manager.m_to_mst(btn_data["end"] - btn_data["time"])
                txt = button.text()
                txt2 = f"Debut : {time_str} / Duree : {end_str}"
                txt3 = [note_widget.toPlainText() for note_widget in self.seg.button_notes.get(button, [])]

                decalage = self.write_text_on_video(frame, txt, txt2, txt3, decalage)

            out.write(frame)
            cpt += 1

        cap.release()
        out.release()

        # Utilisation de MoviePy pour ajouter l'audio original
        video_clip = VideoFileClip(temp_video_path)
        audio_clip = VideoFileClip(self.vlc.path_of_media).audio

        final_clip = video_clip.set_audio(audio_clip)
        #final_clip = video_clip.with_audio(audio_clip)  # Remplacez set_audio par with_audio
        final_clip.write_videofile(self.file_path, codec="libx264", audio_codec="aac")

        video_clip.close()
        audio_clip.close()
        final_clip.close()

        # Suppression du fichier vidéo temporaire
        os.remove(temp_video_path)


    def write_text_on_video(self,frame,txt,txt2,txt3,decalage):
        cv2.putText(frame, txt, (50, decalage+50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, txt2, (50, decalage+80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1, cv2.LINE_AA)

        val=decalage+80
        for i, text in enumerate(txt3):
            val=decalage + 110 + (i * 20)
            self.put_multiline_text_video(frame, text, (50,val))

        return val+10


    def put_multiline_text_video(self,frame, text, position, font_scale=0.5, color=(255, 0, 0), line_spacing=15):
        lines = text.split("\n")  # Découpe par retour à la ligne
        x, y = position

        for i, line in enumerate(lines):
            cv2.putText(frame, line.replace("\t", "    "), (x, y + i * line_spacing),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv2.LINE_AA)



