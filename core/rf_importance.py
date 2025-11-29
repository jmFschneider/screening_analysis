from sklearn.ensemble import RandomForestRegressor

def compute_rf_importances(df, params, response):
    X = df[params].values
    y = df[response].values

    rf = RandomForestRegressor(
        n_estimators=400,
        random_state=0
    )
    rf.fit(X, y)

    return dict(zip(params, rf.feature_importances_))
