import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import threading
from core.image_logic import extract_images_from_pdf, generate_reference_profile

class PreparationWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Préparation des Images (PDF & Références)")
        self.geometry("800x650")
        
        # Variables Extraction
        self.pdf_path = tk.StringVar()
        self.extract_out_dir = tk.StringVar()
        
        # Variables Références
        self.ref_old_dir = tk.StringVar()
        self.ref_new_dir = tk.StringVar()
        self.ref_json_out = tk.StringVar(value="reference_profiles.json")

        # Layout
        self.columnconfigure(0, weight=1)
        
        self.create_extraction_ui()
        self.create_reference_ui()
        self.create_log_ui()

    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
    
    def update_log_threadsafe(self, msg):
        self.after(0, lambda: self.log(msg))

    # =========================================================================
    # 1. UI EXTRACTION PDF
    # =========================================================================
    def create_extraction_ui(self):
        frame = tk.LabelFrame(self, text="1. Extraction Images depuis PDF", padx=10, pady=10, fg="#333", font=("Arial", 10, "bold"))
        frame.pack(fill="x", padx=10, pady=5)
        
        # PDF Input
        f1 = tk.Frame(frame)
        f1.pack(fill="x", pady=2)
        tk.Label(f1, text="Fichier PDF :", width=15, anchor="w").pack(side="left")
        tk.Entry(f1, textvariable=self.pdf_path).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f1, text="...", command=self.browse_pdf).pack(side="left")

        # Dir Output
        f2 = tk.Frame(frame)
        f2.pack(fill="x", pady=2)
        tk.Label(f2, text="Dossier Sortie :", width=15, anchor="w").pack(side="left")
        tk.Entry(f2, textvariable=self.extract_out_dir).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f2, text="...", command=self.browse_extract_dir).pack(side="left")

        # Action
        self.btn_extract = tk.Button(frame, text="Extraire les pages en JPEG", bg="#e6f2ff", command=self.run_extraction)
        self.btn_extract.pack(fill="x", pady=5)

    def browse_pdf(self):
        f = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")], parent=self)
        if f: self.pdf_path.set(f)

    def browse_extract_dir(self):
        d = filedialog.askdirectory(parent=self)
        if d: self.extract_out_dir.set(d)

    def run_extraction(self):
        pdf = self.pdf_path.get()
        out = self.extract_out_dir.get()
        
        if not os.path.exists(pdf):
            messagebox.showerror("Erreur", "Fichier PDF introuvable.", parent=self)
            return
        if not out:
            messagebox.showerror("Erreur", "Veuillez choisir un dossier de sortie.", parent=self)
            return
            
        self.btn_extract.config(state="disabled")
        self.log(f"--- Démarrage Extraction : {os.path.basename(pdf)} ---")
        
        def task():
            try:
                extract_images_from_pdf(pdf, out, progress_callback=self.update_log_threadsafe)
                self.update_log_threadsafe("Extraction terminée.")
                messagebox.showinfo("Succès", "Extraction terminée avec succès.", parent=self)
            except ImportError as e:
                self.update_log_threadsafe(f"ERREUR: {e}")
                self.after(0, lambda: messagebox.showerror("Manque Librairie", str(e), parent=self))
            except Exception as e:
                self.update_log_threadsafe(f"ERREUR: {e}")
                self.after(0, lambda: messagebox.showerror("Erreur", str(e), parent=self))
            finally:
                self.after(0, lambda: self.btn_extract.config(state="normal"))

        threading.Thread(target=task).start()

    # =========================================================================
    # 2. UI CREATION REFERENCES
    # =========================================================================
    def create_reference_ui(self):
        frame = tk.LabelFrame(self, text="2. Création Profils Référence (Gabarits)", padx=10, pady=10, fg="#333", font=("Arial", 10, "bold"))
        frame.pack(fill="x", padx=10, pady=5)
        
        lbl = tk.Label(frame, text="Indiquez deux dossiers contenant des exemples d'images pour chaque catégorie.", justify="left", fg="gray")
        lbl.pack(anchor="w", pady=(0, 5))

        # Dossier ANCIEN
        f1 = tk.Frame(frame)
        f1.pack(fill="x", pady=2)
        tk.Label(f1, text="Dossier 'ANCIEN' :", width=18, anchor="w").pack(side="left")
        tk.Entry(f1, textvariable=self.ref_old_dir).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f1, text="...", command=lambda: self.browse_dir(self.ref_old_dir)).pack(side="left")

        # Dossier NOUVEAU
        f2 = tk.Frame(frame)
        f2.pack(fill="x", pady=2)
        tk.Label(f2, text="Dossier 'NOUVEAU' :", width=18, anchor="w").pack(side="left")
        tk.Entry(f2, textvariable=self.ref_new_dir).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f2, text="...", command=lambda: self.browse_dir(self.ref_new_dir)).pack(side="left")
        
        # Fichier Sortie JSON
        f3 = tk.Frame(frame)
        f3.pack(fill="x", pady=2)
        tk.Label(f3, text="Sortie JSON :", width=18, anchor="w").pack(side="left")
        tk.Entry(f3, textvariable=self.ref_json_out).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(f3, text="...", command=self.browse_save_json).pack(side="left")

        # Action
        self.btn_ref = tk.Button(frame, text="Générer Fichier JSON", bg="#e6ffe6", command=self.run_generation)
        self.btn_ref.pack(fill="x", pady=5)

    def browse_dir(self, var):
        d = filedialog.askdirectory(parent=self)
        if d: var.set(d)
        
    def browse_save_json(self):
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="reference_profiles.json", parent=self)
        if f: self.ref_json_out.set(f)

    def run_generation(self):
        old_d = self.ref_old_dir.get()
        new_d = self.ref_new_dir.get()
        json_out = self.ref_json_out.get()
        
        if not os.path.exists(old_d) or not os.path.exists(new_d):
            messagebox.showerror("Erreur", "Veuillez sélectionner des dossiers valides.", parent=self)
            return
            
        self.btn_ref.config(state="disabled")
        self.log("--- Génération Profils ---")
        
        def task():
            try:
                generate_reference_profile(old_d, new_d, json_out, progress_callback=self.update_log_threadsafe)
                self.update_log_threadsafe("Génération terminée.")
                self.after(0, lambda: messagebox.showinfo("Succès", f"Fichier créé : {json_out}", parent=self))
            except Exception as e:
                self.update_log_threadsafe(f"ERREUR: {e}")
                self.after(0, lambda: messagebox.showerror("Erreur", str(e), parent=self))
            finally:
                self.after(0, lambda: self.btn_ref.config(state="normal"))

        threading.Thread(target=task).start()

    # =========================================================================
    # UI LOGS
    # =========================================================================
    def create_log_ui(self):
        frame = tk.LabelFrame(self, text="Logs")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.txt_log = scrolledtext.ScrolledText(frame, height=8)
        self.txt_log.pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    PreparationWindow(root)
    root.mainloop()
