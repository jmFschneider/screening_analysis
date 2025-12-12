import cv2
import numpy as np
import json
import os
import shutil
import glob
import matplotlib.pyplot as plt

# Tentative d'import de PyMuPDF pour l'extraction PDF
try:
    import fitz
except ImportError:
    fitz = None

# =============================================================================
# OUTILS COMMUNS & TRI
# =============================================================================

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
    except Exception:
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
    # Désactiver l'affichage interactif
    plt.ioff()
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
    try:
        fig.savefig(output_path)
    except:
        pass
    plt.close(fig)

def handle_verso_copy(filename, source_dir, dest_dir):
    """Cherche et copie le fichier Verso associé"""
    potential_names = []
    potential_names.append(filename.replace("R", "V").replace("r", "v"))
    if "R" in filename:
        head, sep, tail = filename.rpartition("R")
        potential_names.append(head + "V" + tail)
    if "r" in filename:
        head, sep, tail = filename.rpartition("r")
        potential_names.append(head + "v" + tail)
        
    for v_name in potential_names:
        if v_name == filename: continue
        v_path = os.path.join(source_dir, v_name)
        if os.path.exists(v_path):
            try:
                shutil.copy2(v_path, os.path.join(dest_dir, v_name))
                return True
            except:
                pass
    return False

# =============================================================================
# OUTILS FUSION & CROP
# =============================================================================

def find_vertical_split_line(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    v_projection = np.sum(binary, axis=0)
    
    start_x = int(w * 0.3)
    end_x = int(w * 0.7)
    center_proj = v_projection[start_x:end_x]
    
    if len(center_proj) == 0: return w // 2
    max_idx = np.argmax(center_proj)
    return start_x + max_idx

def crop_content(img):
    h, w = img.shape[:2]
    split_x = find_vertical_split_line(img)
    width_left = split_x
    width_right = w - split_x
    if width_left > width_right:
        return img[:, :split_x]
    else:
        return img[:, split_x:]

def pad_to_width(img, target_width):
    h, w = img.shape[:2]
    if w >= target_width: return img
    delta = target_width - w
    left = delta // 2
    right = delta - left
    return cv2.copyMakeBorder(img, 0, 0, left, right, cv2.BORDER_CONSTANT, value=[255, 255, 255])

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

# =============================================================================
# FONCTIONS PRINCIPALES (CALLABLES)
# =============================================================================

def run_sorting_logic(source_dir, json_path, progress_callback=None):
    """
    Exécute le tri (V3).
    progress_callback(msg) : fonction pour renvoyer des logs texte.
    Retourne: un dictionnaire avec les chemins des dossiers créés.
    """
    if progress_callback: progress_callback("Chargement des références...")
    refs = load_references(json_path)
    target_size = refs["target_size"]

    dest_old = os.path.join(source_dir, "TRI_ANCIEN")
    dest_new = os.path.join(source_dir, "TRI_NOUVEAU")
    dest_unsure = os.path.join(source_dir, "TRI_INCERTAIN")

    for d in [dest_old, dest_new, dest_unsure]:
        os.makedirs(d, exist_ok=True)

    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(source_dir, ext)))
    
    if progress_callback: progress_callback(f"{len(files)} fichiers trouvés. Début analyse...")

    count_old, count_new, count_unsure = 0, 0, 0

    for f_path in files:
        filename = os.path.basename(f_path)
        if "R" not in filename.upper(): continue

        h_prof, v_prof = get_image_profiles(f_path, target_size)
        if h_prof is None: continue

        score_old_h = compare_profiles_robust(h_prof, refs["old"]["h_mean"])
        score_old_v = compare_profiles_robust(v_prof, refs["old"]["v_mean"])
        score_old = (score_old_h + score_old_v) / 2

        score_new_h = compare_profiles_robust(h_prof, refs["new"]["h_mean"])
        score_new_v = compare_profiles_robust(v_prof, refs["new"]["v_mean"])
        score_new = (score_new_h + score_new_v) / 2
        
        diff = score_old - score_new
        confidence_threshold = 0.05 
        
        target_dest = None
        
        if score_old > score_new and diff > confidence_threshold:
            target_dest = dest_old
            count_old += 1
            log_msg = f"-> ANCIEN ({filename})"
        elif score_new > score_old and abs(diff) > confidence_threshold:
            target_dest = dest_new
            count_new += 1
            log_msg = f"-> NOUVEAU ({filename})"
        else:
            target_dest = dest_unsure
            debug_name = os.path.splitext(filename)[0] + "_DEBUG.png"
            save_debug_plot(os.path.join(dest_unsure, debug_name), filename, h_prof, v_prof, refs)
            count_unsure += 1
            log_msg = f"-> INCERTAIN ({filename})"

        if progress_callback: progress_callback(log_msg)

        shutil.copy2(f_path, os.path.join(target_dest, filename))
        handle_verso_copy(filename, source_dir, target_dest)

    if progress_callback:
        progress_callback("--- Terminé ---")
        progress_callback(f"Anciennes: {count_old} | Nouvelles: {count_new} | Incertaines: {count_unsure}")

    return {"old": dest_old, "new": dest_new, "unsure": dest_unsure}

