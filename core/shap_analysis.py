import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

def compute_shap_analysis(df, params, response):
    """
    Entraîne un modèle Random Forest et calcule les valeurs SHAP.

    Args:
        df (pd.DataFrame): Données.
        params (list): Liste des colonnes paramètres.
        response (str): Colonne réponse.

    Returns:
        tuple: (shap_values, X_df, explainer)
            - shap_values: tableau numpy ou objet Explanation des valeurs SHAP.
            - X_df: DataFrame des features (pour les noms et valeurs).
            - explainer: L'objet explainer (utile pour certains plots).
    """
    if not SHAP_AVAILABLE:
        raise ImportError("La librairie SHAP est requise. Veuillez l'installer avec : pip install shap")

    X = df[params]
    y = df[response]

    # 1. Entraînement du modèle (Random Forest)
    # On utilise un modèle assez profond pour capturer les non-linéarités
    model = RandomForestRegressor(n_estimators=100, max_depth=None, min_samples_leaf=2, random_state=42)
    model.fit(X, y)

    # 2. Création de l'explainer
    # TreeExplainer est optimisé pour les arbres
    explainer = shap.TreeExplainer(model)
    
    # 3. Calcul des SHAP values
    # check_additivity=False permet d'éviter certaines erreurs de précision flottante bénignes
    shap_values = explainer.shap_values(X, check_additivity=False)

    return shap_values, X, explainer
