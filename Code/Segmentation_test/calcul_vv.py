import os

def read_scenes(file_path):
    """
    Lit un fichier texte et renvoie une liste de tuples (start, end) pour chaque ligne.
    Chaque ligne est supposée contenir deux nombres séparés par un espace représentant le début et la fin d'une scène.
    """
    scenes = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    start = int(parts[0])
                    end = int(parts[1])
                    scenes.append((start, end))
                except ValueError:
                    continue  # Ignore la ligne en cas d'erreur de conversion
    return scenes

def compare_scenes(gt_scenes, pred_scenes, tolerance):
    """
    Compare les scènes ground truth et prédites.
    
    Pour chaque scène ground truth, vérifie si une scène prédite existe dont le début et la fin 
    sont dans la tolérance par rapport aux valeurs ground truth.
    Chaque scène ground truth ne peut être associée qu'une seule fois.
    
    Retourne (TP, FP, FN) :
       - TP : nombre de scènes correctement détectées (match),
       - FP : nombre de scènes prédites sans correspondance,
       - FN : nombre de scènes ground truth non trouvées.
    """
    matched_gt = set()    # Indices des scènes ground truth déjà associées
    matched_pred = set()  # Indices des scènes prédites déjà associées
    tp = 0

    for i, pred in enumerate(pred_scenes):
        for j, gt in enumerate(gt_scenes):
            if j in matched_gt:
                continue
            if abs(pred[0] - gt[0]) <= tolerance and abs(pred[1] - gt[1]) <= tolerance:
                tp += 1
                matched_gt.add(j)
                matched_pred.add(i)
                break  # On passe à la scène prédite suivante dès qu'un match est trouvé

    fp = len(pred_scenes) - len(matched_pred)
    fn = len(gt_scenes) - len(matched_gt)
    return tp, fp, fn

def compute_metrics(tp, fp, total_gt):
    """
    Calcule la précision, le rappel et le F1 score.
    La précision est définie par TP / (TP + FP).
    Le rappel (ici calculé comme TP / (nombre total de scènes ground truth)).
    Le F1 score combine la précision et le rappel.
    
    Retourne un tuple (precision, recall, f1_score) sous forme de valeurs décimales.
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / total_gt if total_gt > 0 else 0
    f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
    return precision, recall, f1_score

def evaluate_methods(ground_truth_folder, results_folder, tolerance, methods):
    """
    Pour chaque vidéo (fichier ground truth nommé "nomdevidéo.txt" dans ground_truth_folder),
    compare le fichier de vérité aux résultats générés pour chaque méthode (fichiers "nomdevidéo_méthode.txt").
    
    Affiche les métriques (TP, FP) par vidéo pour chaque méthode, et cumule les valeurs pour calculer 
    la précision, le rappel et le F1 score (les métriques finales sont affichées en pourcentage).
    """
    total_metrics = { method: {'TP': 0, 'FP': 0, 'TotalGT': 0} for method in methods }

    # Parcours des fichiers ground truth (un fichier par vidéo)
    for gt_file_name in os.listdir(ground_truth_folder):
        if not gt_file_name.endswith(".txt"):
            continue
        video_name = os.path.splitext(gt_file_name)[0]
        gt_path = os.path.join(ground_truth_folder, gt_file_name)
        gt_scenes = read_scenes(gt_path)
        total_gt_count = len(gt_scenes)
        
        for method in methods:
            #result_file_name = f"{video_name}_{method}.txt"
            result_file_name = f"{video_name}_gray_{method}.txt"
            result_path = os.path.join(results_folder, result_file_name)
            if not os.path.exists(result_path):
                print(f"Fichier résultat manquant pour {video_name} et méthode {method}")
                continue
            pred_scenes = read_scenes(result_path)
            tp, fp, fn = compare_scenes(gt_scenes, pred_scenes, tolerance)
            print(f"{video_name} - Méthode {method}: TP = {tp}, FP = {fp}, (Scènes Ground Truth = {total_gt_count})")
            total_metrics[method]['TP'] += tp
            total_metrics[method]['FP'] += fp
            total_metrics[method]['TotalGT'] += total_gt_count

    print("\n=== Métriques Totales par Méthode (en %) ===")
    for method, metrics in total_metrics.items():
        tp = metrics['TP']
        fp = metrics['FP']
        total_gt = metrics['TotalGT']
        precision, recall, f1_score = compute_metrics(tp, fp, total_gt)
        print(f"Méthode {method}:")
        print(f"  TP = {tp}, FP = {fp}, Total Scènes Ground Truth = {total_gt}")
        print(f"  Précision = {precision*100:.2f}%, Rappel = {recall*100:.2f}%, F1 Score = {f1_score*100:.2f}%\n")

if __name__ == "__main__":
    # Remplacez ces chemins par ceux de vos dossiers.
    # ground_truth_folder = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/BBC"
    # results_folder = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/BBC_gray_res"
    ground_truth_folder = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/AutoShot/annotations"
    results_folder = r"../../../../../../media/bserva34/Extreme SSD/VV_Segmentation/AutoShot_gray_res"
    
    # Tolérance en nombre de frames à considérer pour la comparaison
    tolerance = 1
    
    # Liste des méthodes à évaluer (les noms doivent correspondre aux suffixes des fichiers résultats)
    methods = [
        "AdaptiveDetector",
        "ContentDetector",
        "ThresholdDetector",
        "HistogramDetector",
        "HashDetector"
    ]
    
    evaluate_methods(ground_truth_folder, results_folder, tolerance, methods)

