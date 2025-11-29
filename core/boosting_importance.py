import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

def compute_gb_importances(df, params, response):
    X = df[params].values
    y = df[response].values

    gb = GradientBoostingRegressor(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=3,
        random_state=0
    )
    gb.fit(X, y)

    return dict(zip(params, gb.feature_importances_))
