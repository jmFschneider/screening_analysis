import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class AnalysisWindow(tk.Toplevel):
    """
    Analyse avancée des paramètres :
    - RandomForest
    - Gradient Boosting
    - Corrélations
    - Importance combinée
    """

    def __init__(self, master, df, params, responses):
        super().__init__(master)
        self.title("Analyse avancée des paramètres")

        self.df = df
        self.params = params
        self.responses = responses
        self.response = responses[0]

        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Boutons actions
        btns = tk.Frame(self)
        btns.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=1)
        btns.columnconfigure(3, weight=1)

        tk.Button(btns, text="RandomForest",
                  command=self.show_rf).grid(row=0, column=0, padx=4)
        tk.Button(btns, text="Gradient Boosting",
                  command=self.show_gb).grid(row=0, column=1, padx=4)
        tk.Button(btns, text="Corrélations",
                  command=self.show_corr).grid(row=0, column=2, padx=4)
        tk.Button(btns, text="Importance combinée",
                  command=self.show_combined).grid(row=0, column=3, padx=4)
        tk.Button(btns, text="Exporter rapport (md)",
                  command=self.export_report).grid(row=1, column=0, columnspan=4, pady=8)

        # Zone graphique
        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    # ============
    # RandomForest
    # ============
    def show_rf(self):
        from core.rf_importance import compute_rf_importances
        imp = compute_rf_importances(self.df, self.params, self.response)

        self._plot_importance(imp, "RandomForest")

    # ===================
    # Gradient Boosting
    # ===================
    def show_gb(self):
        from core.boosting_importance import compute_gb_importances
        imp = compute_gb_importances(self.df, self.params, self.response)

        self._plot_importance(imp, "Gradient Boosting")

    # ===================
    # Corrélations
    # ===================
    def show_corr(self):
        from core.correlation_analysis import compute_correlations
        corr_p, corr_s = compute_correlations(self.df, self.params, self.response)

        self.ax.clear()
        labels = list(corr_p.keys())
        pearson = [corr_p[p] for p in labels]
        spearman = [corr_s[p] for p in labels]

        x = np.arange(len(labels))
        w = 0.35

        self.ax.barh(x - w/2, pearson, height=w, label="Pearson")
        self.ax.barh(x + w/2, spearman, height=w, label="Spearman")

        self.ax.set_yticks(x)
        self.ax.set_yticklabels(labels)
        self.ax.legend()
        self.ax.set_title("Corrélations")

        self.canvas.draw()

    # ================================
    # Importance combinée
    # ================================
    def show_combined(self):
        from core.rf_importance import compute_rf_importances
        from core.boosting_importance import compute_gb_importances
        from core.correlation_analysis import compute_correlations
        from core.combined_importance import combine_importances

        imp_rf = compute_rf_importances(self.df, self.params, self.response)
        imp_gb = compute_gb_importances(self.df, self.params, self.response)
        corr_p, _ = compute_correlations(self.df, self.params, self.response)

        imp = combine_importances(imp_rf, imp_gb, corr_p)

        self._plot_importance(imp, "Importance combinée")

    # ================================
    # Générateur de rapports
    # ================================
    def export_report(self):
        from core.report_generator import generate_markdown_report

        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Tous les fichiers", "*.*")]
        )
        if not path:
            return

        generate_markdown_report(
            path=path,
            df=self.df,
            param_cols=self.params,
            response_col=self.response
        )

        messagebox.showinfo("Rapport", f"Rapport Markdown généré :\n{path}")

    # ===============
    # Plot générique
    # ===============
    def _plot_importance(self, imp, title):
        self.ax.clear()

        labels = list(imp.keys())
        values = list(imp.values())

        self.ax.barh(labels, values)
        self.ax.set_title(title)
        self.ax.set_xlabel("Importance")
        self.fig.tight_layout()

        self.canvas.draw()
