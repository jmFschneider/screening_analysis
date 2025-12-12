import cv2
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def select_file(title):
    root = tk.Tk()
    root.withdraw() # Cacher la fenêtre principale
    file_path = filedialog.askopenfilename(title=title, filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.tif;*.bmp")])
    root.destroy()
    return file_path

def calculate_profiles(img_bgr):
    """Calcule les profils de projection (Y et X)"""
    
    # 1. Préparation
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    # Binarisation inversée (Texte = Blanc, Fond = Noir)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 2. Projection Horizontale (Structure des LIGNES - Axe Y)
    h_projection = np.sum(binary, axis=1) # Somme sur les lignes
    if h_projection.max() > 0:
        h_projection = h_projection / h_projection.max()

    # 3. Projection Verticale (Structure des COLONNES - Axe X)
    v_projection = np.sum(binary, axis=0) # Somme sur les colonnes
    if v_projection.max() > 0:
        v_projection = v_projection / v_projection.max()

    return h_projection, v_projection

def main():
    print("--- Diagnostic Comparatif de Fiches (Structure X & Y) ---")
    
    # 1. Sélection des fichiers
    print("Veuillez sélectionner une ANCIENNE fiche...")
    path_old = select_file("Sélectionnez une ANCIENNE fiche (Type 32)")
    if not path_old: return

    print("Veuillez sélectionner une NOUVELLE fiche...")
    path_new = select_file("Sélectionnez une NOUVELLE fiche (Type 47)")
    if not path_new: return

    # 2. Chargement
    img_old = cv2.imread(path_old)
    img_new = cv2.imread(path_new)

    if img_old is None or img_new is None:
        print("Erreur de chargement des images.")
        return

    # --- Normalisation des tailles (Strict) ---
    # On force une taille standard pour aligner les courbes X et Y
    target_size = (800, 1000) # Largeur, Hauteur
    
    print(f"Redimensionnement forcé à {target_size}px pour alignement strict...")
    img_old = cv2.resize(img_old, target_size, interpolation=cv2.INTER_AREA)
    img_new = cv2.resize(img_new, target_size, interpolation=cv2.INTER_AREA)
    # -------------------------------------------

    # 3. Calculs
    print("Analyse en cours...")
    h_proj_old, v_proj_old = calculate_profiles(img_old)
    h_proj_new, v_proj_new = calculate_profiles(img_new)

    # 4. Affichage Graphique
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(f"Diagnostic Structurel (X et Y)\nAncienne vs Nouvelle", fontsize=14)

    # --- Ligne 1 : Images ---
    ax1 = plt.subplot(2, 2, 1)
    ax1.imshow(cv2.cvtColor(img_old, cv2.COLOR_BGR2RGB))
    ax1.set_title("Ancienne Fiche (Redimensionnée)")
    ax1.axis('off')

    ax2 = plt.subplot(2, 2, 2)
    ax2.imshow(cv2.cvtColor(img_new, cv2.COLOR_BGR2RGB))
    ax2.set_title("Nouvelle Fiche (Redimensionnée)")
    ax2.axis('off')

    # --- Ligne 2 Gauche : Structure Lignes (Axe Y) ---
    ax_y = plt.subplot(2, 2, 3)
    y_axis = np.arange(len(h_proj_old))
    ax_y.plot(h_proj_old, y_axis, color='red', label='Ancienne', alpha=0.8)
    ax_y.plot(h_proj_new, y_axis, color='blue', label='Nouvelle', alpha=0.8)
    ax_y.invert_yaxis() # 0 en haut
    ax_y.set_title("Structure Verticale (Lignes/Paragraphes)")
    ax_y.set_xlabel("Densité")
    ax_y.set_ylabel("Position Y (Haut -> Bas)")
    ax_y.legend()
    ax_y.grid(True, alpha=0.3)

    # --- Ligne 2 Droite : Structure Colonnes (Axe X) ---
    ax_x = plt.subplot(2, 2, 4)
    x_axis = np.arange(len(v_proj_old))
    ax_x.plot(x_axis, v_proj_old, color='red', label='Ancienne', alpha=0.8)
    ax_x.plot(x_axis, v_proj_new, color='blue', label='Nouvelle', alpha=0.8)
    ax_x.set_title("Structure Horizontale (Colonnes/Marges)")
    ax_x.set_xlabel("Position X (Gauche -> Droite)")
    ax_x.set_ylabel("Densité")
    ax_x.legend()
    ax_x.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
