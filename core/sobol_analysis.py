import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

try:
    from SALib.sample import sobol
    from SALib.analyze import sobol as analyze_sobol
    SALIB_AVAILABLE = True
except ImportError:
    SALIB_AVAILABLE = False

def compute_sobol_indices(df, params, response, n_samples=1024):
    """
    Calcule les indices de Sobol (S1, ST) en utilisant un métamodèle Random Forest.
    
    Args:
        df (pd.DataFrame): Données d'entrée.
        params (list): Liste des noms de paramètres.
        response (str): Nom de la colonne réponse.
        n_samples (int): Nombre d'échantillons de base pour la séquence de Sobol (N).
                         Le nombre total d'évaluations sera N * (D + 2) (si second_order=False).

    Returns:
        dict: Dictionnaire contenant les séries pandas 'S1', 'ST', 'S1_conf', 'ST_conf'.
    """
    if not SALIB_AVAILABLE:
        raise ImportError("La librairie SALib est requise. Veuillez l'installer avec : pip install SALib")

    # 1. Entraînement du métamodèle (Random Forest)
    X_train = df[params].values
    y_train = df[response].values
    
    # On utilise un RF assez robuste pour servir de surrogate
    rf = RandomForestRegressor(n_estimators=200, random_state=42)
    rf.fit(X_train, y_train)
    
    # 2. Définition du problème pour SALib (Bornes extraites des données)
    # On suppose que le plan d'expérience couvre l'espace d'intérêt
    problem = {
        'num_vars': len(params),
        'names': params,
        'bounds': [[df[p].min(), df[p].max()] for p in params]
    }
    
    # 3. Génération de l'échantillon de Sobol
    # calc_second_order=False pour se limiter à S1 et ST (plus rapide, moins de points)
    X_sobol = sobol.sample(problem, n_samples, calc_second_order=False)
    
    # 4. Prédiction sur les points virtuels via le métamodèle
    y_sobol = rf.predict(X_sobol)
    
    # 5. Calcul des indices
    si = analyze_sobol.analyze(problem, y_sobol, calc_second_order=False, print_to_console=False)
    
    # Formatage des résultats
    results = {
        "S1": pd.Series(si['S1'], index=params),
        "ST": pd.Series(si['ST'], index=params),
        "S1_conf": pd.Series(si['S1_conf'], index=params),
        "ST_conf": pd.Series(si['ST_conf'], index=params)
    }
    
    return results
