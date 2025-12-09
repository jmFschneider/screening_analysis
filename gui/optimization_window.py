import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import glob
import cv2
from PIL import Image, ImageTk

class OptimizationWindow(tk.Toplevel):
    """
    Fenêtre affichant les zones optimales (Bump Hunting via Arbre de Décision).
    """

    def __init__(self, master, df, params, response_cols, analysis_name="Analyse"):
        super().__init__(master)
        self.title("Découverte de Zones Optimales")
        self.geometry("1100x700")

        self.df = df
        self.params = params
        self.analysis_name = analysis_name
        self.response = response_cols[0] if isinstance(response_cols, list) else response_cols
        
        self.zones = []
        self.last_optimized_coords = None

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
        
        # Info Distance Max
        self.lbl_max_dist = tk.Label(top_frame, text="Dist. Max: -", fg="#333333", bg="#E0E0FF", font=("Arial", 11, "bold"), relief="solid", bd=1)
        self.lbl_max_dist.pack(side="left", padx=15, ipady=3)

        # ==========================
        # Contenu divisé (Gauche: Liste Zones, Droite: Détail/Visu)
        # ==========================
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4)
        paned.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # --- Panneau Gauche : Liste des Top Zones ---
        left_frame = tk.LabelFrame(paned, text="Top Zones Prometteuses")
        paned.add(left_frame, minsize=300)
        
        # Treeview pour lister les zones
        cols = ("Rank", "Mean", "Count", "Dist")
        self.tree = ttk.Treeview(left_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("Rank", text="#")
        self.tree.heading("Mean", text="Moyenne")
        self.tree.heading("Count", text="Nb Pts")
        self.tree.heading("Dist", text="Dist. Ref")
        
        self.tree.column("Rank", width=30, anchor="center")
        self.tree.column("Mean", width=80, anchor="center")
        self.tree.column("Count", width=60, anchor="center")
        self.tree.column("Dist", width=60, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_zone_select)

        # --- Sélection Source Image ---
        img_frame = tk.LabelFrame(left_frame, text="Source Image Test", padx=5, pady=5)
        img_frame.pack(fill="x", padx=5, pady=5)

        tk.Button(img_frame, text="Choisir Dossier...", command=self.select_image_folder, bg="#eeeeee").pack(fill="x", pady=2)
        
        self.combo_images = ttk.Combobox(img_frame, state="readonly")
        self.combo_images.pack(fill="x", pady=2)
        self.combo_images.set("Aucune image")

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
        
        tk.Button(ctrl_sub, text="Visualiser Rendu", 
                  command=self.visualize_render, bg="#ffcc99").pack(side="left", padx=10)

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
            
            # --- Calcul des Distances ---
            # 1. Paramètres actifs (on prend tous ceux analysés)
            active_params = self.params
            
            # 2. Distance Max Théorique (Diagonale d'un hypercube unitaire de dim N)
            max_possible_dist = np.sqrt(len(active_params))
            self.lbl_max_dist.config(text=f"Dist. Max Espace: {max_possible_dist:.2f}")
            
            # Calculer les min/max globaux
            global_bounds = {}
            for p in active_params:
                global_bounds[p] = (self.df[p].min(), self.df[p].max())

            # Helper pour obtenir le centre normalisé [0,1] d'une zone
            def get_norm_center(z_bounds):
                coords = []
                for p in active_params:
                    glob_min, glob_max = global_bounds[p]
                    
                    # Centre de la zone pour ce paramètre
                    # z_bounds contient seulement les contraintes actives
                    z_min, z_max = z_bounds.get(p, (-np.inf, np.inf))
                    
                    # Remplacer les infinis par les bornes globales
                    if z_min == -np.inf: z_min = glob_min
                    if z_max == np.inf: z_max = glob_max
                    
                    # Clamper au cas où l'arbre a fait une coupure bizarre
                    z_min = max(glob_min, z_min)
                    z_max = min(glob_max, z_max)
                    
                    z_c = (z_min + z_max) / 2.0
                    
                    # Normalisation
                    if glob_max > glob_min:
                        norm = (z_c - glob_min) / (glob_max - glob_min)
                    else:
                        norm = 0.5
                    coords.append(norm)
                return np.array(coords)

            # 3. Référence (Zone #1)
            ref_vector = None
            if self.zones:
                ref_vector = get_norm_center(self.zones[0]['bounds'])

            for i, z in enumerate(self.zones):
                mean_val = z['mean']
                
                # Calcul distance
                dist_str = "-"
                if ref_vector is not None:
                    curr_vector = get_norm_center(z['bounds'])
                    # Distance Euclidienne
                    d = np.linalg.norm(curr_vector - ref_vector)
                    dist_str = f"{d:.2f}"

                # Insertion dans le tableau
                self.tree.insert("", "end", iid=i, values=(i+1, f"{mean_val:.4f}", z['count'], dist_str))

            # Sélectionner le premier par défaut
            if self.zones:
                self.tree.selection_set(0)
            else:
                messagebox.showinfo("Info", "Aucune zone significative trouvée.")

        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            import traceback
            traceback.print_exc()

    def on_zone_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        # Reset Fine Opt coords pour éviter confusion si on clique visualier direct
        self.last_optimized_coords = None

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
            
            self.last_optimized_coords = best_coords

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

    def select_image_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner le dossier d'images")
        if folder:
            # Extensions courantes
            exts = ['*.png', '*.jpg', '*.jpeg', '*.tif', '*.tiff', '*.bmp']
            files = []
            for ext in exts:
                files.extend(glob.glob(os.path.join(folder, ext)))
            
            # Garder juste les noms de fichiers
            files = [os.path.basename(f) for f in files]
            files.sort()
            
            self.combo_images['values'] = files
            if files:
                self.combo_images.current(0)
                # Stocker le chemin complet du dossier
                self.image_folder = folder
            else:
                messagebox.showinfo("Info", "Aucune image trouvée dans ce dossier.")

    def visualize_render(self):
        # 1. Vérifier qu'une image est sélectionnée
        if not hasattr(self, 'image_folder') or not self.combo_images.get():
            messagebox.showwarning("Attention", "Veuillez sélectionner une image source d'abord (Panneau Gauche).")
            return
            
        img_name = self.combo_images.get()
        img_path = os.path.join(self.image_folder, img_name)
        
        # 2. Récupérer les paramètres
        # Priorité : Optimisation Fine > Centre Zone Sélectionnée > Rien
        params_to_use = {}
        
        if self.last_optimized_coords:
             params_to_use = self.last_optimized_coords
             source_type = "Optimisation Fine"
        else:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Attention", "Veuillez sélectionner une zone.")
                return
            
            idx = int(selected[0])
            zone = self.zones[idx]
            z_bounds = zone['bounds']
            
            # Pour chaque paramètre possible, on calcule le centre
            # Si le param n'est pas dans z_bounds, on prend le centre global
            temp_params = {}
            for col in self.params: # self.params est la liste des colonnes
                glob_min = self.df[col].min()
                glob_max = self.df[col].max()
                
                # Bornes locales ou globales par défaut
                local_min, local_max = z_bounds.get(col, (-np.inf, np.inf))
                
                if local_min == -np.inf: local_min = glob_min
                if local_max == np.inf: local_max = glob_max
                
                # Centre
                val = (local_min + local_max) / 2.0
                temp_params[col] = val
                
            params_to_use = temp_params
            source_type = f"Centre Zone #{idx+1}"

        # 3. Mapper les paramètres pour ocr_quality_audit
        # Paramètres attendus par pipeline_complet :
        # line_h_size, line_v_size, dilate_iter, norm_kernel, denoise_h, noise_threshold, bin_block_size, bin_c
        
        try:
            # Copie pour modification
            p = params_to_use.copy()
            
            # Préparation du dict final avec typage correct
            ocr_params = {
                'line_h_size': int(p.get('line_h_size', 20)),
                'line_v_size': int(p.get('line_v_size', 20)),
                'dilate_iter': int(p.get('dilate_iter', 1)),
                'norm_kernel': int(p.get('norm_kernel', 79)), # Doit être impair
                'denoise_h': float(p.get('denoise_h', 10.0)),
                'noise_threshold': int(p.get('noise_threshold', 200)), # Souvent int pour seuil pixel
                'bin_block_size': int(p.get('bin_block_size', 11)), # Impair
                'bin_c': float(p.get('bin_c', 2.0))
            }
            
            # Correction parité pour kernels (OpenCV exige impair)
            if ocr_params['norm_kernel'] % 2 == 0: ocr_params['norm_kernel'] += 1
            if ocr_params['bin_block_size'] % 2 == 0: ocr_params['bin_block_size'] += 1
            if ocr_params['line_h_size'] < 1: ocr_params['line_h_size'] = 1
            if ocr_params['line_v_size'] < 1: ocr_params['line_v_size'] = 1

            # 4. Traitement
            import ocr_quality_audit
            
            # Lire image avec OpenCV (niveaux de gris)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError("Impossible de lire l'image.")

            # Appliquer Pipeline
            processed_img = ocr_quality_audit.pipeline_complet(img, ocr_params)
            
            # 5. Afficher Résultat
            self.show_image_window(img, processed_img, img_name, source_type, ocr_params)

        except Exception as e:
            messagebox.showerror("Erreur de Traitement", f"Le traitement a échoué :\n{e}")
            import traceback
            traceback.print_exc()

    def save_image_action(self, img_array, params, batch_mode=False, img_name="result"):
        """
        Sauvegarde l'image (ou le lot) et consigne les détails dans un fichier CSV.
        """
        import datetime
        import ocr_quality_audit # Requis pour le mode batch
        
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%H-%M-%S")
        date_log = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Préparation du nom par défaut pour la boite de dialogue
        base_img_name = os.path.splitext(img_name)[0]
        default_name = f"{base_img_name}_{self.analysis_name}_{timestamp_str}.png"
        
        # Nettoyage
        keep = (' ', '.', '_', '-')
        safe_name = "".join(c for c in default_name if c.isalnum() or c in keep).strip()

        file_path = filedialog.asksaveasfilename(
            title="Sauvegarder le résultat" + (" (Lot)" if batch_mode else ""),
            defaultextension=".png",
            initialfile=safe_name,
            filetypes=[("PNG Image", "*.png")]
        )
        
        if not file_path:
            return

        save_dir = os.path.dirname(file_path)
        log_file = os.path.join(save_dir, "render_history_log.csv") # Changed extension to .csv
        
        # Determine parameter names for CSV header (assuming consistent params structure)
        # This assumes 'params' keys are consistent across all calls within a session
        param_names = list(params.keys())
        header = ["Image", "Date"] + param_names

        try:
            # Check if log file exists to decide whether to write header
            file_exists = os.path.exists(log_file)
            
            # Function to write a log entry
            def write_log_entry(img_filename, log_date, p_dict):
                data_row_values = [img_filename, log_date] + [str(p_dict.get(p_name, "")) for p_name in param_names]
                csv_line = ",".join(data_row_values) + "\n"
                
                with open(log_file, "a", encoding="utf-8") as f:
                    # Write header only if file is new
                    if not file_exists and f.tell() == 0: # f.tell() == 0 ensures it's truly empty
                        f.write(",".join(header) + "\n")
                    f.write(csv_line)

            # === MODE BATCH ===
            if batch_mode:
                if not hasattr(self, 'image_folder') or not self.image_folder:
                    raise ValueError("Le dossier source des images est introuvable.")
                
                # Récupérer toutes les images du dossier source
                exts = ['*.png', '*.jpg', '*.jpeg', '*.tif', '*.tiff', '*.bmp']
                files = []
                for ext in exts:
                    files.extend(glob.glob(os.path.join(self.image_folder, ext)))
                
                if not files:
                    raise ValueError("Aucune image trouvée dans le dossier source.")

                count = 0
                for f_path in files:
                    f_name = os.path.basename(f_path)
                    f_base = os.path.splitext(f_name)[0]
                    
                    # Lecture
                    img_in = cv2.imread(f_path, cv2.IMREAD_GRAYSCALE)
                    if img_in is None: continue
                    
                    # Traitement
                    res = ocr_quality_audit.pipeline_complet(img_in, params)
                    
                    # Nom de sortie : Original_Analyse_Heure.png
                    out_name = f"{f_base}_{self.analysis_name}_{timestamp_str}.png"
                    out_path = os.path.join(save_dir, out_name)
                    
                    # Sauvegarde
                    cv2.imwrite(out_path, res)
                    
                    # Log
                    write_log_entry(out_name, date_log, params)
                    
                    count += 1
                
                messagebox.showinfo("Succès Batch", f"{count} images traitées et sauvegardées dans :\n{save_dir}\nLog CSV mis à jour.")

            # === MODE SINGLE ===
            else:
                # On utilise le chemin choisi par l'utilisateur
                cv2.imwrite(file_path, img_array)
                
                saved_name = os.path.basename(file_path)
                write_log_entry(saved_name, date_log, params)
                
                messagebox.showinfo("Succès", f"Image sauvegardée : {saved_name}\nLog CSV mis à jour.")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Echec de la sauvegarde :\n{e}")
            import traceback
            traceback.print_exc()

    def show_image_window(self, original, processed, title, source_info, params):
        win = tk.Toplevel(self)
        win.title(f"Visualisation : {title} ({source_info})")
        win.geometry("1200x800")
        
        # Convertir OpenCV (BGR/Gray) -> PIL -> ImageTk
        # Original
        orig_pil = Image.fromarray(original)
        
        # Processed (s'assurer uint8)
        proc_pil = Image.fromarray(processed)
        
        # Redimensionner pour affichage si trop grand (max height 600)
        max_h = 600
        scale = min(1.0, max_h / orig_pil.height)
        if scale < 1.0:
            new_size = (int(orig_pil.width * scale), int(orig_pil.height * scale))
            orig_pil = orig_pil.resize(new_size, Image.Resampling.LANCZOS)
            proc_pil = proc_pil.resize(new_size, Image.Resampling.LANCZOS)
            
        orig_tk = ImageTk.PhotoImage(orig_pil)
        proc_tk = ImageTk.PhotoImage(proc_pil)
        
        # Layout
        frame_imgs = tk.Frame(win)
        frame_imgs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Gauche : Original
        lbl_orig = tk.Label(frame_imgs, text="Original", font=("Arial", 12, "bold"))
        lbl_orig.grid(row=0, column=0)
        lbl_img_orig = tk.Label(frame_imgs, image=orig_tk)
        lbl_img_orig.image = orig_tk # Keep ref
        lbl_img_orig.grid(row=1, column=0, padx=5)
        
        # Droite : Traité
        lbl_proc = tk.Label(frame_imgs, text="Traité (Pipeline)", font=("Arial", 12, "bold"))
        lbl_proc.grid(row=0, column=1)
        lbl_img_proc = tk.Label(frame_imgs, image=proc_tk)
        lbl_img_proc.image = proc_tk # Keep ref
        lbl_img_proc.grid(row=1, column=1, padx=5)

        # Contrôles Sauvegarde
        ctrl_frame = tk.Frame(frame_imgs, pady=10)
        ctrl_frame.grid(row=2, column=1)

        self.var_batch_process = tk.BooleanVar(value=False)
        chk_batch = tk.Checkbutton(ctrl_frame, text="Traiter toutes les images du dossier", 
                                   variable=self.var_batch_process, bg="#ffffcc", anchor="w")
        chk_batch.pack(side="top", pady=2)

        # Bouton Sauvegarde
        tk.Button(ctrl_frame, text="Sauvegarder l'image (ou le lot)", bg="#d9f2d9", font=("Arial", 10, "bold"),
                  command=lambda: self.save_image_action(processed, params, 
                                                         batch_mode=self.var_batch_process.get(), 
                                                         img_name=title))\
            .pack(side="top", pady=5)
        
        # Infos Paramètres en bas
        txt_info = scrolledtext.ScrolledText(win, height=6, bg="#f0f0f0")
        txt_info.pack(fill="x", padx=10, pady=10)
        
        txt_info.insert(tk.END, f"Source Paramètres : {source_info}\n")
        txt_info.insert(tk.END, "Paramètres appliqués :\n")
        txt_info.insert(tk.END, str(params))
