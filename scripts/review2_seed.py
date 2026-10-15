"""
Review 2 enablement seed — produces REAL foundation files from existing data so the
five-member team can work in parallel without waiting for each other.

Outputs (all computed from real data, nothing mocked):
  config/review2_skills.json          frozen skill list, derived from real skill frequencies
  data/review2/skill_demand.csv       real skill demand (frequency + % of postings) from job descriptions
  data/review2/skill_trends.csv       real trend slope/class from the existing Google Trends batch
  data/review2/skill_gap.csv          real Demand-Interest Gap join (skills present in both)

Member A later deepens skill_demand (co-occurrence, topics); Member B expands skill_trends
to the full skill list after collecting the remaining Google Trends batches.

Run:
    python scripts/review2_seed.py
"""

import json
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREPROCESSED = os.path.join(ROOT, "data", "processed", "career_market_preprocessed.csv")
TRENDS_IN = os.path.join(ROOT, "data", "raw", "trends", "trends_IN_batch01_2026-09-29.csv")
REVIEW2_DIR = os.path.join(ROOT, "data", "review2")
CONFIG_PATH = os.path.join(ROOT, "config", "review2_skills.json")

# Candidate skill dictionary (display name -> regex). Frequencies are counted on the REAL
# description text; skills with zero matches are dropped. Curated dictionaries are a standard,
# documented skill-extraction method (Ao et al., 2022).
SKILL_PATTERNS = {
    "Python": r"\bpython\b",
    "SQL": r"\bsql\b",
    "Power BI": r"\bpower\s*bi\b",
    "Tableau": r"\btableau\b",
    "Excel": r"\bexcel\b",
    "AWS": r"\baws\b|\bamazon web services\b",
    "Azure": r"\bazure\b",
    "Google Cloud": r"\bgcp\b|\bgoogle cloud\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Machine Learning": r"\bmachine learning\b",
    "Deep Learning": r"\bdeep learning\b",
    "Java": r"\bjava\b",
    "JavaScript": r"\bjavascript\b",
    "React": r"\breact\b",
    "Angular": r"\bangular\b",
    "Linux": r"\blinux\b",
    "SAP": r"\bsap\b",
    "Agile": r"\bagile\b",
    "Scrum": r"\bscrum\b",
    "Communication": r"\bcommunication\b",
    "Leadership": r"\bleadership\b",
    "Spark": r"\bspark\b",
    "Hadoop": r"\bhadoop\b",
    "TensorFlow": r"\btensorflow\b",
    "Git": r"\bgit\b",
    "Jira": r"\bjira\b",
    "SEO": r"\bseo\b",
    "Google Analytics": r"\bgoogle analytics\b",
}

TOP_N = 18            # size of the frozen skill list
RISE_THRESHOLD = 10.0  # % change to call a skill "rising"
DECLINE_THRESHOLD = -10.0


def compute_skill_demand(df: pd.DataFrame) -> pd.DataFrame:
    text = df["description_raw"].fillna("").str.lower()
    n = len(df)
    rows = []
    for name, pattern in SKILL_PATTERNS.items():
        mask = text.str.contains(pattern, regex=True, na=False)
        freq = int(mask.sum())
        if freq == 0:
            continue
        rows.append({"skill": name, "frequency": freq, "pct_postings": round(100 * freq / n, 2)})
    demand = pd.DataFrame(rows).sort_values("frequency", ascending=False).reset_index(drop=True)
    demand["rank"] = demand.index + 1
    return demand


def compute_skill_trends(path: str) -> pd.DataFrame:
    tr = pd.read_csv(path)
    tr["date"] = pd.to_datetime(tr["date"], format="%d-%m-%Y")
    tr = tr.sort_values("date").reset_index(drop=True)
    skill_cols = [c for c in tr.columns if c not in ("date", "isPartial")]
    weeks = np.arange(len(tr))
    rows = []
    for col in skill_cols:
        y = tr[col].astype(float).values
        slope = float(np.polyfit(weeks, y, 1)[0])  # points per week
        first_year = y[:52].mean()
        last_year = y[-52:].mean()
        pct_change = float(100 * (last_year - first_year) / first_year) if first_year else 0.0
        if pct_change >= RISE_THRESHOLD:
            cls = "rising"
        elif pct_change <= DECLINE_THRESHOLD:
            cls = "declining"
        else:
            cls = "stable"
        rows.append({
            "skill": col,
            "slope_per_week": round(slope, 4),
            "pct_change": round(pct_change, 2),
            "class": cls,
        })
    return pd.DataFrame(rows)


def build_gap(demand: pd.DataFrame, trends: pd.DataFrame) -> pd.DataFrame:
    median_rank = demand["rank"].median()
    merged = demand.merge(trends, on="skill", how="inner")
    out = []
    for _, r in merged.iterrows():
        high_demand = r["rank"] <= median_rank
        rising = r["class"] == "rising"
        if high_demand and rising:
            quad, rec = "invest", "Safe bet — in demand and gaining interest."
        elif high_demand and not rising:
            quad, rec = "opportunity", "High demand, flat/falling interest — learn it, low competition."
        elif (not high_demand) and rising:
            quad, rec = "hype", "Rising interest but low employer demand — proceed with caution."
        else:
            quad, rec = "avoid", "Low demand and low interest — not a priority."
        out.append({
            "skill": r["skill"],
            "demand_rank": int(r["rank"]),
            "demand_pct": r["pct_postings"],
            "momentum_class": r["class"],
            "pct_change": r["pct_change"],
            "quadrant": quad,
            "recommendation": rec,
        })
    return pd.DataFrame(out).sort_values("demand_rank").reset_index(drop=True)


def main() -> None:
    os.makedirs(REVIEW2_DIR, exist_ok=True)
    for sub in ("text_mining", "time_series", "combined"):
        os.makedirs(os.path.join(ROOT, "reports", sub), exist_ok=True)

    df = pd.read_csv(PREPROCESSED)
    n = len(df)

    demand = compute_skill_demand(df)
    demand.to_csv(os.path.join(REVIEW2_DIR, "skill_demand.csv"), index=False)

    skill_list = demand["skill"].head(TOP_N).tolist()
    config = {
        "anchor": "SQL",
        "geo": "IN",
        "timeframe": "today 5-y",
        "generated_from": f"real skill-frequency count over {n} job postings",
        "source_file": "data/processed/career_market_preprocessed.csv",
        "skills": skill_list,
    }
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)

    trends = compute_skill_trends(TRENDS_IN)
    trends.to_csv(os.path.join(REVIEW2_DIR, "skill_trends.csv"), index=False)

    gap = build_gap(demand, trends)
    gap.to_csv(os.path.join(REVIEW2_DIR, "skill_gap.csv"), index=False)

    print(f"Postings analysed: {n}")
    print(f"Skills detected  : {len(demand)} (frozen list = top {len(skill_list)})")
    print(f"Trends skills    : {len(trends)} (from existing batch01)")
    print(f"Gap rows         : {len(gap)} (skills present in both sources)")
    print("\nTop 10 skills by real demand:")
    print(demand.head(10).to_string(index=False))
    print("\nReal trend classes:")
    print(trends.to_string(index=False))
    print("\nDemand-Interest Gap (real, partial coverage):")
    print(gap.to_string(index=False))


if __name__ == "__main__":
    main()