def run_fusion_logic(source_dir, crop_verso=False, progress_callback=None):
    """
    Exécute la fusion (Cropped/Full).
    """
    suffix = "_CROPPED" if crop_verso else "_FULL"
    dest_dir = os.path.join(source_dir, f"FUSION{suffix}")
    os.makedirs(dest_dir, exist_ok=True)

    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(source_dir, ext)))

    if progress_callback: progress_callback(f"Fusion dans {os.path.basename(dest_dir)}...")
    
    count = 0
    for r_path in files:
        filename = os.path.basename(r_path)
        if "R" not in filename.upper(): continue
        
        v_path = find_verso_path(r_path)
        if not v_path: continue

        img_r = cv2.imread(r_path)
        img_v = cv2.imread(v_path)
        if img_r is None or img_v is None: continue

        # Recto toujours entier
        part_r = img_r
        
        # Verso selon option
        if crop_verso:
            part_v = crop_content(img_v)
        else:
            part_v = img_v
        
        target_width = max(part_r.shape[1], part_v.shape[1])
        final_r = pad_to_width(part_r, target_width)
        final_v = pad_to_width(part_v, target_width)
        
        separator = np.full((30, target_width, 3), 255, dtype=np.uint8)

        try:
            combined = cv2.vconcat([final_r, separator, final_v])
            out_name = filename.replace("R", "FINAL").replace("r", "FINAL")
            if out_name == filename: out_name = os.path.splitext(filename)[0] + "_FINAL.jpg"
            cv2.imwrite(os.path.join(dest_dir, out_name), combined)
            count += 1
            if progress_callback: progress_callback(f"Fusionné: {out_name}")
        except Exception as e:
            if progress_callback: progress_callback(f"Erreur {filename}: {e}")

    if progress_callback: progress_callback(f"Terminé. {count} images générées.")
    return dest_dir

# =============================================================================
# OUTILS PRÉPARATION (PDF & REFERENTIEL)
# =============================================================================

def extract_images_from_pdf(pdf_path, output_dir, dpi=200, progress_callback=None):
    """
    Extrait chaque page du PDF en image JPEG.
    Nécessite la librairie PyMuPDF (fitz).
    """
    if fitz is None:
        raise ImportError("La librairie 'PyMuPDF' (fitz) est requise. Installez-la via 'pip install pymupdf'.")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        doc = fitz.open(pdf_path)
        total = len(doc)
        if progress_callback: progress_callback(f"Ouverture PDF : {total} pages détectées.")

        for i, page in enumerate(doc):
            # Rendu de la page en image (Pixmap)
            pix = page.get_pixmap(dpi=dpi)
            
            # Nom de fichier : page_001.jpg
            out_name = f"page_{i+1:03d}.jpg"
            out_path = os.path.join(output_dir, out_name)
            
            pix.save(out_path)
            
            if progress_callback and i % 5 == 0:
                progress_callback(f"Extraction page {i+1}/{total}...")
        
        if progress_callback: progress_callback("Extraction terminée avec succès.")
        return True

    except Exception as e:
        if progress_callback: progress_callback(f"Erreur extraction : {e}")
        raise e

def _compute_folder_stats(folder_path, target_size=(800, 1000), limit=50):
    """Helper pour calculer les stats d'un dossier (Moyenne/Std des profils)"""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.bmp']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder_path, ext)))
    
    files = sorted(files)[:limit]
    if not files: return None

    h_profiles = []
    v_profiles = []
    
    for f_path in files:
        try:
            img = cv2.imread(f_path)
            if img is None: continue
            
            # Normalisation stricte
            img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            h_prof = np.sum(binary, axis=1)
            v_prof = np.sum(binary, axis=0)
            
            if h_prof.max() > 0: h_prof = h_prof / h_prof.max()
            if v_prof.max() > 0: v_prof = v_prof / v_prof.max()
            
            h_profiles.append(h_prof)
            v_profiles.append(v_prof)
        except:
            pass
            
    if not h_profiles: return None
    
    return {
        'h_mean': np.mean(h_profiles, axis=0).tolist(),
        'h_std': np.std(h_profiles, axis=0).tolist(),
        'v_mean': np.mean(v_profiles, axis=0).tolist(),
        'v_std': np.std(v_profiles, axis=0).tolist()
    }

def generate_reference_profile(folder_old, folder_new, output_json, progress_callback=None):
    """
    Crée le fichier JSON de référence à partir de deux dossiers d'exemples.
    """
    target_size = (800, 1000)
    
    if progress_callback: progress_callback("Analyse du groupe ANCIEN...")
    stats_old = _compute_folder_stats(folder_old, target_size)
    if not stats_old: raise ValueError("Aucune image valide trouvée dans le dossier ANCIEN.")

    if progress_callback: progress_callback("Analyse du groupe NOUVEAU...")
    stats_new = _compute_folder_stats(folder_new, target_size)
    if not stats_new: raise ValueError("Aucune image valide trouvée dans le dossier NOUVEAU.")
    
    export_data = {
        "target_size": target_size,
        "old": stats_old,
        "new": stats_new
    }
    
    if progress_callback: progress_callback(f"Sauvegarde dans {os.path.basename(output_json)}...")
    with open(output_json, "w") as f:
        json.dump(export_data, f)
        
    return True
