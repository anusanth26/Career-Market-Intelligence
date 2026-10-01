"""
Clean-posting yield analysis for one collection run (output of scripts/collect_adzuna.py).

    python scripts/analyze_coverage.py                      # latest run
    python scripts/analyze_coverage.py --run-dir data/raw/adzuna/runs/<run_id>

Funnel per role (rows mapped to the role from ANY query, by title only):
    API count (from the API)  ->  raw rows retrieved  ->  title-matched rows
    ->  exact-ID duplicates removed  ->  near-duplicates removed (normalized title + company +
        first N description chars)  ->  employer cap  ->  CLEAN count

Nothing is deleted from raw data. Every removal is written to analysis/dedup_removals.csv.
Rules, thresholds and the salary floor/ceiling come from the config snapshot stored in the run.
Writes everything to <run_dir>/analysis/.
"""

import argparse
import csv
import glob
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from role_mapping import compile_rules, map_title, normalize_title  # noqa: E402

ALPHANUM = re.compile(r"[^a-z0-9]+")


def norm_text(s) -> str:
    return ALPHANUM.sub(" ", (s or "").lower()).strip()


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def latest_run(root="data/raw/adzuna/runs"):
    runs = sorted(d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d))
    if not runs:
        sys.exit("No runs found.")
    return runs[-1]


# ── pipeline ──────────────────────────────────────────────────────────

def dedupe_and_cap(pool, settings, role_label, removals, attrib):
    """pool: list of row dicts in retrieval order. Returns clean rows. Updates removals (log) and
    attrib[variant_key][counter] so removals can be attributed to the variant that retrieved them."""
    n_chars = settings["dedup_description_chars"]

    # 1. exact Adzuna ID
    seen, stage1 = {}, []
    for row in pool:
        rid = row["id"]
        if rid in seen:
            attrib[row["vkey"]]["exact_dup"] += 1
            removals.append(removal(role_label, row, "exact_id_duplicate", seen[rid]))
        else:
            seen[rid] = rid
            stage1.append(row)

    # 2. near-duplicates
    keyed, stage2 = {}, []
    for row in stage1:
        key = (norm_text(row["title"]), norm_text(row["employer"]), norm_text(row["description"])[:n_chars])
        if key in keyed:
            attrib[row["vkey"]]["near_dup"] += 1
            removals.append(removal(role_label, row, "near_duplicate(title+company+desc_prefix)", keyed[key]))
        else:
            keyed[key] = row["id"]
            stage2.append(row)

    # 3. employer concentration cap (postings with no employer are never capped)
    cap_n = max(1, math.floor(settings["employer_cap_fraction"] * len(stage2)))
    by_emp = defaultdict(list)
    for row in stage2:
        if row["employer_norm"]:
            by_emp[row["employer_norm"]].append(row)
    drop = set()
    for emp, rows in by_emp.items():
        if len(rows) > cap_n:
            keep = sorted(rows, key=lambda r: (r["created"] or "", -r["order"]), reverse=True)[:cap_n]
            keep_ids = {r["id"] for r in keep}
            for r in rows:
                if r["id"] not in keep_ids:
                    drop.add(r["id"])
                    attrib[r["vkey"]]["cap"] += 1
                    removals.append(removal(role_label, r, f"employer_cap(>{cap_n} per employer)", ""))
    clean = [r for r in stage2 if r["id"] not in drop]
    return clean, cap_n


def removal(role, row, reason, kept_id):
    return {"role": role, "adzuna_id": row["id"], "employer": row["employer"], "title": row["title"],
            "reason": reason, "kept_id": kept_id, "query_variant": row["variant"]}


