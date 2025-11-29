import pandas as pd

def load_csv(path):
    """
    Charge un CSV avec détection automatique du séparateur.
    Retourne un DataFrame pandas.
    """
    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        try:
            return pd.read_csv(path, sep=";")
        except Exception as e:
            raise RuntimeError(f"Impossible de lire le CSV : {e}")
