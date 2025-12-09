# Installation - Screening Analysis

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Tesseract OCR installé sur le système

## Configuration de l'environnement

### 1. Créer un environnement virtuel

```bash
cd /chemin/vers/screening_analysis
python -m venv .venv
```

### 2. Activer l'environnement virtuel

**Linux/Ubuntu :**
```bash
source .venv/bin/activate
```

**Windows :**
```bash
.venv\Scripts\activate
```

## Installation des dépendances

### 1. Installer les packages Python

```bash
pip install -r requirements.txt
```

### 2. Installer le package OCR_Quality_Audit (local)

Si vous avez le package OCR_Quality_Audit en local :

```bash
pip install -e /chemin/vers/OCR_Quality_Audit[windows]
```

## Détails techniques

### OpenCV sans CUDA

Ce projet utilise **opencv-python** (version wheel pré-compilée de PyPI) :
- ✅ Fonctionne sur **Ubuntu et Windows**
- ✅ Pas de compilation nécessaire
- ✅ Pas de support CUDA (utilise uniquement le CPU)
- ✅ Compatible avec NumPy 2.x

**Pourquoi pas CUDA ?**
- La compilation d'OpenCV avec CUDA est complexe et longue
- Pour l'OCR et l'analyse d'images statiques, le CPU est largement suffisant
- La version wheel est plus simple à installer et maintenir

### NumPy 2.x

Le projet nécessite **NumPy >= 2.0** car :
- `opencv-python >= 4.12` requiert NumPy 2.x
- `SALib >= 1.5` requiert NumPy 2.x
- Les versions wheel pré-compilées d'OpenCV sont compatibles

### Dépendances principales

| Package | Version | Usage |
|---------|---------|-------|
| opencv-python | >= 4.8.0 | Traitement d'images |
| numpy | >= 2.0 | Calcul numérique |
| pytesseract | >= 0.3.13 | OCR |
| optuna | >= 4.6.0 | Optimisation |
| SALib | >= 1.5.0 | Analyse de sensibilité |
| matplotlib | >= 3.8.0 | Visualisation |
| pandas | >= 2.1.1 | Manipulation de données |

## Lancement de l'application

```bash
python app.py
```

## Résolution de problèmes

### Erreur NumPy "cannot be run in NumPy 2.x"

Si vous voyez cette erreur, cela signifie qu'OpenCV a été compilé avec NumPy 1.x.

**Solution :**
```bash
pip uninstall opencv-python -y
pip install --only-binary=:all: opencv-python
```

Cela force l'installation de la version wheel pré-compilée compatible NumPy 2.x.

### Erreur d'import cv2

Vérifiez que vous êtes bien dans l'environnement virtuel :
```bash
which python  # Linux
where python  # Windows
```

### Tesseract non trouvé

Installez Tesseract OCR sur votre système :

**Ubuntu :**
```bash
sudo apt-get install tesseract-ocr
```

**Windows :**
Téléchargez et installez depuis : https://github.com/UB-Mannheim/tesseract/wiki

## Notes

- Ce projet n'utilise pas le GPU pour OpenCV
- Si vous avez besoin du GPU pour d'autres tâches (deep learning), utilisez PyTorch avec CUDA
- L'environnement virtuel doit être activé à chaque session de travail
