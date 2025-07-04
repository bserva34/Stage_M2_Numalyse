import cv2

def compute_sharpness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def apply_blur_and_save(image_path):
    # Charger l'image
    image = cv2.imread(image_path)
    if image is None:
        print("Erreur : l'image n'a pas pu être chargée.")
        return

    # Niveaux de flou (taille du noyau pour le flou gaussien)
    blur_levels = {
        "light": (3, 3),
        "medium": (7, 7),
        "strong": (15, 15)
    }

    print(compute_sharpness(image))

    for level, kernel in blur_levels.items():
        blurred = cv2.GaussianBlur(image, kernel, 0)
        sharpness = compute_sharpness(blurred)
        filename = f"{level}_blur_sharpness_{sharpness:.2f}.jpg"
        cv2.imwrite(filename, blurred)
        print(f"Image enregistrée : {filename}")

# Exemple d'utilisation
apply_blur_and_save("chat.jpeg")
