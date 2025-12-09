import sys
import os
import struct
import math
from pypdf import PdfReader

# Table de quantification Luminance standard (IJG)
# Utilisée comme référence pour calculer le facteur de qualité
STD_LUMINANCE_QUANT_TBL = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99
]

def estimate_jpeg_quality(jpeg_data):
    """
    Estime la qualité JPEG (1-100) en analysant la table de quantification (DQT).
    Retourne une chaîne (ex: "~85") ou None si échec.
    """
    try:
        # Recherche du marqueur DQT (Define Quantization Table) : FF DB
        # On parcourt le flux d'octets
        i = 0
        while i < len(jpeg_data) - 1:
            if jpeg_data[i] == 0xFF and jpeg_data[i+1] == 0xDB:
                # DQT trouvé !
                # Structure: [FF DB] [Length (2)] [QT Info (1)] [Table (64)]
                length = struct.unpack(">H", jpeg_data[i+2:i+4])[0]
                
                # On regarde la première table (souvent Luminance, ID 0)
                # QT Info : bit 0-3 = ID, bit 4-7 = précision
                qt_info = jpeg_data[i+4]
                qt_id = qt_info & 0x0F
                
                if qt_id == 0: # Table 0 (Luminance)
                    # Lire les 64 octets de la table
                    table_data = jpeg_data[i+5 : i+5+64]
                    if len(table_data) < 64:
                        return None
                    
                    # Calculer le facteur de mise à l'échelle moyen par rapport au standard
                    total_scale = 0
                    for j in range(64):
                        val_file = table_data[j]
                        val_std = STD_LUMINANCE_QUANT_TBL[j]
                        # Eviter division par 0
                        if val_std == 0: val_std = 1
                        total_scale += (val_file * 100.0) / val_std
                        
                    avg_scale = total_scale / 64.0
                    
                    # Formule inverse de l'IJG pour retrouver la Qualité Q
                    # Scale = 5000 / Q (si Q < 50)
                    # Scale = 200 - 2*Q (si Q > 50)
                    
                    # Donc :
                    # Si Scale > 100 (Qualité < 50) -> Q = 5000 / Scale
                    # Si Scale <= 100 (Qualité >= 50) -> Q = (200 - Scale) / 2
                    
                    if avg_scale == 0: 
                        est_quality = 100
                    elif avg_scale >= 100:
                        est_quality = 5000 / avg_scale
                    else:
                        est_quality = (200 - avg_scale) / 2
                    
                    return int(est_quality)
                
                # Avancer au prochain segment
                i += length + 2
            else:
                i += 1
                # Optimisation : Si on trouve FF C0 (Start of Frame), on arrête, les DQT sont avant.
                if i < len(jpeg_data)-1 and jpeg_data[i] == 0xFF and jpeg_data[i+1] == 0xC0:
                    break
        return None
    except Exception:
        return None

def get_obj_filter_and_quality(obj):
    """Extrait le filtre et tente d'estimer la qualité si JPEG."""
    filters = obj.get('/Filter')
    quality_str = ""
    
    filter_list = []
    if filters:
        if isinstance(filters, list):
            filter_list = [str(f) for f in filters]
        else:
            filter_list = [str(filters)]
    else:
        filter_list = ["None (Raw)"]
        
    # Si c'est du JPEG (DCTDecode), on essaie d'extraire les données pour calculer la qualité
    if "DCTDecode" in [f.lstrip('/') for f in filter_list]:
        try:
            data = obj.get_data()
            if data:
                q = estimate_jpeg_quality(data)
                if q:
                    quality_str = f" [Qualité Est.: ~{q} %]"
        except Exception:
            pass
            
    return filter_list, quality_str

def analyze_xobjects(xobjects, results):
    """Parcourt récursivement les XObjects."""
    if not xobjects:
        return

    for obj_name in xobjects:
        try:
            obj = xobjects[obj_name].get_object()
            subtype = obj.get('/Subtype')

            if subtype == '/Image':
                filters, quality = get_obj_filter_and_quality(obj)
                # On stocke une chaîne descriptive complète
                desc = f"{', '.join(filters)}{quality}"
                results.append(desc)
            
            elif subtype == '/Form':
                if '/Resources' in obj and '/XObject' in obj['/Resources']:
                    analyze_xobjects(obj['/Resources']['/XObject'].get_object(), results)
                    
        except Exception:
            continue

def get_image_info(pdf_path):
    if not os.path.exists(pdf_path):
        return {"error": f"Fichier non trouvé: {pdf_path}"}
    
    results = []
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            if '/Resources' in page and '/XObject' in page['/Resources']:
                xobjects = page['/Resources']['/XObject'].get_object()
                analyze_xobjects(xobjects, results)
    except Exception as e:
        return {"error": f"Erreur analyse: {e}"}

    return results

def interpret_result(res_string):
    """Traduit le résultat technique en conseil humain."""
    if "DCTDecode" in res_string:
        # Extraction de la qualité si présente
        quality = "inconnue"
        if "Qualité Est." in res_string:
            import re
            match = re.search(r"~([0-9]+) %", res_string)
            if match:
                q_val = int(match.group(1))
                if q_val >= 90:
                    return f"JPEG {q_val}% (Très bonne qualité - Peu d'impact OCR)"
                elif q_val >= 75:
                    return f"JPEG {q_val}% (Qualité moyenne - Artefacts probables)"
                else:
                    return f"JPEG {q_val}% (Qualité basse - ⚠️ Impact OCR fort probable)"
        return f"JPEG (Qualité {quality})"
        
    elif any(x in res_string for x in ["FlateDecode", "LZWDecode", "CCITTFaxDecode"]):
        return "Sans perte (Parfait pour OCR)"
    elif "JBIG2Decode" in res_string:
        return "JBIG2 (Attention aux substitutions de caractères)"
    elif "JPXDecode" in res_string:
        return "JPEG 2000"
    else:
        return res_string

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Utilisation: python check_pdf_compression.py <fichier.pdf>")
        sys.exit(1)

    pdf_file_path = sys.argv[1]
    print(f"--- Analyse Qualité : {os.path.basename(pdf_file_path)} ---")
    
    raw_results = get_image_info(pdf_file_path)

    if isinstance(raw_results, dict) and "error" in raw_results:
        print(f"Erreur : {raw_results['error']}")
    elif not raw_results:
        print("❌ Aucune image raster détectée.")
    else:
        from collections import Counter
        counts = Counter(raw_results)
        
        print(f"\nImages trouvées : {len(raw_results)}\n")
        
        for raw_desc, count in counts.items():
            human_desc = interpret_result(raw_desc)
            print(f"🔹 {count} image(s) : {human_desc}")
            if "JPEG" in human_desc and "Qualité" not in human_desc: # Si on n'a pas réussi à estimer
                 print(f"   (Interne: {raw_desc})")
