import numpy as np
import pandas as pd


def compute_group_stats(df_group, param_cols, response_cols):
    """
    Calcule :
    - Moyenne
    - Min
    - Max
    - Écart-type
    pour les paramètres et les réponses d'un groupe.
    """

    stats = {
        "n_points": len(df_group),
        "params": {},
        "responses": {}
    }

    # Paramètres
    for col in param_cols:
        series = df_group[col].astype(float)
        stats["params"][col] = {
            "mean": float(series.mean()),
            "min": float(series.min()),
            "max": float(series.max()),
            "std": float(series.std(ddof=1))
        }

    # Réponses
    for col in response_cols:
        series = df_group[col].astype(float)
        stats["responses"][col] = {
            "mean": float(series.mean()),
            "min": float(series.min()),
            "max": float(series.max()),
            "std": float(series.std(ddof=1))
        }

    return stats


def group_by_multidimensional_sort(df, param_cols, response_cols, group_size=10):
    """
    Implémentation A1 :
    - tri multidimensionnel
    - regroupement en paquets de group_size
    - calcul des statistiques complètes
    """
    df_sorted = df.sort_values(by=param_cols, ascending=True).reset_index(drop=True)

    total = len(df_sorted)
    groups = []
    results = []

    for start in range(0, total, group_size):
        end = min(start + group_size, total)
        group = df_sorted.iloc[start:end]
        groups.append(group)

        stats = compute_group_stats(group, param_cols, response_cols)
        stats["group_idx"] = len(results)
        results.append(stats)

    return results
