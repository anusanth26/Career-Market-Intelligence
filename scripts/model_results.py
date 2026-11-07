"""Honest evaluation numbers for the dashboards. Trains the standard salary models (same settings as the shipped
ones) on the salary-labelled rows and scores them two ways:
  holdout   stratified 80/20 split (employers can appear on both sides, so this runs optimistic)
  grouped   5-fold CV where a company never sits in both train and test (closer to unseen postings)
Writes CSVs to tableau_dashboard/extracts/ and confusion-matrix PNGs to reports/eda/. Does not touch models/.

    python scripts/model_results.py
"""
import os
import sys

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold, train_test_split

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import engineer_features  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tableau_dashboard", "extracts")
SEED = 42

df = pd.read_csv(os.path.join(ROOT, "data/processed/career_market_preprocessed.csv"))
df = df[df.salary_mid.notna() & df.salary_band.notna()].reset_index(drop=True)
df = engineer_features(df)
cols = [c for c in df.columns if c.startswith(("skill_", "role_", "location_bucket_"))] + ["is_full_time", "skill_count", "seniority_ordinal"]
cols = list(dict.fromkeys(cols))
X = df[cols].astype(float)
groups = df.employer.fillna("unknown").astype(str)

TASKS = {
    "band": (df.salary_band.astype(str), lambda: RandomForestClassifier(n_estimators=300, max_depth=8, random_state=SEED)),
    # binary target is built per split from the training median so the test fold never sets its own threshold
    "binary": (None, lambda: RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=5, random_state=SEED)),
}


def binary_target(train_idx, idx):
    med = df.salary_mid.iloc[train_idx].median()
    return (df.salary_mid.iloc[idx] >= med).map({True: "above", False: "below"})


def score(task, y_tr, y_te, model):
    base = DummyClassifier(strategy="most_frequent").fit(X.loc[y_tr.index], y_tr)
    model.fit(X.loc[y_tr.index], y_tr)
    pred = model.predict(X.loc[y_te.index])
    return pred, accuracy_score(y_te, base.predict(X.loc[y_te.index]))


rows, cm_rows, oof = [], [], {}
for task, (y_all, make) in TASKS.items():
    # holdout
    idx = np.arange(len(df))
    strat = y_all if y_all is not None else binary_target(idx, idx)
    tr, te = train_test_split(idx, test_size=0.2, stratify=strat, random_state=SEED)
    y_tr, y_te = (y_all.iloc[tr], y_all.iloc[te]) if y_all is not None else (binary_target(tr, tr), binary_target(tr, te))
    pred, base = score(task, y_tr, y_te, make())
    rows.append((task, "holdout", accuracy_score(y_te, pred), f1_score(y_te, pred, average="macro"), base, len(te)))

    # employer-grouped CV
    folds_acc, folds_f1, folds_base, preds, trues = [], [], [], [], []
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    for tr, te in sgkf.split(X, strat, groups):
        y_tr, y_te = (y_all.iloc[tr], y_all.iloc[te]) if y_all is not None else (binary_target(tr, tr), binary_target(tr, te))
        pred, base = score(task, y_tr, y_te, make())
        folds_acc.append(accuracy_score(y_te, pred)); folds_f1.append(f1_score(y_te, pred, average="macro"))
        folds_base.append(base); preds += list(pred); trues += list(y_te)
    rows.append((task, "employer_grouped_cv", np.mean(folds_acc), np.mean(folds_f1), np.mean(folds_base), len(df)))
    labels = sorted(set(trues))
    for i, a in enumerate(labels):
        for j, p in enumerate(labels):
            cm_rows.append((task, a, p, int(confusion_matrix(trues, preds, labels=labels)[i, j])))

cm = pd.DataFrame(cm_rows, columns=["task", "actual", "predicted", "count"])
for task, g in cm.groupby("task"):
    m = g.pivot(index="actual", columns="predicted", values="count")
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.imshow(m.values, cmap="Blues")
    ax.set_xticks(range(len(m.columns)), m.columns); ax.set_yticks(range(len(m.index)), m.index)
    for (i, j), v in np.ndenumerate(m.values):
        ax.text(j, i, v, ha="center", va="center", color="white" if v > m.values.max() / 2 else "black")
    ax.set(xlabel="Predicted", ylabel="Actual", title=f"{task}: employer-grouped CV, all {len(df)} postings")
    fig.tight_layout(); fig.savefig(os.path.join(ROOT, "reports", "eda", f"cm_{task}.png"), dpi=150); plt.close(fig)

res = pd.DataFrame(rows, columns=["task", "evaluation", "accuracy", "macro_f1", "majority_baseline_accuracy", "n_scored"]).round(4)
res.to_csv(os.path.join(OUT, "model_results.csv"), index=False)
cm.to_csv(os.path.join(OUT, "confusion_matrix.csv"), index=False)

fi = []
for task, (y_all, make) in TASKS.items():
    y = y_all if y_all is not None else binary_target(np.arange(len(df)), np.arange(len(df)))
    m = make().fit(X, y)
    fi += [(task, c, v) for c, v in zip(cols, m.feature_importances_)]
pd.DataFrame(fi, columns=["task", "feature", "importance"]).round(4).to_csv(os.path.join(OUT, "feature_importance.csv"), index=False)
print(f"rows scored: {len(df)}, employers: {groups.nunique()}, features: {len(cols)}")
print(res.to_string(index=False))
