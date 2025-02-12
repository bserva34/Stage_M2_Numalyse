from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QRadioButton, QLabel, QLineEdit, QDialog, QButtonGroup, QHBoxLayout
import os
import cv2

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

        # Boutons OK/Annuler
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", dialog)
        cancel_button = QPushButton("Annuler", dialog)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        dialog_layout.addLayout(button_layout)

        def on_ok():
            if(self.file_path):
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
                elements.append(Paragraph("Étude cinématographique", title_style))

                # Ajout des boutons et notes
                for btn_data in self.seg.stock_button:
                    button = btn_data["button"]
                    time_str = self.time_manager.m_to_mst(btn_data["time"])
                    end_str = self.time_manager.m_to_mst(btn_data["end"]-btn_data["time"])
                    
                    # Titre pour chaque bouton
                    elements.append(Paragraph(f"- {button.text()} → Début : {time_str} / Durée : {end_str}", subtitle_style))

                    # Notes associées
                    for note_widget in self.seg.button_notes.get(button, []):
                        note_text = note_widget.toPlainText()
                        elements.append(Paragraph(f"{note_text}", note_style))

                # Génération du fichier PDF
                doc.build(elements)
                print(f"Fichier PDF enregistré : {self.file_path}")

            except Exception as e:
                print(f"Erreur lors de l'exportation PDF : {e}")

    #exporte la seg dans une super vidéo
    def export_video(self):
        if self.file_path:
            if not self.file_path.lower().endswith(".mp4"):
                self.file_path += ".mp4"
            print("exporte vidéo annoté")

            cap = cv2.VideoCapture(self.vlc.path_of_media)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(self.file_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))
            cpt=0
            txt=""
            while cap.isOpened():               
                
                for i in range(0,len(self.seg.stock_frame)):
                    if (self.seg.stock_frame[i][0]==cpt):
                        btn_data=self.seg.stock_button[i]
                        txt=btn_data["button"].text()
                        break

                ret, frame = cap.read()
                if not ret:
                    break   
   
                cv2.putText(frame, txt, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                            1, (0, 0, 255), 2, cv2.LINE_AA)

                out.write(frame)
                cpt+=1

            cap.release()
            out.release()

