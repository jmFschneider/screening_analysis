import tkinter as tk
from tkinter import messagebox, scrolledtext
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class SobolWindow(tk.Toplevel):
    """
    Fenêtre d'analyse de sensibilité de Sobol (Indices S1 et ST).
    Utilise un Random Forest comme métamodèle pour calculer les indices.
    """

    def __init__(self, master, df, params, response_cols):
        super().__init__(master)
        self.title("Analyse de Sobol (S1 / ST)")
        self.geometry("900x700")

        self.df = df
        self.params = params
        # On prend la première réponse par défaut si liste
        self.response = response_cols[0] if isinstance(response_cols, list) else response_cols
        self.response_cols = response_cols # On garde la liste complète si besoin de changer

        self.results = None

        # Layout principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Contrôles
        self.rowconfigure(1, weight=4) # Graphique
        self.rowconfigure(2, weight=1) # Logs/Texte

        # ==========================
        # Zone de contrôles
        # ==========================
        ctrl_frame = tk.Frame(self)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        tk.Label(ctrl_frame, text=f"Réponse : {self.response}", font=("Arial", 10, "bold")).pack(side="left", padx=10)
        
        tk.Button(ctrl_frame, text="Lancer Analyse Sobol", 
                  command=self.run_sobol_analysis, bg="#dddddd").pack(side="left", padx=10)

        # ==========================
        # Zone Graphique
        # ==========================
        self.fig = Figure(figsize=(7, 5))
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # ==========================
        # Zone Logs / Résultats chiffrés
        # ==========================
        self.log_text = scrolledtext.ScrolledText(self, height=10)
        self.log_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        self.log_text.insert(tk.END, "Prêt pour l'analyse de Sobol.\n")
        self.log_text.insert(tk.END, "Cette méthode utilise un Random Forest pour approximer la surface de réponse\n")
        self.log_text.insert(tk.END, "et calculer les indices de variance (S1 : effet principal, ST : effet total).\n\n")

    def run_sobol_analysis(self):
        self.log_text.insert(tk.END, "Calcul en cours... (génération échantillons + prédictions)\n")
        self.update_idletasks()

        try:
            from core.sobol_analysis import compute_sobol_indices
            
            # Calcul
            # On utilise N=2048 par défaut pour une bonne précision sans être trop lent
            res = compute_sobol_indices(self.df, self.params, self.response, n_samples=2048)
            self.results = res
            
            # Affichage Texte
            self.log_text.insert(tk.END, "-"*40 + "\n")
            self.log_text.insert(tk.END, f"Résultats Sobol pour '{self.response}' :\n")
            self.log_text.insert(tk.END, f"{ 'Paramètre':<20} {'S1':<10} {'ST':<10}\n")
            self.log_text.insert(tk.END, "-"*40 + "\n")
            
            # Tri par ST décroissant
            sorted_params = res["ST"].sort_values(ascending=False).index
            
            for p in sorted_params:
                s1_val = res["S1"][p]
                st_val = res["ST"][p]
                self.log_text.insert(tk.END, f"{p:<20} {s1_val:.4f}     {st_val:.4f}\n")
            
            self.log_text.insert(tk.END, "\n")
            
            # Affichage Graphique
            self.plot_results(res, sorted_params)

        except ImportError as e:
            messagebox.showerror("Erreur", str(e))
            self.log_text.insert(tk.END, f"ERREUR : {e}\n")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")
            self.log_text.insert(tk.END, f"ERREUR : {e}\n")

    def plot_results(self, res, sorted_params):
        self.ax.clear()
        
        # Préparation des données
        indices = np.arange(len(sorted_params))
        width = 0.35
        
        s1_vals = [res["S1"][p] for p in sorted_params]
        st_vals = [res["ST"][p] for p in sorted_params]
        
        # Barres
        rects1 = self.ax.bar(indices - width/2, s1_vals, width, label='S1 (Effet Principal)', alpha=0.8)
        rects2 = self.ax.bar(indices + width/2, st_vals, width, label='ST (Effet Total)', alpha=0.8)
        
        # Labels
        self.ax.set_ylabel('Indice de Sobol')
        self.ax.set_title(f'Indices de Sobol - {self.response}')
        self.ax.set_xticks(indices)
        self.ax.set_xticklabels(sorted_params, rotation=45, ha="right")
        self.ax.legend()
        
        self.ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        self.fig.tight_layout()
        self.canvas.draw()
