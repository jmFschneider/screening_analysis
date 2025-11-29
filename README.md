# 📊 Screening Analysis & PCA Explorer  
Analyse avancée de screenings paramétriques — PCA, RandomForest, Gradient Boosting, rapports automatiques

---

## ✨ Présentation

**Screening Analysis & PCA Explorer** est une application complète d’analyse exploratoire destinée à l’étude de screenings paramétriques en vision, OCR ou traitement d’image.

Elle permet de :
- Visualiser des points expérimentaux
- Identifier les paramètres influents
- Explorer les relations non linéaires
- Réduire la dimension via PCA
- Générer des rapports automatiques
- Préparer efficacement les screenings suivants

Cette application est pensée pour les ingénieurs, chercheurs, data scientists et pour toute personne qui souhaite optimiser un processus complexe basé sur de multiples paramètres.

---

## 🧠 Fonctionnalités principales

### 🟦 Analyse PCA (Analyse en Composantes Principales)
- Projections PC1 / PC2
- Coloration par réponse
- Choix de palette (Viridis, Plasma, Coolwarm…)
- Sélection des paramètres utilisés dans PCA
- Auto-sélection via RandomForest
- Affichage des **loadings PC1 / PC2**, côte à côte
- Export des projections PCA (CSV, PNG)

---

### 🔥 Fenêtre d’analyse avancée
Module dédié regroupant plusieurs analyses statistiques et ML :

#### ✔ RandomForest — Importance globale
Mesure robuste de l’influence des paramètres.

#### ✔ Gradient Boosting — Importance fine
Analyse sensible aux interactions non linéaires.

#### ✔ Corrélations (Pearson & Spearman)
Heatmap ou barplots pour relations linéaires et monotones.

#### ✔ Importance combinée (RF + GB + Corr)
Score unique pour identifier :
- paramètres critiques
- paramètres secondaires
- paramètres négligeables

#### ✔ Exports graphiques (PNG)

---

### 📄 Générateur automatique de rapport (Markdown)
En un clic, l’application génère un rapport structuré contenant :

- Résumé du screening  
- PCA + loadings  
- Importances (RF, GB, combinée)  
- Corrélations  
- Recommandations pour les screenings suivants  
- Annexes (capturées via l’application)

Le fichier `.md` peut être importé dans :
- Word
- VS Code
- Obsidian
- GitHub Pages
- Pandoc (vers PDF)

---

## 📷 Captures d’écran (à ajouter)

Vous pouvez ajouter des images dans ce dossier, par exemple :