def salary_stats(rows, settings):
    floor, ceil_ = settings["salary_floor"], settings["salary_ceiling"]
    n = len(rows)
    smin = [r for r in rows if r["salary_min"] is not None]
    smax = [r for r in rows if r["salary_max"] is not None]
    both = [r for r in rows if r["salary_min"] is not None and r["salary_max"] is not None]
    any_sal = [r for r in rows if r["salary_min"] is not None or r["salary_max"] is not None]
    pred = [r for r in rows if r["salary_pred"] == "1"]
    below = [r for r in any_sal if min(v for v in (r["salary_min"], r["salary_max"]) if v is not None) < floor]
    above = [r for r in any_sal if max(v for v in (r["salary_min"], r["salary_max"]) if v is not None) > ceil_]
    inverted = [r for r in both if r["salary_min"] > r["salary_max"]]
    point = [r for r in both if r["salary_min"] == r["salary_max"]]
    bad = {id(r) for r in below + above + inverted}
    return {
        "clean_postings": n, "salary_min_count": len(smin), "salary_max_count": len(smax),
        "salary_both_count": len(both), "salary_any_count": len(any_sal),
        "salary_percentage": round(100 * len(smin) / n, 1) if n else 0.0,
        "predicted_count": len(pred), "predicted_percentage": round(100 * len(pred) / n, 1) if n else 0.0,
        "suspicious_below_floor": len(below), "suspicious_above_ceiling": len(above),
        "suspicious_min_gt_max": len(inverted), "point_salary_min_eq_max": len(point),
        "salary_valid_count_after_floor_ceiling": len([r for r in any_sal if id(r) not in bad]),
        "salary_floor": floor, "salary_ceiling": ceil_,
    }


def architect_audit(pool_unique, cfg_role):
    it_terms, bld_terms = cfg_role["audit"]["it_terms"], cfg_role["audit"]["building_terms"]

    def has(term, norm):
        return f" {term} " in f" {norm} "
    classes, samples = Counter(), defaultdict(Counter)
    for r in pool_unique:
        n = normalize_title(r["title"])
        it, bld = any(has(t, n) for t in it_terms), any(has(t, n) for t in bld_terms)
        c = "likely_it_architect" if it and not bld else "likely_building_architect" if bld and not it else "ambiguous"
        classes[c] += 1
        samples[c][r["title"]] += 1
    total = sum(classes.values())
    return {
        "unique_architect_titled_postings_analyzed": total,
        "counts": dict(classes),
        "percent": {k: round(100 * v / total, 1) if total else 0 for k, v in classes.items()},
        "top_titles": {k: v.most_common(20) for k, v in samples.items()},
        "method": ("Rule-based on title tokens only. 'ambiguous' includes bare titles such as 'Architect' or "
                   "'Senior Architect' and titles with both IT and building cues. Sample = the most recent "
                   "postings returned by title_only='architect' (sort_by=date), NOT a random sample."),
    }


