from pathlib import Path

from core.pca import compute_pca
from core.rf_importance import compute_rf_importances
from core.boosting_importance import compute_gb_importances
from core.correlation_analysis import compute_correlations
from core.combined_importance import combine_importances


def generate_markdown_report(
    path,
    df,
    param_cols,
    response_col,
    title="Rapport d'analyse de screening"
):
    """
    Génère un rapport Markdown complet et l'enregistre dans 'path'.
    - df : DataFrame complet
    - param_cols : liste des paramètres utilisés
    - response_col : nom de la réponse principale
    """

    path = Path(path)

    # ------------------------
    # Infos de base
    # ------------------------
    n_points = len(df)
    n_params = len(param_cols)

    # ------------------------
    # PCA
    # ------------------------
    df_pca, explained, pca_model = compute_pca(df, param_cols)
    loadings = pca_model.components_

    # ------------------------
    # Importances RF / GB / Corr / Combinée
    # ------------------------
    imp_rf = compute_rf_importances(df, param_cols, response_col)
    imp_gb = compute_gb_importances(df, param_cols, response_col)
    corr_p, corr_s = compute_correlations(df, param_cols, response_col)
    imp_combined = combine_importances(imp_rf, imp_gb, corr_p)

    # Tri pour affichage
    def sorted_dict(d):
        return sorted(d.items(), key=lambda x: x[1], reverse=True)

    rf_sorted = sorted_dict(imp_rf)
    gb_sorted = sorted_dict(imp_gb)
    comb_sorted = sorted_dict(imp_combined)

    # ------------------------
    # Construction du Markdown
    # ------------------------
    lines = []

    lines.append(f"# {title}\n")
    lines.append("## 1. Résumé général\n")
    lines.append(f"- Nombre de points : **{n_points}**")
    lines.append(f"- Nombre de paramètres : **{n_params}**")
    lines.append(f"- Paramètres analysés : `{', '.join(param_cols)}`")
    lines.append(f"- Réponse principale : `{response_col}`\n")

    # ------------------------
    # PCA
    # ------------------------
    lines.append("## 2. Analyse PCA\n")

    lines.append(f"- PC1 explique **{explained[0]*100:.1f}%** de la variance.")
    if len(explained) > 1:
        lines.append(f"- PC2 explique **{explained[1]*100:.1f}%** de la variance.\n")
    else:
        lines.append("")

    lines.append("### 2.1 Loadings des composantes principales\n")

    # PC1
    lines.append(f"**PC1 ({explained[0]*100:.1f}% var.)**\n")
    lines.append("| Paramètre | Poids PC1 |")
    lines.append("|-----------|-----------|")
    for param, weight in zip(param_cols, loadings[0]):
        lines.append(f"| `{param}` | {weight:+.4f} |")
    lines.append("")

    # PC2 si dispo
    if len(loadings) > 1:
        lines.append(f"**PC2 ({explained[1]*100:.1f}% var.)**\n")
        lines.append("| Paramètre | Poids PC2 |")
        lines.append("|-----------|-----------|")
        for param, weight in zip(param_cols, loadings[1]):
            lines.append(f"| `{param}` | {weight:+.4f} |")
        lines.append("")

    # ------------------------
    # Importances RF
    # ------------------------
    lines.append("## 3. Importances des paramètres\n")

    lines.append("### 3.1 RandomForest\n")
    lines.append("| Paramètre | Importance RF |")
    lines.append("|-----------|---------------|")
    for p, v in rf_sorted:
        lines.append(f"| `{p}` | {v:.4f} |")
    lines.append("")

    # ------------------------
    # Importances GB
    # ------------------------
    lines.append("### 3.2 Gradient Boosting\n")
    lines.append("| Paramètre | Importance GB |")
    lines.append("|-----------|---------------|")
    for p, v in gb_sorted:
        lines.append(f"| `{p}` | {v:.4f} |")
    lines.append("")

    # ------------------------
    # Corrélations
    # ------------------------
    lines.append("### 3.3 Corrélations avec la réponse\n")
    lines.append(f"_Réponse :_ `{response_col}`\n")

    lines.append("| Paramètre | Corr. Pearson | Corr. Spearman |")
    lines.append("|-----------|----------------|----------------|")
    for p in param_cols:
        cp = corr_p.get(p, 0.0)
        cs = corr_s.get(p, 0.0)
        lines.append(f"| `{p}` | {cp:+.4f} | {cs:+.4f} |")
    lines.append("")

    # ------------------------
    # Importance combinée
    # ------------------------
    lines.append("### 3.4 Importance combinée (RF + GB + Corr)\n")
    lines.append("_Score combiné = 0.5·RF + 0.4·GB + 0.1·|corrPearson|_\n")

    lines.append("| Rang | Paramètre | Importance combinée |")
    lines.append("|------|-----------|---------------------|")
    for i, (p, v) in enumerate(comb_sorted, start=1):
        lines.append(f"| {i} | `{p}` | {v:.4f} |")
    lines.append("")

    # ------------------------
    # Recommandations automatiques (simples)
    # ------------------------
    lines.append("## 4. Recommandations (brouillon automatique)\n")

    if comb_sorted:
        top_params = [p for p, _ in comb_sorted[:3]]
        weak_params = [p for p, _ in comb_sorted[-3:]]

        lines.append(f"- Paramètres dominants à explorer finement : `{', '.join(top_params)}`")
        lines.append(f"- Paramètres probablement secondaires (à fixer ou réduire) : `{', '.join(weak_params)}`\n")

    lines.append("**Idées de screening suivant :**\n")
    lines.append("- Reserrer les plages de variation des paramètres dominants autour des zones performantes.")
    lines.append("- Fixer les paramètres faibles à une valeur médiane raisonnable.")
    lines.append("- Lancer un second screening local pour affiner la zone optimale.\n")

    # ------------------------
    # Annexes
    # ------------------------
    lines.append("## 5. Annexes\n")
    lines.append("- Projections PCA (PC1, PC2) exportables depuis la fenêtre PCA.")
    lines.append("- Graphiques d’importance (RF, GB, combinée) exportables depuis la fenêtre d’analyse avancée.")
    lines.append("- Données complètes disponibles dans les exports CSV.\n")

    # Écriture du fichier
    path.write_text("\n".join(lines), encoding="utf-8")
