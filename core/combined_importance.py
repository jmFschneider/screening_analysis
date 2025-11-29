def combine_importances(imp_rf, imp_gb, corr_p):
    params = imp_rf.keys()

    combined = {}
    for p in params:
        combined[p] = (
            0.5 * imp_rf[p] +
            0.4 * imp_gb[p] +
            0.1 * abs(corr_p[p])
        )
    return combined
