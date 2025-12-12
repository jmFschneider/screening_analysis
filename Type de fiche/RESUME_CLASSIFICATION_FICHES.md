# Synthèse du Projet : Classification Automatique des Fiches "Anciennes" / "Nouvelles"

## 1. Contexte et Problématique Initiale
L'objectif était de développer une méthode automatique pour différencier deux types de fiches (désignées comme "Anciennes" et "Nouvelles", correspondant aux formats 32-R/V et 47-R/V), à partir d'images JPEG issues de numérisations.

Les contraintes initiales rendant la tâche complexe étaient :
*   **Dimensions :** Supposées identiques, ce qui s'est avéré faux en pratique.
*   **Luminosité :** Non fiable, certaines fiches anciennes étant aussi claires que les nouvelles.
*   **Ordre aléatoire :** Les fiches étaient mélangées dans un même répertoire.

## 2. Démarche et Diagnostic

Nous avons procédé par étapes pour identifier les caractéristiques discriminantes :

### a. Vérification des Dimensions (Script `check_image_dimensions.py`)
*   **Observation :** Contrairement à l'attente initiale, les images présentaient une grande variabilité de dimensions. Cela a été confirmé par un script qui a analysé les largeurs et hauteurs de toutes les images du répertoire.
*   **Conclusion :** Les dimensions brutes des fichiers ne pouvaient pas servir de critère fiable pour la classification, probablement en raison des variations de rognage lors de la numérisation PDF ou de la conversion JPEG.

### b. Analyse Structurelle et Colorimétrique (Scripts `compare_cards_diagnostic.py` & `average_profile_diagnostic.py`)
Face à l'impossibilité d'utiliser les dimensions, nous nous sommes tournés vers l'analyse du **contenu structurel** des fiches.

*   **Le principe des "Profils de Projection" :** En binarisant l'image (noir et blanc) et en sommant les pixels horizontalement et verticalement, on obtient une "signature" qui représente la densité de l'encre le long des axes X et Y. Ces courbes sont des "empreintes" de la mise en page (position des lignes, paragraphes, marges, colonnes).
*   **Normalisation :** Pour comparer ces signatures, il a été crucial de redimensionner toutes les images à une taille standard (800x1000 pixels) avant l'analyse, afin de garantir un alignement parfait des profils.
*   **Profils Moyens et Robustesse :** Pour fiabiliser la méthode, nous avons développé un script (`average_profile_diagnostic.py`) permettant de calculer un "profil moyen" (gabarit) pour le groupe "Anciennes" et pour le groupe "Nouvelles", en se basant sur plusieurs images de chaque catégorie. L'écart-type de ces profils moyens a également été calculé pour évaluer la variabilité.
*   **Diagnostic Visuel :** Les scripts de diagnostic ont permis de visualiser ces profils moyens et de constater visuellement des différences claires et consistantes dans la mise en page des fiches "Anciennes" et "Nouvelles" sur les deux axes (horizontal et vertical).

## 3. Solution de Classification Automatique (Script `auto_sort_cards_v2.py`)

Basé sur les gabarits identifiés, un script de tri automatique a été développé :

### a. Fichier de Référence (`reference_profiles.json`)
*   Ce fichier est généré par le script `average_profile_diagnostic.py`.
*   Il contient les profils de projection moyens (horizontaux et verticaux) ainsi que l'écart-type de chaque catégorie ("Anciennes" et "Nouvelles"), ainsi que la taille de normalisation (`target_size`).
*   Il sert de "cerveau" au processus de tri, définissant ce qui caractérise une fiche "Ancienne" ou "Nouvelle".

### b. Logique de Tri (`auto_sort_cards_v2.py`)
1.  **Chargement des Références :** Le script charge le fichier `reference_profiles.json`.
2.  **Filtrage des Fichiers :** Il ne traite que les images dont le nom contient la lettre "R" (pour "Recto"), ignorant les autres fichiers (ex: "V" pour Verso).
3.  **Traitement des Images :** Pour chaque image "R" trouvée :
    *   Elle est lue et redimensionnée à la `target_size` définie dans le fichier de référence.
    *   Ses profils de projection (horizontal et vertical) sont calculés.
4.  **Comparaison Robuste :** Les profils de l'image sont comparés aux profils de référence "Ancien" et "Nouveau" en utilisant une méthode de corrélation robuste aux décalages (shift). Cette méthode permet de trouver le meilleur alignement entre les courbes, compensant ainsi les petites variations de cadrage du scanner.
5.  **Décision et Tri :** L'image est classée dans la catégorie (Ancienne ou Nouvelle) dont le profil correspond le mieux. Un seuil de confiance est appliqué : si la différence entre les scores "Ancien" et "Nouveau" est trop faible, l'image est placée dans un dossier "Incertain".
6.  **Dossiers de Sortie :** Les images triées sont copiées dans des sous-dossiers `TRI_ANCIEN`, `TRI_NOUVEAU` et `TRI_INCERTAIN` créés automatiquement dans le répertoire source.

### c. Outil de Débogage Intégré
*   Pour chaque image classée comme "Incertaine", le script génère un fichier `_DEBUG.png` à côté de l'image originale dans le dossier `TRI_INCERTAIN`.
*   Ce fichier superpose les profils de l'image incertaine avec les profils de référence "Ancien" et "Nouveau", permettant une analyse visuelle rapide de la raison de l'incertitude.

## 4. Résultats et Perspectives
Le système a montré une très grande efficacité (1 image incertaine sur 50 testées). L'analyse de cette image incertaine a permis de découvrir un **troisième type de fiche**, validant la robustesse du système à identifier des exceptions.

### Possibilités d'Évolution Future :
*   **Gestion du 3ème Type :** Intégrer un profil de référence pour ce "Type 3" afin d'automatiser sa classification.
*   **Traitement des "V" (Verso) :** Étendre le tri aux fiches "V" (Verso), en supposant que le Recto et le Verso de la même fiche sont du même type.
*   **Industrialisation :** Adapter le script pour traiter des volumes plus importants ou être intégré dans un workflow de traitement de documents.

Ce projet a démontré l'efficacité de l'analyse structurelle des documents numérisés pour leur classification automatique, même en présence de variabilité dans les conditions de numérisation.
