import tkinter as tk
from tkinter import filedialog, scrolledtext
import pandas as pd
import numpy as np


class OptimizerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Analyse des points — GUI complète (A1 + sélection robuste)")

        self.df = None
        self.param_cols = []
        self.response_cols = []
        self.results = None

        # -----------------------
        # Frame fichier & chargement
        # -----------------------
        file_frame = tk.Frame(master)
        file_frame.pack(fill="x", padx=8, pady=6)

        tk.Label(file_frame, text="Fichier :").pack(side="left")
        self.file_entry = tk.Entry(file_frame, width=60)
        self.file_entry.pack(side="left", padx=6)

        tk.Button(file_frame, text="Parcourir...", command=self.ask_and_load_file).pack(side="left", padx=6)

        # -----------------------
        # Infos fichier
        # -----------------------
        info_frame = tk.LabelFrame(master, text="Informations du fichier")
        info_frame.pack(fill="both", padx=8, pady=6)

        self.info_text = scrolledtext.ScrolledText(info_frame, height=6, wrap="none")
        self.info_text.pack(fill="both")

        # -----------------------
        # Sélection des colonnes
        # -----------------------
        select_frame = tk.LabelFrame(master, text="Sélection des paramètres (features) et réponses (scores)")
        select_frame.pack(fill="both", padx=8, pady=6)

        # Listbox paramètres (exportselection=False pour garder sélection visible)
        tk.Label(select_frame, text="Paramètres").grid(row=0, column=0, padx=6, pady=(4,0))
        self.param_listbox = tk.Listbox(
            select_frame,
            selectmode="extended",
            height=12,
            width=40,
            exportselection=False
        )
        self.param_listbox.grid(row=1, column=0, padx=6, pady=4)

        # Listbox réponses
        tk.Label(select_frame, text="Réponses").grid(row=0, column=1, padx=6, pady=(4,0))
        self.resp_listbox = tk.Listbox(
            select_frame,
            selectmode="extended",
            height=12,
            width=40,
            exportselection=False
        )
        self.resp_listbox.grid(row=1, column=1, padx=6, pady=4)

        # Boutons liés à la sélection
        btn_frame = tk.Frame(select_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(4,8))

        tk.Button(btn_frame, text="Afficher sélection courante", command=self.show_current_selection).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Valider la sélection", command=self.validate_selection).pack(side="left", padx=6)
        tk.Label(btn_frame, text="(Ctrl+clic / Shift+clic pour multi-sélection)", fg="gray").pack(side="left", padx=12)

        # -----------------------
        # Actions (Analyse)
        # -----------------------
        action_frame = tk.Frame(master)
        action_frame.pack(fill="x", padx=8, pady=6)

        tk.Button(action_frame, text="Lancer Analyse (A1 - tri multidim.)", command=self.run_analysis).pack(side="left", padx=6)
        tk.Button(action_frame, text="Exporter résultats CSV", command=self.export_results_csv).pack(side="left", padx=6)

        # -----------------------
        # Logs / Avancement
        # -----------------------
        log_frame = tk.LabelFrame(master, text="Logs / Avancement")
        log_frame.pack(fill="both", padx=8, pady=6, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill="both", expand=True)

    # -----------------------
    # Chargement fichier (avec dialogue)
    # -----------------------
    def ask_and_load_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, path)
        self.load_file(path)

    def load_file(self, path):
        self.log_text.insert(tk.END, f"Chargement du fichier : {path}\n")
        self.log_text.see(tk.END)

        try:
            # auto-détection du séparateur (',' ou ';' etc.)
            self.df = pd.read_csv(path, sep=None, engine="python")
        except Exception as e:
            self.log_text.insert(tk.END, f"Erreur lecture CSV avec détection automatique : {e}\n")
            self.log_text.insert(tk.END, "Tentative avec séparateur ';'...\n")
            try:
                self.df = pd.read_csv(path, sep=";")
            except Exception as e2:
                self.log_text.insert(tk.END, f"Erreur lecture CSV : {e2}\n")
                return

        # afficher infos
        self.info_text.delete("1.0", tk.END)
        rows, cols = self.df.shape
        self.info_text.insert(tk.END, f"Lignes : {rows}\nColonnes : {cols}\n\nColonnes :\n")
        for col in self.df.columns:
            self.info_text.insert(tk.END, f" - {col}\n")

        # remplir listbox tout en conservant la sélection précédente si existante
        self.refresh_listboxes()

        self.log_text.insert(tk.END, "Fichier chargé et listbox mises à jour.\n")
        self.log_text.see(tk.END)

    # -----------------------
    # Refresh listboxes avec restauration de sélection
    # -----------------------
    def refresh_listboxes(self):
        # récupérer sélection précédente (noms)
        old_params = []
        old_resps = []
        try:
            old_params = [self.param_listbox.get(i) for i in self.param_listbox.curselection()]
            old_resps = [self.resp_listbox.get(i) for i in self.resp_listbox.curselection()]
        except Exception:
            pass

        # reset
        self.param_listbox.delete(0, tk.END)
        self.resp_listbox.delete(0, tk.END)

        # remplir
        for col in self.df.columns:
            self.param_listbox.insert(tk.END, col)
            self.resp_listbox.insert(tk.END, col)

        # restaurer la sélection si possible
        for i, col in enumerate(self.df.columns):
            if col in old_params:
                self.param_listbox.selection_set(i)
            if col in old_resps:
                self.resp_listbox.selection_set(i)

    # -----------------------
    # Debug : afficher sélection courante
    # -----------------------
    def show_current_selection(self):
        if self.df is None:
            self.log_text.insert(tk.END, "[debug] Aucun fichier chargé.\n")
            return

        feat_idx = self.param_listbox.curselection()
        targ_idx = self.resp_listbox.curselection()

        feats = [self.param_listbox.get(i) for i in feat_idx]
        targs = [self.resp_listbox.get(i) for i in targ_idx]

        self.log_text.insert(tk.END, f"[debug] indices features : {feat_idx}\n")
        self.log_text.insert(tk.END, f"[debug] indices responses: {targ_idx}\n")
        self.log_text.insert(tk.END, f"[debug] features sélectionnés : {feats}\n")
        self.log_text.insert(tk.END, f"[debug] responses sélectionnés : {targs}\n")
        self.log_text.see(tk.END)

    # -----------------------
    # Valider sélection (stocke noms des colonnes)
    # -----------------------
    def validate_selection(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé.\n")
            return

        self.param_cols = [self.param_listbox.get(i) for i in self.param_listbox.curselection()]
        self.response_cols = [self.resp_listbox.get(i) for i in self.resp_listbox.curselection()]

        self.log_text.insert(tk.END, "Lecture de la sélection...\n")
        self.log_text.insert(tk.END, f"Paramètres sélectionnés : {self.param_cols}\n")
        self.log_text.insert(tk.END, f"Réponses sélectionnées : {self.response_cols}\n")
        if not self.param_cols or not self.response_cols:
            self.log_text.insert(tk.END, "⚠ Merci de sélectionner au moins un paramètre ET une réponse.\n")
        else:
            self.log_text.insert(tk.END, "Sélection validée. Prêt pour l'analyse.\n")
        self.log_text.see(tk.END)

    # -----------------------
    # Analyse A1 : tri multidimensionnel et groupes de 10
    # -----------------------
    def run_analysis(self):
        if self.df is None:
            self.log_text.insert(tk.END, "⚠ Aucun fichier chargé.\n")
            return
        if not self.param_cols or not self.response_cols:
            self.log_text.insert(tk.END, "⚠ Sélection incomplète (paramètres ou réponses manquantes).\n")
            return

        self.log_text.insert(tk.END, "\n=== Début Analyse A1 (tri multidimensionnel) ===\n")
        self.log_text.see(tk.END)

        # Tri lexicographique selon les paramètres (du bas vers le haut)
        try:
            df_sorted = self.df.sort_values(by=self.param_cols, ascending=True).reset_index(drop=True)
        except Exception as e:
            self.log_text.insert(tk.END, f"Erreur lors du tri par colonnes {self.param_cols} : {e}\n")
            self.log_text.see(tk.END)
            return

        total = len(df_sorted)
        step = 10
        groups = []
        for start in range(0, total, step):
            end = min(start + step, total)
            group = df_sorted.iloc[start:end]
            groups.append(group)

        self.log_text.insert(tk.END, f"Nombre total de points : {total}\n")
        self.log_text.insert(tk.END, f"Nombre de groupes formés (taille ≈10) : {len(groups)}\n")

        # calcul des moyennes
        results = []
        for idx, grp in enumerate(groups):
            mean_params = grp[self.param_cols].astype(float).mean().to_dict()
            mean_resps = grp[self.response_cols].astype(float).mean().to_dict()
            npoints = len(grp)
            results.append({
                "groupe_idx": idx,
                "n_points": npoints,
                "mean_params": mean_params,
                "mean_responses": mean_resps
            })
            self.log_text.insert(tk.END, f"groupe {idx}: n={npoints}, mean_responses={mean_resps}\n")

        self.results = results
        self.log_text.insert(tk.END, "=== Analyse A1 terminée. Résultats stockés dans self.results ===\n")
        self.log_text.see(tk.END)

    # -----------------------
    # Export CSV simple des résultats (si présents)
    # -----------------------
    def export_results_csv(self):
        if not self.results:
            self.log_text.insert(tk.END, "⚠ Pas de résultats à exporter. Lance d'abord l'analyse.\n")
            self.log_text.see(tk.END)
            return

        # convertir en DataFrame "aplati"
        rows = []
        for r in self.results:
            row = {"groupe_idx": r["groupe_idx"], "n_points": r["n_points"]}
            # ajouter paramètres moyens
            for k, v in r["mean_params"].items():
                row[f"mean_param__{k}"] = v
            # ajouter réponses moyennes
            for k, v in r["mean_responses"].items():
                row[f"mean_resp__{k}"] = v
            rows.append(row)

        out_df = pd.DataFrame(rows)

        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path:
            return
        out_df.to_csv(path, index=False)
        self.log_text.insert(tk.END, f"Résultats exportés vers : {path}\n")
        self.log_text.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = OptimizerGUI(root)
    root.geometry("920x680")
    root.mainloop()
