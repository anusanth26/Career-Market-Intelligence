#!/usr/bin/env python3
"""
Salary-focused augmentation for the Career Market dataset (ADDITIVE, non-destructive).

Problem it solves
-----------------
The final modelling dataset has only ~599 rows with a real salary (9%). Adzuna exposes a
`salary_min` filter that returns ONLY postings carrying a salary, so we can collect MORE real
salaried postings for the India market and merge the new ones in. No data is fabricated.

Two stages
----------
    python scripts/augment_salary_data.py collect        # pull salary-only postings -> new raw run
    python scripts/augment_salary_data.py merge           # dedupe + append new salaried rows to final CSV

Guarantees
----------
* Existing raw data is never touched; new raw goes to data/raw/adzuna/salary_augment_<ts>/.
* `merge` backs up data/final/career_market_core_analysis.csv to data/archive/ before writing.
* New rows are deduped by job_id against the existing dataset (no duplicates added).
* Role is assigned from the TITLE only (reuses scripts/role_mapping.py); only the 10 core roles
  are kept; salary flags/plausibility reuse the exact rules from config/dataset_build.json.
* Every new row carries source_run = the augment run id, so it is fully traceable.

Setup: ADZUNA_APP_ID / ADZUNA_APP_KEY in .env (same as the main collector).
"""

import argparse
import glob
import json
import os
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from role_mapping import compile_rules, map_title  # noqa: E402

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

ROLES_PATH = os.path.join(ROOT, "config", "roles.json")
BUILD_CFG_PATH = os.path.join(ROOT, "config", "dataset_build.json")
FINAL_CSV = os.path.join(ROOT, "data", "final", "career_market_core_analysis.csv")
RAW_ROOT = os.path.join(ROOT, "data", "raw", "adzuna")
ARCHIVE_DIR = os.path.join(ROOT, "data", "archive")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"
COUNTRY_CODE = "in"
SALARY_MIN_FILTER = 1
PAGE_CAP = 8  # safety cap on pages per variant (page_size 50 -> up to 400 records/variant)
ALNUM = re.compile(r"[^a-z0-9]+")


def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text):
    text = str(text)
    for secret in (APP_ID, APP_KEY):
        if secret:
            text = text.replace(secret, "***")
    return re.sub(r"(app_(?:id|key)=)[^&\s'\"]+", r"\1***", text)


def slug(text):
    return ALNUM.sub("_", text.lower()).strip("_")


def norm_text(s):
    return ALNUM.sub(" ", (s or "").lower()).strip()


def to_float(v):
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def load_configs():
    with open(ROLES_PATH, encoding="utf-8") as f:
        roles_cfg = json.load(f)
    with open(BUILD_CFG_PATH, encoding="utf-8") as f:
        build_cfg = json.load(f)
    core_scope = build_cfg["scope"]["core"]
    core_roles = {r for roles in core_scope.values() for r in roles}
    domain_of = {r: dom for dom, roles in core_scope.items() for r in roles}
    return roles_cfg, build_cfg, core_roles, domain_of


# ── collect stage ─────────────────────────────────────────────────────

def api_get(session, page, title_only, max_days_old, timeout):
    params = {
        "app_id": APP_ID, "app_key": APP_KEY,
        "results_per_page": 50, "title_only": title_only,
        "max_days_old": max_days_old, "sort_by": "date",
        "salary_min": SALARY_MIN_FILTER,
    }
    for attempt in range(4):
        try:
            r = session.get(BASE_URL.format(page=page), params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json(), None
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(min(60, 2 ** attempt) + random.uniform(0, 1))
                continue
            return None, f"HTTP {r.status_code}: {redact(r.text[:160])}"
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt < 3:
                time.sleep(min(60, 2 ** attempt) + random.uniform(0, 1))
                continue
            return None, redact(f"{type(e).__name__}: {e}")
    return None, "retries_exhausted"


def collect():
    if not APP_ID or not APP_KEY:
        sys.exit("ERROR: set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env")
    roles_cfg, _, core_roles, _ = load_configs()
    settings = roles_cfg["settings"]
    interval = settings["min_interval_seconds"]
    max_days_old = settings["max_days_old"]
    timeout = settings["request_timeout_seconds"]

    run_id = f"salary_augment_{datetime.now():%Y%m%dT%H%M%SZ}"
    run_dir = os.path.join(RAW_ROOT, run_id)
    os.makedirs(run_dir, exist_ok=False)

    session = requests.Session()
    manifest = {"run_id": run_id, "started": iso_now(), "country": COUNTRY_CODE,
                "salary_min": SALARY_MIN_FILTER, "max_days_old": max_days_old,
                "queries": [], "total_raw_records": 0}
    seen_ids = set()
    print(f"Run {run_id}\nCollecting salary-only postings for {len(core_roles)} core roles (India)...\n")

    for role_entry in roles_cfg["roles"]:
        if role_entry["role"] not in core_roles or COUNTRY_CODE not in role_entry.get("countries", []):
            continue
        role = role_entry["role"]
        for variant in role_entry["variants"]:
            query = variant if isinstance(variant, str) else variant["query"]
            rec_path = os.path.join(run_dir, f"records_{slug(role)}__{slug(query)}.jsonl")
            q_records, api_count = 0, None
            for page in range(1, PAGE_CAP + 1):
                data, err = api_get(session, page, query, max_days_old, timeout)
                time.sleep(interval)
                if data is None:
                    manifest["queries"].append({"role": role, "query": query, "page": page, "error": err})
                    break
                if api_count is None:
                    api_count = data.get("count")
                results = data.get("results", [])
                if not results:
                    break
                with open(rec_path, "a", encoding="utf-8") as f:
                    for pos, raw in enumerate(results):
                        f.write(json.dumps({
                            "collection": {"run_id": run_id, "collected_at": iso_now(),
                                           "source": "adzuna", "country": COUNTRY_CODE,
                                           "query_variant": query, "query_role": role,
                                           "adzuna_id": str(raw.get("id")), "page": page, "position": pos},
                            "raw": raw,
                        }, ensure_ascii=False) + "\n")
                        seen_ids.add(str(raw.get("id")))
                q_records += len(results)
                if len(results) < 50:
                    break
            manifest["queries"].append({"role": role, "query": query, "api_count": api_count, "records": q_records})
            manifest["total_raw_records"] += q_records
            print(f"  {role:28s} {query!r:36s} api_count={api_count} records={q_records}", flush=True)

    manifest["finished"] = iso_now()
    manifest["unique_ids_collected"] = len(seen_ids)
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nCollected {manifest['total_raw_records']} raw records "
          f"({len(seen_ids)} unique ids) into {os.path.relpath(run_dir, ROOT)}")
    print("Next: python scripts/augment_salary_data.py merge")


