"""Feature builder for the standard salary models. Matches how models/salary_{band,binary}_model.joblib
were trained in notebooks/career_market_intelligence.ipynb (same 31 columns), so scripts and dashboard agree."""
import re

import pandas as pd

SKILLS = ["python", "sql", "communication", "azure", "machine_learning", "agile", "aws", "linux", "java", "sap", "docker"]
SENIORITY_MAP = {"Entry": 0, "Mid": 1, "Senior": 2}
TOP_REGIONS = ["Unknown", "Karnataka", "Maharashtra", "Telangana", "Tamil Nadu", "Gujarat", "Delhi", "Uttar Pradesh"]


def skill_pattern(skill):
    # letter-only boundaries so "java" does not match "javascript" and "sap" does not match "sapient"
    return r"(?<![a-z])" + re.escape(skill).replace("_", r"[ _-]?") + r"(?![a-z])"


def engineer_features(df):
    out = df.copy()
    text = out["description_clean"].fillna("").astype(str).str.lower()
    for s in SKILLS:
        out[f"skill_{s}"] = text.str.contains(skill_pattern(s.replace("_", " ")), regex=True).astype(int)
    out["skill_count"] = out[[f"skill_{s}" for s in SKILLS]].sum(axis=1)
    out["seniority_ordinal"] = out["seniority_level"].map(SENIORITY_MAP).fillna(1).astype(int)
    out["is_full_time"] = (out["contract_time"] == "full_time").astype(int)
    out["location_bucket"] = out["location_region"].where(out["location_region"].isin(TOP_REGIONS), "other")
    dummies = pd.get_dummies(out[["role", "location_bucket"]].fillna("Unknown"), drop_first=True, dtype=int)
    return pd.concat([out, dummies], axis=1)
