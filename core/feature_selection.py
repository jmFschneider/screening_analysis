import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def compute_correlations(df, param_cols, response_col):
    """
    Corrélation absolue entre chaque paramètre et la réponse.
    """
    corrs = {}
    y = df[response_col].astype(float)

    for col in param_cols:
        corrs[col] = abs(df[col].astype(float).corr(y))

    return corrs


def compute_rf_importance(df, param_cols, response_col):
    """
    Importance des paramètres selon un RandomForest.
    """
    X = df[param_cols].astype(float).values
    y = df[response_col].astype(float).values

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    importances = model.feature_importances_
    return {col: imp for col, imp in zip(param_cols, importances)}


def compute_pca_loadings(df, param_cols, n_components=2):
    """
    Importance PCA = norme des loadings sur PC1/PC2.
    """
    X = df[param_cols].astype(float).values
    Xs = StandardScaler().fit_transform(X)

    pca = PCA(n_components=n_components)
    pca.fit(Xs)

    loadings = pca.components_

    scores = {}

    for idx, col in enumerate(param_cols):
        scores[col] = float(np.sqrt(loadings[0, idx]**2 + loadings[1, idx]**2))

    return scores


def auto_select_parameters(df, param_cols, response_col, top_k=3):
    """
    Fusion pondérée des 3 indicateurs : corr, RF, PCA-loadings.
    Retourne les top paramètres.
    """
    corr = compute_correlations(df, param_cols, response_col)
    rf   = compute_rf_importance(df, param_cols, response_col)
    pca  = compute_pca_loadings(df, param_cols)

    scores = {}

    for p in param_cols:
        # Fusion pondérée (modifiable)
        scores[p] = (
            0.4 * corr[p] +
            0.4 * rf[p] +
            0.2 * pca[p]
        )

    # Tri décroissant
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    selected = [p for p, _ in ranked[:top_k]]
    return selected, ranked
