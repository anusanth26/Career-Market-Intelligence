#!/usr/bin/env python3
"""
Freezes the dataset policy on top of the full validated dataset produced by scripts/build_dataset.py.

  full validated dataset (8,489 rows)  ->  [A] career_market_full_validated   (every retained row, policy columns added)
                                       ->  [B] career_market_core_analysis    (core roles after the deterministic 5% employer cap)

No preprocessing, no EDA, no features, no models, no network calls. Deterministic (explicit sort orders, no randomness except seeded
sampling for the human-validation template).

    python scripts/build_dataset.py && python scripts/finalize_dataset.py     # build, then freeze
    python scripts/finalize_dataset.py --check-reproducible                   # runs build+finalize twice in temp dirs and compares
"""
import argparse, hashlib, json, math, os, random, re, subprocess, sys, tempfile
from collections import Counter
from datetime import datetime, timezone

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_dataset as bd  # noqa: E402  (FIELD_SPEC, helpers only; nothing is re-built here)

CFG = json.load(open(os.path.join(ROOT, "config", "dataset_build.json"), encoding="utf-8"))
FP = CFG["final_policy"]
TG = CFG["targets"]
CORE_ROLES = [r for rs in CFG["scope"]["core"].values() for r in rs]
CONDITIONAL_ROLES = list(CFG["scope"]["conditional"])
ADJACENT_ROLES = CFG["scope"]["adjacent_not_core"]
LIST_COLS = {"location_area", "salary_flags", "query_roles_seen", "also_seen_in"}
NEW_SPEC = [
    ("role_status", "DERIVED", "core | conditional_limited (core role failing a dataset target or forced conditional by policy) | conditional | adjacent_not_core"),
    ("employer_cap_status", "DERIVED", "core rows: retained | excluded_by_5pct_cap; other partitions: not_applicable. Rows excluded by the cap stay in the full validated dataset"),
    ("in_core_analysis_dataset", "DERIVED", "True for core-role rows retained by the employer cap (membership of the final core analysis dataset)"),
]
FINAL_COLUMNS = ["job_id", "title", "role", "role_scope", "role_status", "domain", "role_group", "mapping_tier", "employer", "employer_normalized", "employer_missing",
                 "description_raw", "location_display", "location_area", "location_country", "location_region", "location_has_region", "latitude", "longitude",
                 "created", "created_date", "category_label", "category_tag", "contract_type", "contract_time", "salary_min", "salary_max", "salary_is_predicted",
                 "salary_present", "salary_flags", "salary_passes_plausibility_screen", "source_run", "source_file", "source_query", "source_query_role",
                 "collection_timestamp", "collection_date", "collection_method", "query_roles_seen", "also_seen_in", "id_dup_count", "near_dup_group_size", "near_dup_key",
                 "employer_cap_status", "in_core_analysis_dataset", "description_length", "description_is_truncated", "description_short_flag", "language_flag"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def num_id(s):
    return int(s) if s and str(s).isdigit() else 10 ** 18


def conc(employers, n_rows):
    emp = Counter(e for e in employers if e)
    n = sum(emp.values())
    if not n:
        return {"rows": n_rows, "rows_with_employer": 0, "unique_employers": 0, "top_employer_count": 0, "top_employer_percentage": None, "effective_number_of_employers": None}
    top, cnt = emp.most_common(1)[0]
    return {"rows": n_rows, "rows_with_employer": n, "unique_employers": len(emp), "top_employer_count": cnt,
            "top_employer_percentage": round(100 * cnt / n, 2), "effective_number_of_employers": round(1 / sum((v / n) ** 2 for v in emp.values()), 1)}


def quantiles(v):
    if not v:
        return {}
    v = sorted(v)
    at = lambda q: v[min(len(v) - 1, int(q * len(v)))]
    return {"n": len(v), "min": v[0], "p5": at(.05), "p25": at(.25), "median": at(.5), "p75": at(.75), "p95": at(.95), "max": v[-1]}


def to_bytes(df):
    d = df.copy()
    for c in LIST_COLS:
        if c in d:
            d[c] = d[c].apply(bd.jdump)
    return d.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")


def salary_block(rows):
    pres = [r for r in rows if r["salary_present"]]
    val = [r for r in pres if r["salary_passes_plausibility_screen"]]
    mid = lambda r: ((r["salary_min"] if pd.notna(r["salary_min"]) else r["salary_max"]) + (r["salary_max"] if pd.notna(r["salary_max"]) else r["salary_min"])) / 2
    fl = Counter(f for r in pres for f in r["salary_flags"])
    txt = [(r["description_raw"] or "").lower() for r in pres]
    cnt = lambda pat: sum(1 for t in txt if re.search(pat, t))
    return {"rows": len(rows), "salary_present": len(pres), "salary_missing": len(rows) - len(pres), "salary_present_pct": round(100 * len(pres) / max(1, len(rows)), 1),
            "salary_predicted": sum(1 for r in rows if r["salary_is_predicted"] == "1"),
            "salary_valid_under_working_screen": len(val), "salary_invalid": len(pres) - len(val),
            "invalid_reason_counts": {k: v for k, v in sorted(fl.items()) if k in ("adzuna_predicted", "min_gt_max", "non_positive", "below_floor", "above_ceiling")},
            "informational_counts": {k: v for k, v in sorted(fl.items()) if k in ("point_value", "one_sided")},
            "both_min_and_max_present": sum(1 for r in rows if pd.notna(r["salary_min"]) and pd.notna(r["salary_max"])),
            "valid_midpoint_distribution_raw_units": quantiles([mid(r) for r in val]),
            "snippet_mentions_among_salaried": {"per_month_or_monthly": cnt(r"per month|monthly|/month"), "per_annum_or_annual": cnt(r"per annum|p\.a\.|per year|annual"),
                                                "lpa_or_lakh": cnt(r"\blpa\b|lakh|lacs?\b"), "hourly": cnt(r"per hour|hourly|/hour"), "usd_or_dollar": cnt(r"\$|usd\b"), "inr_or_rupee": cnt(r"inr\b|rs\.?\s?\d|₹")}}


def run(out_root, verbose=True):
    log = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    proc = os.path.join(out_root, "data", "processed", "adzuna")
    aud = os.path.join(out_root, "data", "audits", "dataset")
    stage_pq, stage_csv = (os.path.join(proc, "career_market_dataset.parquet"), os.path.join(proc, "career_market_dataset.csv"))
    if not os.path.exists(stage_pq):
        sys.exit("Run scripts/build_dataset.py first (stage output missing).")
    base_manifest = json.load(open(os.path.join(proc, "dataset_manifest.json"), encoding="utf-8"))
    df = pd.read_parquet(stage_pq)
    for c in LIST_COLS:
        df[c] = df[c].apply(lambda v: [] if v is None else list(v))
    df = df.astype(object).where(df.notna(), None)
    rows = df.to_dict("records")

    # ── deterministic 5% employer cap, core roles only ───────────────
    frac = FP["employer_cap"]["fraction"]
    by_role = {r: [x for x in rows if x["role_scope"] == "core" and x["role"] == r] for r in CORE_ROLES}
    excluded = []
    for role in CORE_ROLES:
        rs = by_role[role]
        cap_n = max(1, math.floor(frac * len(rs)))
        groups = {}
        for x in rs:
            if x["employer_normalized"]:
                groups.setdefault(x["employer_normalized"], []).append(x)
        for emp in sorted(groups):
            g = groups[emp]
            if len(g) > cap_n:
                g_sorted = sorted(g, key=lambda x: (x["created"] or "", -num_id(x["job_id"])), reverse=True)
                for rank, x in enumerate(g_sorted, 1):
                    if rank > cap_n:
                        excluded.append({"role": role, "job_id": x["job_id"], "employer": x["employer"], "created": x["created"], "employer_rows_in_role_before_cap": len(g),
                                         "cap_per_employer_in_role": cap_n, "rank_within_employer_most_recent_first": rank, "reason": "employer_cap_5pct"})
    drop_ids = {e["job_id"] for e in excluded}
    for x in rows:
        x["employer_cap_status"] = ("excluded_by_5pct_cap" if x["job_id"] in drop_ids else "retained") if x["role_scope"] == "core" else "not_applicable"
    # consistency with the flag computed during the build
    flag_mismatch = sum(1 for x in rows if x["role_scope"] == "core" and (x["employer_cap_status"] == "retained") != bool(x["employer_cap_5pct_retained"]))
    assert flag_mismatch == 0, f"cap decisions differ from the build-stage flag ({flag_mismatch})"

    # ── per-role audit and status (evaluated on the AFTER-CAP data) ──
    audit, status_of = [], {}
    for role in CORE_ROLES:
        before = by_role[role]
        after = [x for x in before if x["employer_cap_status"] == "retained"]
        cb, ca = conc([x["employer_normalized"] for x in before], len(before)), conc([x["employer_normalized"] for x in after], len(after))
        canon_after = sum(1 for x in after if x["mapping_tier"] == "canonical")
        checks = {"final_count_ge_400": len(after) >= TG["clean_per_core_role"], "canonical_ge_300": canon_after >= TG["canonical_per_core_role"],
                  "unique_employers_ge_100": ca["unique_employers"] >= TG["distinct_employers_per_role"],
                  "top_employer_le_6pct": (ca["top_employer_percentage"] or 100) <= TG["top_employer_pct_max"],
                  "effective_employers_ge_50": (ca["effective_number_of_employers"] or 0) >= TG["effective_employers_min"]}
        reasons = []
        if not checks["final_count_ge_400"]:
            reasons.append("below minimum dataset-size target")
        for k in ("canonical_ge_300", "unique_employers_ge_100", "top_employer_le_6pct", "effective_employers_ge_50"):
            if not checks[k]:
                reasons.append(f"fails {k}")
        if role in FP["forced_conditional_roles"] and not reasons:
            reasons.append(FP["forced_conditional_roles"][role]["reason"])
        status = "conditional_limited" if reasons else "core"
        status_of[role] = status
        audit.append({"role": role, "records_before_cap": len(before), "records_after_cap": len(after), "records_removed_by_cap": len(before) - len(after),
                      "unique_employers_before": cb["unique_employers"], "unique_employers": ca["unique_employers"],
                      "top_employer_percentage_before": cb["top_employer_percentage"], "top_employer_percentage_after": ca["top_employer_percentage"],
                      "top_employer_count_before": cb["top_employer_count"], "top_employer_count_after": ca["top_employer_count"],
                      "effective_employers_before": cb["effective_number_of_employers"], "effective_employers": ca["effective_number_of_employers"],
                      "cap_per_employer": max(1, math.floor(frac * len(before))), "canonical_title_after_cap": canon_after,
                      "target_checks_after_cap": checks, "status": status, "status_reasons": reasons,
                      "note": "top_employer_percentage_after is measured on the reduced role total, so it can stay slightly above 5%"})
    for x in rows:
        x["role_status"] = status_of[x["role"]] if x["role_scope"] == "core" else ("conditional" if x["role_scope"] == "conditional" else "adjacent_not_core")
        x["in_core_analysis_dataset"] = x["role_scope"] == "core" and x["employer_cap_status"] == "retained"

    # ── frozen datasets ──────────────────────────────────────────────
    full = pd.DataFrame(rows)[FINAL_COLUMNS]
    core = full[full["in_core_analysis_dataset"]].copy()
    assert len(full) == base_manifest["final_count"]
    files = {}
    for name, d in (("career_market_full_validated", full), ("career_market_core_analysis", core)):
        b = to_bytes(d)
        d.to_parquet(os.path.join(proc, name + ".parquet"), engine="pyarrow", index=False, compression="zstd")
        open(os.path.join(proc, name + ".csv"), "wb").write(b)
        files[name] = {"rows": len(d), "content_sha256": hashlib.sha256(b).hexdigest(), "parquet": f"data/processed/adzuna/{name}.parquet", "csv": f"data/processed/adzuna/{name}.csv"}
    os.remove(stage_pq)
    os.remove(stage_csv)  # the stage copy is superseded by career_market_full_validated

    W = lambda d, n, o: json.dump(o, open(os.path.join(d, n), "w", encoding="utf-8"), indent=1, sort_keys=True, ensure_ascii=False)
    # ── employer audit ───────────────────────────────────────────────
    pd.DataFrame(audit)[["role", "records_before_cap", "records_after_cap", "unique_employers", "top_employer_percentage_before", "top_employer_percentage_after",
                         "effective_employers", "records_removed_by_cap", "status"]].to_csv(os.path.join(aud, "employer_cap_audit.csv"), index=False, lineterminator="\n")
    ex_df = pd.DataFrame(excluded, columns=["role", "job_id", "employer", "created", "employer_rows_in_role_before_cap", "cap_per_employer_in_role", "rank_within_employer_most_recent_first", "reason"])
    ex_df = ex_df.sort_values(["role", "job_id"], key=lambda s: s.map(num_id) if s.name == "job_id" else s)
    ex_df.to_csv(os.path.join(aud, "employer_cap_exclusions.csv"), index=False, lineterminator="\n")
    tot_before, tot_after = sum(a["records_before_cap"] for a in audit), sum(a["records_after_cap"] for a in audit)
    W(aud, "employer_cap_audit.json", {
        "policy": FP["employer_cap"], "applied": True, "records_removed_by_cap_total": tot_before - tot_after, "core_records_before_cap": tot_before, "core_records_after_cap": tot_after,
        "per_role": audit, "uncapped_statistics_are_not_hidden": "records_before_cap / *_before columns are the uncapped figures; the excluded rows remain in the full validated dataset",
        "exclusions_file": "employer_cap_exclusions.csv (one line per excluded record)",
        "core_after_cap": conc([x["employer_normalized"] for x in rows if x["in_core_analysis_dataset"]], tot_after)})

    # ── final role counts ────────────────────────────────────────────
    counts = []
    for role in CORE_ROLES + CONDITIONAL_ROLES + ADJACENT_ROLES:
        rs = [x for x in rows if x["role"] == role]
        if not rs:
            continue
        scope = rs[0]["role_scope"]
        fin = [x for x in rs if x["in_core_analysis_dataset"]] if scope == "core" else rs
        counts.append({"role": role, "partition": scope, "uncapped_count": len(rs), "final_count": len(fin), "status": rs[0]["role_status"],
                       "unique_employers": len({x["employer_normalized"] for x in fin if x["employer_normalized"]}), "canonical_title_count": sum(1 for x in fin if x["mapping_tier"] == "canonical"),
                       "employer_cap_applied": scope == "core", "in_core_analysis_dataset": scope == "core"})
    sec_rows = [x for x in rows if x["role_group"] == "Security (conditional family)"]
    W(aud, "final_role_counts.json", {
        "pipeline": {"raw": base_manifest["raw_record_count"], "id_deduplicated": base_manifest["id_deduplicated_count"], "near_deduplicated": base_manifest["near_deduplicated_count"],
                     "full_validated_final_retained": len(full), "core_uncapped": tot_before, "core_analysis_after_employer_cap": tot_after,
                     "conditional_rows": sum(1 for x in rows if x["role_scope"] == "conditional"), "adjacent_rows": sum(1 for x in rows if x["role_scope"] == "adjacent_not_core")},
        "per_role": counts, "security_merged_view_rows": len(sec_rows), "note": "core final_count is after the employer cap; conditional and adjacent partitions are not capped"})

    # ── salary quality (regenerated) ─────────────────────────────────
    core_unc = [x for x in rows if x["role_scope"] == "core"]
    core_fin = [x for x in rows if x["in_core_analysis_dataset"]]
    W(aud, "salary_quality_report.json", {
        "salary_period_interpretation": FP["salary"]["period_interpretation"], "salary_currency_interpretation": FP["salary"]["currency_interpretation"],
        "screen_definition": "salary_passes_plausibility_screen = present, not Adzuna-predicted, min <= max, and 100,000 <= value <= 10,000,000 in RAW units. A numeric screen only; it does not assert annual pay or INR",
        "currency_field_in_source": False, "period_field_in_source": False,
        "full_validated_dataset": salary_block(rows), "core_uncapped": salary_block(core_unc), "final_core_analysis_dataset": salary_block(core_fin),
        "final_core_by_role": {r: salary_block([x for x in core_fin if x["role"] == r]) for r in CORE_ROLES},
        "locations_of_salaried_final_core": dict(Counter(x["location_country"] for x in core_fin if x["salary_present"])),
        "earlier_figures_for_comparison": {"core_rows": 6662, "present": 602, "valid_under_screen": 523, "missing": 6060, "invalid": 79, "predicted": 0},
        "not_done": "No salary bands, no model, no currency or period normalisation; the supervised target is a later-phase decision."})

    # ── validation status per role ───────────────────────────────────
    sp_dir = os.path.join(ROOT, "data", "audits", "dataset", "mapping_spotcheck")
    sp = json.load(open(os.path.join(sp_dir, "summary.json"), encoding="utf-8"))["per_role"]
    val = {}
    for role in CORE_ROLES:
        v = sp[role]
        val[role] = {"current_validation_method": "manual spot-check of role titles against a fixed rubric (correct / ambiguous / incorrect) by the project workflow (an AI assistant); NOT independent human validation",
                     "sample_size": v["sample_n"], "sample_seed": 20261002, "correct": v["correct"], "ambiguous": v["ambiguous"], "incorrect": v["incorrect"],
                     "observed_precision_pct": v["precision_pct"], "ci95_wilson_pct": v["ci95_wilson_pct"], "ambiguity_rate_pct": v["ambiguity_rate_pct"],
                     "pooled_with_earlier_audit": {"n": v["combined_new_plus_carried"]["n"], "precision_pct": v["combined_new_plus_carried"]["precision_pct"]},
                     "validation_status": "AI-assisted spot-check complete; independent human validation not done", "independent_human_validation": "PENDING"}
    for role in CONDITIONAL_ROLES + ADJACENT_ROLES:
        val[role] = {"current_validation_method": "none (not sampled)", "sample_size": 0, "observed_precision_pct": None, "validation_status": "not sampled", "independent_human_validation": "PENDING"}
    W(aud, "mapping_validation_status.json", {
        "role_assignment": "title-based only (regex rules on the job title; description, skills, salary, category, employer and query are never used)",
        "independent_human_validation_overall": "PENDING", "per_role": val,
        "input_files_sha256": {"mapping_spotcheck/summary.json": sha256_file(os.path.join(sp_dir, "summary.json")), "mapping_spotcheck/labels.csv": sha256_file(os.path.join(sp_dir, "labels.csv"))},
        "human_validation_template": "human_validation/human_validation_template.csv (blank labels; a teammate fills it in later)"})
    # template for the independent human review (deterministic sample, no labels, no tier)
    hv_dir = os.path.join(aud, "human_validation")
    os.makedirs(hv_dir, exist_ok=True)
    hv = []
    for role in CORE_ROLES:
        rs = sorted([x for x in core_fin if x["role"] == role], key=lambda x: num_id(x["job_id"]))
        for k in sorted(random.Random(f"{FP['human_validation']['seed']}-{role}").sample(range(len(rs)), FP["human_validation"]["titles_per_core_role"])):
            hv.append({"role": role, "job_id": rs[k]["job_id"], "title": rs[k]["title"], "reviewer_label": "", "reviewer_notes": "", "reviewer_name": "", "review_date": ""})
    pd.DataFrame(hv).to_csv(os.path.join(hv_dir, "human_validation_template.csv"), index=False, lineterminator="\n")
    open(os.path.join(hv_dir, "README.md"), "w").write(
        "# Independent human validation (PENDING)\n\nFill `reviewer_label` for each row with one of: `correct` (the title clearly names the role), `ambiguous` (a debatable variant, hybrid or manager-level title) or `incorrect` (a different job family). Do not look at the mapping rules first. Add your name and date. Then report per-role precision = correct / (correct + incorrect) and the ambiguity rate. The sample is deterministic (seed %d, %d titles per core role) and contains no labels from the project workflow.\n" % (FP["human_validation"]["seed"], FP["human_validation"]["titles_per_core_role"]))

    # ── schema (frozen) ──────────────────────────────────────────────
    spec = {n: (o, d) for n, o, d in bd.FIELD_SPEC}
    spec.update({n: (o, d) for n, o, d in NEW_SPEC})
    W(proc, "schema.json", {"dataset": "career_market", "version": CFG["dataset_version"], "frozen": True, "views": {k: v["rows"] for k, v in files.items()}, "column_order": FINAL_COLUMNS,
        "fields": [{"name": c, "origin": spec[c][0], "description": spec[c][1], "dtype": str(full[c].dtype), "missing_pct_full_validated": round(100 * sum(1 for x in rows if x[c] in (None, "", [])) / len(rows), 1)} for c in FINAL_COLUMNS],
        "origin_legend": {"SOURCE": "copied unchanged from the Adzuna raw record", "DERIVED": "computed deterministically", "PROVENANCE": "collection metadata (or file-name derived for the legacy pull)"},
        "rules": ["role is TITLE-BASED; never use title, role, source_query_role or mapping_tier as predictive features", "no text normalisation, tokenisation, embeddings or skill vectors are stored", "salary period and currency are unresolved"],
        "fields_deliberately_not_carried": ["redirect_url", "adref", "title_normalized", "description_normalized", "matched_pattern_index"]})

    # ── manifest ─────────────────────────────────────────────────────
    core_rc = {r: {"uncapped": len(by_role[r]), "final_after_cap": sum(1 for x in by_role[r] if x["employer_cap_status"] == "retained")} for r in CORE_ROLES}
    pm = next(a for a in audit if a["role"] == "Project Manager")
    manifest = {
        "dataset_version": CFG["dataset_version"], "finalization_complete": True, "downstream_status": "Preprocessing, EDA, modelling and other analytics have NOT started",
        "source_file_count": base_manifest["source_file_count"], "raw_record_count": base_manifest["raw_record_count"], "id_deduplicated_count": base_manifest["id_deduplicated_count"],
        "near_deduplicated_count": base_manifest["near_deduplicated_count"], "final_retained_count": len(full),
        "core_record_count": {"uncapped": tot_before, "final_analysis_dataset_after_cap": tot_after},
        "conditional_record_count": sum(1 for x in rows if x["role_scope"] == "conditional"), "adjacent_record_count": sum(1 for x in rows if x["role_scope"] == "adjacent_not_core"),
        "role_counts": {"core": core_rc, "conditional_and_adjacent": {c["role"]: c["final_count"] for c in counts if c["partition"] != "core"}},
        "role_status": status_of,
        "employer_statistics": {"unique_employers_full_validated": len({x["employer_normalized"] for x in rows if x["employer_normalized"]}),
                                "core_before_cap": conc([x["employer_normalized"] for x in core_unc], len(core_unc)), "core_after_cap": conc([x["employer_normalized"] for x in core_fin], len(core_fin)),
                                "per_role_file": "data/audits/dataset/employer_cap_audit.json"},
        "salary_statistics": {"final_core_analysis_dataset": {k: v for k, v in salary_block(core_fin).items() if k in ("rows", "salary_present", "salary_missing", "salary_predicted", "salary_valid_under_working_screen", "salary_invalid")},
                              "core_uncapped": {k: v for k, v in salary_block(core_unc).items() if k in ("rows", "salary_present", "salary_missing", "salary_predicted", "salary_valid_under_working_screen", "salary_invalid")},
                              "salary_period_interpretation": "unresolved", "salary_currency_interpretation": "unresolved", "file": "data/audits/dataset/salary_quality_report.json"},
        "project_manager_status": {"count_uncapped": pm["records_before_cap"], "count_after_cap": pm["records_after_cap"], "status": "conditional", "reason": "below minimum dataset-size target (400)",
                                   "mapping_policy": "canonical-only", "adjacent_families_kept_separate": {r: sum(1 for x in rows if x["role"] == r) for r in ADJACENT_ROLES}, "no_records_fabricated_or_mapping_relaxed": True},
        "employer_cap_policy": {**FP["employer_cap"], "applied": True, "records_removed": tot_before - tot_after, "exclusions_file": "data/audits/dataset/employer_cap_exclusions.csv"},
        "validation_status": {"role_assignment": "title-based", "mapping_spot_check": "AI-assisted, complete (not independent)", "independent_human_validation": "PENDING", "details": "data/audits/dataset/mapping_validation_status.json"},
        "build_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "raw_files_unchanged_verified_by_sha256": base_manifest["raw_files_unchanged_verified_by_sha256"], "raw_source_files": base_manifest["raw_source_files"],
        "config_sha256": {"dataset_build.json": sha256_file(os.path.join(ROOT, "config", "dataset_build.json")), "roles.json": sha256_file(os.path.join(ROOT, "config", "roles.json"))},
        "output_files": files, "python": base_manifest["python"], "pandas": base_manifest["pandas"],
        "reproducibility_status": "not yet run (python scripts/finalize_dataset.py --check-reproducible)"}
    W(proc, "dataset_manifest.json", manifest)
    log(f"[final] full validated {len(full)} | core uncapped {tot_before} -> analysis dataset {tot_after} (cap removed {tot_before - tot_after}) | statuses {status_of}")
    return manifest


def _tree_hashes(root, volatile=("dataset_manifest.json", "reproducibility_check.json")):
    out = {}
    for base in (os.path.join(root, "data", "processed", "adzuna"), os.path.join(root, "data", "audits", "dataset")):
        for dp, _, fs in os.walk(base):
            if "mapping_spotcheck" in dp:
                continue
            for f in sorted(fs):
                if f in volatile:
                    continue
                p = os.path.join(dp, f)
                if f.endswith(".parquet"):
                    d = pd.read_parquet(p)
                    out[os.path.relpath(p, root)] = hashlib.sha256(d.astype(str).to_csv(index=False).encode()).hexdigest()
                else:
                    out[os.path.relpath(p, root)] = sha256_file(p)
    m = json.load(open(os.path.join(root, "data", "processed", "adzuna", "dataset_manifest.json")))
    for k in ("build_timestamp", "reproducibility_status"):
        m.pop(k, None)
    out["dataset_manifest.json(stripped)"] = hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()
    return out


def check_reproducible():
    hashes = []
    for _ in range(2):
        tmp = tempfile.mkdtemp(prefix="cmi_final_")
        for script in ("build_dataset.py", "finalize_dataset.py"):
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script), "--output-root", tmp, "--quiet"], check=True)
        hashes.append(_tree_hashes(tmp))
    main = _tree_hashes(ROOT)
    same = hashes[0] == hashes[1]
    diff = sorted(k for k in set(hashes[0]) | set(hashes[1]) if hashes[0].get(k) != hashes[1].get(k))
    vs_main = sorted(k for k in set(hashes[0]) | set(main) if hashes[0].get(k) != main.get(k))
    out = {"runs": 2, "result": "PASS" if same else "FAIL", "files_compared": len(hashes[0]), "differences_between_runs": diff, "differences_vs_main_outputs": vs_main,
           "compared": "row content of every dataset view (CSV bytes and Parquet logical content), role assignments, cap exclusions, all audit and report files, manifest statistics (build_timestamp and this status excluded)",
           "full_validated_content_sha256": json.load(open(os.path.join(ROOT, "data/processed/adzuna/dataset_manifest.json")))["output_files"]["career_market_full_validated"]["content_sha256"]}
    json.dump(out, open(os.path.join(ROOT, "data", "audits", "dataset", "reproducibility_check.json"), "w"), indent=1, sort_keys=True)
    mp = os.path.join(ROOT, "data", "processed", "adzuna", "dataset_manifest.json")
    m = json.load(open(mp))
    m["reproducibility_status"] = {"result": out["result"], "runs": 2, "matches_main_outputs": not vs_main, "detail": "data/audits/dataset/reproducibility_check.json"}
    json.dump(m, open(mp, "w"), indent=1, sort_keys=True, ensure_ascii=False)
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-root", default=ROOT)
    ap.add_argument("--check-reproducible", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.check_reproducible:
        sys.exit(0 if check_reproducible()["result"] == "PASS" else 1)
    run(a.output_root, verbose=not a.quiet)
