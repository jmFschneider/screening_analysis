import cv2
import numpy as np
import os
import glob
import tkinter as tk
from tkinter import filedialog

def find_verso_path(r_path):
    """Devine le chemin du fichier Verso à partir du Recto"""
    directory, filename = os.path.split(r_path)
    name, ext = os.path.splitext(filename)
    
    # Stratégies de remplacement R -> V
    candidates = []
    
    # 1. Remplacement simple du dernier caractère R par V dans le nom
    if "R" in name:
        head, sep, tail = name.rpartition("R")
        candidates.append(head + "V" + tail + ext)
    if "r" in name:
        head, sep, tail = name.rpartition("r")
        candidates.append(head + "v" + tail + ext)
        
    # 2. Remplacement barbare (si le nom est simple)
    candidates.append(filename.replace("R", "V").replace("r", "v"))

    for c in candidates:
        v_path = os.path.join(directory, c)
        if os.path.exists(v_path) and v_path != r_path:
            return v_path
            
    return None

def resize_to_width(img, target_width):
    """Redimensionne une image en gardant le ratio pour atteindre une largeur cible"""
    h, w = img.shape[:2]
    scale = target_width / w
    new_h = int(h * scale)
    return cv2.resize(img, (target_width, new_h), interpolation=cv2.INTER_AREA)

def main():
    print("--- Fusion Verticale Recto/Verso ---")
    
    root = tk.Tk()
    root.withdraw()

    # 1. Sélection Dossier
    print("Sélectionnez le dossier contenant les paires (ex: TRI_ANCIEN)...")
    source_dir = filedialog.askdirectory()
    if not source_dir: return

    # 2. Dossier Sortie
    dest_dir = os.path.join(source_dir, "FUSIONNES")
    os.makedirs(dest_dir, exist_ok=True)

    # 3. Listing
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(source_dir, ext)))

    count = 0
    
    for r_path in files:
        filename = os.path.basename(r_path)
        
        # On ne traite que les RECTO comme point de départ
        if "R" not in filename.upper(): continue
        
        print(f"Traitement : {filename} ... ", end="")
        
        # Trouver le Verso
        v_path = find_verso_path(r_path)
        
        if not v_path:
            print("Verso introuvable (Ignoré)")
            continue

        # Lecture
        img_r = cv2.imread(r_path)
        img_v = cv2.imread(v_path)

        if img_r is None or img_v is None:
            print("Erreur lecture image.")
            continue

        # Mise à l'échelle du Verso pour matcher la largeur du Recto
        # (Esthétique indispensable pour la fusion verticale)
        target_width = img_r.shape[1]
        img_v_resized = resize_to_width(img_v, target_width)

        # Création d'une barre de séparation blanche (20 pixels)
        separator = np.full((20, target_width, 3), 255, dtype=np.uint8)

        # Fusion Verticale (Recto / Séparateur / Verso)
        try:
            combined = cv2.vconcat([img_r, separator, img_v_resized])
            
            # Sauvegarde
            out_name = filename.replace("R", "COMPLET").replace("r", "COMPLET")
            # Si le replace n'a pas marché (pas de R), on suffixe
            if out_name == filename:
                out_name = os.path.splitext(filename)[0] + "_COMPLET.jpg"
                
            out_path = os.path.join(dest_dir, out_name)
            cv2.imwrite(out_path, combined)
            
            print("OK -> FUSIONNES")
            count += 1
            
        except Exception as e:
            print(f"Erreur fusion : {e}")

    print("\n" + "="*30)
    print(f"Terminé ! {count} fiches fusionnées.")
    print(f"Disponibles dans : {dest_dir}")

if __name__ == "__main__":
    main()
