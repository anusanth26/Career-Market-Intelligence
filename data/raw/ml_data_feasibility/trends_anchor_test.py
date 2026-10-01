"""
Gate 5: small validation of the Google Trends anchor/chaining strategy. NOT a data collection.
~9 requests, geo=IN, timeframe='today 5-y', 12 skills from the core roles. Raw CSVs go to
data/raw/ml_data_feasibility/trends_anchor_test/ (kept separate from data/raw/trends/).

Acceptance criteria, DECLARED BEFORE RUNNING (proposals, not from a source):
  R1 repeatability : same request repeated 3x -> for terms with batch mean >= 10, median |diff| between repeats <= 2 points
                     and Pearson r >= 0.98
  R2 companion-independence : the ratio mean(term)/mean(anchor) measured in two different requests that both contain
                     the pair differs by <= 15% when both means >= 10
  R3 chain accuracy : chained estimate (via mid anchor) vs direct co-request estimate of a low-volume skill on the
                     high-anchor scale: relative error of the 5-year mean <= 15% when the direct value's batch mean >= 10;
                     otherwise the direct value is below the resolution rule and cannot serve as ground truth
  R4 resolution rule : a term is usable in a request only if its mean >= 10 (integer rounding <= ~5% of the mean)

    python data/raw/ml_data_feasibility/trends_anchor_test.py
"""

import json
import os
import random
import time
import warnings
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from pytrends.request import TrendReq

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trends_anchor_test")
os.makedirs(OUT, exist_ok=True)
GEO, TIMEFRAME = "IN", "today 5-y"
PAUSE = (18, 28)

# request plan: (name, terms)
PLAN = [
    ("B1", ["SQL", "Python", "Docker", "Kubernetes", "Tableau"]),
    ("B2", ["SQL", "Power BI", "Figma", "SEO", "Jira"]),
    ("B3", ["SQL", "Terraform", "Snowflake", "Photoshop", "Docker"]),
    ("B1_repeat2", ["SQL", "Python", "Docker", "Kubernetes", "Tableau"]),
    ("B1_repeat3", ["SQL", "Python", "Docker", "Kubernetes", "Tableau"]),
]
# adaptive requests are appended after the survey (need the measured levels)


def fetch(terms):
    py = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
    for attempt in range(1, 6):
        try:
            py.build_payload(terms, cat=0, timeframe=TIMEFRAME, geo=GEO)
            df = py.interest_over_time()
            if df.empty:
                raise RuntimeError("empty frame")
            return df.drop(columns=["isPartial"], errors="ignore")
        except Exception as e:  # noqa: BLE001
            print(f"    attempt {attempt} failed: {type(e).__name__}; sleeping {60 * attempt}s", flush=True)
            time.sleep(60 * attempt)
    raise RuntimeError(f"gave up on {terms}")


