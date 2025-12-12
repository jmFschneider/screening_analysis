import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import threading
from core.image_logic import run_sorting_logic, run_fusion_logic

class ImageWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Finalisation Traitement Images")
        self.geometry("900x700")
        
        # Variables
        self.json_path = tk.StringVar()
        self.source_dir = tk.StringVar()
        
        self.sorted_dirs = {} # Pour stocker les chemins de sortie du tri
        
        # Layout principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0) # Step 1
        self.rowconfigure(1, weight=0) # Step 2
        self.rowconfigure(2, weight=1) # Logs

        self.create_step1_ui()
        self.create_step2_ui()
        self.create_log_ui()
        
        # Essayer de trouver le JSON automatiquement
        self.auto_locate_json()

    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def auto_locate_json(self):
        # Cherche dans "Type de fiche" ou racine
        candidates = [
            os.path.join("Type de fiche", "reference_profiles.json"),
            "reference_profiles.json"
        ]
        for c in candidates:
            if os.path.exists(c):
                self.json_path.set(os.path.abspath(c))
                self.log(f"Fichier référence trouvé : {c}")
                break

    # =========================================================================
    # UI STEP 1 : TRI
    # =========================================================================
    def create_step1_ui(self):
        frame = tk.LabelFrame(self, text="ÉTAPE 1 : Tri Automatique (Ancien / Nouveau)", padx=10, pady=10, fg="blue", font=("Arial", 10, "bold"))
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Ligne 1 : JSON
        f1 = tk.Frame(frame)
        f1.pack(fill="x", pady=2)
        tk.Label(f1, text="Profils Ref (JSON) :", width=15, anchor="w").pack(side="left")
        tk.Entry(f1, textvariable=self.json_path).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f1, text="...", command=self.browse_json).pack(side="left")

        # Ligne 2 : Source
        f2 = tk.Frame(frame)
        f2.pack(fill="x", pady=2)
        tk.Label(f2, text="Dossier Images :", width=15, anchor="w").pack(side="left")
        tk.Entry(f2, textvariable=self.source_dir).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f2, text="...", command=self.browse_source).pack(side="left")

        # Bouton Action
        self.btn_sort = tk.Button(frame, text="Lancer le Tri", bg="#dddddd", command=self.start_sorting)
        self.btn_sort.pack(fill="x", pady=5)

    def browse_json(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], parent=self)
        if f: self.json_path.set(f)

    def browse_source(self):
        d = filedialog.askdirectory(parent=self)
        if d: self.source_dir.set(d)

    def start_sorting(self):
        json_p = self.json_path.get()
        src_d = self.source_dir.get()
        
        if not os.path.exists(json_p):
            messagebox.showerror("Erreur", "Fichier JSON introuvable.", parent=self)
            return
        if not os.path.exists(src_d):
            messagebox.showerror("Erreur", "Dossier Source introuvable.", parent=self)
            return
            
        self.btn_sort.config(state="disabled")
        self.log("--- Démarrage du Tri ---")
        
        # Threading pour ne pas geler l'UI
        def task():
            try:
                # Appel Core Logic
                res = run_sorting_logic(src_d, json_p, progress_callback=self.update_log_threadsafe)
                self.sorted_dirs = res
                self.after(0, self.on_sort_finished)
            except Exception as e:
                self.update_log_threadsafe(f"ERREUR FATALE: {e}")
                self.after(0, lambda: self.btn_sort.config(state="normal"))

        threading.Thread(target=task).start()

    def update_log_threadsafe(self, msg):
        self.after(0, lambda: self.log(msg))

    def on_sort_finished(self):
        self.btn_sort.config(state="normal")
        self.log("--- Tri Terminé ---")
        messagebox.showinfo("Succès", "Le tri est terminé. Vous pouvez passer à la fusion.", parent=self)
        
        # Activer l'étape 2
        self.frame_step2.config(fg="green") # Visuel
        self.btn_fuse_new.config(state="normal")
        self.btn_fuse_old.config(state="normal")
        
        # Pré-remplir les chemins si possible (optionnel)

    # =========================================================================
    # UI STEP 2 : FUSION
    # =========================================================================
    def create_step2_ui(self):
        self.frame_step2 = tk.LabelFrame(self, text="ÉTAPE 2 : Fusion Recto/Verso", padx=10, pady=10, fg="gray", font=("Arial", 10, "bold"))
        self.frame_step2.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        lbl = tk.Label(self.frame_step2, text="Cette étape utilise les dossiers générés par le tri (TRI_NOUVEAU / TRI_ANCIEN).\nChoisissez quel groupe traiter :", justify="left")
        lbl.pack(anchor="w", pady=5)
        
        btn_frame = tk.Frame(self.frame_step2)
        btn_frame.pack(fill="x")
        
        # Bouton Fusion NOUVELLE (Avec Crop)
        self.btn_fuse_new = tk.Button(btn_frame, text="Fusionner 'NOUVELLES' (Avec Découpe Verso)", 
                                      bg="#ccffcc", state="disabled",
                                      command=lambda: self.start_fusion("new"))
        self.btn_fuse_new.pack(side="left", fill="x", expand=True, padx=5)

        # Bouton Fusion ANCIENNE (Sans Crop)
        self.btn_fuse_old = tk.Button(btn_frame, text="Fusionner 'ANCIENNES' (Sans Découpe)", 
                                      bg="#ffcccc", state="disabled",
                                      command=lambda: self.start_fusion("old"))
        self.btn_fuse_old.pack(side="left", fill="x", expand=True, padx=5)

    def start_fusion(self, mode):
        # Déterminer dossier source
        target_dir = ""
        do_crop = False
        
        if mode == "new":
            target_dir = self.sorted_dirs.get("new", "")
            if not target_dir: # Fallback manuel si tri pas fait dans cette session
                target_dir = os.path.join(self.source_dir.get(), "TRI_NOUVEAU")
            do_crop = True
        else:
            target_dir = self.sorted_dirs.get("old", "")
            if not target_dir:
                target_dir = os.path.join(self.source_dir.get(), "TRI_ANCIEN")
            do_crop = False
            
        if not os.path.exists(target_dir):
            # Demander manuellement si introuvable
            target_dir = filedialog.askdirectory(title=f"Sélectionnez le dossier {mode.upper()}", parent=self)
            if not target_dir: return

        self.log(f"--- Démarrage Fusion ({mode.upper()}) sur {target_dir} ---")
        
        def task():
            try:
                run_fusion_logic(target_dir, crop_verso=do_crop, progress_callback=self.update_log_threadsafe)
                self.update_log_threadsafe("--- Fusion Terminée ---")
            except Exception as e:
                self.update_log_threadsafe(f"ERREUR: {e}")

        threading.Thread(target=task).start()

    # =========================================================================
    # UI LOGS
    # =========================================================================
    def create_log_ui(self):
        frame = tk.LabelFrame(self, text="Journal d'exécution")
        frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        self.txt_log = scrolledtext.ScrolledText(frame, height=10)
        self.txt_log.pack(fill="both", expand=True)

if __name__ == "__main__":
    # Test autonome
    root = tk.Tk()
    win = ImageWindow(root)
    root.mainloop()
