import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# On tente d'importer shap ici pour l'utiliser dans le plot
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

class ShapWindow(tk.Toplevel):
    """
    Fenêtre d'analyse d'interprétabilité SHAP.
    Affiche :
    1. Beeswarm plot (Résumé global)
    2. Dependence plot (Analyse fine des interactions)
    """

    def __init__(self, master, df, params, response_cols):
        super().__init__(master)
        self.title("Analyse d'Interprétabilité (SHAP)")
        self.geometry("1000x800")

        self.df = df
        self.params = params
        self.active_params = list(params)  # Liste modifiable pour l'exclusion
        self.response = response_cols[0] if isinstance(response_cols, list) else response_cols
        
        self.shap_values = None
        self.X_data = None
        self.explainer = None

        # Layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Contrôles Haut
        self.rowconfigure(1, weight=0) # Contrôles Exclusion (Nouveau)
        self.rowconfigure(2, weight=1) # Graphique

        # ==========================
        # Zone de Contrôles (Haut)
        # ==========================
        ctrl_frame = tk.Frame(self)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        tk.Label(ctrl_frame, text=f"Réponse : {self.response}", font=("Arial", 10, "bold")).pack(side="left", padx=10)

        # Bouton de calcul
        self.btn_calc = tk.Button(ctrl_frame, text="Calculer SHAP", command=self.run_shap, bg="#dddddd")
        self.btn_calc.pack(side="left", padx=10)

        # Choix du type de graphique
        tk.Label(ctrl_frame, text=" |  Graphique : ").pack(side="left", padx=5)
        self.plot_type = tk.StringVar(value="summary")
        
        rb_sum = tk.Radiobutton(ctrl_frame, text="Résumé (Beeswarm)", variable=self.plot_type, 
                                value="summary", command=self.refresh_plot)
        rb_sum.pack(side="left")
        
        rb_dep = tk.Radiobutton(ctrl_frame, text="Dépendance", variable=self.plot_type, 
                                value="dependence", command=self.refresh_plot)
        rb_dep.pack(side="left")

        # Dropdown pour Dependence Plot (caché ou grisé initialement)
        # 1. Variable principale (X-axis)
        tk.Label(ctrl_frame, text="Var (X):").pack(side="left", padx=(10, 2))
        self.dep_var = tk.StringVar()
        self.combo_dep = ttk.Combobox(ctrl_frame, textvariable=self.dep_var, values=self.active_params, state="readonly", width=15)
        self.combo_dep.pack(side="left", padx=2)
        
        self.combo_dep.bind("<<ComboboxSelected>>", lambda e: self.refresh_plot())

        # 2. Variable d'interaction (Color / Y-axis logic)
        tk.Label(ctrl_frame, text="Interaction (Color):").pack(side="left", padx=(10, 2))
        self.int_var = tk.StringVar(value="Auto")
        self.combo_int = ttk.Combobox(ctrl_frame, textvariable=self.int_var, values=["Auto"], state="readonly", width=15)
        self.combo_int.pack(side="left", padx=2)
        self.combo_int.bind("<<ComboboxSelected>>", lambda e: self.refresh_plot())

        # ==========================
        # Zone Exclusion Dynamique
        # ==========================
        excl_frame = tk.Frame(self, bg="#f0f0f0", bd=1, relief="sunken")
        excl_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        tk.Label(excl_frame, text="Exclusion Dynamique :", bg="#f0f0f0", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        tk.Button(excl_frame, text="Exclure le Top 1 (Relancer)", 
                  command=lambda: self.exclude_top_k(1), bg="#ffcccc").pack(side="left", padx=5, pady=2)
        
        tk.Button(excl_frame, text="Exclure le Top 2 (Relancer)", 
                  command=lambda: self.exclude_top_k(2), bg="#ffcccc").pack(side="left", padx=5, pady=2)
                  
        tk.Button(excl_frame, text="Réinitialiser Paramètres", 
                  command=self.reset_params, bg="#ccffcc").pack(side="left", padx=15, pady=2)
        
        self.lbl_active = tk.Label(excl_frame, text="", bg="#f0f0f0", font=("Arial", 8, "italic"))
        self.lbl_active.pack(side="right", padx=10)

        # ==========================
        # Zone Graphique
        # ==========================
        # SHAP utilise matplotlib.pyplot de manière globale.
        # Pour l'intégrer proprement, on crée une Figure spécifique via plt.figure()
        # et on la passe au Canvas.
        self.fig = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=2, column=0, sticky="nsew")

        # Initial state
        self.toggle_controls()
        self.update_active_label()

    def toggle_controls(self):
        """Active/Désactive le dropdown selon le mode."""
        if self.plot_type.get() == "dependence":
            self.combo_dep.config(state="readonly")
            self.combo_int.config(state="readonly")
        else:
            self.combo_dep.config(state="disabled")
            self.combo_int.config(state="disabled")

    def update_active_label(self):
        count = len(self.active_params)
        total = len(self.params)
        self.lbl_active.config(text=f"Paramètres actifs : {count} / {total}")
        
        # Mettre à jour les listes des combobox
        self.combo_dep['values'] = self.active_params
        if self.active_params:
            if self.dep_var.get() not in self.active_params:
                self.combo_dep.current(0)
        
        self.combo_int['values'] = ["Auto"] + self.active_params

    def reset_params(self):
        self.active_params = list(self.params)
        self.update_active_label()
        self.run_shap()

    def exclude_top_k(self, k):
        """Exclut les k paramètres les plus importants de l'analyse actuelle."""
        if self.shap_values is None:
            messagebox.showinfo("Info", "Veuillez d'abord lancer un calcul SHAP.")
            return

        # 1. Calculer l'importance moyenne absolue pour chaque feature
        # shap_values est un array (n_samples, n_features)
        importances = np.abs(self.shap_values).mean(axis=0)
        
        # Associer noms et importances
        feature_importance = list(zip(self.X_data.columns, importances))
        
        # Trier par importance décroissante
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        # 2. Identifier les tops
        top_features = [x[0] for x in feature_importance[:k]]
        
        # 3. Retirer de la liste active
        removed_count = 0
        for f in top_features:
            if f in self.active_params:
                self.active_params.remove(f)
                removed_count += 1
        
        if removed_count == 0:
            messagebox.showinfo("Info", "Plus de paramètres à retirer.")
            return

        # 4. Relancer
        messagebox.showinfo("Exclusion", f"Paramètre(s) retiré(s) : {', '.join(top_features)}\nLe modèle va être ré-entraîné.")
        self.update_active_label()
        self.run_shap()

    def run_shap(self):
        """Lance le calcul SHAP (peut être long)."""
        if not SHAP_AVAILABLE:
            messagebox.showerror("Erreur", "La librairie 'shap' n'est pas installée.\nInstallez-la avec : pip install shap")
            return
            
        if not self.active_params:
            messagebox.showwarning("Attention", "Aucun paramètre actif !")
            return

        self.config(cursor="watch")
        self.btn_calc.config(state="disabled", text="Calcul en cours...")
        self.update()

        try:
            from core.shap_analysis import compute_shap_analysis
            
            # On utilise self.active_params au lieu de self.params
            self.shap_values, self.X_data, self.explainer = compute_shap_analysis(
                self.df, self.active_params, self.response
            )
            
            self.refresh_plot()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul SHAP :\n{e}")
        finally:
            self.config(cursor="")
            self.btn_calc.config(state="normal", text="Recalculer SHAP")

    def refresh_plot(self):
        """Met à jour le graphique."""
        self.toggle_controls()
        
        if self.shap_values is None:
            return

        # Nettoyer la figure
        self.fig.clear()
        
        # Activer la figure pour que SHAP dessine dessus
        plt.figure(self.fig.number)
        
        ptype = self.plot_type.get()
        
        try:
            if ptype == "summary":
                # Beeswarm plot
                shap.summary_plot(self.shap_values, self.X_data, show=False, plot_size=None)
                # Le titre n'est pas ajouté par défaut
                plt.title(f"SHAP Summary (Beeswarm) - {self.response}")
                
            elif ptype == "dependence":
                # Dependence plot
                feature_name = self.dep_var.get()
                if not feature_name:
                    return
                
                # Gestion interaction
                interaction_val = self.int_var.get()
                if interaction_val == "Auto":
                    idx = 'auto'
                else:
                    idx = interaction_val

                # dependence_plot dessine aussi sur la figure active
                # interaction_index='auto' trouve automatiquement la variable d'interaction la plus forte
                shap.dependence_plot(feature_name, self.shap_values, self.X_data, 
                                     show=False, interaction_index=idx, ax=plt.gca())
                plt.title(f"SHAP Dependence - {feature_name}")

            # Force le redessin
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Erreur d'affichage", f"Impossible d'afficher le graphique :\n{e}")
