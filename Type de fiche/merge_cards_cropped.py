import cv2
import numpy as np
import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox

def find_vertical_split_line(img):
    """
    Trouve l'abscisse (X) de la ligne verticale la plus intense
    située dans la zone centrale de l'image (entre 30% et 70% de la largeur).
    """
    h, w = img.shape[:2]
    
    # Conversion gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Détection de contours verticaux (Sobel X) ou seuillage
    # Ici, on utilise un seuillage inversé car le trait est souvent noir/foncé
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Projection verticale (Somme des pixels noirs sur l'axe Y pour chaque colonne X)
    v_projection = np.sum(binary, axis=0)
    
    # On ne regarde que le centre (ex: entre 30% et 70% de la largeur)
    # pour éviter les bords de l'image
    start_x = int(w * 0.3)
    end_x = int(w * 0.7)
    
    center_proj = v_projection[start_x:end_x]
    
    if len(center_proj) == 0:
        return w // 2 # Fallback milieu
    
    # Trouver l'indice du pic maximum dans cette zone
    max_idx = np.argmax(center_proj)
    
    # Coordonnée absolue
    split_x = start_x + max_idx
    
    return split_x

def crop_content(img):
    """
    Coupe l'image à la ligne verticale détectée.
    Garde la partie la plus large (le contenu).
    """
    h, w = img.shape[:2]
    split_x = find_vertical_split_line(img)
    
    # On a deux morceaux : Gauche et Droite
    # On garde le morceau le plus large (hypothese : le contenu est plus gros que la marge)
    width_left = split_x
    width_right = w - split_x
    
    if width_left > width_right:
        # On garde la gauche
        # On retire un peu (ex: 5px) pour ne pas garder le trait noir lui-même
        return img[:, :split_x]
    else:
        # On garde la droite
        return img[:, split_x:]

def pad_to_width(img, target_width):
    """
    Ajoute des bandes blanches sur les côtés pour atteindre la largeur cible
    sans déformer l'image (Pas de resize).
    """
    h, w = img.shape[:2]
    
    if w >= target_width:
        return img
    
    delta = target_width - w
    # On centre l'image (moitié gauche, moitié droite)
    left = delta // 2
    right = delta - left
    
    # Couleur blanche
    color = [255, 255, 255]
    
    padded_img = cv2.copyMakeBorder(img, 0, 0, left, right, cv2.BORDER_CONSTANT, value=color)
    return padded_img

def find_verso_path(r_path):
    directory, filename = os.path.split(r_path)
    name, ext = os.path.splitext(filename)
    candidates = []
    if "R" in name:
        head, sep, tail = name.rpartition("R")
        candidates.append(head + "V" + tail + ext)
    if "r" in name:
        head, sep, tail = name.rpartition("r")
        candidates.append(head + "v" + tail + ext)
    candidates.append(filename.replace("R", "V").replace("r", "v"))

    for c in candidates:
        v_path = os.path.join(directory, c)
        if os.path.exists(v_path) and v_path != r_path:
            return v_path
    return None

def main():
    print("--- Fusion Recto/Verso (Universel) ---")
    
    root = tk.Tk()
    root.withdraw()

    print("Sélectionnez le dossier contenant les images (TRI_ANCIEN ou TRI_NOUVEAU)...")
    source_dir = filedialog.askdirectory()
    if not source_dir: return

    # Question sur la stratégie de découpe
    do_crop_verso = messagebox.askyesno(
        "Option de Traitement", 
        "Voulez-vous DÉCOUPER automatiquement le Verso ?\n\n"
        "- OUI : Pour les 'Nouvelles' fiches (supprime la marge).\n"
        "- NON : Pour les 'Anciennes' fiches (garde tout)."
    )
    
    suffix = "_CROPPED" if do_crop_verso else "_FULL"
    dest_dir = os.path.join(source_dir, f"FUSION{suffix}")
    os.makedirs(dest_dir, exist_ok=True)

    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(source_dir, ext)))

    count = 0
    
    for r_path in files:
        filename = os.path.basename(r_path)
        if "R" not in filename.upper(): continue
        
        print(f"Traitement : {filename} ... ", end="")
        
        v_path = find_verso_path(r_path)
        if not v_path:
            print("Verso manquant.")
            continue

        img_r = cv2.imread(r_path)
        img_v = cv2.imread(v_path)

        if img_r is None or img_v is None: continue

        # 1. Préparation des parties
        # Recto : Toujours entier
        part_r = img_r 
        
        # Verso : Découpé ou Entier selon le choix utilisateur
        if do_crop_verso:
            part_v = crop_content(img_v)
        else:
            part_v = img_v
        
        # 2. Harmonisation des largeurs (Padding)
        # On calcule la largeur max requise (le plus large impose sa loi)
        target_width = max(part_r.shape[1], part_v.shape[1])
        
        final_r = pad_to_width(part_r, target_width)
        final_v = pad_to_width(part_v, target_width)
        
        # 3. Séparateur blanc
        separator = np.full((30, target_width, 3), 255, dtype=np.uint8)

        # 4. Fusion Verticale
        try:
            combined = cv2.vconcat([final_r, separator, final_v])
            
            out_name = filename.replace("R", "FINAL").replace("r", "FINAL")
            if out_name == filename: out_name = os.path.splitext(filename)[0] + "_FINAL.jpg"
                
            cv2.imwrite(os.path.join(dest_dir, out_name), combined)
            print("OK")
            count += 1
        except Exception as e:
            print(f"Erreur: {e}")

    print("\n" + "="*30)
    print(f"Terminé : {count} fiches traitées.")
    print(f"Dossier : {dest_dir}")

if __name__ == "__main__":
    main()
