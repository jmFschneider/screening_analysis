import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor, _tree
from sklearn.ensemble import RandomForestRegressor

def find_optimal_zones(df, params, response, top_k=4, max_depth=4, min_samples_leaf=0.05):
    """
    Identifie les zones (feuilles d'un arbre de décision) où la réponse est maximisée.
    """
    X = df[params].values
    y = df[response].values

    # 1. Entraîner un arbre de régression simple et lisible
    tree = DecisionTreeRegressor(max_depth=max_depth, min_samples_leaf=min_samples_leaf, random_state=42)
    tree.fit(X, y)

    # 2. Parcourir l'arbre
    tree_rules = []
    
    def recurse(node, bounds):
        if tree.tree_.feature[node] != _tree.TREE_UNDEFINED:
            name_idx = tree.tree_.feature[node]
            threshold = tree.tree_.threshold[node]
            
            left_bounds = bounds.copy()
            left_min, left_max = left_bounds.get(name_idx, (-np.inf, np.inf))
            left_bounds[name_idx] = (left_min, min(left_max, threshold))
            recurse(tree.tree_.children_left[node], left_bounds)
            
            right_bounds = bounds.copy()
            right_min, right_max = right_bounds.get(name_idx, (-np.inf, np.inf))
            right_bounds[name_idx] = (max(right_min, threshold), right_max)
            recurse(tree.tree_.children_right[node], right_bounds)
        else:
            predicted_value = tree.tree_.value[node][0][0]
            sample_count = tree.tree_.n_node_samples[node]
            
            named_bounds = {}
            rule_strings = []
            
            for idx, (b_min, b_max) in bounds.items():
                p_name = params[idx]
                is_bounded_min = (b_min != -np.inf)
                is_bounded_max = (b_max != np.inf)
                
                if is_bounded_min or is_bounded_max:
                    named_bounds[p_name] = (b_min, b_max)
                    if is_bounded_min and is_bounded_max:
                        rule_strings.append(f"{b_min:.3f} < {p_name} <= {b_max:.3f}")
                    elif is_bounded_min:
                        rule_strings.append(f"{p_name} > {b_min:.3f}")
                    else:
                        rule_strings.append(f"{p_name} <= {b_max:.3f}")

            tree_rules.append({
                'mean': predicted_value,
                'count': sample_count,
                'rules': rule_strings,
                'bounds': named_bounds
            })

    recurse(0, {})
    sorted_zones = sorted(tree_rules, key=lambda x: x['mean'], reverse=True)
    return sorted_zones[:top_k]

def refine_optimal_point(df, params, response, zone_bounds, expansion_pct=0.1, n_iter=5000):
    """
    Cherche le point optimal à l'intérieur (ou proche) d'une zone donnée via un métamodèle.
    
    Args:
        df: Données d'entraînement.
        params: Liste des paramètres.
        response: Colonne réponse.
        zone_bounds: Dict {param: (min, max)} définissant la zone.
        expansion_pct: Pourcentage d'élargissement des bornes (ex: 0.1 pour 10%).
        n_iter: Nombre de points simulés.
    """
    # 1. Entraîner un métamodèle robuste sur tout l'espace
    # (On utilise un RF plus profond que l'arbre de décision pour la finesse)
    X = df[params].values
    y = df[response].values
    rf = RandomForestRegressor(n_estimators=200, random_state=42)
    rf.fit(X, y)
    
    # 2. Définir les bornes de recherche
    search_bounds = []
    for p in params:
        # Bornes globales absolues (physiques)
        global_min, global_max = df[p].min(), df[p].max()
        
        # Bornes de la zone (si définies, sinon globales)
        if p in zone_bounds:
            z_min, z_max = zone_bounds[p]
            # Gestion des infinis de l'arbre
            if z_min == -np.inf: z_min = global_min
            if z_max == np.inf: z_max = global_max
        else:
            z_min, z_max = global_min, global_max
            
        # Calcul de l'étendue
        span = z_max - z_min
        if span == 0: span = (global_max - global_min) * 0.1 # Securité
        
        # Application de l'expansion
        target_min = max(global_min, z_min - span * expansion_pct)
        target_max = min(global_max, z_max + span * expansion_pct)
        
        search_bounds.append((target_min, target_max))
        
    # 3. Génération aléatoire (Uniforme) dans l'hypercube étendu
    # Shape: (n_iter, n_params)
    random_samples = np.random.uniform(
        low=[b[0] for b in search_bounds],
        high=[b[1] for b in search_bounds],
        size=(n_iter, len(params))
    )
    
    # 4. Prédiction
    preds = rf.predict(random_samples)
    
    # 5. Trouver le max
    idx_max = np.argmax(preds)
    best_val = preds[idx_max]
    best_coords = dict(zip(params, random_samples[idx_max]))
    
    return best_val, best_coords