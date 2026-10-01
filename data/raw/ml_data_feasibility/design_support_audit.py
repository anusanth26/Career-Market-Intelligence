"""
Per-role measurements that the dataset design (config/career_scope.json, report/dataset_design.md) rests on.
Read-only over the existing runs; makes NO API calls and trains nothing.

    python data/raw/ml_data_feasibility/design_support_audit.py
Writes data/raw/ml_data_feasibility/design_support_audit.json
"""

import csv
import json
import os
import random
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)
import adzuna_label_audit as ala  # noqa: E402  (reuses the exact clean-set construction)
from analyze_coverage import norm_text, read_jsonl  # noqa: E402
from role_mapping import compile_rules, normalize_title  # noqa: E402

RUNS = ala.RUNS
ROLES13 = ala.CORE + ["UX Designer", "Financial Analyst"] + ala.SECURITY


def run_queries(run):
    return read_jsonl(os.path.join(RUNS, run, "queries.jsonl"))


def main():
    clean_by_role, settings = ala.build_clean()
    cfg = json.load(open(os.path.join(ROOT, "config", "roles.json")))
    rules = {r["role"]: r for r in compile_rules(cfg["roles"])}
    out = {"per_role": {}, "api_budget": {}, "raw_field_presence": {}, "manual_precision_sample": {}}

    # --- coverage rows from the analysis outputs of the runs that pulled each role completely
    cov = {}
    for run in {ala.FEAS, ala.DEEP, ala.SEC}:
        p = os.path.join(RUNS, run, "analysis", "coverage_results.csv")
        for r in csv.DictReader(open(p)):
            cov[(run, r["canonical_role"], r["level"], r["query_variant"])] = r

    # --- API cost (pages) by role in the run that supplied it, and per-variant API counts
    queries = {run: run_queries(run) for run in {ala.FEAS, ala.DEEP, ala.SEC}}
    now = datetime(2026, 9, 29, 18, 0, tzinfo=timezone.utc)
    for role in ROLES13:
        run = ala.SOURCE_RUN[role]
        qs = [q for q in queries[run] if q["query_role"] == role]
        pages = sum(q["pages_ok"] for q in qs)
        primary = qs[0]
        role_row = cov[(run, role, "role", "ALL_VARIANTS")]
        rs = clean_by_role[role]
        n = len(rs)
        emp = Counter(r["employer_norm"] for r in rs if r["employer_norm"])
        norm = lambda t: normalize_title(t)
        canon = rules[role]["_match"][0]
        canon_n = sum(1 for r in rs if canon.search(norm(r["title"])))
        lens = [len(r["description"]) for r in rs]
        created = sorted(r["created"] for r in rs if r["created"])
        wk = Counter()
        for c in created:
            d = datetime.strptime(c[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            wk[(now - d).days // 7] += 1
        # last-7-day inflow is only trustworthy when the newest-first pull reached back past 7 days for every variant
        reached_back = all((q["created_min"] or "9999") < (now - timedelta(days=7)).strftime("%Y-%m-%d") for q in qs)
        tm = int(role_row["title_match_count"])
        ex, nd = int(role_row["exact_duplicates_removed"]), int(role_row["near_duplicates_removed"])
        uniq_after_exact = tm - ex
        out["per_role"][role] = {
            "source_run": run,
            "api_count_by_variant": {q["query"]: q["api_count"] for q in qs},
            "api_count_primary_variant": primary["api_count"],
            "raw_rows_own_queries": int(role_row["raw_count"]), "title_matched_rows": tm,
            "exact_dup_removed": ex, "near_dup_removed": nd, "employer_cap_removed": int(role_row["employer_cap_removed"]),
            "clean": n, "yield_clean_per_raw": round(n / max(1, int(role_row["raw_count"])), 3),
            "near_dup_rate_of_unique_ids_pct": round(100 * nd / max(1, uniq_after_exact), 1),
            "title_match_rate_of_raw_pct": round(100 * tm / max(1, int(role_row["raw_count"])), 1),
            "distinct_employers": len(emp), "top_employer_share_pct": round(100 * max(emp.values()) / n, 1) if emp else None,
            "effective_number_of_employers_1_over_sum_share_sq": round(1 / sum((v / n) ** 2 for v in emp.values()), 1) if emp else None,
            "mapping_tier_canonical_title_pct": round(100 * canon_n / n, 1),
            "mapping_tier_synonym_pct": round(100 * (n - canon_n) / n, 1),
            "description_nonempty_pct": round(100 * sum(1 for l in lens if l > 0) / n, 1),
            "description_ge_200_chars_pct": round(100 * sum(1 for l in lens if l >= 200) / n, 1),
            "description_len_min_median": [min(lens), st.median(lens)],
            "created_min_max": [created[0][:10], created[-1][:10]] if created else None,
            "clean_by_weeks_ago_0_is_latest": {str(k): v for k, v in sorted(wk.items())},
            "last_7_days_inflow_clean_lower_bound": wk.get(0, 0) if reached_back else None,
            "pull_reached_back_past_7_days_for_all_variants": reached_back,
            "pages_used_to_collect": pages, "queries": len(qs),
            "variants_capped_by_record_limit": [q["query"] for q in qs if q["capped_by_max_records"]],
        }
        # manual-precision sample: 12 random clean titles, fixed seed
        rnd = random.Random(7)
        out["manual_precision_sample"][role] = [r["title"] for r in rnd.sample(rs, min(12, n))]

    # --- API budget: pages spent by everything run so far on 2026-09-29
    total_pages = sum(q["pages_ok"] for run in queries for q in queries[run])
    all_runs = sorted(d for d in os.listdir(RUNS) if os.path.isdir(os.path.join(RUNS, d)))
    smoke = [d for d in all_runs if d.endswith("smoke")]
    smoke_pages = sum(q["pages_ok"] for d in smoke for q in run_queries(d))
    cov_probe = json.load(open(os.path.join(ROOT, "data", "raw", "adzuna", "coverage_2026-09-29.json")))
    probe_calls = sum(1 for r in cov_probe["results"] for c in ("in", "gb", "us") if c in r)
    failed = sum(q["http_failures"] for d in all_runs for q in run_queries(d))
    out["api_budget"] = {
        "documented_limits_from_terms_of_service": "25/min, 250/day, 1000/week, 2500/month",
        "pages_in_collection_runs_this_date": total_pages + smoke_pages, "coverage_probe_calls": probe_calls,
        "failed_attempts_503": failed,
        "approx_total_hits_on_2026-09-29_excl_a_few_manual_curl_tests": total_pages + smoke_pages + probe_calls,
        "pages_for_10_core_roles_full_baseline": sum(v["pages_used_to_collect"] for r, v in out["per_role"].items() if r in ala.CORE),
        "note": "collection-run pages exclude the 9 failed attempts; the smoke run is counted separately above",
    }

    # --- raw field presence on all rows of the main feasibility run
    d = os.path.join(RUNS, ala.FEAS)
    keys, n = Counter(), 0
    nested = Counter()
    for q in queries[ala.FEAS]:
        for rec in read_jsonl(os.path.join(d, q["records_file"])):
            raw = rec["raw"]
            n += 1
            for k, v in raw.items():
                if v not in (None, "", [], {}):
                    keys[k] += 1
            if (raw.get("company") or {}).get("display_name"):
                nested["company.display_name"] += 1
            if (raw.get("category") or {}).get("tag"):
                nested["category.tag"] += 1
            if len((raw.get("location") or {}).get("area", [])) >= 2:
                nested["location.area>=2_levels"] += 1
            if (raw.get("location") or {}).get("display_name"):
                nested["location.display_name"] += 1
    out["raw_field_presence"] = {"rows": n, "top_level_nonempty_pct": {k: round(100 * v / n, 1) for k, v in sorted(keys.items())},
                                 "nested_nonempty_pct": {k: round(100 * v / n, 1) for k, v in nested.items()}}
    # top categories (Adzuna's own label) per role, to document role/category overlap
    cats = defaultdict(Counter)
    for role in ala.CORE:
        for r in clean_by_role[role]:
            cats[role][r["category"]] += 1
    out["adzuna_category_label_by_role_top3"] = {r: c.most_common(3) for r, c in cats.items()}
    json.dump(out, open(os.path.join(HERE, "design_support_audit.json"), "w"), indent=2, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "manual_precision_sample"}, indent=1, default=str))
    print("\n=== MANUAL PRECISION SAMPLE (12 random clean titles per role, seed 7) ===")
    for role, ts in out["manual_precision_sample"].items():
        print(f"\n[{role}]")
        for t in ts:
            print("   -", t)


if __name__ == "__main__":
    main()
