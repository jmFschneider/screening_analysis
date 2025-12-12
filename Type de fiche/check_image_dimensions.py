import os
import glob
import pandas as pd
from PIL import Image
import tkinter as tk
from tkinter import filedialog

def analyze_dimensions():
    print("--- Analyseur de Dimensions d'Images ---")
    
    # 1. Sélection du dossier
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Sélectionnez le dossier contenant les images (jpeg)")
    root.destroy()

    if not directory:
        print("Aucun dossier sélectionné.")
        return

    print(f"Analyse du dossier : {directory} ...")

    # 2. Récupération des fichiers
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.tif', '*.tiff', '*.bmp']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(directory, ext)))
        # Version minuscule/majuscule pour Linux/Windows parfois sensible
        files.extend(glob.glob(os.path.join(directory, ext.upper())))

    files = sorted(list(set(files))) # Doublons et tri

    if not files:
        print("Aucune image trouvée.")
        return

    # 3. Extraction des dimensions
    data = []
    print(f"{len(files)} images trouvées. Lecture des en-têtes...")

    for f_path in files:
        try:
            with Image.open(f_path) as img:
                w, h = img.size
                filename = os.path.basename(f_path)
                data.append({
                    "Fichier": filename,
                    "Largeur": w,
                    "Hauteur": h,
                    "Définition (Mpx)": round((w * h) / 1_000_000, 2),
                    "Ratio": round(w/h, 3)
                })
        except Exception as e:
            print(f"Erreur sur {os.path.basename(f_path)}: {e}")

    # 4. Analyse et Affichage
    df = pd.DataFrame(data)

    if df.empty:
        print("Aucune donnée extraite.")
        return

    print("\n" + "="*50)
    print("RÉSUMÉ DES GROUPES DE DIMENSIONS")
    print("="*50)

    # On groupe par Largeur/Hauteur pour voir les 'types' de fiches
    summary = df.groupby(['Largeur', 'Hauteur']).size().reset_index(name='Nombre d\'images')
    print(summary.to_string(index=False))

    print("\n" + "="*50)
    print("DÉTAIL (5 premiers et 5 derniers)")
    print("="*50)
    print(df[['Fichier', 'Largeur', 'Hauteur']].head(5).to_string(index=False))
    print("...")
    print(df[['Fichier', 'Largeur', 'Hauteur']].tail(5).to_string(index=False))

    # Export optionnel
    csv_path = os.path.join(directory, "dimensions_report.csv")
    df.to_csv(csv_path, index=False)
    print(f"\n[Info] Rapport complet sauvegardé dans : {csv_path}")

if __name__ == "__main__":
    analyze_dimensions()
