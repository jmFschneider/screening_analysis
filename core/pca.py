import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def compute_pca(df, param_cols, n_components=2, normalize=True):
    """
    PCA sur les paramètres sélectionnés.
    Retour :
    - df_pca avec PC1, PC2
    - variance expliquée
    - modèle PCA (optionnel)
    """
    X = df[param_cols].astype(float).values

    if normalize:
        X = StandardScaler().fit_transform(X)

    pca = PCA(n_components=n_components)
    pcs = pca.fit_transform(X)

    df_pca = pd.DataFrame({
        "PC1": pcs[:, 0],
        "PC2": pcs[:, 1]
    })

    explained = pca.explained_variance_ratio_

    return df_pca, explained, pca
