"""Precomputes the saved band model's output for every posting profile so Tableau can show a what-if page
(Tableau cannot run scikit-learn). Writes extracts/predictions.csv."""
import itertools
import os

import joblib
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = joblib.load(os.path.join(ROOT, "models", "salary_band_model.joblib"))
cols = m["feature_columns"]
roles = ["Business Analyst", "Data Analyst", "Data Engineer", "Data Scientist", "Devops / Cloud Engineer",
         "Digital Marketing", "Graphic Designer", "Product Manager", "Project Manager", "Software Engineer"]
states = ["Karnataka", "Maharashtra", "Telangana", "Delhi", "Uttar Pradesh", "Tamil Nadu", "Gujarat", "Unknown", "other"]
seniority = {"Entry": 0, "Mid": 1, "Senior": 2}
profiles = {"No listed skills": [], "Python + SQL": ["python", "sql"], "Python + SQL + AWS": ["python", "sql", "aws"],
            "Cloud stack (AWS, Azure, Docker, Linux)": ["aws", "azure", "docker", "linux"]}

rows, recs = [], []
for role, sen, st, ft, (pname, skills) in itertools.product(roles, seniority, states, (1, 0), profiles.items()):
    v = {c: 0 for c in cols}
    v.update(is_full_time=ft, seniority_ordinal=seniority[sen], skill_count=len(skills))
    for k in (f"role_{role}", f"location_bucket_{st}"):
        if k in v:
            v[k] = 1
    for s in skills:
        v[f"skill_{s}"] = 1
    rows.append(v)
    recs.append((role, sen, st, "Full time" if ft else "Other contract", pname))
X = pd.DataFrame(rows)[cols]
X[m["numeric_cols"]] = m["scaler"].transform(X[m["numeric_cols"]])
P = pd.DataFrame(m["model"].predict_proba(X), columns=[f"p_{c}" for c in m["classes"]])
out = pd.concat([pd.DataFrame(recs, columns=["role", "seniority", "state", "contract", "skill_profile"]), P], axis=1)
out["predicted_band"] = P.idxmax(axis=1).str.replace("p_", "")
out["top_probability"] = P.max(axis=1)
out.round(4).to_csv(os.path.join(ROOT, "tableau_dashboard", "extracts", "predictions.csv"), index=False)
print(out.shape, out.predicted_band.value_counts().to_dict())
