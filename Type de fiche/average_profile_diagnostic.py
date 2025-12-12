import cv2
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import tkinter as tk
from tkinter import filedialog
import json

# Configuration
TARGET_SIZE = (800, 1000) # Largeur, Hauteur

def load_and_process_folder(folder_path, label, limit=20):
    """Charge les images d'un dossier et calcule les profils moyens"""
    print(f"--- Traitement du groupe : {label} ---")
    
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.bmp']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    # On limite le nombre pour que ça ne soit pas trop long
    files = sorted(files)[:limit]
    
    if not files:
        print(f"Aucune image trouvée dans {folder_path}")
        return None

    h_profiles = []
    v_profiles = []
    
    count = 0
    for f_path in files:
        try:
            img = cv2.imread(f_path)
            if img is None: continue
            
            # 1. Normalisation taille
            img = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_AREA)
            
            # 2. Prétraitement
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # 3. Projections
            # Axe Y (Lignes)
            h_prof = np.sum(binary, axis=1)
            # Axe X (Colonnes)
            v_prof = np.sum(binary, axis=0)
            
            # Normalisation individuelle (0-1) pour éviter qu'une page très noire écrase les autres
            if h_prof.max() > 0: h_prof = h_prof / h_prof.max()
            if v_prof.max() > 0: v_prof = v_prof / v_prof.max()
            
            h_profiles.append(h_prof)
            v_profiles.append(v_prof)
            count += 1
            print(f"  - {os.path.basename(f_path)} OK")
            
        except Exception as e:
            print(f"  - Erreur sur {os.path.basename(f_path)}: {e}")

    if count == 0:
        return None
        
    # Calcul des statistiques (Moyenne et Ecart-Type)
    stats = {
        'h_mean': np.mean(h_profiles, axis=0),
        'h_std': np.std(h_profiles, axis=0),
        'v_mean': np.mean(v_profiles, axis=0),
        'v_std': np.std(v_profiles, axis=0),
        'count': count,
        'label': label
    }
    return stats

def main():
    print("--- Générateur de Profil Moyen (Gabarit) ---")
    
    root = tk.Tk()
    root.withdraw()

    # 1. Sélection Dossiers
    print("Sélectionnez le dossier des ANCIENNES fiches...")
    dir_old = filedialog.askdirectory(title="Dossier ANCIENNES Fiches (Groupe A)")
    if not dir_old: return

    print("Sélectionnez le dossier des NOUVELLES fiches...")
    dir_new = filedialog.askdirectory(title="Dossier NOUVELLES Fiches (Groupe B)")
    if not dir_new: return
    
    root.destroy()

    # 2. Calculs
    stats_old = load_and_process_folder(dir_old, "Anciennes", limit=50)
    stats_new = load_and_process_folder(dir_new, "Nouvelles", limit=50)

    if not stats_old or not stats_new:
        print("Erreur: Impossible de calculer les statistiques (dossiers vides ?).")
        return

    # 3. Affichage
    fig, (ax_y, ax_x) = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle(f"Comparaison des Profils Moyens (sur {stats_old['count']} vs {stats_new['count']} images)", fontsize=16)

    # --- Graphique 1 : Structure Verticale (Lignes - Axe Y) ---
    y_axis = np.arange(len(stats_old['h_mean']))
    
    # Old (Rouge)
    ax_y.plot(stats_old['h_mean'], y_axis, color='red', label='Anciennes (Moyenne)', linewidth=2)
    ax_y.fill_betweenx(y_axis, 
                       stats_old['h_mean'] - stats_old['h_std'], 
                       stats_old['h_mean'] + stats_old['h_std'], 
                       color='red', alpha=0.2, label='Variation (Std)')
    
    # New (Bleu)
    ax_y.plot(stats_new['h_mean'], y_axis, color='blue', label='Nouvelles (Moyenne)', linewidth=2)
    ax_y.fill_betweenx(y_axis, 
                       stats_new['h_mean'] - stats_new['h_std'], 
                       stats_new['h_mean'] + stats_new['h_std'], 
                       color='blue', alpha=0.2, label='Variation (Std)')

    ax_y.invert_yaxis()
    ax_y.set_title("Structure Verticale (Lignes/Paragraphes)")
    ax_y.set_ylabel("Position Y (Haut -> Bas)")
    ax_y.set_xlabel("Densité Moyenne")
    ax_y.legend()
    ax_y.grid(True, alpha=0.3)

    # --- Graphique 2 : Structure Horizontale (Colonnes - Axe X) ---
    x_axis = np.arange(len(stats_old['v_mean']))
    
    # Old (Rouge)
    ax_x.plot(x_axis, stats_old['v_mean'], color='red', label='Anciennes', linewidth=2)
    ax_x.fill_between(x_axis, 
                      stats_old['v_mean'] - stats_old['v_std'], 
                      stats_old['v_mean'] + stats_old['v_std'], 
                      color='red', alpha=0.2)
    
    # New (Bleu)
    ax_x.plot(x_axis, stats_new['v_mean'], color='blue', label='Nouvelles', linewidth=2)
    ax_x.fill_between(x_axis, 
                      stats_new['v_mean'] - stats_new['v_std'], 
                      stats_new['v_mean'] + stats_new['v_std'], 
                      color='blue', alpha=0.2)

    ax_x.set_title("Structure Horizontale (Colonnes/Marges)")
    ax_x.set_xlabel("Position X (Gauche -> Droite)")
    ax_x.legend()
    ax_x.grid(True, alpha=0.3)

    plt.tight_layout()
    
    # --- SAUVEGARDE ---
    # 1. Sauvegarde de l'image du graphique
    plot_filename = "comparaison_profils.png"
    fig.savefig(plot_filename)
    print(f"\n[Succès] Graphique sauvegardé sous : {plot_filename}")

    # 2. Sauvegarde des données (Gabarits) pour le tri automatique
    json_filename = "reference_profiles.json"
    
    # On prépare les données (conversion numpy -> list pour le JSON)
    export_data = {
        "target_size": TARGET_SIZE,
        "old": {
            "h_mean": stats_old['h_mean'].tolist(),
            "h_std": stats_old['h_std'].tolist(),
            "v_mean": stats_old['v_mean'].tolist(),
            "v_std": stats_old['v_std'].tolist()
        },
        "new": {
            "h_mean": stats_new['h_mean'].tolist(),
            "h_std": stats_new['h_std'].tolist(),
            "v_mean": stats_new['v_mean'].tolist(),
            "v_std": stats_new['v_std'].tolist()
        }
    }
    
    with open(json_filename, "w") as f:
        json.dump(export_data, f)
        
    print(f"[Succès] Profils de référence sauvegardés sous : {json_filename}")
    print("Vous pouvez maintenant utiliser ce fichier pour lancer le tri automatique.")

    plt.show()

if __name__ == "__main__":
    main()
