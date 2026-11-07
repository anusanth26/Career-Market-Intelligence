"""Salary regression with conformalized quantile regression (Romano, Patterson, Candes 2019).

Predicts log salary midpoint and returns a range with ~(1-ALPHA) coverage. Split is by employer
(60% train, 20% calibration, 20% test) so no company appears in two parts.
Usage: python scripts/salary_cqr.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder

SEED, ALPHA = 42, 0.2  # ALPHA 0.2 -> 80% target coverage
ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data/processed/career_market_preprocessed.csv")
df = df[df["salary_band"].notna()].reset_index(drop=True)  # same 1,101 rows as the notebook's band task
y = np.log(df["salary_mid"].to_numpy())
CATS = ["role", "seniority_level", "location_region", "contract_time"]
groups = df["employer"].fillna("unknown")

outer = GroupShuffleSplit(1, test_size=0.2, random_state=SEED)
rest, te = next(outer.split(df, groups=groups))
inner = GroupShuffleSplit(1, test_size=0.25, random_state=SEED)
a, b = next(inner.split(rest, groups=groups.iloc[rest]))
tr, ca = rest[a], rest[b]
assert not set(groups.iloc[tr]) & set(groups.iloc[te]) and not set(groups.iloc[ca]) & set(groups.iloc[te])

ohe = OneHotEncoder(handle_unknown="ignore").fit(df.loc[tr, CATS].fillna("unknown"))
tfidf = TfidfVectorizer(min_df=5, max_df=0.6, sublinear_tf=True, stop_words="english").fit(df.loc[tr, "description_raw"])
svd = TruncatedSVD(50, random_state=SEED).fit(tfidf.transform(df.loc[tr, "description_raw"]))


def feats(idx, text=True):
    X = ohe.transform(df.loc[idx, CATS].fillna("unknown"))
    if text:
        X = hstack([X, csr_matrix(svd.transform(tfidf.transform(df.loc[idx, "description_raw"])))])
    return X.tocsr()


def cqr(text):
    """Fit lo/med/hi quantile models on train, calibrate on calibration, return test (lo, med, hi)."""
    m = {q: GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=150, max_depth=3,
                                      learning_rate=0.05, subsample=0.8, random_state=SEED)
         .fit(feats(tr, text), y[tr]) for q in (ALPHA / 2, 0.5, 1 - ALPHA / 2)}
    lo_c, hi_c = m[ALPHA / 2].predict(feats(ca, text)), m[1 - ALPHA / 2].predict(feats(ca, text))
    score = np.maximum(lo_c - y[ca], y[ca] - hi_c)
    n = len(ca)
    qhat = np.quantile(score, min(1.0, np.ceil((n + 1) * (1 - ALPHA)) / n), method="higher")
    Xt = feats(te, text)
    return m[ALPHA / 2].predict(Xt) - qhat, m[0.5].predict(Xt), m[1 - ALPHA / 2].predict(Xt) + qhat


def report(name, lo, med, hi):
    cov = float(np.mean((y[te] >= lo) & (y[te] <= hi)))
    return {"model": name, "MAE_INR": round(float(np.mean(np.abs(np.exp(med) - np.exp(y[te])))), 0),
            "coverage": round(cov, 3), "median_width_ratio_hi_over_lo": round(float(np.median(np.exp(hi - lo))), 2)}


# baseline: role median + split-conformal interval from calibration residuals
role_med = pd.Series(y[tr]).groupby(df.loc[tr, "role"].to_numpy()).median()
g = df["role"].map(role_med).fillna(np.median(y[tr])).to_numpy()
res = np.abs(y[ca] - g[ca])
q = np.quantile(res, min(1.0, np.ceil((len(ca) + 1) * (1 - ALPHA)) / len(ca)), method="higher")
rows = [report("role median + conformal", g[te] - q, g[te], g[te] + q)]
rows.append(report("CQR, structured only", *cqr(False)))
rows.append(report("CQR, structured + text (final)", *cqr(True)))
out = pd.DataFrame(rows)
print(f"rows={len(df)} train={len(tr)} calib={len(ca)} test={len(te)} target coverage={1 - ALPHA}")
print(out.to_string(index=False))
(ROOT / "reports/summaries").mkdir(parents=True, exist_ok=True)
out.to_csv(ROOT / "reports/summaries/salary_cqr_results.csv", index=False)
