from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QRadioButton, QLabel, QLineEdit, QDialog, QButtonGroup, QHBoxLayout, QApplication
from PySide6.QtCore import Qt

from moviepy.editor import VideoFileClip

import os
import cv2
import numpy as np
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


    def __init__(self,parent=None,vlc=None):
        super().__init__(parent)
        self.seg=parent
        self.vlc=vlc

        self.file_path=None

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

        self.folder_button=QPushButton("Sélectionner l'emplacement du fichier",self)
        self.folder_button.setStyleSheet("background-color: red;")
        self.folder_button.clicked.connect(self.save_export)
        dialog_layout.addWidget(self.folder_button)

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

    #boite de dialog pour save le fichier exporter
    def save_export(self, content=""):
        if os.name == "nt":  # Windows
            default_dir = "C:/"
        else:  # Linux/Mac
            default_dir = "/"

        file_path, _ = QFileDialog.getSaveFileName(self, "Nommer le fichier texte", default_dir)

        self.file_path=file_path
        if(file_path):
            self.folder_button.setStyleSheet("background-color: green;")

    #exporte dans la segmentation et annotations dans un fichier pdf
    def export_pdf(self):
        if self.file_path:
            if not self.file_path.lower().endswith(".pdf"):
                self.file_path += ".pdf"

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
                    end_str = self.time_manager.m_to_mst(btn_data["end"]-btn_data["time"])
                    
                    # Titre pour chaque bouton
                    elements.append(Paragraph(f"- {button.text()} -> Début : {time_str} / Durée : {end_str}", self.subtitle_style))

                    # Notes associées
                    for note_widget in self.seg.button_notes.get(button, []):
                        note_text = note_widget.toPlainText()
                        #elements.append(Paragraph(f"{note_text}", self.note_style))
                        self.put_multiline_text(elements,note_text)

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
        if self.file_path:
            if not self.file_path.lower().endswith(".mp4"):
                self.file_path += ".mp4"

            temp_video_path = "temp_video.mp4"

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
                decalage=0
                for btn_data in active_texts:
                    button = btn_data["button"]
                    time_str = self.time_manager.m_to_mst(btn_data["time"])
                    end_str = self.time_manager.m_to_mst(btn_data["end"] - btn_data["time"])
                    txt = button.text()
                    txt2 = f"Debut : {time_str} / Duree : {end_str}"
                    txt3 = [note_widget.toPlainText() for note_widget in self.seg.button_notes.get(button, [])]

                    decalage=self.write_text_on_video(frame,txt,txt2,txt3,decalage)                    

                out.write(frame)
                cpt += 1

            cap.release()
            out.release()

            # Utilisation de MoviePy pour ajouter l'audio original
            video_clip = VideoFileClip(temp_video_path)
            audio_clip = VideoFileClip(self.vlc.path_of_media).audio

            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(self.file_path, codec="libx264", audio_codec="aac")

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




    # def draw_text_pil(self,frame, text, position, font_size=20, color=(255, 255, 255)):
    #     """ Affiche du texte avec accents en utilisant PIL. """
    #     pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    #     draw = ImageDraw.Draw(pil_img)

    #     try:
    #         font = ImageFont.truetype("arial.ttf", font_size)  # Remplace par une police UTF-8 valide
    #     except IOError:
    #         font = ImageFont.load_default()

    #     draw.text(position, text, font=font, fill=color)
    #     return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # def put_multiline_text(self,frame, text, position, font_size=15, color=(255, 0, 0), line_spacing=20):
    #     """ Affiche un texte multi-lignes avec support des accents. """
    #     lines = text.split("\n")
    #     x, y = position
    #     for i, line in enumerate(lines):
    #         frame = self.draw_text_pil(frame, line.replace("\t", "    "), (x, y + i * line_spacing), font_size, color)
    #     return frame

    # def export_video(self):
    #     if self.file_path:
    #         if not self.file_path.lower().endswith(".mp4"):
    #             self.file_path += ".mp4"
    #         print("Exportation de la vidéo annotée...")

    #         cap = cv2.VideoCapture(self.vlc.path_of_media)
    #         fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    #         out = cv2.VideoWriter(self.file_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))
    #         cpt = 0
    #         txt = ""
    #         txt2 = ""
    #         txt3 = []

    #         while cap.isOpened():
    #             for i in range(len(self.seg.stock_frame)):
    #                 if self.seg.stock_frame[i][0] == cpt:
    #                     btn_data = self.seg.stock_button[i]
    #                     button = btn_data["button"]
    #                     time_str = self.time_manager.m_to_mst(btn_data["time"])
    #                     end_str = self.time_manager.m_to_mst(btn_data["end"] - btn_data["time"])
    #                     txt = button.text()
    #                     txt2 = f"Début : {time_str} / Durée : {end_str}"
    #                     txt3 = [note_widget.toPlainText() for note_widget in self.seg.button_notes.get(button, [])]
    #                     break

    #             ret, frame = cap.read()
    #             if not ret:
    #                 break

    #             frame = self.draw_text_pil(frame, txt, (50, 50), 30, (0, 0, 255))  # Texte principal
    #             frame = self.draw_text_pil(frame, txt2, (50, 80), 20, (0, 255, 0))  # Infos temps

    #             for i, note in enumerate(txt3):
    #                 frame = self.put_multiline_text(frame, note, (50, 110 + (i * 30)), 15)  # Notes

    #             out.write(frame)
    #             cpt += 1

    #         cap.release()
    #         out.release()