# ── merge stage ───────────────────────────────────────────────────────

def salary_flags(lo, hi, is_predicted, floor, ceiling):
    """Exact replica of the salary screen in scripts/build_dataset.py."""
    pres = lo is not None or hi is not None
    a = lo if lo is not None else hi
    b = hi if hi is not None else lo
    flags = []
    if pres:
        if is_predicted == "1":
            flags.append("adzuna_predicted")
        if lo is not None and hi is not None and lo > hi:
            flags.append("min_gt_max")
        if a is not None and a <= 0:
            flags.append("non_positive")
        elif a is not None and a < floor:
            flags.append("below_floor")
        if b is not None and b > ceiling:
            flags.append("above_ceiling")
        if lo is not None and hi is not None and lo == hi:
            flags.append("point_value")
        if (lo is None) != (hi is None):
            flags.append("one_sided")
    bad = {"adzuna_predicted", "min_gt_max", "non_positive", "below_floor", "above_ceiling"}
    passes = bool(pres and not (set(flags) & bad))
    return pres, flags, passes


def latest_run_dir():
    runs = sorted(glob.glob(os.path.join(RAW_ROOT, "salary_augment_*")))
    return runs[-1] if runs else None


def build_row(raw, prov, role_info, build_cfg, run_id, records_file):
    role, role_scope, domain, role_group, mapping_tier = role_info
    co = raw.get("company") if isinstance(raw.get("company"), dict) else {}
    lo_ = raw.get("location") if isinstance(raw.get("location"), dict) else {}
    ca = raw.get("category") if isinstance(raw.get("category"), dict) else {}
    area = list(lo_.get("area")) if isinstance(lo_.get("area"), list) else []
    desc = raw.get("description") if isinstance(raw.get("description"), str) else ""
    title = raw.get("title") if isinstance(raw.get("title"), str) else None
    employer = co.get("display_name") or None
    smin, smax = to_float(raw.get("salary_min")), to_float(raw.get("salary_max"))
    is_pred = None if raw.get("salary_is_predicted") in (None, "") else str(raw.get("salary_is_predicted"))
    floor = build_cfg["quality"]["salary"]["floor"]
    ceiling = build_cfg["quality"]["salary"]["ceiling"]
    pres, flags, passes = salary_flags(smin, smax, is_pred, floor, ceiling)
    created = raw.get("created")
    try:
        cdate = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d") if created else None
    except (TypeError, ValueError):
        cdate = None
    q = build_cfg["quality"]
    letters = [ch for ch in ((title or "") + desc) if ch.isalpha()]
    non_en = letters and sum(1 for ch in letters if ord(ch) > 127) / len(letters) > q["non_english_ratio_threshold"]
    return {
        "job_id": str(raw["id"]) if raw.get("id") not in (None, "") else None,
        "title": title, "role": role, "role_scope": role_scope, "role_status": role_scope,
        "domain": domain, "role_group": role_group, "mapping_tier": mapping_tier,
        "employer": employer, "employer_normalized": norm_text(employer),
        "employer_missing": not (employer or "").strip(),
        "description_raw": desc or None,
        "location_display": lo_.get("display_name") or None,
        "location_area": json.dumps(area, ensure_ascii=False),
        "location_country": area[0] if area else None,
        "location_region": area[1] if len(area) > 1 else None,
        "location_has_region": len(area) > 1,
        "latitude": to_float(raw.get("latitude")), "longitude": to_float(raw.get("longitude")),
        "created": created, "created_date": cdate,
        "category_label": ca.get("label"), "category_tag": ca.get("tag"),
        "contract_type": raw.get("contract_type"), "contract_time": raw.get("contract_time"),
        "salary_min": smin, "salary_max": smax, "salary_is_predicted": is_pred,
        "salary_present": pres, "salary_flags": json.dumps(flags),
        "salary_passes_plausibility_screen": passes,
        "source_run": run_id, "source_file": records_file,
        "source_query": prov.get("query_variant"), "source_query_role": prov.get("query_role"),
        "collection_timestamp": prov.get("collected_at"),
        "collection_date": (prov.get("collected_at") or "")[:10] or None,
        "collection_method": "adzuna_api_salary_filter",
        "query_roles_seen": None, "also_seen_in": None,
        "id_dup_count": 1, "near_dup_group_size": 1, "near_dup_key": None,
        "employer_cap_status": "not_applicable", "in_core_analysis_dataset": True,
        "description_length": len(desc),
        "description_is_truncated": desc.rstrip().endswith("…"),
        "description_short_flag": 0 < len(desc) < q["short_description_chars"],
        "language_flag": "non_english_suspected" if non_en else "english_or_ascii",
    }


