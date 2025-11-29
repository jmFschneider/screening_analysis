import pandas as pd

def export_group_results(results, path):
    """
    Exporte les résultats statistiques vers un CSV aplati.
    Compatible A1, C2-Fixe et C2-Adaptatif.
    """
    rows = []

    for g in results:
        row = {}

        # Identifiants de groupe selon la méthode utilisée
        if "group_idx" in g:
            row["group_idx"] = g["group_idx"]
        if "cluster_idx" in g:
            row["cluster_idx"] = g["cluster_idx"]
        if "subgroup_idx" in g:
            row["subgroup_idx"] = g["subgroup_idx"]
        if "adaptive" in g:
            row["adaptive_group"] = g["adaptive"]

        # Nombre de points
        row["n_points"] = g["n_points"]

        # Paramètres
        for col, stats in g["params"].items():
            for k, v in stats.items():
                row[f"param_{col}_{k}"] = v

        # Réponses
        for col, stats in g["responses"].items():
            for k, v in stats.items():
                row[f"response_{col}_{k}"] = v

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
