def compter_lignes_plan(file_path):
    """
    Affiche la première ligne (nombre de plans) et compte :
    - les lignes où le premier mot est 'plan' (insensible à la casse),
    - les lignes où ce n'est pas le cas.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lignes = f.readlines()

    if not lignes:
        print("Le fichier est vide.")
        return 0, 0, None

    premiere_ligne = lignes[0].strip()
    print(f"Nb total de plans: {premiere_ligne}")

    lignes_utiles = lignes[1:]  # Ignorer la première ligne

    nb_avec_plan = 0
    nb_sans_plan = 0

    for ligne in lignes_utiles:
        ligne = ligne.strip()
        if not ligne:
            continue  # Ignore les lignes vides

        premier_mot = ligne.split()[0].lower() if ligne.split() else ""
        if premier_mot == "plan":
            nb_avec_plan += 1
        else:
            nb_sans_plan += 1

    return nb_avec_plan, nb_sans_plan, premiere_ligne


if __name__ == "__main__":
    #chemin_fichier = r"../../../../../../media/bserva34/Extreme SSD/Segmentation/VV_adele/VV_adele.txt"
    chemin_fichier = r"../../../../../../media/bserva34/Extreme SSD/Segmentation/LaVieDAdele/LaVieDAdele.txt"
    try:
        avec_plan, sans_plan, total_plans = compter_lignes_plan(chemin_fichier)
        print(f"Nb plans ok: {avec_plan}")
        print(f"Plans manquant: {sans_plan}")
    except FileNotFoundError:
        print("Fichier non trouvé. Vérifiez le chemin et réessayez.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
