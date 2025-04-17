import statistics
import numpy as np

def ms_en_hmsd(ms):
    total_secondes = ms / 1000
    heures = int(total_secondes // 3600)
    minutes = int((total_secondes % 3600) // 60)
    secondes = int(total_secondes % 60)
    dixiemes = int((ms % 1000) / 100)
    return f"{heures:02}:{minutes:02}:{secondes:02}:{dixiemes}"

def analyser_fichier(fichier, toutes_valeurs, totaux_durees, totaux_n, toutes_valeurs_associees, moyennes_associees_par_fichier):
    try:
        with open(fichier, 'r') as f:
            lignes = f.readlines()
            durees = []
            valeurs_associees = []

            for ligne in lignes:
                if "_" in ligne:
                    partie_duree, partie_associee = ligne.strip().split("_")
                    duree = float(partie_duree)
                    associee = float(partie_associee)
                    durees.append(duree)
                    valeurs_associees.append(associee)

        if not durees:
            print(f"{fichier} : Le fichier est vide ou mal formaté.")
            return

        toutes_valeurs.extend(durees)
        toutes_valeurs_associees.extend(valeurs_associees)
        total = sum(durees)
        n = len(durees)

        totaux_durees.append(total)
        totaux_n.append(n)

        moyenne = statistics.mean(durees)
        nombre_frame=sum(valeurs_associees)
        mediane = statistics.median(durees)
        ecart_type = statistics.stdev(durees) if n > 1 else 0.0
        quartiles = np.percentile(durees, [25, 50, 75])
        moyenne_associee = statistics.mean(valeurs_associees)
        moyennes_associees_par_fichier.append(nombre_frame)

        print(fichier)
        print(f"Durée totale : {ms_en_hmsd(total)}")
        print(f"Nombre total de frames : {nombre_frame}")
        print(f"Nombre de Plans : {n}")
        print(f"Moyenne : {ms_en_hmsd(moyenne)}")
        print(f"Médiane : {ms_en_hmsd(mediane)}")
        print(f"1er quartile (Q1) : {ms_en_hmsd(quartiles[0])}")
        print(f"3e quartile (Q3) : {ms_en_hmsd(quartiles[2])}")
        print(f"Écart-type : {ms_en_hmsd(ecart_type)}")
        print(f"Nombre de Frame moyen par plan: {moyenne_associee:.2f}\n")

    except FileNotFoundError:
        print(f"Le fichier '{fichier}' est introuvable.")
    except ValueError:
        print("Erreur : chaque ligne doit contenir deux nombres séparés par un underscore ('_').")

# Fichiers à analyser
fichiers = ["adele.txt", "4.txt", "fallstaff.txt", "mof.txt", "shinning.txt"]

# Données globales
toutes_valeurs = []
toutes_valeurs_associees = []
totaux_durees = []
totaux_n = []
moyennes_associees_par_fichier = []

# Analyse par fichier
for fichier in fichiers:
    analyser_fichier(fichier, toutes_valeurs, totaux_durees, totaux_n, toutes_valeurs_associees, moyennes_associees_par_fichier)

# Stats globales
if toutes_valeurs and toutes_valeurs_associees:
    moyenne_duree_par_fichier = sum(totaux_durees) / len(totaux_durees)
    moyenne_nombre_plans_par_fichier = sum(totaux_n) / len(totaux_n)
    moyenne_valeurs_associees_global = statistics.mean(toutes_valeurs_associees)
    moyenne_valeurs_associees_par_fichier = sum(moyennes_associees_par_fichier) / len(moyennes_associees_par_fichier)

    moyenne = statistics.mean(toutes_valeurs)
    mediane = statistics.median(toutes_valeurs)
    ecart_type = statistics.stdev(toutes_valeurs) if len(toutes_valeurs) > 1 else 0.0
    quartiles = np.percentile(toutes_valeurs, [25, 50, 75])

    print("=== STATISTIQUES GLOBALES MOYENNES (PAR FICHIER) ===")
    print(f"Durée moyenne d'un film : {ms_en_hmsd(moyenne_duree_par_fichier)}")
    print(f"Nombre moyen de Plans par film : {moyenne_nombre_plans_par_fichier:.2f}")
    print(f"Temps moyen d'un plan : {ms_en_hmsd(moyenne)}")
    print(f"Médiane : {ms_en_hmsd(mediane)}")
    print(f"1er quartile : {ms_en_hmsd(quartiles[0])}")
    print(f"3e quartile : {ms_en_hmsd(quartiles[2])}")
    print(f"Écart-type : {ms_en_hmsd(ecart_type)}")
    print(f"Moyenne nombres frames par plan : {moyenne_valeurs_associees_global:.2f}")
    print(f"Moyenne nombres frames totale: {moyenne_valeurs_associees_par_fichier:.2f}")
else:
    print("Aucune donnée valide trouvée dans les fichiers.")

