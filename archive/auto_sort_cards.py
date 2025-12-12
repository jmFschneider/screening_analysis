import cv2
import numpy as np
import json
import os
import shutil
import glob
import tkinter as tk
from tkinter import filedialog

def load_references(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Convertir les listes en numpy arrays pour les calculs
    refs = {
        "target_size": tuple(data["target_size"]),
        "old": {
            "h_mean": np.array(data["old"]["h_mean"]),
            "v_mean": np.array(data["old"]["v_mean"])
        },
        "new": {
            "h_mean": np.array(data["new"]["h_mean"]),
            "v_mean": np.array(data["new"]["v_mean"])
        }
    }
    return refs

def get_image_profiles(img_path, target_size):
    """Extrait les profils d'une image donnée (même logique que le diagnostique)"""
    try:
        img = cv2.imread(img_path)
        if img is None: return None, None

        # Redimensionnement strict
        img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
        
        # Binarisation
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Projections
        h_prof = np.sum(binary, axis=1)
        v_prof = np.sum(binary, axis=0)
        
        # Normalisation (0-1)
        if h_prof.max() > 0: h_prof = h_prof / h_prof.max()
        if v_prof.max() > 0: v_prof = v_prof / v_prof.max()
        
        return h_prof, v_prof
    except Exception as e:
        print(f"Erreur lecture {img_path}: {e}")
        return None, None

def compare_profiles(prof, ref_mean):
    """
    Compare deux courbes via corrélation de Pearson.
    1.0 = identique, 0.0 = aucun rapport.
    """
    if len(prof) != len(ref_mean):
        return 0
    return np.corrcoef(prof, ref_mean)[0, 1]

def main():
    print("--- Tri Automatique de Fiches (Basé sur 'R') ---")
    
    root = tk.Tk()
    root.withdraw()

    # 1. Charger les références
    # On cherche d'abord dans le dossier courant, sinon on demande
    default_json = os.path.join("Type de fiche", "reference_profiles.json")
    
    if os.path.exists(default_json):
        json_path = default_json
        print(f"Fichier de référence trouvé : {json_path}")
    elif os.path.exists("reference_profiles.json"):
        json_path = "reference_profiles.json"
        print(f"Fichier de référence trouvé : {json_path}")
    else:
        print("Veuillez sélectionner le fichier 'reference_profiles.json'...")
        json_path = filedialog.askopenfilename(title="Où est reference_profiles.json ?", filetypes=[("JSON", "*.json")])
        if not json_path: return

    refs = load_references(json_path)
    target_size = refs["target_size"]

    # 2. Sélectionner le dossier source
    print("Sélectionnez le dossier contenant les images à trier...")
    source_dir = filedialog.askdirectory(title="Dossier Source (Images en vrac)")
    if not source_dir: return

    # 3. Préparer les dossiers de sortie
    dest_old = os.path.join(source_dir, "TRI_ANCIEN")
    dest_new = os.path.join(source_dir, "TRI_NOUVEAU")
    dest_unsure = os.path.join(source_dir, "TRI_INCERTAIN")

    for d in [dest_old, dest_new, dest_unsure]:
        os.makedirs(d, exist_ok=True)

    # 4. Traitement
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(source_dir, ext)))
    
    count_old = 0
    count_new = 0
    count_unsure = 0
    
    print(f"\nDébut du tri sur {len(files)} fichiers potentiels...")
    
    for f_path in files:
        filename = os.path.basename(f_path)
        
        # FILTRE : Uniquement les fichiers contenant "R" (ou "r")
        if "R" not in filename.upper():
            continue

        print(f"Analyse : {filename} ... ", end="")
        
        h_prof, v_prof = get_image_profiles(f_path, target_size)
        
        if h_prof is None:
            print("Erreur image.")
            continue

        # Comparaison (Score de corrélation)
        # On fait la moyenne des scores Lignes (H) et Colonnes (V)
        
        # Score vs ANCIEN
        score_old_h = compare_profiles(h_prof, refs["old"]["h_mean"])
        score_old_v = compare_profiles(v_prof, refs["old"]["v_mean"])
        score_old = (score_old_h + score_old_v) / 2

        # Score vs NOUVEAU
        score_new_h = compare_profiles(h_prof, refs["new"]["h_mean"])
        score_new_v = compare_profiles(v_prof, refs["new"]["v_mean"])
        score_new = (score_new_h + score_new_v) / 2
        
        # Décision
        diff = score_old - score_new
        
        # Seuil de confiance (si la différence est trop faible, on hésite)
        confidence_threshold = 0.05 
        
        dest = None
        if score_old > score_new and diff > confidence_threshold:
            dest = dest_old
            print(f"-> ANCIEN (Conf: {diff:.2f})")
            count_old += 1
        elif score_new > score_old and abs(diff) > confidence_threshold:
            dest = dest_new
            print(f"-> NOUVEAU (Conf: {abs(diff):.2f})")
            count_new += 1
        else:
            dest = dest_unsure
            print(f"-> INCERTAIN (Diff trop faible: {diff:.3f})")
            count_unsure += 1
            
        # Copie du fichier
        try:
            shutil.copy2(f_path, os.path.join(dest, filename))
        except Exception as e:
            print(f"Erreur copie : {e}")

    print("\n" + "="*30)
    print("BILAN DU TRI")
    print("="*30)
    print(f"Anciennes Fiches (R) : {count_old}")
    print(f"Nouvelles Fiches (R) : {count_new}")
    print(f"Incertaines        : {count_unsure}")
    print(f"Fichiers ignorés (Pas 'R') : {len(files) - (count_old + count_new + count_unsure)}")
    print(f"\nLes fichiers ont été COPIÉS dans : {source_dir}")

if __name__ == "__main__":
    main()
