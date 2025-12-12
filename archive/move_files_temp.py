import shutil
import os

source_files = [
    "compare_cards_diagnostic.py",
    "check_image_dimensions.py",
    "average_profile_diagnostic.py",
    "auto_sort_cards_v3_recto_verso.py",
    "merge_cards_cropped.py",
    "RESUME_CLASSIFICATION_FICHES.md"
]

destination_dir = r"C:\Projets\screening_analysis\Type de fiche" # r pour raw string

# Ensure the destination directory exists
os.makedirs(destination_dir, exist_ok=True)

for file_name in source_files:
    source_path = os.path.join(os.getcwd(), file_name)
    destination_path = os.path.join(destination_dir, file_name)
    
    if os.path.exists(source_path):
        print(f"Déplacement de {file_name} vers {destination_dir}...")
        try:
            shutil.move(source_path, destination_path)
            print(f"  {file_name} déplacé avec succès.")
        except Exception as e:
            print(f"  Erreur lors du déplacement de {file_name} : {e}")
    else:
        print(f"Le fichier {file_name} n'existe pas dans le répertoire actuel. Ignoré.")

print("Déplacements terminés.")
