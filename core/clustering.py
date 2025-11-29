import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from core.grouping import compute_group_stats


def kmeans_cluster(df, param_cols, n_clusters=10, random_state=42):
    """
    Applique KMeans uniquement sur les paramètres.
    Retourne:
    - labels : cluster de chaque point
    - centres : centroïdes des clusters
    """
    X = df[param_cols].astype(float).values

    model = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init="auto"
    )

    labels = model.fit_predict(X)
    centers = model.cluster_centers_

    return labels, centers


# ---------------------------------------------------------
# C2-FIXE : groupes de taille fixe à l'intérieur de chaque cluster
# ---------------------------------------------------------

def group_kmeans_fixed(df, param_cols, response_cols,
                       group_size=10, n_clusters=10):
    """
    Méthode C2-Fixe:
    - KMeans pour identifier des clusters homogènes
    - tri interne par distance au centroïde
    - découpage en sous-groupes de taille fixe
    """
    labels, centers = kmeans_cluster(df, param_cols, n_clusters=n_clusters)

    df_local = df.copy()
    df_local["cluster"] = labels

    results = []

    for c in range(n_clusters):

        cluster_df = df_local[df_local["cluster"] == c]

        if len(cluster_df) == 0:
            continue

        # distance au centroïde
        X = cluster_df[param_cols].astype(float).values
        dists = np.linalg.norm(X - centers[c], axis=1)

        cluster_df = cluster_df.copy()
        cluster_df["dist_center"] = dists
        cluster_df = cluster_df.sort_values("dist_center")

        # découpage en groupes fixes
        total = len(cluster_df)

        for start in range(0, total, group_size):
            end = min(start + group_size, total)
            g = cluster_df.iloc[start:end].drop(columns=["dist_center"])

            stats = compute_group_stats(g, param_cols, response_cols)
            stats["cluster_idx"] = c
            stats["subgroup_idx"] = len(results)

            results.append(stats)

    return results


# ---------------------------------------------------------
# C2-ADAPTATIF : taille variable en fonction de l’homogénéité
# ---------------------------------------------------------

def group_kmeans_adaptive(df, param_cols, response_cols,
                          n_clusters=10,
                          std_threshold=2.0,
                          min_group_size=5):
    """
    Méthode C2-Adaptative:
    - KMeans pour créer des clusters homogènes
    - tri interne par distance
    - construction de sous-groupes jusqu’à ce que
      l’écart-type dépasse un seuil
    """
    labels, centers = kmeans_cluster(df, param_cols, n_clusters=n_clusters)

    df_local = df.copy()
    df_local["cluster"] = labels

    results = []

    for c in range(n_clusters):
        cluster_df = df_local[df_local["cluster"] == c]

        if len(cluster_df) == 0:
            continue

        # distance au centroïde
        X = cluster_df[param_cols].astype(float).values
        dists = np.linalg.norm(X - centers[c], axis=1)

        cluster_df = cluster_df.copy()
        cluster_df["dist_center"] = dists
        cluster_df = cluster_df.sort_values("dist_center")

        current_group = []
        group_points = []

        for idx, row in cluster_df.drop(columns=["dist_center"]).iterrows():

            group_points.append(row)

            # calcul temporaire du std pour décider si on coupe
            temp_df = pd.DataFrame(group_points)

            stats_temp = compute_group_stats(temp_df, param_cols, response_cols)

            # si groupe trop hétérogène ET taille minimale atteinte -> couper
            max_std = max(
                [stats_temp["responses"][col]["std"] for col in response_cols]
            )

            if max_std > std_threshold and len(group_points) >= min_group_size:
                # terminer groupe précédent sans le dernier point
                group_points.pop()
                final_df = pd.DataFrame(group_points)
                stats_final = compute_group_stats(final_df, param_cols, response_cols)

                stats_final["cluster_idx"] = c
                stats_final["subgroup_idx"] = len(results)
                stats_final["adaptive"] = True

                results.append(stats_final)

                # recommencer un groupe avec le point exclu
                group_points = [row]

        # dernier groupe
        if len(group_points) > 0:
            final_df = pd.DataFrame(group_points)
            stats_final = compute_group_stats(final_df, param_cols, response_cols)
            stats_final["cluster_idx"] = c
            stats_final["subgroup_idx"] = len(results)
            stats_final["adaptive"] = True

            results.append(stats_final)

    return results
