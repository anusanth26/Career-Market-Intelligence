#!/usr/bin/env python3
"""
Deterministic sampling for the manual role-mapping spot-check of the BUILT dataset (no network, no model).

    python scripts/mapping_spotcheck.py sample     # writes data/audits/dataset/mapping_spotcheck/samples.json
    python scripts/mapping_spotcheck.py metrics    # reads labels.csv (manual labels) and writes summary.json

Sampling: fresh seed 20261001 (the earlier audit used 20260930; 20261001 was drawn before the near-duplicate refinement and is superseded), 20 titles per core role (50 for Project Manager, whose rule
changed). Labels are assigned by a reviewer in labels.csv; the mapping code never labels its own output.
"""
import csv, json, os, random, sys
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "data", "audits", "dataset", "mapping_spotcheck")
DATA = os.path.join(ROOT, "data", "processed", "adzuna", "career_market_full_validated.parquet")
SEED = 20261002
CORE = ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer",
        "Business Analyst", "Product Manager", "Project Manager", "Digital Marketing", "Graphic Designer"]
N = {r: 20 for r in CORE}; N["Project Manager"] = 50

def sample():
    df = pd.read_parquet(DATA, columns=["job_id", "role", "title", "mapping_tier"])
    os.makedirs(OUT, exist_ok=True)
    out = {"seed": SEED, "roles": {}}
    for role in CORE:
        d = df[df.role == role].sort_values("job_id", key=lambda s: s.astype("int64"))
        pick = random.Random(f"{SEED}-{role}").sample(range(len(d)), N[role])
        d = d.iloc[sorted(pick)]
        out["roles"][role] = [{"i": k + 1, "job_id": r.job_id, "title": r.title, "tier": r.mapping_tier} for k, r in enumerate(d.itertuples())]
    json.dump(out, open(os.path.join(OUT, "samples.json"), "w"), indent=1, ensure_ascii=False)
    for role, items in out["roles"].items():
        print(f"\\n##S {role}")
        for it in items: print(f"{it['i']:>2} {it['tier'][0].upper()} | {it['title']}")

def metrics():
    lab = list(csv.DictReader(open(os.path.join(OUT, "labels.csv"), encoding="utf-8")))
    prev = json.load(open(os.path.join(ROOT, "data", "raw", "ml_data_feasibility", "mapping_precision", "summary.json")))["summary"]
    res = {}
    for role in CORE:
        rows = [r for r in lab if r["role"] == role]
        c = {k: sum(1 for r in rows if r["label"] == k) for k in ("correct", "ambiguous", "incorrect")}
        n = len(rows)
        prec = c["correct"] / (c["correct"] + c["incorrect"]) if c["correct"] + c["incorrect"] else None
        z = 1.96; m = c["correct"] + c["incorrect"]
        lo = hi = None
        if m:
            p = prec; d = 1 + z * z / m; ctr = (p + z * z / (2 * m)) / d; half = z * ((p * (1 - p) / m + z * z / (4 * m * m)) ** 0.5) / d
            lo, hi = round(100 * (ctr - half), 1), round(100 * (ctr + half), 1)
        res[role] = {"sample_n": n, **c, "precision_pct": round(100 * prec, 1) if prec is not None else None, "ci95_wilson_pct": [lo, hi],
                     "ambiguity_rate_pct": round(100 * c["ambiguous"] / n, 1), "strict_precision_pct": round(100 * c["correct"] / n, 1),
                     "previous_audit_precision_pct": prev[role]["precision_pct"], "previous_audit_ambiguity_pct": prev[role]["ambiguity_rate_pct"],
                     "incorrect_titles": [r["title"] for r in rows if r["label"] == "incorrect"], "ambiguous_titles": [r["title"] for r in rows if r["label"] == "ambiguous"][:6]}
    # carry forward the earlier 50-title audit where the SAME posting is still in the dataset with the SAME role
    prev_rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "data", "raw", "ml_data_feasibility", "mapping_precision", "labels.csv"), encoding="utf-8")) if not str(r["sample_index"]).startswith("U")]
    ds = pd.read_parquet(DATA, columns=["job_id", "role"]).set_index("job_id")["role"].to_dict()
    for role in CORE:
        pr = [r for r in prev_rows if r["role"] == role]
        kept = [r for r in pr if ds.get(str(r["adzuna_id"])) == role]
        pc = {k: sum(1 for r in kept if r["label"] == k) for k in ("correct", "ambiguous", "incorrect")}
        new = res[role]
        tc = {k: pc[k] + new[k] for k in ("correct", "ambiguous", "incorrect")}
        mm = tc["correct"] + tc["incorrect"]
        res[role]["carried_forward_from_earlier_audit"] = {"earlier_sample_n": len(pr), "still_in_dataset_same_role": len(kept), **pc,
            "note": "Earlier labels are reused only for postings still present with the same role; for Project Manager the rule changed, so carried labels cover only titles that still map to it"}
        res[role]["combined_new_plus_carried"] = {"n": sum(tc.values()), **tc, "precision_pct": round(100 * tc["correct"] / mm, 1) if mm else None,
                                                  "ambiguity_rate_pct": round(100 * tc["ambiguous"] / sum(tc.values()), 1)}
    json.dump({"seed": SEED, "reviewer": "AI assistant (manual judgement); NOT independently verified by a human", "per_role": res}, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    for r, v in res.items(): print(f"{r:26} n={v['sample_n']:>2} correct={v['correct']:>2} amb={v['ambiguous']:>2} inc={v['incorrect']:>2} precision={v['precision_pct']}% CI{v['ci95_wilson_pct']} amb%={v['ambiguity_rate_pct']} (prev {v['previous_audit_precision_pct']}%) | combined n={v['combined_new_plus_carried']['n']} precision={v['combined_new_plus_carried']['precision_pct']}% amb={v['combined_new_plus_carried']['ambiguity_rate_pct']}%")

if __name__ == "__main__":
    {"sample": sample, "metrics": metrics}[sys.argv[1]]()
