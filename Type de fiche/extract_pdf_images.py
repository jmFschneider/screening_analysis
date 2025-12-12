#!/usr/bin/env python3
"""
Script pour extraire les images recto/verso des fiches d'observation PDF
"""
import os
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

def extract_pdf_images(pdf_path, output_dir):
    """
    Extrait les deux premières pages d'un PDF en tant qu'images JPEG

    Args:
        pdf_path: Chemin vers le fichier PDF
        output_dir: Répertoire de sortie pour les images
    """
    # Ouvrir le PDF
    doc = fitz.open(pdf_path)

    # Obtenir le nom du fichier sans l'extension
    pdf_name = Path(pdf_path).stem

    # S'assurer qu'il y a au moins 2 pages
    if len(doc) < 2:
        print(f"Attention: {pdf_name}.pdf a moins de 2 pages ({len(doc)} page(s))")

    # Extraire les deux premières pages
    suffixes = ["-R", "-V"]
    pages_to_extract = min(2, len(doc))

    for page_num in range(pages_to_extract):
        # Charger la page
        page = doc[page_num]

        # Convertir la page en image (300 DPI pour haute qualité)
        # zoom = 300/72 = 4.166... pour obtenir 300 DPI
        zoom = 300 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Construire le nom du fichier de sortie
        output_filename = f"{pdf_name}{suffixes[page_num]}.jpg"
        output_path = os.path.join(output_dir, output_filename)

        # Convertir le pixmap en image PIL pour la rotation
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        # Rotation de 90° dans le sens horaire (équivalent à -90°)
        img_rotated = img.rotate(-90, expand=True)

        # Sauvegarder l'image rotée
        img_rotated.save(output_path, 'JPEG', quality=95)
        print(f"Image extraite et pivotée: {output_filename}")

    # Fermer le document
    doc.close()

def main():
    # Définir les chemins
    pdf_dir = r"C:\Projets\GONM\pdf_conversion\media_300dpi\pdf"
    output_dir = r"C:\Projets\GONM\pdf_conversion\media_300dpi\jpeg"

    # Vérifier que le répertoire PDF existe
    if not os.path.exists(pdf_dir):
        print(f"Erreur: Le répertoire {pdf_dir} n'existe pas")
        return

    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)

    # Lister tous les fichiers PDF
    pdf_files = sorted([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])

    if not pdf_files:
        print(f"Aucun fichier PDF trouvé dans {pdf_dir}")
        return

    print(f"Traitement de {len(pdf_files)} fichier(s) PDF...\n")

    # Traiter chaque PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"Traitement de: {pdf_file}")
        try:
            extract_pdf_images(pdf_path, output_dir)
        except Exception as e:
            print(f"Erreur lors du traitement de {pdf_file}: {e}")
        print()

    print(f"Extraction terminée! Images sauvegardées dans: {output_dir}")

if __name__ == "__main__":
    main()
