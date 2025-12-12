import cv2
import numpy as np
import json
import os
import shutil
import glob
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

plt.ioff()

def load_references(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    
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
    try:
        img = cv2.imread(img_path)
        if img is None: return None, None

        img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        h_prof = np.sum(binary, axis=1)
        v_prof = np.sum(binary, axis=0)
        
        if h_prof.max() > 0: h_prof = h_prof / h_prof.max()
        if v_prof.max() > 0: v_prof = v_prof / v_prof.max()
        
        return h_prof, v_prof
    except Exception as e:
        print(f"Erreur lecture {img_path}: {e}")
        return None, None

def compare_profiles_robust(prof, ref_mean, max_shift=30):
    best_corr = -1.0
    n = len(prof)
    
    for shift in range(-max_shift, max_shift + 1):
        if shift < 0:
            p_slice = prof[-shift:] 
            r_slice = ref_mean[:shift]
        elif shift > 0:
            p_slice = prof[:-shift]
            r_slice = ref_mean[shift:]
        else:
            p_slice = prof
            r_slice = ref_mean
            
        if len(p_slice) < n * 0.8: continue

        try:
            corr = np.corrcoef(p_slice, r_slice)[0, 1]
            if not np.isnan(corr) and corr > best_corr:
                best_corr = corr
        except:
            pass

    return max(0, best_corr)

def save_debug_plot(output_path, filename, h_prof, v_prof, refs):
    fig, (ax_h, ax_v) = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle(f"Analyse Incertitude : {filename}", fontsize=14)

    y_ax = np.arange(len(h_prof))
    ax_h.plot(h_prof, y_ax, 'k-', label='Image Incertaine', linewidth=2)
    ax_h.plot(refs['old']['h_mean'], y_ax, 'r--', label='Ref ANCIENNE', alpha=0.7)
    ax_h.plot(refs['new']['h_mean'], y_ax, 'b--', label='Ref NOUVELLE', alpha=0.7)
    ax_h.invert_yaxis()
    ax_h.set_title("Profil Vertical (Lignes)")
    ax_h.legend()

    x_ax = np.arange(len(v_prof))
    ax_v.plot(x_ax, v_prof, 'k-', label='Image Incertaine', linewidth=2)
    ax_v.plot(x_ax, refs['old']['v_mean'], 'r--', label='Ref ANCIENNE', alpha=0.7)
    ax_v.plot(x_ax, refs['new']['v_mean'], 'b--', label='Ref NOUVELLE', alpha=0.7)
    ax_v.set_title("Profil Horizontal (Colonnes)")
    
    plt.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

def handle_verso(filename, source_dir, dest_dir):
    """Cherche et copie le fichier Verso associé"""
    # Stratégie de remplacement simple
    # On remplace le dernier 'R' par 'V' ou 'r' par 'v'
    # Attention aux noms comme "Rare_Card_R.jpg" -> "Vare_Card_V.jpg"
    
    potential_names = []
    
    # Tentative 1 : Remplacement simple R->V (Risqué si le nom contient d'autres R)
    potential_names.append(filename.replace("R", "V").replace("r", "v"))
    
    # Tentative 2 : Remplacement intelligent du dernier caractère R
    if "R" in filename:
        head, sep, tail = filename.rpartition("R")
        potential_names.append(head + "V" + tail)
    if "r" in filename:
        head, sep, tail = filename.rpartition("r")
        potential_names.append(head + "v" + tail)
        
    # On teste les candidats
    copied = False
    for v_name in potential_names:
        if v_name == filename: continue # Évite de copier le fichier sur lui-même
        
        v_path = os.path.join(source_dir, v_name)
        if os.path.exists(v_path):
            try:
                shutil.copy2(v_path, os.path.join(dest_dir, v_name))
                print(f"   + Verso inclus : {v_name}")
                copied = True
                break # On a trouvé, on arrête
            except Exception as e:
                print(f"   ! Erreur copie verso : {e}")
    
    if not copied:
        # print(f"   (Pas de Verso trouvé pour {filename})")
        pass

def main():
    print("--- Tri Automatique V3 (Recto + Verso) ---")
    
    root = tk.Tk()
    root.withdraw()

    # 1. Références
    default_json = os.path.join("Type de fiche", "reference_profiles.json")
    if os.path.exists(default_json):
        json_path = default_json
    elif os.path.exists("reference_profiles.json"):
        json_path = "reference_profiles.json"
    else:
        json_path = filedialog.askopenfilename(title="Fichier reference_profiles.json", filetypes=[("JSON", "*.json")])
        if not json_path: return

    refs = load_references(json_path)
    target_size = refs["target_size"]

    # 2. Source
    print("Sélectionnez le dossier contenant les images...")
    source_dir = filedialog.askdirectory()
    if not source_dir: return

    # 3. Dossiers Sortie
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
    
    print(f"\nDébut de l'analyse robuste (+/- 30px shift)...")
    
    for f_path in files:
        filename = os.path.basename(f_path)
        # On ne traite que les RECTO pour l'analyse
        if "R" not in filename.upper(): continue

        print(f"Analyse : {filename} ... ", end="")
        
        h_prof, v_prof = get_image_profiles(f_path, target_size)
        if h_prof is None: continue

        # --- Comparaison Robuste ---
        score_old_h = compare_profiles_robust(h_prof, refs["old"]["h_mean"])
        score_old_v = compare_profiles_robust(v_prof, refs["old"]["v_mean"])
        score_old = (score_old_h + score_old_v) / 2

        score_new_h = compare_profiles_robust(h_prof, refs["new"]["h_mean"])
        score_new_v = compare_profiles_robust(v_prof, refs["new"]["v_mean"])
        score_new = (score_new_h + score_new_v) / 2
        
        diff = score_old - score_new
        confidence_threshold = 0.05 
        
        target_dest = None
        
        # --- Décision ---
        if score_old > score_new and diff > confidence_threshold:
            target_dest = dest_old
            print(f"-> ANCIEN (Conf:{diff:.2f})")
            count_old += 1
            
        elif score_new > score_old and abs(diff) > confidence_threshold:
            target_dest = dest_new
            print(f"-> NOUVEAU (Conf:{abs(diff):.2f})")
            count_new += 1
            
        else:
            # CAS INCERTAIN
            target_dest = dest_unsure
            debug_name = os.path.splitext(filename)[0] + "_DEBUG.png"
            save_debug_plot(os.path.join(dest_unsure, debug_name), filename, h_prof, v_prof, refs)
            print(f"-> INCERTAIN (Diff:{diff:.3f})")
            count_unsure += 1

        # --- Copie Recto ---
        shutil.copy2(f_path, os.path.join(target_dest, filename))
        
        # --- Gestion Verso ---
        handle_verso(filename, source_dir, target_dest)

    print("\n" + "="*30)
    print("BILAN V3 (Recto+Verso)")
    print("="*30)
    print(f"Anciennes (R) : {count_old}")
    print(f"Nouvelles (R) : {count_new}")
    print(f"Incertaines (R) : {count_unsure}")

if __name__ == "__main__":
    main()
