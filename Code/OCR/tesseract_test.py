import cv2
import pytesseract
import sys

# Définir le chemin vers Tesseract si nécessaire (Windows uniquement)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(image_path):
    try:
        # Charger l'image
        image = cv2.imread(image_path)
        if image is None:
            print("Erreur: Impossible de charger l'image.")
            return
        
        #affichage des langues dispo
        #print(pytesseract.get_languages(config=''))

        gray=image
        
        # Extraire le texte
        text = pytesseract.image_to_string(gray,lang='fra')

        cv2.imwrite('res.png', gray)
        
        # Afficher le texte extrait
        print("Texte extrait:\n", text)
    except Exception as e:
        print(f"Une erreur est survenue: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Utilisation: python script.py chemin_vers_image")
    else:
        extract_text(sys.argv[1])
