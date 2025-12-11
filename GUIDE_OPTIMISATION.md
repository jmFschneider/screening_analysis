# Guide d'Utilisation : Fenêtre de Découverte de Zones Optimales

Ce document décrit le fonctionnement de l'interface d'optimisation ("Recherche Zones Opt.") de l'application. Cette fenêtre est dédiée à l'identification automatique des combinaisons de paramètres (recettes) qui maximisent la performance.

## 1. Principe Général
L'outil utilise un algorithme de **Bump Hunting** (basé sur des arbres de décision) pour découper l'espace des paramètres en "boîtes" (hyper-rectangles) où la moyenne de la réponse (score) est significativement plus élevée que la moyenne globale.

## 2. Description de l'Interface

L'écran est divisé en plusieurs sections :

### A. Barre Supérieure (Configuration)
*   **Optimisation pour :** Indique quelle colonne (réponse) est analysée.
*   **Bouton "Lancer la recherche" :** Exécute l'algorithme d'analyse sur les données chargées.
*   **Profondeur Arbre :** Paramètre technique (défaut: 4). Une valeur plus élevée crée des zones plus spécifiques (règles plus complexes), mais risque de capturer du bruit.
*   **Dist. Max :** Indicateur passif donnant la distance maximale théorique dans l'espace des paramètres (utile pour interpréter la colonne "Dist" des résultats).

### B. Panneau Gauche : Résultats et Sources
*   **Top Zones Prometteuses :** Tableau listant les meilleures zones identifiées.
    *   *Rank :* Rang de la zone.
    *   *Mean :* Score moyen des points inclus dans cette zone.
    *   *Count :* Nombre de points expérimentaux tombant dans cette zone.
    *   *Dist :* Distance du centre de cette zone par rapport à la meilleure zone (Zone #1). Permet de voir si une solution alternative est "proche" ou "très différente" de la meilleure solution.
*   **Source Image Test :** Permet de sélectionner un dossier contenant des images. Ces images serviront à tester visuellement les paramètres (via le bouton "Visualiser Rendu").

### C. Panneau Central : Détails et Outils
Ce panneau change en fonction de la zone ou du point sélectionné.

*   **Zone d'Information (Partagée) :**
    *   **Gauche - "Détails de la zone sélectionnée" :** Affiche les règles explicites définissant la zone (ex: `line_h_size <= 25.0`).
    *   **Droite - "Valeurs du point sélectionné" :** Affiche les valeurs exactes des paramètres lorsqu'on clique sur une ligne du graphique de coordonnées parallèles (voir section D).

*   **Graphique de Distribution :**
    *   Histogramme gris : Distribution de la performance sur *toute* la population.
    *   Trait Rouge : Moyenne de la zone sélectionnée.
    *   Trait Noir : Moyenne globale.
    *   Bande Verte : Visualisation de la plage du filtre manuel (voir ci-dessous).

*   **Filtre Manuel (Curseur Vert) :**
    *   Permet de définir manuellement une plage de performance "cible" (Position et Largeur).
    *   **Bouton "Exporter Rapport de Sélection" :** Génère un rapport PDF/Markdown analysant les points qui tombent dans cette bande verte (analyse de criticité des paramètres).

*   **Exploration Fine (Métamodèle) :**
    *   Tente de prédire un point encore meilleur *à l'intérieur* de la zone sélectionnée, en utilisant une interpolation locale.
    *   **Bouton "Visualiser Rendu" :** Applique les paramètres (du point optimisé, de la zone, ou du point cliqué manuellement) sur l'image sélectionnée pour juger de la qualité visuelle.

### D. Panneau Droit : Vue Globale (Coordonnées Parallèles)
Ce graphique permet de visualiser les données en haute dimension.
*   **Axe X :** Les différents paramètres.
*   **Axe Y :** Valeur normalisée (0 = Min global, 1 = Max global).
*   **Lignes :** Chaque ligne représente un point (une expérience). La couleur indique la performance (Bleu = faible, Rouge = fort).
*   **Interactivité :** Vous pouvez **cliquer sur une ligne** pour la sélectionner. Ses valeurs s'afficheront dans le panneau central ("Valeurs du point sélectionné") et ce point deviendra la référence pour la "Visualisation du Rendu".
*   **Pourcentages (haut du graphe) :** Indiquent la **réduction de variance**. Si vous filtrez les données (via le curseur vert), ce chiffre indique à quel point ce paramètre est devenu "contraint" (critique). Une valeur élevée signifie que ce paramètre est très important pour la performance sélectionnée.

## 3. Scénario d'Utilisation Type

1.  **Charger** les données et lancer l'interface via "Recherche Zones Opt.".
2.  Cliquer sur **"Lancer la recherche"**.
3.  Sélectionner la **Zone #1** dans la liste de gauche.
4.  Lire les **Règles** (panneau central gauche) pour comprendre "la recette" (ex: "Il faut un `denoise` faible").
5.  (Optionnel) Utiliser le **Curseur Vert** pour isoler les 10% meilleurs points et cliquer sur **"Exporter Rapport"** pour avoir une analyse statistique de robustesse.
6.  Regarder le **Graphique Parallèle** (droite). Cliquer sur une ligne rouge vif (haute performance) qui semble intéressante.
7.  Vérifier ses valeurs exactes dans le panneau central droit ("Valeurs du point sélectionné").
8.  Sélectionner une image test (Panneau Gauche) et cliquer sur **"Visualiser Rendu"**. L'application va traiter l'image avec les paramètres du point cliqué pour valider que le résultat visuel est correct.
