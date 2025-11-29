import numpy as np
import pandas as pd

def compute_correlations(df, params, response):
    corr_p = df[[response] + params].corr(method="pearson")[response].to_dict()
    corr_s = df[[response] + params].corr(method="spearman")[response].to_dict()

    corr_p.pop(response)
    corr_s.pop(response)

    return corr_p, corr_s