def merge():
    roles_cfg, build_cfg, core_roles, domain_of = load_configs()
    rules = compile_rules(roles_cfg["roles"])
    # role_group for core roles follows the pipeline: core roles use their own name
    run_dir = latest_run_dir()
    if not run_dir:
        sys.exit("No salary_augment_* run found. Run the collect stage first.")
    run_id = os.path.basename(run_dir)
    print(f"Merging from run: {run_id}")

    existing = pd.read_csv(FINAL_CSV, low_memory=False)
    existing_ids = set(existing["job_id"].astype(str))
    before_total = len(existing)
    before_salaried = int(existing["salary_present"].sum()) if "salary_present" in existing else 0
    before_valid = int(existing["salary_passes_plausibility_screen"].sum()) if "salary_passes_plausibility_screen" in existing else 0

    new_rows, seen_new, skipped = [], set(), {"dup_existing": 0, "dup_in_batch": 0, "non_core_role": 0, "no_salary": 0, "no_id": 0}
    for path in sorted(glob.glob(os.path.join(run_dir, "records_*.jsonl"))):
        records_file = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                raw, prov = obj["raw"], obj["collection"]
                jid = str(raw.get("id")) if raw.get("id") not in (None, "") else None
                if not jid:
                    skipped["no_id"] += 1
                    continue
                if jid in existing_ids:
                    skipped["dup_existing"] += 1
                    continue
                if jid in seen_new:
                    skipped["dup_in_batch"] += 1
                    continue
                m = map_title(raw.get("title") or "", rules)
                if m["role"] not in core_roles:
                    skipped["non_core_role"] += 1
                    continue
                norm = m["normalized_title"]
                rc = next(r for r in roles_cfg["roles"] if r["role"] == m["role"])
                hits = [i for i, p in enumerate(rc.get("match", [])) if re.search(p, norm)]
                mapping_tier = "canonical" if hits and hits[0] == 0 else "synonym"
                role_info = (m["role"], "core", domain_of.get(m["role"]), m["role"], mapping_tier)
                row = build_row(raw, prov, role_info, build_cfg, run_id, records_file)
                if not row["salary_present"]:
                    skipped["no_salary"] += 1
                    continue
                seen_new.add(jid)
                new_rows.append(row)

    print(f"\nNew unique salaried core-role rows found: {len(new_rows)}")
    print(f"Skipped: {skipped}")
    if not new_rows:
        print("Nothing to merge.")
        return

    new_df = pd.DataFrame(new_rows)
    # align to existing schema (existing column order wins; fill any missing)
    for col in existing.columns:
        if col not in new_df.columns:
            new_df[col] = None
    new_df = new_df[existing.columns]

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    backup = os.path.join(ARCHIVE_DIR, f"career_market_core_analysis_backup_{datetime.now():%Y%m%dT%H%M%S}.csv")
    existing.to_csv(backup, index=False)

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.to_csv(FINAL_CSV, index=False)

    after_salaried = int(combined["salary_present"].sum())
    after_valid = int(combined["salary_passes_plausibility_screen"].sum())
    print(f"\nBacked up original to: {os.path.relpath(backup, ROOT)}")
    print(f"Final dataset: {os.path.relpath(FINAL_CSV, ROOT)}")
    print("\n--- before -> after ---")
    print(f"total rows            : {before_total:6d} -> {len(combined)}")
    print(f"salary_present rows   : {before_salaried:6d} -> {after_salaried}")
    print(f"pass plausibility     : {before_valid:6d} -> {after_valid}")
    print(f"new salaried added    : +{after_salaried - before_salaried}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["collect", "merge"], help="collect = pull from API; merge = append to final CSV")
    args = ap.parse_args()
    if args.stage == "collect":
        collect()
    else:
        merge()


if __name__ == "__main__":
    main()
