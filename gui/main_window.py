import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.loader import load_csv
from core.grouping import group_by_multidimensional_sort
from core.clustering import group_kmeans_fixed, group_kmeans_adaptive
from core.export import export_group_results
from core.pca import compute_pca


class PCAWindow(tk.Toplevel):
    """
    Fenêtre PCA avancée (v2.3) :
    - PCA 2D
    - cases à cocher pour sélectionner les paramètres
    - choix de palette
    - sélection automatique (RF + corr + PCA)
    - export CSV / PNG
    - affichage des loadings PC1 et PC2 côte à côte
    - figure entièrement réinitialisée à chaque refresh (pas de bugs Matplotlib)
    """

    def __init__(self, master, df, param_cols, response_cols):
        super().__init__(master)
        self.title("Analyse PCA (avancée)")

        self.df = df
        self.all_param_cols = param_cols.copy()
        self.param_cols = param_cols.copy()
        self.response_cols = response_cols.copy()

        # Variables interface
        self.color_mode = tk.StringVar(value="response")
        self.color_map = tk.StringVar(value="viridis")
        self.selected_params = {}

        # ================================
        # Layout principal
        # ================================
        self.columnconfigure(0, weight=3)  # figure + loadings
        self.columnconfigure(1, weight=1)  # panneau latéral
        self.rowconfigure(0, weight=4)     # figure
        self.rowconfigure(1, weight=1)     # loadings

        # ================================
        # FIGURE PCA
        # ================================
        self.fig = Figure(figsize=(7, 6))
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # ================================
        # ZONE LOADINGS PC1 & PC2 côte à côte
        # ================================
        self.loadings_frame = tk.Frame(self)
        self.loadings_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        self.loadings_frame.columnconfigure(0, weight=1)
        self.loadings_frame.columnconfigure(1, weight=1)

        self.pc1_text = tk.Text(self.loadings_frame, height=12, width=40)
        self.pc1_text.grid(row=0, column=0, sticky="nsew", padx=4)

        self.pc2_text = tk.Text(self.loadings_frame, height=12, width=40)
        self.pc2_text.grid(row=0, column=1, sticky="nsew", padx=4)

        # ================================
        # PANNEAU LATÉRAL
        # ================================
        side = tk.Frame(self)
        side.grid(row=0, column=1, rowspan=2, sticky="ns", padx=10, pady=10)

        # -------------------------
        # Paramètres PCA
        # -------------------------
        tk.Label(side, text="Paramètres PCA :", font=("Arial", 10, "bold"))\
            .pack(anchor="w")
        tk.Button(side, text="Analyse avancée",
                  command=self.open_analysis).pack(fill="x", pady=12)

        param_frame = tk.Frame(side)
        param_frame.pack(anchor="w")

        for col in self.all_param_cols:
            var = tk.BooleanVar(value=(col in self.param_cols))
            self.selected_params[col] = var
            tk.Checkbutton(param_frame, text=col, variable=var).pack(anchor="w")

        tk.Button(side, text="Appliquer paramètres",
                  command=self.apply_selected_params).pack(fill="x", pady=5)

        # -------------------------
        # Coloration
        # -------------------------
        tk.Label(side, text="Colorier par :", font=("Arial", 10, "bold")).pack(anchor="w", pady=10)

        tk.Radiobutton(side, text="Réponse", variable=self.color_mode, value="response",
                       command=self.refresh_pca).pack(anchor="w")
        tk.Radiobutton(side, text="Aucun", variable=self.color_mode, value="none",
                       command=self.refresh_pca).pack(anchor="w")

        # -------------------------
        # Palette
        # -------------------------
        tk.Label(side, text="Palette :", font=("Arial", 10, "bold")).pack(anchor="w", pady=10)

        palettes = ["viridis", "plasma", "inferno", "magma", "cividis",
                    "coolwarm", "RdBu", "Spectral", "seismic"]

        tk.OptionMenu(side, self.color_map, *palettes,
                      command=lambda _: self.refresh_pca()).pack(fill="x")

        # -------------------------
        # Auto sélection
        # -------------------------
        tk.Label(side, text="Sélection auto :", font=("Arial", 10, "bold")).pack(anchor="w", pady=10)
        tk.Button(side, text="Optimiser paramètres",
                  command=self.auto_select_params).pack(fill="x")

        # -------------------------
        # Export
        # -------------------------
        tk.Label(side, text="Export :", font=("Arial", 10, "bold")).pack(anchor="w", pady=10)
        tk.Button(side, text="Exporter CSV", command=self.export_csv).pack(fill="x")
        tk.Button(side, text="Exporter PNG", command=self.export_png).pack(fill="x", pady=5)

        # Colorbar (si présente)
        self.cbar = None

        # PCA initiale
        self.refresh_pca()

    # =========================================================
    # Appliquer la sélection de cases à cocher
    # =========================================================
    def apply_selected_params(self):
        selected = [p for p, v in self.selected_params.items() if v.get()]

        if len(selected) < 2:
            messagebox.showinfo("Info", "Veuillez sélectionner au moins deux paramètres.")
            return

        self.param_cols = selected
        self.refresh_pca()

    # =========================================================
    # PCA + affichage loadings
    # =========================================================
    def refresh_pca(self):
        # Reset complet de la figure (fixe tous les bugs colorbar)
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)

        df_pca, explained, pca = compute_pca(self.df, self.param_cols)

        # Coloration des points
        color = None
        if self.color_mode.get() == "response" and len(self.response_cols) > 0:
            col = self.response_cols[0]
            df_pca[col] = self.df[col]
            color = df_pca[col]

        sc = self.ax.scatter(
            df_pca["PC1"], df_pca["PC2"],
            c=color if color is not None else "gray",
            cmap=self.color_map.get(),
            s=26
        )

        # Colorbar
        if color is not None:
            self.cbar = self.fig.colorbar(sc, ax=self.ax)
            self.cbar.set_label(self.response_cols[0])
        else:
            self.cbar = None

        # Titres
        self.ax.set_xlabel(f"PC1 ({explained[0]*100:.1f}% var)")
        self.ax.set_ylabel(f"PC2 ({explained[1]*100:.1f}% var)")
        self.ax.set_title("Projection PCA")

        self.canvas.draw()

        # ========================
        # LOADINGS PCA (PC1 & PC2)
        # ========================
        loads = pca.components_

        self.pc1_text.delete("1.0", tk.END)
        self.pc2_text.delete("1.0", tk.END)

        # --- PC1 ---
        self.pc1_text.insert(tk.END, f"PC1 ({explained[0]*100:.1f}% var)\n\n")
        for param, weight in zip(self.param_cols, loads[0]):
            self.pc1_text.insert(tk.END, f"{param:<20} {weight:+.4f}\n")

        # --- PC2 ---
        if len(loads) > 1:
            self.pc2_text.insert(tk.END, f"PC2 ({explained[1]*100:.1f}% var)\n\n")
            for param, weight in zip(self.param_cols, loads[1]):
                self.pc2_text.insert(tk.END, f"{param:<20} {weight:+.4f}\n")

    # =========================================================
    # Auto sélection (RF + PCA + corr)
    # =========================================================
    def auto_select_params(self):
        from core.feature_selection import auto_select_parameters

        if len(self.response_cols) == 0:
            messagebox.showinfo("Info", "Aucune réponse sélectionnée.")
            return

        response = self.response_cols[0]

        selected, ranked = auto_select_parameters(
            self.df, self.all_param_cols, response, top_k=3
        )

        # Mise à jour cases à cocher
        for p, var in self.selected_params.items():
            var.set(p in selected)

        self.param_cols = selected
        self.refresh_pca()

        messagebox.showinfo(
            "Optimisation terminée",
            f"Paramètres retenus : {', '.join(selected)}"
        )

        # =====================================================================
        # analysis
        # =====================================================================
    def open_analysis(self):
        from gui.analysis_window import AnalysisWindow
        AnalysisWindow(self, self.df, self.param_cols, self.response_cols)

    # =========================================================
    # Exports
    # =========================================================
    def export_csv(self):
        df_pca, _, _ = compute_pca(self.df, self.param_cols)

        if len(self.response_cols):
            df_pca[self.response_cols[0]] = self.df[self.response_cols[0]]

        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return

        df_pca.to_csv(path, index=False)

    def export_png(self):
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if not path:
            return

        self.fig.savefig(path, dpi=300)