# ── main ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir")
    ap.add_argument("--out-dir", help="write results here instead of <run_dir>/analysis (for sensitivity runs)")
    ap.add_argument("--config", help="re-map with these rules/thresholds instead of the run's config snapshot")
    args = ap.parse_args()
    run_dir = args.run_dir or latest_run()
    out_dir = args.out_dir or os.path.join(run_dir, "analysis")
    os.makedirs(out_dir, exist_ok=True)

    manifest = json.load(open(os.path.join(run_dir, "run_manifest.json"), encoding="utf-8"))
    cfg = json.load(open(args.config, encoding="utf-8")) if args.config else manifest["config_snapshot"]
    settings = cfg["settings"]
    role_cfg = {r["role"]: r for r in cfg["roles"]}
    rules = compile_rules(cfg["roles"])
    queries = read_jsonl(os.path.join(run_dir, "queries.jsonl"))
    # calendar-day window (Adzuna's max_days_old granularity); older manifests stored an exact timestamp
    window_start = manifest["window_start"][:10] + "T00:00:00Z"
    exact_start = manifest.get("window_start_exact_timestamp") or manifest["window_start"]

    # load all rows in retrieval order, map roles by title
    rows, order = [], 0
    for q in queries:
        for rec in read_jsonl(os.path.join(run_dir, q["records_file"])):
            raw, col = rec["raw"], rec["collection"]
            m = map_title(raw.get("title", ""), rules)
            rows.append({
                "order": order, "id": str(raw.get("id")), "title": raw.get("title", ""),
                "description": raw.get("description", ""), "created": raw.get("created"),
                "employer": (raw.get("company") or {}).get("display_name") or "",
                "employer_norm": norm_text((raw.get("company") or {}).get("display_name")),
                "salary_min": raw.get("salary_min"), "salary_max": raw.get("salary_max"),
                "salary_pred": str(raw.get("salary_is_predicted", "")),
                "country": col["country"], "variant": col["query_variant"], "query_role": col["query_role"],
                "map_status": m["status"], "mapped_role": m["role"], "map_reason": m["reason"],
                "in_window": bool(raw.get("created")) and raw["created"] >= window_start,
            })
            order += 1
    out_of_window = sum(1 for r in rows if not r["in_window"])
    before_exact = sum(1 for r in rows if r["created"] and r["created"] < exact_start)

    removals, results, salary_rows = [], [], []
    inspection = []  # variant-level title/status inspection for manual review
    role_summary = []
    pools_unique = {}
    ts_max = max(q["pull_finished"] for q in queries)

    countries = sorted({q["country"] for q in queries})
    for country in countries:
        crow = [r for r in rows if r["country"] == country]
        for role in [r["role"] for r in cfg["roles"]]:
            rq = [q for q in queries if q["country"] == country and q["query_role"] == role]
            if not rq:
                continue
            cfgr = role_cfg[role]
            pool = [r for r in crow if r["mapped_role"] == role and r["in_window"]]
            for r in pool:
                r["vkey"] = r["variant"] if r["query_role"] == role else "(other roles' queries)"
            attrib = defaultdict(Counter)
            clean, cap_n = dedupe_and_cap(pool, settings, role, removals, attrib)
            pools_unique[(country, role)] = list({r["id"]: r for r in pool}.values())
            for r in clean:
                attrib[r["vkey"]]["clean"] += 1
                attrib[r["vkey"]]["salary"] += r["salary_min"] is not None

            def emit(level, variant, api, raw_n, tm, a, ts, extra=None):
                cl = a["clean"]
                results.append({
                    "level": level, "domain": cfgr["domain"], "canonical_role": role, "tier": cfgr.get("tier"),
                    "query_variant": variant, "country": country, "api_count": api, "raw_count": raw_n,
                    "title_match_count": tm, "exact_duplicates_removed": a["exact_dup"],
                    "near_duplicates_removed": a["near_dup"], "employer_cap_removed": a["cap"],
                    "clean_count": cl, "salary_count": a["salary"],
                    "salary_percentage": round(100 * a["salary"] / cl, 1) if cl else 0.0,
                    "collection_timestamp": ts, **(extra or {}),
                })

            # variant-level rows (marginal contribution, in retrieval order)
            for q in rq:
                vrows = [r for r in crow if r["variant"] == q["query"] and r["query_role"] == role]
                st = Counter(r["map_status"] if r["mapped_role"] in (None, role) else "mapped_to_other_role"
                             for r in vrows)
                tm = sum(1 for r in vrows if r["mapped_role"] == role and r["in_window"])
                emit("variant", q["query"], q["api_count"], q["raw_records"], tm, attrib[q["query"]],
                     q["pull_finished"], {
                         "unmatched_count": st["unmatched"], "excluded_by_rule_count": st["excluded_by_rule"],
                         "ambiguous_multi_count": st["ambiguous_multi"],
                         "mapped_to_other_role_count": st["mapped_to_other_role"],
                         "capped_by_max_records": q["capped_by_max_records"], "query_status": q["status"]})
                for (status, title), n in Counter(
                        (r["map_status"] if r["mapped_role"] in (None, role) else f"mapped:{r['mapped_role']}",
                         r["title"]) for r in vrows).most_common(400):
                    inspection.append({"role": role, "query_variant": q["query"], "status": status,
                                       "title": title, "n": n})
            if attrib.get("(other roles' queries)"):
                emit("variant", "(other roles' queries)", "", "", sum(1 for r in pool if r["vkey"].startswith("(other")),
                     attrib["(other roles' queries)"], ts_max)

            # role-level row
            total = Counter()
            for a in attrib.values():
                total.update(a)
            raw_own = sum(q["raw_records"] for q in rq)
            api_sum = sum(q["api_count"] or 0 for q in rq)
            capped = any(q["capped_by_max_records"] for q in rq)
            yield_rate = total["clean"] / raw_own if raw_own else 0
            projected = round(total["clean"] * api_sum / raw_own) if raw_own and capped else None
            emit("role", "ALL_VARIANTS", rq[0]["api_count"], raw_own, len(pool), total, ts_max, {
                "capped_by_max_records": capped, "api_count_sum_over_variants": api_sum,
                "yield_clean_per_raw": round(yield_rate, 3), "employer_cap_n": cap_n,
                "projected_clean_if_fully_pulled_UPPER_BOUND_inferred": projected,
                "query_status": "partial" if any(q["status"] != "complete" for q in rq) else "complete"})
            role_summary.append(results[-1])
            if cfgr.get("tier") != "audit":
                salary_rows.append({"country": country, "role": role, **salary_stats(clean, settings)})

    # group rows (e.g. all security titles combined, deduplicated together)
    groups = defaultdict(list)
    for r in cfg["roles"]:
        if r.get("group"):
            groups[r["group"]].append(r["role"])
    for g, members in groups.items():
        for country in countries:
            pool = [r for r in rows if r["country"] == country and r["mapped_role"] in members and r["in_window"]]
            for r in pool:
                r["vkey"] = r["variant"]
            attrib = defaultdict(Counter)
            clean, _ = dedupe_and_cap(pool, settings, f"GROUP:{g}", removals, attrib)
            tot = Counter()
            for a in attrib.values():
                tot.update(a)
            sal = sum(r["salary_min"] is not None for r in clean)
            results.append({
                "level": "group", "domain": "Technology & Data", "canonical_role": f"GROUP:{g} (all members combined)",
                "tier": "probe", "query_variant": "ALL_MEMBERS", "country": country, "api_count": "",
                "raw_count": "", "title_match_count": len(pool), "exact_duplicates_removed": tot["exact_dup"],
                "near_duplicates_removed": tot["near_dup"], "employer_cap_removed": tot["cap"],
                "clean_count": len(clean), "salary_count": sal,
                "salary_percentage": round(100 * sal / len(clean), 1) if clean else 0.0,
                "collection_timestamp": ts_max})

    # ── write tables ─────────────────────────────────────────────────
    def write_csv(name, data):
        if not data:
            return
        keys = list(dict.fromkeys(k for d in data for k in d))
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(data)

    write_csv("coverage_results.csv", results)
    write_csv("dedup_removals.csv", removals)
    write_csv("salary_audit.csv", salary_rows)
    write_csv("variant_title_inspection.csv", inspection)

    # architect contamination
    for (country, role), pool in pools_unique.items():
        if "audit" in role_cfg[role]:
            with open(os.path.join(out_dir, "architect_audit.json"), "w") as f:
                json.dump({"country": country, **architect_audit(pool, role_cfg[role])}, f, indent=2)

    # ── scope decision ───────────────────────────────────────────────
    thr, border = settings["clean_threshold"], settings["borderline_threshold"]
    decisions, table = [], []
    for r in role_summary:
        if r["tier"] == "audit":
            continue
        proj = r["projected_clean_if_fully_pulled_UPPER_BOUND_inferred"]
        if r["query_status"] != "complete":
            d, why = "CONDITIONAL", "collection incomplete (failures) - rerun before deciding"
        elif r["clean_count"] >= thr:
            d, why = "DEFINITELY INCLUDE", f"clean_count {r['clean_count']} >= {thr} (measured)"
        elif r["capped_by_max_records"] and proj and proj >= thr:
            d, why = "CONDITIONAL", (f"pull was capped at the per-query record limit; clean {r['clean_count']} < {thr} "
                                     f"but upper-bound projection {proj} >= {thr} [inferred] - needs deeper pull")
        elif r["clean_count"] >= border:
            d, why = "CONDITIONAL", f"borderline: {border} <= clean {r['clean_count']} < {thr}"
        else:
            d, why = "EXCLUDE", (f"clean {r['clean_count']} < {border}"
                                 + ("" if not r["capped_by_max_records"] else " (capped pull)"))
        decisions.append({**r, "decision": d, "reason": why})
        table.append((r["domain"], r["canonical_role"], r["api_count"], r["clean_count"],
                      r["salary_percentage"], "YES" if r["clean_count"] >= thr else "NO", d))

    with open(os.path.join(out_dir, "summary_table.md"), "w") as f:
        f.write("| Domain | Role | API Count (primary variant) | Clean Count | Salary % | Pass 400? | Decision |\n"
                "|---|---|---:|---:|---:|---|---|\n")
        for t in table:
            f.write(f"| {t[0]} | {t[1]} | {t[2]} | {t[3]} | {t[4]} | {t[5]} | {t[6]} |\n")
    write_csv("scope_decision.csv", [{k: d[k] for k in ("domain", "canonical_role", "tier", "api_count", "raw_count",
              "title_match_count", "clean_count", "salary_percentage", "capped_by_max_records", "decision", "reason")}
              for d in decisions])

    # ── collector audit checks (evidence for the quality audit) ──────
    fails = [json.loads(l) for l in open(os.path.join(run_dir, "attempts.jsonl"))] \
        if os.path.exists(os.path.join(run_dir, "attempts.jsonl")) else []
    contiguous = True
    for q in queries:
        pages = sorted({rec["collection"]["page"] for rec in read_jsonl(os.path.join(run_dir, q["records_file"]))})
        contiguous &= pages == list(range(1, len(pages) + 1))
    checks = {
        "run_id": manifest["run_id"], "queries": len(queries), "rows_total": len(rows),
        "title_only_sent_for_every_query": all(q["request_params"].get("title_only") == q["query"] for q in queries),
        "max_days_old_sent": sorted({q["request_params"].get("max_days_old") for q in queries}),
        "sort_by_sent": sorted({q["request_params"].get("sort_by") for q in queries}),
        "window_start_calendar_day": window_start,
        "rows_before_calendar_day_window": out_of_window,
        "rows_before_exact_timestamp_window": before_exact,
        "earliest_created_in_run": min(r["created"] for r in rows if r["created"]),
        "queries_created_sorted_desc": sum(q["created_sorted_desc"] for q in queries),
        "queries_not_sorted_desc": [q["query"] for q in queries if not q["created_sorted_desc"]],
        "pages_contiguous_from_1_in_every_query": contiguous,
        "duplicate_ids_within_a_single_query_total": sum(q["duplicate_ids_within_query"] for q in queries),
        "api_count_logged_for_every_query": all(q["api_count"] is not None for q in queries),
        "queries_with_zero_results": [q["query"] for q in queries if q["raw_records"] == 0],
        "http_failures_total": sum(q["http_failures"] for q in queries),
        "retries_total": sum(q["retries"] for q in queries),
        "failed_attempt_log_entries": len(fails),
        "failed_status_counts": dict(Counter(str(a.get("status")) for a in fails if "status" in a)),
        "queries_not_complete": [q["query"] for q in queries if q["status"] != "complete"],
        "api_count_varied_within_query": [q["query"] for q in queries if q["api_count_min"] != q["api_count_max"]],
        "mapping_status_counts": dict(Counter(r["map_status"] for r in rows)),
        "credentials_present_in_run_files": any(
            s and s in open(p, encoding="utf-8", errors="ignore").read()
            for p in glob.glob(os.path.join(run_dir, "*")) if os.path.isfile(p)
            for s in [os.getenv("ADZUNA_APP_KEY")]),
    }
    json.dump(checks, open(os.path.join(out_dir, "audit_checks.json"), "w"), indent=2)
    print(open(os.path.join(out_dir, "summary_table.md")).read())
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