def run(name, terms, store, log):
    print(f"[{name}] {terms}", flush=True)
    df = fetch(terms)
    df.to_csv(os.path.join(OUT, f"{name}.csv"))
    store[name] = df
    log.append({"request": name, "terms": terms, "rows": len(df), "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "means": {t: round(float(df[t].mean()), 2) for t in terms}})
    time.sleep(random.uniform(*PAUSE))


def main():
    store, log = {}, []
    for name, terms in PLAN:
        run(name, terms, store, log)

    # level survey on the SQL scale
    sql_scale = {}
    for name in ("B1", "B2", "B3"):
        df = store[name]
        for t in df.columns:
            if t != "SQL":
                sql_scale.setdefault(t, []).append(df[t].mean() / df["SQL"].mean())
    levels = {t: float(np.mean(v)) for t, v in sql_scale.items()}
    # mid anchor: the skill whose SQL-scale level is closest to 0.4 among those >= 0.3 (falls back to Docker)
    cand = {t: l for t, l in levels.items() if 0.25 <= l <= 0.9}
    mid = min(cand, key=lambda t: abs(t and cand[t] - 0.45)) if cand else "Docker"
    low = [t for t, l in sorted(levels.items(), key=lambda x: x[1]) if t != mid][:4]
    L1 = [mid] + low
    G1 = ["SQL"] + low[:4]  # direct co-request of the low skills with the high anchor
    run("L1_mid_anchor", L1, store, log)
    run("G1_direct_with_SQL", G1, store, log)

    res = {"geo": GEO, "timeframe": TIMEFRAME, "requests": log, "levels_on_SQL_scale": {k: round(v, 3) for k, v in levels.items()},
           "mid_anchor_chosen": mid, "low_skills_tested": low}

    # R1 repeatability (B1 x3)
    reps = [store["B1"], store["B1_repeat2"], store["B1_repeat3"]]
    r1 = {}
    for t in store["B1"].columns:
        a = np.vstack([r[t].values for r in reps])
        diffs = [np.abs(a[i] - a[j]) for i in range(3) for j in range(i + 1, 3)]
        corr = [np.corrcoef(a[i], a[j])[0, 1] for i in range(3) for j in range(i + 1, 3)]
        r1[t] = {"mean": round(float(a.mean()), 2), "median_abs_diff": float(np.median(np.concatenate(diffs))),
                 "max_abs_diff": float(np.max(np.concatenate(diffs))), "min_pearson_r": round(float(np.min(corr)), 4),
                 "identical_across_repeats": bool(np.all(a[0] == a[1]) and np.all(a[0] == a[2]))}
    res["R1_repeatability"] = r1

    # R2 companion independence: Docker/SQL ratio in B1 vs B3 (Docker in both with SQL)
    def ratio(df, x, y="SQL"):
        return float(df[x].mean() / df[y].mean())
    res["R2_companion_independence"] = {
        "Docker_over_SQL_in_B1": round(ratio(store["B1"], "Docker"), 4),
        "Docker_over_SQL_in_B3": round(ratio(store["B3"], "Docker"), 4),
        "relative_difference_pct": round(100 * abs(ratio(store["B1"], "Docker") - ratio(store["B3"], "Docker")) / ratio(store["B1"], "Docker"), 1),
        "series_pearson_Docker_B1_vs_B3": round(float(np.corrcoef(store["B1"]["Docker"], store["B3"]["Docker"])[0, 1]), 4),
        "SQL_series_pearson_B1_vs_B2": round(float(np.corrcoef(store["B1"]["SQL"], store["B2"]["SQL"])[0, 1]), 4),
    }

    # R3 chained vs direct for low skills
    # mid anchor level on SQL scale from B1/B3 (whichever contain both), then chain L1 through the mid anchor
    mid_over_sql = np.mean([ratio(store[b], mid) for b in ("B1", "B2", "B3") if mid in store[b].columns])
    chain = {}
    for t in low:
        chained = float(store["L1_mid_anchor"][t].mean() / store["L1_mid_anchor"][mid].mean() * mid_over_sql)  # in SQL units
        direct_mean = float(store["G1_direct_with_SQL"][t].mean())
        direct = float(direct_mean / store["G1_direct_with_SQL"]["SQL"].mean())
        chain[t] = {"chained_over_SQL": round(chained, 4), "direct_over_SQL": round(direct, 4),
                    "direct_batch_mean_points": round(direct_mean, 2),
                    "direct_meets_resolution_rule_ge_10": direct_mean >= 10,
                    "relative_error_pct": round(100 * abs(chained - direct) / direct, 1) if direct > 0 else None,
                    "series_pearson_L1_vs_G1": round(float(np.corrcoef(store["L1_mid_anchor"][t], store["G1_direct_with_SQL"][t])[0, 1]), 4),
                    "share_zero_weeks_in_direct": round(float((store["G1_direct_with_SQL"][t] == 0).mean()), 3),
                    "share_zero_weeks_in_mid_anchor_batch": round(float((store["L1_mid_anchor"][t] == 0).mean()), 3)}
    res["R3_chain_vs_direct"] = {"mid_anchor": mid, "mid_over_SQL": round(float(mid_over_sql), 4), "per_skill": chain}
    # R4 resolution: mean of each term per batch
    res["R4_batch_means"] = {n: {t: round(float(df[t].mean()), 2) for t in df.columns} for n, df in store.items()}
    json.dump(res, open(os.path.join(HERE, "trends_anchor_test.json"), "w"), indent=2)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