class MainWindow:

    def __init__(self, master):
        self.master = master
        master.title("Analyse des points — A1 / C2 / PCA")

        self.df = None
        self.param_cols = []
        self.response_cols = []
        self.results = None

        # -------------------------
        # Fichier
        # -------------------------
        file_frame = tk.Frame(master)
        file_frame.pack(fill="x", padx=10, pady=6)

        tk.Label(file_frame, text="Fichier CSV :").pack(side="left")
        self.file_entry = tk.Entry(file_frame, width=60)
        self.file_entry.pack(side="left", padx=6)
        tk.Button(file_frame, text="Parcourir...", command=self.ask_load_file).pack(side="left", padx=6)

        # -------------------------
        # Infos fichier
        # -------------------------
        info_frame = tk.LabelFrame(master, text="Infos fichier")
        info_frame.pack(fill="both", padx=10, pady=6)
        self.info_text = scrolledtext.ScrolledText(info_frame, height=6)
        self.info_text.pack(fill="both")

        # -------------------------
        # Sélection paramètres / réponses
        # -------------------------
        sel_frame = tk.LabelFrame(master, text="Sélection des colonnes")
        sel_frame.pack(fill="both", padx=10, pady=6)

        tk.Label(sel_frame, text="Paramètres").grid(row=0, column=0)
        self.param_listbox = tk.Listbox(sel_frame, selectmode="extended", exportselection=False, height=12)
        self.param_listbox.grid(row=1, column=0, padx=5)

        tk.Label(sel_frame, text="Réponses").grid(row=0, column=1)
        self.resp_listbox = tk.Listbox(sel_frame, selectmode="extended", exportselection=False, height=12)
        self.resp_listbox.grid(row=1, column=1, padx=5)

        # Zone Statistiques
        tk.Label(sel_frame, text="Statistiques (Sélection)").grid(row=0, column=2)
        self.stats_text = scrolledtext.ScrolledText(sel_frame, height=12, width=60, font=("Consolas", 9))
        self.stats_text.grid(row=1, column=2, padx=5)

        tk.Button(sel_frame, text="Valider la sélection", command=self.validate_columns).grid(
            row=2, column=0, columnspan=3, pady=6
        )

        # -------------------------
        # Paramètres d'analyse
        # -------------------------
        opt_frame = tk.LabelFrame(master, text="Options d'analyse")
        opt_frame.pack(fill="x", padx=10, pady=6)

        # Taille groupe A1 / C2-Fixe
        tk.Label(opt_frame, text="Taille groupe (A1 / C2-Fixe) :").grid(row=0, column=0, sticky="w")
        self.group_size_var = tk.StringVar(value="10")
        tk.Entry(opt_frame, textvariable=self.group_size_var, width=6).grid(row=0, column=1, sticky="w", padx=4)

        # Nb clusters KMeans
        tk.Label(opt_frame, text="Nombre de clusters (C2) :").grid(row=1, column=0, sticky="w")
        self.n_clusters_var = tk.StringVar(value="10")
        tk.Entry(opt_frame, textvariable=self.n_clusters_var, width=6).grid(row=1, column=1, sticky="w", padx=4)

        # Mode C2
        self.mode_c2_var = tk.StringVar(value="fixed")
        tk.Radiobutton(opt_frame, text="C2-Fixe", variable=self.mode_c2_var, value="fixed").grid(row=2, column=0, sticky="w")
        tk.Radiobutton(opt_frame, text="C2-Adaptatif", variable=self.mode_c2_var, value="adaptive").grid(row=2, column=1, sticky="w")

        # Seuil sigma C2-Adaptatif
        tk.Label(opt_frame, text="Seuil sigma (C2-Adaptatif) :").grid(row=3, column=0, sticky="w")
        self.std_thresh_var = tk.StringVar(value="2.5")
        tk.Entry(opt_frame, textvariable=self.std_thresh_var, width=6).grid(row=3, column=1, sticky="w", padx=4)

        # -------------------------
        # Boutons d'analyse
        # -------------------------
        action_frame = tk.Frame(master)
        action_frame.pack(fill="x", padx=10, pady=6)

        tk.Button(action_frame, text="Lancer A1", command=self.run_A1).pack(side="left", padx=6)
        tk.Button(action_frame, text="Lancer C2", command=self.run_C2).pack(side="left", padx=6)
        tk.Button(action_frame, text="Afficher PCA", command=self.show_pca).pack(side="left", padx=6)
        tk.Button(action_frame, text="Exporter CSV", command=self.export_csv).pack(side="left", padx=6)
        tk.Button(action_frame, text="Analyse Sobol", command=self.show_sobol).pack(side="left", padx=6)
        tk.Button(action_frame, text="Analyse SHAP", command=self.show_shap).pack(side="left", padx=6)
        tk.Button(action_frame, text="Recherche Zones Opt.", command=self.show_optimization).pack(side="left", padx=6)

        # -------------------------
        # Logs
        # -------------------------
        log_frame = tk.LabelFrame(master, text="Logs")
        log_frame.pack(fill="both", expand=True, padx=10, pady=6)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill="both", expand=True)

    # =====================================================================
    # Fichier
    # =====================================================================
    def ask_load_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if not path:
            return
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, path)
        self.load_file(path)

    def load_file(self, path):
        try:
            self.df = load_csv(path)
        except Exception as e:
            self.log_text.insert(tk.END, f"Erreur de chargement : {e}\n")
            return

        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, f"{len(self.df)} lignes, {len(self.df.columns)} colonnes\n\nColonnes :\n")

        self.param_listbox.delete(0, tk.END)
        self.resp_listbox.delete(0, tk.END)

        for col in self.df.columns:
            self.info_text.insert(tk.END, f"- {col}\n")
            self.param_listbox.insert(tk.END, col)
            self.resp_listbox.insert(tk.END, col)

        self.log_text.insert(tk.END, "Fichier chargé.\n")

    # =====================================================================
    # Colonnes
    # =====================================================================
    def validate_columns(self):
        self.param_cols = [self.param_listbox.get(i) for i in self.param_listbox.curselection()]
        self.response_cols = [self.resp_listbox.get(i) for i in self.resp_listbox.curselection()]

        # Reset Stats Text
        self.stats_text.delete("1.0", tk.END)

        if not self.param_cols or not self.response_cols:
            self.log_text.insert(tk.END, "⚠ Sélection incomplète (paramètres ou réponses).\n")
            self.stats_text.insert(tk.END, "Veuillez sélectionner des paramètres et au moins une réponse.")
        else:
            self.log_text.insert(tk.END, f"Paramètres : {self.param_cols}\n")
            self.log_text.insert(tk.END, f"Réponses : {self.response_cols}\n")

            # Calcul des stats pour chaque réponse
            for resp in self.response_cols:
                if resp not in self.df.columns:
                    continue
                
                col_data = self.df[resp]
                try:
                    mean_val = col_data.mean()
                    std_val = col_data.std()
                    var_val = col_data.var()
                    min_val = col_data.min()
                    max_val = col_data.max()
                    
                    # Récupération des paramètres pour le min et le max
                    idx_min = col_data.idxmin()
                    idx_max = col_data.idxmax()
                    
                    params_min = self.df.loc[idx_min, self.param_cols].to_dict()
                    params_max = self.df.loc[idx_max, self.param_cols].to_dict()

                    # Affichage formaté
                    self.stats_text.insert(tk.END, f"--- {resp} ---\n")
                    self.stats_text.insert(tk.END, f"Moyenne  : {mean_val:.4f}\n")
                    self.stats_text.insert(tk.END, f"Variance : {var_val:.4f} (Std: {std_val:.4f})\n\n")
                    
                    # Affichage côte à côte (Colonne gauche : MIN, Colonne droite : MAX)
                    # On utilise un padding de 35 caractères pour la colonne de gauche
                    col_width = 35
                    
                    header_line = f"{'[MIN] : ' + f'{min_val:.4f}':<{col_width}} {'[MAX] : ' + f'{max_val:.4f}'}\n"
                    self.stats_text.insert(tk.END, header_line)
                    
                    # On suppose que params_min et params_max ont les mêmes clés (paramètres)
                    for p in params_min.keys():
                        v_min = params_min[p]
                        v_max = params_max[p]
                        
                        # Formatage des lignes de paramètres
                        str_min = f"  - {p}: {v_min:.4f}"
                        str_max = f"  - {p}: {v_max:.4f}"
                        
                        line = f"{str_min:<{col_width}} {str_max}\n"
                        self.stats_text.insert(tk.END, line)
                    
                    self.stats_text.insert(tk.END, "\n" + "="*60 + "\n")

                except Exception as e:
                    self.stats_text.insert(tk.END, f"Erreur stats sur {resp}: {e}\n")

    # =====================================================================
    # A1
    # =====================================================================
    def run_A1(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé.\n")
            return
        if not self.param_cols or not self.response_cols:
            self.log_text.insert(tk.END, "⚠ Sélection incomplète pour A1.\n")
            return

        size = int(self.group_size_var.get())
        self.results = group_by_multidimensional_sort(
            self.df, self.param_cols, self.response_cols, group_size=size
        )
        self.log_text.insert(tk.END, "Analyse A1 terminée.\n")

    # =====================================================================
    # C2
    # =====================================================================
    def run_C2(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé.\n")
            return
        if not self.param_cols or not self.response_cols:
            self.log_text.insert(tk.END, "⚠ Sélection incomplète pour C2.\n")
            return

        n_clusters = int(self.n_clusters_var.get())

        if self.mode_c2_var.get() == "fixed":
            group_size = int(self.group_size_var.get())
            self.results = group_kmeans_fixed(
                self.df, self.param_cols, self.response_cols,
                group_size=group_size, n_clusters=n_clusters
            )
            self.log_text.insert(tk.END, "Analyse C2-Fixe terminée.\n")
        else:
            threshold = float(self.std_thresh_var.get())
            self.results = group_kmeans_adaptive(
                self.df, self.param_cols, self.response_cols,
                n_clusters=n_clusters, std_threshold=threshold
            )
            self.log_text.insert(tk.END, "Analyse C2-Adaptative terminée.\n")

    # =====================================================================
    # PCA
    # =====================================================================
    def show_pca(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé pour PCA.\n")
            return
        if not self.param_cols:
            self.log_text.insert(tk.END, "⚠ Aucun paramètre sélectionné.\n")
            return

        PCAWindow(self.master, self.df, self.param_cols, self.response_cols)
        self.log_text.insert(tk.END, "Fenêtre PCA avancée ouverte.\n")

    # =====================================================================
    # Export CSV
    # =====================================================================
    def export_csv(self):
        if not self.results:
            self.log_text.insert(tk.END, "⚠ Aucune analyse à exporter.\n")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return

        export_group_results(self.results, path)
        self.log_text.insert(tk.END, f"Résultats exportés vers : {path}\n")

    # =====================================================================
    # Sobol
    # =====================================================================
    def show_sobol(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé pour Sobol.\n")
            return
        if not self.param_cols:
            self.log_text.insert(tk.END, "⚠ Aucun paramètre sélectionné.\n")
            return

        from gui.sobol_window import SobolWindow
        SobolWindow(self.master, self.df, self.param_cols, self.response_cols)
        self.log_text.insert(tk.END, "Fenêtre Analyse Sobol ouverte.\n")

    # =====================================================================
    # SHAP
    # =====================================================================
    def show_shap(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé pour SHAP.\n")
            return
        if not self.param_cols:
            self.log_text.insert(tk.END, "⚠ Aucun paramètre sélectionné.\n")
            return

        from gui.shap_window import ShapWindow
        ShapWindow(self.master, self.df, self.param_cols, self.response_cols)
        self.log_text.insert(tk.END, "Fenêtre Analyse SHAP ouverte.\n")

    # =====================================================================
    # OPTIMIZATION
    # =====================================================================
    def show_optimization(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé pour Optimisation.\n")
            return
        if not self.param_cols:
            self.log_text.insert(tk.END, "⚠ Aucun paramètre sélectionné.\n")
            return

        from gui.optimization_window import OptimizationWindow
        OptimizationWindow(self.master, self.df, self.param_cols, self.response_cols)
        self.log_text.insert(tk.END, "Fenêtre Optimisation ouverte.\n")


def launch_app():
    root = tk.Tk()
    MainWindow(root)
    root.geometry("1050x750")
    root.mainloop()
