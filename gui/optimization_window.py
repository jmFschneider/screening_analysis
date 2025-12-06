import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class OptimizationWindow(tk.Toplevel):
    """
    Fenêtre affichant les zones optimales (Bump Hunting via Arbre de Décision).
    """

    def __init__(self, master, df, params, response_cols):
        super().__init__(master)
        self.title("Découverte de Zones Optimales")
        self.geometry("1100x700")

        self.df = df
        self.params = params
        self.response = response_cols[0] if isinstance(response_cols, list) else response_cols
        
        self.zones = []

        # Layout principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Top bar
        self.rowconfigure(1, weight=1) # Contenu (PanedWindow)

        # ==========================
        # Barre supérieure
        # ==========================
        top_frame = tk.Frame(self, padx=10, pady=10)
        top_frame.grid(row=0, column=0, sticky="ew")
        
        tk.Label(top_frame, text=f"Optimisation pour : {self.response}", font=("Arial", 11, "bold")).pack(side="left")
        
        tk.Button(top_frame, text="Lancer la recherche", command=self.run_search, bg="#dddddd").pack(side="left", padx=20)

        # Paramètres simples
        tk.Label(top_frame, text="Profondeur Arbre :",).pack(side="left", padx=5)
        self.spin_depth = tk.Spinbox(top_frame, from_=2, to=6, width=3)
        self.spin_depth.delete(0, "end")
        self.spin_depth.insert(0, 4) # Défaut
        self.spin_depth.pack(side="left")

        # ==========================
        # Contenu divisé (Gauche: Liste Zones, Droite: Détail/Visu)
        # ==========================
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4)
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # --- Panneau Gauche : Liste des Top Zones ---
        left_frame = tk.LabelFrame(paned, text="Top Zones Prometteuses")
        paned.add(left_frame, minsize=300)
        
        # Treeview pour lister les zones
        cols = ("Rank", "Mean", "Count")
        self.tree = ttk.Treeview(left_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("Rank", text="#")
        self.tree.heading("Mean", text="Moyenne Zone")
        self.tree.heading("Count", text="Nb Points")
        
        self.tree.column("Rank", width=40, anchor="center")
        self.tree.column("Mean", width=100, anchor="center")
        self.tree.column("Count", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_zone_select)

        # --- Panneau Droite : Détails de la zone sélectionnée ---
        right_frame = tk.Frame(paned)
        paned.add(right_frame, minsize=500)
        
        # Zone Texte pour les règles
        self.lbl_detail = tk.Label(right_frame, text="Détails de la zone sélectionnée", font=("Arial", 10, "bold"))
        self.lbl_detail.pack(anchor="w", pady=5)
        
        self.txt_rules = scrolledtext.ScrolledText(right_frame, height=8, font=("Consolas", 10), bg="#f9f9f9")
        self.txt_rules.pack(fill="x", padx=5)

        # Zone Graphique (Boxplot comparatif : Global vs Zone)
        self.fig = Figure(figsize=(5, 3))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, pady=5)

        # --- Panneau Optimisation Fine ---
        opt_frame = tk.LabelFrame(right_frame, text="Exploration Fine (Métamodèle)", padx=5, pady=5)
        opt_frame.pack(fill="x", padx=5, pady=5)

        # Contrôles
        ctrl_sub = tk.Frame(opt_frame)
        ctrl_sub.pack(fill="x")
        
        tk.Label(ctrl_sub, text="Extension du domaine (%) :").pack(side="left")
        self.scale_ext = tk.Scale(ctrl_sub, from_=0, to=20, orient=tk.HORIZONTAL, length=150)
        self.scale_ext.set(5) # Défaut 5%
        self.scale_ext.pack(side="left", padx=10)
        
        tk.Button(ctrl_sub, text="Chercher le Maximum (Est.)", 
                  command=self.run_fine_optimization, bg="#ccffcc").pack(side="left", padx=10)

        # Résultat texte
        self.txt_opt_res = scrolledtext.ScrolledText(opt_frame, height=5, font=("Consolas", 9), bg="#e6ffe6")
        self.txt_opt_res.pack(fill="x", pady=5)


    def run_search(self):
        try:
            from core.optimization_finder import find_optimal_zones
            
            depth = int(self.spin_depth.get())
            
            # Appel algo
            self.zones = find_optimal_zones(
                self.df, self.params, self.response,
                top_k=6, # On en récupère un peu plus pour laisser le choix
                max_depth=depth
            )
            
            # Remplir la liste
            self.tree.delete(*self.tree.get_children())
            
            global_mean = self.df[self.response].mean()
            
            for i, z in enumerate(self.zones):
                mean_val = z['mean']
                # gain = ((mean_val - global_mean) / abs(global_mean)) * 100
                
                # Insertion dans le tableau
                self.tree.insert("", "end", iid=i, values=(i+1, f"{mean_val:.4f}", z['count']))

            # Sélectionner le premier par défaut
            if self.zones:
                self.tree.selection_set(0)
            else:
                messagebox.showinfo("Info", "Aucune zone significative trouvée.")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def on_zone_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        idx = int(selected[0])
        zone = self.zones[idx]
        
        # 1. Afficher les règles
        self.txt_rules.delete("1.0", tk.END)
        self.txt_rules.insert(tk.END, f"=== Zone #{idx+1} ===\n")
        self.txt_rules.insert(tk.END, f"Moyenne Locale : {zone['mean']:.4f}\n")
        self.txt_rules.insert(tk.END, f"Moyenne Globale: {self.df[self.response].mean():.4f}\n")
        self.txt_rules.insert(tk.END, "-"*30 + "\nCONSIGNES (Règles) :\n")
        
        for r in zone['rules']:
            self.txt_rules.insert(tk.END, f"• {r}\n")

        if not zone['rules']:
            self.txt_rules.insert(tk.END, "(Toute la population - Arbre racine)\n")

        # Reset Fine Opt
        self.txt_opt_res.delete("1.0", tk.END)

        # 2. Afficher le graphique comparatif
        self.plot_comparison(zone)

    def run_fine_optimization(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Veuillez sélectionner une zone d'abord.")
            return
        
        idx = int(selected[0])
        zone = self.zones[idx]
        expansion = self.scale_ext.get() / 100.0 # Convertir % en float
        
        self.txt_opt_res.delete("1.0", tk.END)
        self.txt_opt_res.insert(tk.END, "Simulation en cours...\n")
        self.update()
        
        try:
            from core.optimization_finder import refine_optimal_point
            
            best_val, best_coords = refine_optimal_point(
                self.df, self.params, self.response,
                zone_bounds=zone['bounds'],
                expansion_pct=expansion
            )
            
            self.txt_opt_res.delete("1.0", tk.END)
            self.txt_opt_res.insert(tk.END, f"--- Optimum Estimé (Ext: {expansion*100:.0f}%) ---\n")
            self.txt_opt_res.insert(tk.END, f"Réponse Prévue : {best_val:.4f}\n")
            self.txt_opt_res.insert(tk.END, "Paramètres :\n")
            for p, v in best_coords.items():
                self.txt_opt_res.insert(tk.END, f"  {p:<15} : {v:.4f}\n")
                
        except Exception as e:
            self.txt_opt_res.insert(tk.END, f"Erreur: {e}")

    def plot_comparison(self, zone):
        self.ax.clear() 
        
        # Données Globales
        data_global = self.df[self.response].values
        
        # Données Locales (On filtre le DF pour retrouver les points de cette zone)
        # Pour simplifier l'affichage sans re-filtrer lourdement, 
        # on peut juste afficher la moyenne zone vs distribution globale
        # Ou mieux : simuler une distribution normale autour de la moyenne zone (approx)
        # MAIS l'idéal est de récupérer les indices si possible.
        # Pour l'instant, le `find_optimal_zones` renvoie stats agrégées.
        
        # On va afficher : 
        # 1. Histogramme gris de TOUTE la distribution
        # 2. Ligne verticale ROUGE pour la moyenne de la ZONE
        # 3. Ligne verticale NOIRE pour la moyenne GLOBALE
        
        self.ax.hist(data_global, bins=30, color='lightgray', label='Distribution Globale', alpha=0.7)
        
        global_mean = data_global.mean()
        zone_mean = zone['mean']
        
        self.ax.axvline(global_mean, color='black', linestyle='--', linewidth=2, label=f'Moyenne Globale ({global_mean:.2f})')
        self.ax.axvline(zone_mean, color='red', linewidth=3, label=f'Moyenne Zone ({zone_mean:.2f})')
        
        self.ax.set_title(f"Positionnement de la Zone #{self.tree.selection()[0]} (rouge)")
        self.ax.legend()
        self.canvas.draw()
