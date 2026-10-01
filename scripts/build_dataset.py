#!/usr/bin/env python3
"""
Builds the canonical Career Market Intelligence dataset from the Adzuna data ALREADY COLLECTED.

  RAW (immutable) -> READ -> NORMALIZE -> ID-DEDUP -> NEAR-DEDUP -> ROLE ASSIGNMENT (title only) -> QUALITY FILTER -> DATASET

Makes NO network calls (no Adzuna, no Google Trends). Reads raw files read-only and verifies by checksum that they were not
modified. Deterministic: no randomness, explicit sorting, no wall-clock values inside the dataset content.

    python scripts/build_dataset.py                      # build into data/processed/adzuna and data/audits/dataset
    python scripts/build_dataset.py --check-reproducible # build twice into temp dirs and compare content hashes

Rules and thresholds: config/dataset_build.json. Mapping rules: config/roles.json (+ overrides in dataset_build.json).
Documentation: report/dataset_documentation.md
"""

import argparse
import copy
import glob
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from role_mapping import compile_rules, map_title, normalize_title  # noqa: E402

CFG_PATH = os.path.join(ROOT, "config", "dataset_build.json")
ROLES_PATH = os.path.join(ROOT, "config", "roles.json")
ALNUM = re.compile(r"[^a-z0-9]+")


# ── small helpers ─────────────────────────────────────────────────────

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_text(s):
    return ALNUM.sub(" ", (s or "").lower()).strip()


def parse_iso(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def num_id(s):
    return int(s) if s and str(s).isdigit() else 10 ** 18


def norm_description(d):
    t = unicodedata.normalize("NFKC", d or "")
    t = re.sub(r"[​‌‍⁠﻿]", "", t)
    t = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", t)
    t = re.sub(r"(?:…|\.\.\.)\s*$", "", t.strip())
    return re.sub(r"\s+", " ", t).strip().lower()


def to_float(v):
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def jdump(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


# ── 1. discovery + reading (read-only) ────────────────────────────────

def discover(raw_root, cfg):
    legacy = sorted(glob.glob(os.path.join(raw_root, cfg["sources"]["legacy_glob"])))
    runs = []
    rd = os.path.join(raw_root, cfg["sources"]["runs_dir"])
    if os.path.isdir(rd):
        for r in sorted(os.listdir(rd)):
            d = os.path.join(rd, r)
            if os.path.isdir(d) and glob.glob(os.path.join(d, cfg["sources"]["run_records_glob"])):
                runs.append(d)
    return legacy, runs


def read_all(raw_root, cfg):
    """Returns rows (one per raw record incl. duplicates), file inventory, malformed-record log, window/reference info."""
    legacy_files, run_dirs = discover(raw_root, cfg)
    pull_log = {}
    pl = os.path.join(raw_root, cfg["sources"]["legacy_pull_log"])
    if os.path.exists(pl):
        pull_log = json.load(open(pl, encoding="utf-8"))
    rows, inventory, malformed = [], [], []
    window_starts, collected_max = [], None

    def make_row(raw, prov):
        co = raw.get("company") if isinstance(raw.get("company"), dict) else {}
        lo = raw.get("location") if isinstance(raw.get("location"), dict) else {}
        ca = raw.get("category") if isinstance(raw.get("category"), dict) else {}
        return {
            "job_id": str(raw["id"]) if raw.get("id") not in (None, "") else None,
            "title": raw.get("title") if isinstance(raw.get("title"), str) else None,
            "employer": co.get("display_name") or None,
            "description_raw": raw.get("description") if isinstance(raw.get("description"), str) else None,
            "location_display": lo.get("display_name") or None,
            "location_area": list(lo.get("area")) if isinstance(lo.get("area"), list) else [],
            "latitude": to_float(raw.get("latitude")), "longitude": to_float(raw.get("longitude")),
            "created": raw.get("created"), "category_label": ca.get("label"), "category_tag": ca.get("tag"),
            "salary_min": to_float(raw.get("salary_min")), "salary_max": to_float(raw.get("salary_max")),
            "salary_is_predicted": None if raw.get("salary_is_predicted") in (None, "") else str(raw.get("salary_is_predicted")),
            "contract_type": raw.get("contract_type"), "contract_time": raw.get("contract_time"), **prov,
        }

    for f in legacy_files:
        rel = os.path.relpath(f, ROOT)
        m = re.match(r"adzuna_(.+)_(\d{4}-\d{2}-\d{2})\.json$", os.path.basename(f))
        slug, date = (m.group(1), m.group(2)) if m else (None, None)
        query = slug.replace("_", " ") if slug else None
        if query and pull_log and query not in pull_log.get("categories", {}):
            query = None  # do not invent provenance not corroborated by the pull log
        n_ok = n_bad = 0
        try:
            data = json.load(open(f, encoding="utf-8"))
        except (ValueError, OSError) as e:
            malformed.append({"file": rel, "line": None, "reason": f"unreadable file: {e}"})
            inventory.append({"path": rel, "kind": "legacy_json", "records": 0, "sha256": sha256_file(f), "bytes": os.path.getsize(f)})
            continue
        for i, raw in enumerate(data if isinstance(data, list) else []):
            if not isinstance(raw, dict):
                malformed.append({"file": rel, "line": i, "reason": "record is not an object"})
                n_bad += 1
                continue
            rows.append(make_row(raw, {
                "source_run": f"legacy_pull_{date}", "source_file": os.path.basename(f), "source_query": query,
                "source_query_role": cfg["legacy_query_to_role"].get(query) if query else None,
                "collection_timestamp": None, "collection_date": date, "collection_method": "legacy_free_text_relevance_sorted",
                "page": None, "position": i, "has_run_provenance": False}))
            n_ok += 1
        inventory.append({"path": rel, "kind": "legacy_json", "records": n_ok, "malformed": n_bad, "sha256": sha256_file(f),
                          "bytes": os.path.getsize(f), "query_from_filename_confirmed_by_pull_log": query is not None})

    for d in run_dirs:
        run = os.path.basename(d)
        man = json.load(open(os.path.join(d, "run_manifest.json"), encoding="utf-8"))
        window_starts.append(man.get("window_start"))
        qmeta = {}
        qp = os.path.join(d, "queries.jsonl")
        if os.path.exists(qp):
            for line in open(qp, encoding="utf-8"):
                if line.strip():
                    q = json.loads(line)
                    qmeta[q["records_file"]] = q
        for f in sorted(glob.glob(os.path.join(d, cfg["sources"]["run_records_glob"]))):
            rel = os.path.relpath(f, ROOT)
            q = qmeta.get(os.path.basename(f), {})
            params = q.get("request_params", {})
            method = "title_only_date_sorted" if params.get("title_only") and params.get("sort_by") == "date" else "unknown"
            n_ok = n_bad = 0
            for ln, line in enumerate(open(f, encoding="utf-8"), 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    raw, col = rec["raw"], rec["collection"]
                    assert isinstance(raw, dict)
                except (ValueError, KeyError, AssertionError) as e:
                    malformed.append({"file": rel, "line": ln, "reason": f"malformed record: {type(e).__name__}"})
                    n_bad += 1
                    continue
                ts = col.get("collected_at")
                collected_max = ts if ts and (collected_max is None or ts > collected_max) else collected_max
                rows.append(make_row(raw, {
                    "source_run": run, "source_file": os.path.basename(f), "source_query": col.get("query_variant"),
                    "source_query_role": col.get("query_role"), "collection_timestamp": ts,
                    "collection_date": ts[:10] if ts else None, "collection_method": method, "page": col.get("page"),
                    "position": col.get("position"), "has_run_provenance": True}))
                n_ok += 1
            inventory.append({"path": rel, "kind": "run_jsonl", "run": run, "records": n_ok, "malformed": n_bad,
                              "sha256": sha256_file(f), "bytes": os.path.getsize(f), "query": q.get("query"),
                              "api_count_logged_by_collector": q.get("api_count"), "collection_method": method})
    window_start = min(w for w in window_starts if w)[:10] + "T00:00:00Z" if any(window_starts) else None
    return rows, inventory, malformed, window_start, collected_max, {"legacy_files": len(legacy_files), "run_dirs": [os.path.basename(d) for d in run_dirs]}


# ── 2. exact-ID dedup ─────────────────────────────────────────────────

def id_dedup(rows):
    groups = defaultdict(list)
    no_id = []
    for r in rows:
        (groups[r["job_id"]] if r["job_id"] else no_id).append(r)
    kept, stats = [], Counter()
    conflicts = []
    for jid in sorted(groups, key=num_id):
        g = sorted(groups[jid], key=lambda r: (not r["has_run_provenance"], r["collection_timestamp"] or "9999", r["source_run"],
                                               r["source_file"], r["page"] or 0, r["position"] or 0))
        rep = dict(g[0])
        rep["id_dup_count"] = len(g)
        rep["also_seen_in"] = sorted({f"{x['source_run']}|{x['source_query']}" for x in g} - {f"{rep['source_run']}|{rep['source_query']}"})
        rep["query_roles_seen"] = sorted({x["source_query_role"] for x in g if x["source_query_role"]})
        if len(g) > 1:
            stats["ids_with_duplicates"] += 1
            runs_ = {x["source_run"] for x in g}
            stats["ids_seen_in_multiple_source_runs"] += len(runs_) > 1
            stats["ids_duplicated_within_one_source_run"] += len(runs_) < len(g)
            stats["ids_seen_in_legacy_and_run"] += any(not x["has_run_provenance"] for x in g) and any(x["has_run_provenance"] for x in g)
            diff = [k for k in ("title", "employer", "created", "description_raw") if len({x[k] for x in g}) > 1]
            sal = len({(x["salary_min"], x["salary_max"]) for x in g}) > 1
            if diff or sal:
                conflicts.append({"job_id": jid, "differing_fields": diff + (["salary"] if sal else [])})
        kept.append(rep)
    return kept, no_id, {"multiplicity": dict(sorted(Counter(min(x["id_dup_count"], 10) for x in kept).items())),
                         "conflicting_duplicates": len(conflicts), "conflict_examples": conflicts[:10], **stats}


# ── 3. near-duplicate detection ───────────────────────────────────────

def near_dedup(recs, n_chars):
    """Candidate groups: normalized title + employer + first `n_chars` normalized description characters (the project's defined key).
    A candidate is merged into a representative ONLY if the FULL normalized snippet is also identical. Evidence (see
    report/dataset_documentation.md): the 150-character key alone collapses templated postings (e.g. Accenture) whose required skills or
    years of experience differ after character 150, i.e. legitimate separate vacancies."""
    groups = defaultdict(list)
    for r in recs:
        t, e, d = norm_text(r["title"]), norm_text(r["employer"]), norm_text(r["description_raw"])[:n_chars]
        r["near_dup_key"] = hashlib.sha1(f"{t}|{e}|{d}".encode()).hexdigest()[:16] if (t and e and d) else None
        if r["near_dup_key"]:
            groups[r["near_dup_key"]].append(r)
    removed, dup_groups, cand_groups, would_remove_150, collisions = [], [], 0, 0, []
    for key in sorted(groups):
        g = groups[key]
        if len(g) == 1:
            continue
        cand_groups += 1
        would_remove_150 += len(g) - 1
        sub = defaultdict(list)
        for x in g:
            sub[norm_text(x["description_raw"])].append(x)
        if len(sub) > 1:
            collisions.append({"key": key, "title": g[0]["title"], "employer": g[0]["employer"], "candidate_size": len(g), "distinct_full_snippets": len(sub),
                               "job_ids": [x["job_id"] for x in g][:8],
                               "snippet_tails_after_150_chars": [x["description_raw"][150:260] for x in g[:3]]})
        for full in sorted(sub):
            m = sub[full]
            if len(m) == 1:
                continue
            m.sort(key=lambda r: (-(parse_iso(r["created"]).timestamp() if parse_iso(r["created"]) else 0), num_id(r["job_id"])))
            rep = m[0]
            rep["near_dup_group_size"] = len(m)
            rep["query_roles_seen"] = sorted(set(rep["query_roles_seen"]).union(*[x["query_roles_seen"] for x in m[1:]]))
            rep["also_seen_in"] = sorted(set(rep["also_seen_in"]).union(*[set(x["also_seen_in"]) | {f"{x['source_run']}|{x['source_query']}"} for x in m[1:]]))
            for x in m[1:]:
                removed.append({"job_id": x["job_id"], "kept_job_id": rep["job_id"], "title": x["title"], "employer": x["employer"],
                                "near_dup_key": key, "source_run": x["source_run"]})
            dup_groups.append({"key": key, "size": len(m), "title": rep["title"], "employer": rep["employer"], "job_ids": [x["job_id"] for x in m],
                               "distinct_location_labels": len({x["location_display"] for x in m}), "created_dates": sorted({(x["created"] or "")[:10] for x in m})})
    gone = {x["job_id"] for x in removed}
    survivors = [r for r in recs if r["job_id"] not in gone]
    for r in survivors:
        r.setdefault("near_dup_group_size", 1)
    dup_groups.sort(key=lambda g: (-g["size"], g["key"]))
    collisions.sort(key=lambda c: (-c["candidate_size"], c["key"]))
    n_aff = sum(g["size"] for g in dup_groups)
    return survivors, removed, {
        "candidate_key": "normalized title + normalized employer + first %d normalized description characters" % n_chars,
        "confirmation_rule": "merge only if the FULL normalized snippet is identical",
        "candidate_groups_by_150_char_key": cand_groups, "records_the_150_char_key_alone_would_remove": would_remove_150,
        "confirmed_duplicate_groups": len(dup_groups), "records_in_confirmed_groups": n_aff, "records_removed": len(removed),
        "records_kept_as_template_collisions": would_remove_150 - len(removed),
        "records_before": len(recs), "records_after": len(survivors),
        "percent_removed_of_id_deduped": round(100 * len(removed) / max(1, len(recs)), 2),
        "records_without_complete_key_not_checked": sum(1 for r in recs if not r["near_dup_key"]),
        "confirmed_groups_with_differing_location_labels": sum(1 for g in dup_groups if g["distinct_location_labels"] > 1),
        "confirmed_groups_spanning_multiple_created_dates": sum(1 for g in dup_groups if len(g["created_dates"]) > 1),
        "group_size_distribution": dict(sorted(Counter(g["size"] for g in dup_groups).items())),
        "examples_largest_confirmed_groups": dup_groups[:6],
        "examples_template_collisions_kept": collisions[:6],
        "note": "Differing location labels inside confirmed groups are mostly the same place written at different granularity (e.g. 'India' vs 'Vadodara, Gujarat'), so location is not used to block a merge.",
    }


# ── 4. role assignment (TITLE ONLY) ───────────────────────────────────

def build_rules(cfg):
    roles = copy.deepcopy(json.load(open(ROLES_PATH, encoding="utf-8"))["roles"])
    ov = cfg["role_rule_overrides"]
    for r in roles:
        if r["role"] in ov["replace"]:
            r.update(ov["replace"][r["role"]])
    roles += copy.deepcopy(ov["add"])
    return compile_rules(roles), {r["role"]: r for r in roles}


def scope_of(role, cfg):
    sc = cfg["scope"]
    for dom, rs in sc["core"].items():
        if role in rs:
            return "core", dom, role
    if role in sc["conditional"]:
        return "conditional", None, sc["conditional"][role]
    if role in sc["adjacent_not_core"]:
        return "adjacent_not_core", None, None
    if role in sc["excluded_domain_roles"]:
        return "excluded_domain", None, None
    return "unknown", None, None


def assign_roles(recs, cfg):
    rules, rulemap = build_rules(cfg)
    for r in recs:
        m = map_title(r["title"] or "", rules)
        r["mapping_status"], r["role"], r["mapping_candidates"] = m["status"], m["role"], m["candidates"]
        r["title_normalized"] = m["normalized_title"]
        r["mapping_tier"], r["matched_pattern_index"] = None, None
        if m["role"]:
            rc = rulemap[m["role"]]
            hits = [i for i, p in enumerate(rc["match"]) if re.search(p, m["normalized_title"])]
            r["matched_pattern_index"] = hits[0] if hits else None
            r["mapping_tier"] = "canonical" if hits and hits[0] == 0 else "synonym"
            r["role_scope"], r["domain"], r["role_group"] = scope_of(m["role"], cfg)
        else:
            r["role_scope"], r["domain"], r["role_group"] = None, None, None
    return rulemap


# ── 5. quality filtering ──────────────────────────────────────────────

def quality(recs, cfg, window_start, collected_max):
    q = cfg["quality"]
    ws = parse_iso(window_start) if window_start else None
    ref = parse_iso(collected_max) if collected_max else None
    if ref:
        ref = ref + timedelta(hours=q["future_tolerance_hours"])
    stats = Counter()
    for r in recs:
        c = parse_iso(r["created"])
        r["created_parsed_ok"] = c is not None
        r["created_date"] = c.strftime("%Y-%m-%d") if c else None
        desc = r["description_raw"] or ""
        r["description_normalized"] = norm_description(desc)
        r["description_length"] = len(desc)
        r["description_is_truncated"] = desc.rstrip().endswith("…")
        r["description_short_flag"] = 0 < len(desc) < q["short_description_chars"]
        letters = [ch for ch in ((r["title"] or "") + desc) if ch.isalpha()]
        r["language_flag"] = "non_english_suspected" if letters and sum(1 for ch in letters if ord(ch) > 127) / len(letters) > q["non_english_ratio_threshold"] else "english_or_ascii"
        r["title_missing"] = not (r["title"] or "").strip()
        r["employer_missing"] = not (r["employer"] or "").strip()
        r["employer_normalized"] = norm_text(r["employer"])
        area = r["location_area"]
        r["location_country"] = area[0] if area else None
        r["location_region"] = area[1] if len(area) > 1 else None
        r["location_has_region"] = len(area) > 1
        # salary: numeric plausibility screen only; the API gives no currency or period, so the period interpretation is UNRESOLVED
        lo, hi = r["salary_min"], r["salary_max"]
        pres = lo is not None or hi is not None
        a, b = (lo if lo is not None else hi), (hi if hi is not None else lo)
        flags = []
        if pres:
            if r["salary_is_predicted"] == "1":
                flags.append("adzuna_predicted")
            if a is not None and b is not None and lo is not None and hi is not None and lo > hi:
                flags.append("min_gt_max")
            if a is not None and a <= 0:
                flags.append("non_positive")
            elif a is not None and a < q["salary"]["floor"]:
                flags.append("below_floor")
            if b is not None and b > q["salary"]["ceiling"]:
                flags.append("above_ceiling")
            if lo is not None and hi is not None and lo == hi:
                flags.append("point_value")  # informational, not invalid
            if (lo is None) != (hi is None):
                flags.append("one_sided")  # informational
        r["salary_present"] = pres
        r["salary_flags"] = flags
        bad = {"adzuna_predicted", "min_gt_max", "non_positive", "below_floor", "above_ceiling"}
        r["salary_passes_plausibility_screen"] = bool(pres and not (set(flags) & bad))
        # exclusion reasons in order
        reason = None
        if not r["job_id"] or r["title_missing"]:
            reason = "missing_identity"
        elif not desc.strip():
            reason = "empty_description"
        elif c is None:
            reason = "unparseable_created"
        elif ref and c > ref:
            reason = "future_created"
        elif ws and c < ws:
            reason = "outside_90_day_window"
        r["quality_exclusion"] = reason
        stats[reason or "pass"] += 1
    return stats


def employer_cap_flag(final, frac):
    by_role = defaultdict(list)
    for r in final:
        by_role[r["role"]].append(r)
    for role, rs in by_role.items():
        cap = max(1, math.floor(frac * len(rs)))
        by_emp = defaultdict(list)
        for r in rs:
            if r["employer_normalized"]:
                by_emp[r["employer_normalized"]].append(r)
        drop = set()
        for emp, g in by_emp.items():
            if len(g) > cap:
                g.sort(key=lambda r: (r["created"] or "", -num_id(r["job_id"])), reverse=True)
                drop |= {x["job_id"] for x in g[cap:]}
        for r in rs:
            r["employer_cap_5pct_retained"] = r["job_id"] not in drop
        by_role[role] = cap
    return dict(by_role)


# ── metrics helpers ───────────────────────────────────────────────────

def concentration(employers, n_rows_total):
    emp = Counter(e for e in employers if e)
    n = sum(emp.values())
    if not n:
        return {"rows": n_rows_total, "rows_with_employer": 0, "unique_employers": 0, "top_employer_count": 0, "top_employer_percentage": None, "effective_number_of_employers": None}
    top, cnt = emp.most_common(1)[0]
    return {"rows": n_rows_total, "rows_with_employer": n, "unique_employers": len(emp), "top_employer_count": cnt,
            "top_employer_percentage": round(100 * cnt / n, 2), "effective_number_of_employers": round(1 / sum((v / n) ** 2 for v in emp.values()), 1)}


def quantiles(v):
    if not v:
        return {}
    v = sorted(v)
    at = lambda q: v[min(len(v) - 1, int(q * len(v)))]
    return {"n": len(v), "min": v[0], "p5": at(.05), "p25": at(.25), "median": at(.5), "p75": at(.75), "p95": at(.95), "max": v[-1]}


FIELD_SPEC = [  # name, origin, description
    ("job_id", "SOURCE", "Adzuna job id (raw `id`), string"),
    ("role", "DERIVED", "Role label from TITLE-ONLY rules (config/roles.json + overrides in config/dataset_build.json)"),
    ("role_scope", "DERIVED", "core | conditional | adjacent_not_core"),
    ("domain", "DERIVED", "Domain for core roles only"),
    ("role_group", "DERIVED", "Core: role name; conditional security families: 'Security (conditional family)'; UX/Financial Analyst: own name"),
    ("mapping_tier", "DERIVED", "canonical = first (canonical) title pattern matched; synonym = another documented variant"),
    ("title", "SOURCE", "Original title, unchanged"),
    ("employer", "SOURCE", "raw company.display_name (may be missing)"),
    ("employer_normalized", "DERIVED", "Lowercase alphanumeric normalisation used for grouping"),
    ("employer_missing", "DERIVED", "True when company.display_name is absent"),
    ("description_raw", "SOURCE", "Adzuna description SNIPPET (about 500 characters), unchanged"),
    ("description_length", "DERIVED", "Character count of description_raw"),
    ("description_is_truncated", "DERIVED", "description_raw ends with the ellipsis character"),
    ("description_short_flag", "DERIVED", "0 < length < 200"),
    ("language_flag", "DERIVED", "non_english_suspected if >30% of alphabetic characters in title+description are non-ASCII (flag only)"),
    ("location_display", "SOURCE", "raw location.display_name"),
    ("location_area", "SOURCE", "raw location.area (list, country first)"),
    ("location_country", "DERIVED", "First element of location_area"),
    ("location_region", "DERIVED", "Second element of location_area, when present"),
    ("location_has_region", "DERIVED", "location_area has at least two levels"),
    ("latitude", "SOURCE", "raw latitude (about half of postings)"),
    ("longitude", "SOURCE", "raw longitude"),
    ("created", "SOURCE", "raw created timestamp (UTC string)"),
    ("created_date", "DERIVED", "Date part of created"),
    ("category_label", "SOURCE", "raw category.label (Adzuna's own category; not a domain label)"),
    ("category_tag", "SOURCE", "raw category.tag"),
    ("contract_type", "SOURCE", "raw contract_type (sparse)"),
    ("contract_time", "SOURCE", "raw contract_time"),
    ("salary_min", "SOURCE", "raw salary_min; currency and period are NOT provided by the API (interpretation unresolved)"),
    ("salary_max", "SOURCE", "raw salary_max"),
    ("salary_is_predicted", "SOURCE", "raw salary_is_predicted ('0'/'1')"),
    ("salary_present", "DERIVED", "salary_min or salary_max present"),
    ("salary_flags", "DERIVED", "JSON list: adzuna_predicted, min_gt_max, non_positive, below_floor, above_ceiling (invalid); point_value, one_sided (informational)"),
    ("salary_passes_plausibility_screen", "DERIVED", "Present, not Adzuna-predicted, min <= max, and within a numeric range of 100,000 to 10,000,000. This is a NUMERIC SCREEN ONLY: the API provides no currency or pay-period field and the period interpretation is UNRESOLVED"),
    ("source_run", "PROVENANCE", "Run directory name, or legacy_pull_<date>"),
    ("source_file", "PROVENANCE", "Raw file the kept record came from"),
    ("source_query", "PROVENANCE", "Query text (title_only variant for runs; category name from filename for legacy, confirmed by pull log)"),
    ("source_query_role", "PROVENANCE", "Config role that requested the posting. NOT the role label"),
    ("collection_timestamp", "PROVENANCE", "Page fetch time (runs only; null for legacy)"),
    ("collection_date", "PROVENANCE", "Date of collection"),
    ("collection_method", "PROVENANCE", "title_only_date_sorted (audited runs) or legacy_free_text_relevance_sorted"),
    ("query_roles_seen", "DERIVED", "JSON list of every query role that retrieved this posting (after dedup merge)"),
    ("also_seen_in", "DERIVED", "JSON list of other 'run|query' sources that returned the same or a near-duplicate posting"),
    ("id_dup_count", "DERIVED", "Number of raw records with this job id"),
    ("near_dup_group_size", "DERIVED", "Number of identical-snippet duplicates merged into this posting (1 = none)"),
    ("near_dup_key", "DERIVED", "Candidate-group hash of normalized title + employer + first 150 description chars (null if any part missing); merging additionally required an identical full snippet"),
    ("employer_cap_5pct_retained", "DERIVED", "Would this row survive the design's 5%-per-employer cap within its role? FLAG ONLY; nothing was removed"),
]
COLUMNS = [f[0] for f in FIELD_SPEC]
LIST_COLS = {"location_area", "salary_flags", "query_roles_seen", "also_seen_in"}


def frame(final):
    df = pd.DataFrame([{c: (r.get(c)) for c in COLUMNS} for r in final], columns=COLUMNS)
    for c in LIST_COLS:
        df[c] = df[c].apply(lambda v: list(v) if isinstance(v, (list, tuple)) else [])
    return df


def csv_bytes(df):
    d = df.copy()
    for c in LIST_COLS:
        d[c] = d[c].apply(jdump)
    return d.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")


# ── main pipeline ─────────────────────────────────────────────────────

def run(out_root, verbose=True):
    cfg = json.load(open(CFG_PATH, encoding="utf-8"))
    raw_root = os.path.join(ROOT, cfg["sources"]["raw_root"])
    proc_dir = os.path.join(out_root, "data", "processed", "adzuna")
    aud_dir = os.path.join(out_root, "data", "audits", "dataset")
    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(aud_dir, exist_ok=True)
    log = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    tg = cfg["targets"]

    # 1. read (read-only)
    rows, inventory, malformed, window_start, collected_max, src_info = read_all(raw_root, cfg)
    hashes_before = {i["path"]: i["sha256"] for i in inventory}
    n_raw = len(rows)
    log(f"[1] raw records: {n_raw} from {len(inventory)} files (malformed {len(malformed)}); window_start {window_start}")
    raw_by_qrole = Counter(r["source_query_role"] for r in rows if r["source_query_role"])
    ids_by_source = defaultdict(set)
    for r in rows:
        if r["job_id"]:
            ids_by_source[r["source_run"]].add(r["job_id"])
    src_names = sorted(ids_by_source)
    overlap = {f"{a} & {b}": len(ids_by_source[a] & ids_by_source[b]) for i, a in enumerate(src_names) for b in src_names[i + 1:]}
    legacy_ids = set().union(*[v for k, v in ids_by_source.items() if k.startswith("legacy_pull_")]) if any(k.startswith("legacy_pull_") for k in src_names) else set()
    run_ids = set().union(*[v for k, v in ids_by_source.items() if not k.startswith("legacy_pull_")]) if any(not k.startswith("legacy_pull_") for k in src_names) else set()

    # 2. exact-ID dedup
    recs, no_id, id_stats = id_dedup(rows)
    id_report = {"records_before_id_dedup": n_raw, "unique_job_ids": len(recs), "duplicate_job_id_count": n_raw - len(no_id) - len(recs),
                 "records_after_id_dedup": len(recs), "records_without_job_id": len(no_id),
                 "representative_rule": cfg["dedup"]["representative_for_same_id"], **id_stats}
    ids_by_qrole = Counter(qr for r in recs for qr in r["query_roles_seen"])
    log(f"[2] ID dedup: {n_raw} -> {len(recs)} ({id_report['duplicate_job_id_count']} duplicates)")

    # 3. near-duplicates
    survivors, near_removed, near_report = near_dedup(recs, cfg["dedup"]["near_duplicate_description_chars"])
    surv_by_qrole = Counter(qr for r in survivors for qr in r["query_roles_seen"])
    log(f"[3] near-dup: {len(recs)} -> {len(survivors)} ({len(near_removed)} removed, {near_report['confirmed_duplicate_groups']} groups)")

    # 4. title-only role assignment, 5. quality rules
    assign_roles(survivors, cfg)
    qstats = quality(survivors, cfg, window_start, collected_max)
    excluded, final = [], []
    for r in sorted(survivors, key=lambda r: num_id(r["job_id"])):
        if r["role"] is None:
            excluded.append((r, "role_assignment", r["mapping_status"]))
        elif r["role_scope"] not in ("core", "conditional", "adjacent_not_core"):
            excluded.append((r, "role_assignment", f"{r['role_scope']}:{r['role']}"))
        elif r["quality_exclusion"]:
            excluded.append((r, "quality_filter", r["quality_exclusion"]))
        else:
            final.append(r)
    excluded += [(r, "id_dedup", "missing_job_id") for r in no_id]  # never dropped silently
    scope_order = {"core": 0, "conditional": 1, "adjacent_not_core": 2}
    final.sort(key=lambda r: (scope_order[r["role_scope"]], r["role"], num_id(r["job_id"])))
    caps = employer_cap_flag(final, cfg["dedup"]["employer_cap_fraction_flag_only"])
    log(f"[4-5] role assignment + quality filter: {len(survivors)} -> {len(final)} final")

    # ── dataset files ────────────────────────────────────────────────
    df = frame(final)
    cbytes = csv_bytes(df)
    content_sha = hashlib.sha256(cbytes).hexdigest()
    df.to_parquet(os.path.join(proc_dir, "career_market_dataset.parquet"), engine="pyarrow", index=False, compression="zstd")
    open(os.path.join(proc_dir, "career_market_dataset.csv"), "wb").write(cbytes)

    # ── audit: source inventory ──────────────────────────────────────
    write = lambda d, n, o: json.dump(o, open(os.path.join(d, n), "w", encoding="utf-8"), indent=1, sort_keys=True, ensure_ascii=False)
    key_counts = Counter()
    for r in rows:
        for k in ("job_id", "title", "employer", "description_raw", "location_display", "created", "category_label", "salary_min", "salary_max", "latitude", "contract_type", "contract_time"):
            key_counts[k] += r[k] not in (None, "")
    write(aud_dir, "source_inventory.json", {
        "raw_root": cfg["sources"]["raw_root"], "source_files": inventory, "file_counts": src_info,
        "raw_records_total": n_raw, "malformed_records": malformed, "malformed_count": len(malformed),
        "records_per_source_run": {k: sum(1 for r in rows if r["source_run"] == k) for k in src_names},
        "unique_ids_per_source_run": {k: len(v) for k, v in ids_by_source.items()},
        "pairwise_id_overlap_between_source_runs": overlap,
        "legacy_unique_ids": len(legacy_ids), "run_unique_ids": len(run_ids), "ids_in_both_legacy_and_runs": len(legacy_ids & run_ids),
        "field_presence_across_all_raw_records": {k: {"present": v, "pct": round(100 * v / n_raw, 1)} for k, v in sorted(key_counts.items())},
        "non_record_files_not_read": cfg["sources"]["non_record_files_ignored"],
        "window_start_from_run_manifests": window_start, "latest_collection_timestamp": collected_max,
        "schema_note": "Legacy files are JSON arrays of raw records without collection metadata; run files are JSONL {collection, raw}. `raw` schemas are identical field-for-field."})
    write(aud_dir, "dedup_report.json", {"exact_id": id_report, "near_duplicate": near_report,
                                         "removed_near_duplicates_file": "near_duplicate_removals.csv (see audits folder)"})
    pd.DataFrame(near_removed, columns=["job_id", "kept_job_id", "title", "employer", "near_dup_key", "source_run"]).sort_values("job_id", key=lambda s: s.map(num_id)).to_csv(
        os.path.join(aud_dir, "near_duplicate_removals.csv"), index=False, lineterminator="\n")
    pd.DataFrame([{"job_id": r["job_id"], "title": r["title"], "employer": r["employer"], "stage": st, "reason": rs,
                   "source_run": r["source_run"], "created": r["created"]} for r, st, rs in excluded]).to_csv(
        os.path.join(aud_dir, "excluded_records.csv"), index=False, lineterminator="\n")

    # ── role funnel / mapping report / sample-size audit ─────────────
    all_roles = (sorted({r for rs in cfg["scope"]["core"].values() for r in rs}, key=lambda x: x)
                 + list(cfg["scope"]["conditional"]) + cfg["scope"]["adjacent_not_core"] + cfg["scope"]["excluded_domain_roles"])
    core_roles = [r for rs in cfg["scope"]["core"].values() for r in rs]
    all_roles = core_roles + list(cfg["scope"]["conditional"]) + cfg["scope"]["adjacent_not_core"] + cfg["scope"]["excluded_domain_roles"]
    fin_by_role = defaultdict(list)
    for r in final:
        fin_by_role[r["role"]].append(r)
    surv_mapped = Counter(r["role"] for r in survivors if r["role"])
    q_excl_by_role = defaultdict(Counter)
    for r in survivors:
        if r["role"] and r["role_scope"] in ("core", "conditional", "adjacent_not_core") and r["quality_exclusion"]:
            q_excl_by_role[r["role"]][r["quality_exclusion"]] += 1
    role_report, sample_audit = {}, {}
    for role in all_roles:
        own = [r for r in survivors if role in r["query_roles_seen"]]
        st = Counter(("mapped_to_this_role" if r["role"] == role else "mapped_to_other_role" if r["role"] else r["mapping_status"]) for r in own)
        scope = scope_of(role, cfg)[0]
        fr = fin_by_role.get(role, [])
        emp_rows = [r["employer_normalized"] for r in fr]
        conc = concentration(emp_rows, len(fr))
        capped = [r for r in fr if r["employer_cap_5pct_retained"]]
        conc_cap = concentration([r["employer_normalized"] for r in capped], len(capped))
        canon = sum(1 for r in fr if r["mapping_tier"] == "canonical")
        role_report[role] = {
            "scope": scope, "raw_candidates_retrieved_by_role_queries": raw_by_qrole.get(role),
            "unique_candidates_after_id_dedup": ids_by_qrole.get(role), "candidates_after_near_dedup": len(own) if own else None,
            "mapped_count": st["mapped_to_this_role"] if own else None,
            "mapping_percentage": round(100 * st["mapped_to_this_role"] / len(own), 1) if own else None,
            "ambiguous_count": st["ambiguous_multi"] if own else None, "excluded_count": st["excluded_by_rule"] if own else None,
            "unmatched_count": st["unmatched"] if own else None, "mapped_to_other_role_count": st["mapped_to_other_role"] if own else None,
            "title_mapped_any_query": surv_mapped.get(role, 0),
        }
        if scope in ("core", "conditional", "adjacent_not_core"):
            fun = {"raw_count": raw_by_qrole.get(role), "after_id_dedup": ids_by_qrole.get(role), "after_near_dedup": len(own) if own else None,
                   "after_title_mapping_any_query": surv_mapped.get(role, 0), "quality_excluded": dict(q_excl_by_role[role]),
                   "after_quality_filtering_final_candidate_count": len(fr), "canonical_title_count": canon,
                   "unique_employers": conc["unique_employers"], "missing_employer_rows": len(fr) - conc["rows_with_employer"],
                   "employer_concentration_uncapped": conc, "employer_concentration_5pct_cap_view": conc_cap,
                   "employer_cap_rows_flagged_over_cap": len(fr) - len(capped), "employer_cap_n_per_employer": caps.get(role)}
            if scope == "core":
                chk = {"clean_ge_400": len(fr) >= tg["clean_per_core_role"], "canonical_ge_300": canon >= tg["canonical_per_core_role"],
                       "employers_ge_100": conc["unique_employers"] >= tg["distinct_employers_per_role"],
                       "top_employer_le_6pct_uncapped": (conc["top_employer_percentage"] or 100) <= tg["top_employer_pct_max"],
                       "top_employer_le_6pct_capped_view": (conc_cap["top_employer_percentage"] or 100) <= tg["top_employer_pct_max"],
                       "effective_employers_ge_50_uncapped": (conc["effective_number_of_employers"] or 0) >= tg["effective_employers_min"]}
                cap_canon = sum(1 for r in capped if r["mapping_tier"] == "canonical")
                chk.update({"clean_ge_400_capped_view": len(capped) >= tg["clean_per_core_role"], "canonical_ge_300_capped_view": cap_canon >= tg["canonical_per_core_role"],
                            "employers_ge_100_capped_view": conc_cap["unique_employers"] >= tg["distinct_employers_per_role"],
                            "effective_employers_ge_50_capped_view": (conc_cap["effective_number_of_employers"] or 0) >= tg["effective_employers_min"]})
                chk["all_targets_met_capped_view"] = all(chk[k] for k in ("clean_ge_400_capped_view", "canonical_ge_300_capped_view", "employers_ge_100_capped_view", "top_employer_le_6pct_capped_view", "effective_employers_ge_50_capped_view"))
                chk["all_targets_met_uncapped"] = all(chk[k] for k in ("clean_ge_400", "canonical_ge_300", "employers_ge_100", "top_employer_le_6pct_uncapped", "effective_employers_ge_50_uncapped"))
                fun["target_checks"] = chk
            sample_audit[role] = fun
    sec_roles = [r for r, g in cfg["scope"]["conditional"].items() if g == "Security (conditional family)"]
    sec_final = [r for r in final if r["role"] in sec_roles]
    sample_audit["Security (conditional family, merged view)"] = {
        "after_quality_filtering_final_candidate_count": len(sec_final),
        "unique_employers": len({r["employer_normalized"] for r in sec_final if r["employer_normalized"]}),
        "members": {r: len(fin_by_role.get(r, [])) for r in sec_roles},
        "note": "Merging the five families is a team decision; they are stored as separate role values."}
    write(aud_dir, "role_mapping_report.json", {
        "mapping_rules": "config/roles.json + overrides in config/dataset_build.json (TITLE ONLY: description, skills, salary, category, employer, query are never used)",
        "project_manager_decision": cfg["role_rule_overrides"]["_decision"], "per_role": role_report,
        "unmatched_or_ambiguous_survivors": dict(Counter(r["mapping_status"] for r in survivors if not r["role"])),
        "excluded_domain_records": dict(Counter(r["role"] for r in survivors if r["role_scope"] == "excluded_domain")),
        "manual_precision_note": "Manual precision is measured separately (data/audits/dataset/mapping_spotcheck/); this file reports mapping coverage only."})
    write(aud_dir, "sample_size_audit.json", {"targets": tg, "per_role": sample_audit,
        "stage_definitions": {"raw_count": "raw rows returned by the role's own queries (before any dedup)", "after_id_dedup": "unique job ids among them",
        "after_near_dedup": "records surviving near-duplicate removal that the role's queries retrieved", "after_title_mapping_any_query": "surviving records whose TITLE maps to the role, whichever query retrieved them",
        "after_quality_filtering_final_candidate_count": "final dataset rows with role = this role (may include rows retrieved by other roles' queries)"}})

    # ── employer concentration report ────────────────────────────────
    core_fin = [r for r in final if r["role_scope"] == "core"]
    write(aud_dir, "employer_concentration_report.json", {
        "targets": {"top_employer_pct_max": tg["top_employer_pct_max"], "effective_employers_min": tg["effective_employers_min"], "distinct_employers_min": tg["distinct_employers_per_role"]},
        "employer_cap_status": "The 5%-per-employer cap is part of the collection design but was NEVER applied to raw data; earlier analysis applied it only when computing clean counts. The FULL validated dataset does NOT remove rows for it (`employer_cap_5pct_retained` flags them); scripts/finalize_dataset.py applies the cap deterministically to build the final core analysis dataset. These are the UNCAPPED statistics.",
        "per_role": {r: {"uncapped": sample_audit[r]["employer_concentration_uncapped"], "capped_view": sample_audit[r]["employer_concentration_5pct_cap_view"],
                        "top_employers_uncapped": Counter(x["employer"] for x in fin_by_role.get(r, []) if x["employer"]).most_common(5)} for r in sample_audit if r in fin_by_role},
        "core_overall": concentration([r["employer_normalized"] for r in core_fin], len(core_fin)),
        "employers_with_more_than_10_core_postings": sum(1 for v in Counter(r["employer_normalized"] for r in core_fin if r["employer_normalized"]).values() if v > 10),
        "rows_missing_employer_core": sum(1 for r in core_fin if r["employer_missing"])})

    # ── salary quality ───────────────────────────────────────────────
    def sal_block(rs):
        pres = [r for r in rs if r["salary_present"]]
        val = [r for r in pres if r["salary_passes_plausibility_screen"]]
        mid = lambda r: ((r["salary_min"] if r["salary_min"] is not None else r["salary_max"]) + (r["salary_max"] if r["salary_max"] is not None else r["salary_min"])) / 2
        fl = Counter(f for r in pres for f in r["salary_flags"])
        txt = [(r["description_raw"] or "").lower() for r in pres]
        cnt = lambda pat: sum(1 for t in txt if re.search(pat, t))
        return {"rows": len(rs), "salary_present": len(pres), "salary_missing": len(rs) - len(pres), "salary_present_pct": round(100 * len(pres) / max(1, len(rs)), 1),
                "salary_min_present": sum(1 for r in rs if r["salary_min"] is not None), "salary_max_present": sum(1 for r in rs if r["salary_max"] is not None),
                "both_present": sum(1 for r in rs if r["salary_min"] is not None and r["salary_max"] is not None),
                "salary_predicted": sum(1 for r in rs if r["salary_is_predicted"] == "1"),
                "salary_valid_under_working_screen": len(val), "salary_invalid": len(pres) - len(val),
                "invalid_reason_counts": {k: v for k, v in sorted(fl.items()) if k in ("adzuna_predicted", "min_gt_max", "non_positive", "below_floor", "above_ceiling")},
                "informational_counts": {k: v for k, v in sorted(fl.items()) if k in ("point_value", "one_sided")},
                "valid_midpoint_distribution": quantiles([mid(r) for r in val]),
                "snippet_period_or_currency_mentions_among_salaried": {"per_month": cnt(r"per month|monthly|/month|per annum|p\.a\.|per year|annual"), "monthly_only": cnt(r"per month|monthly|/month"),
                    "lpa_or_lakh": cnt(r"\blpa\b|lakh|lacs?\b"), "hourly": cnt(r"per hour|hourly|/hour"), "usd_or_dollar": cnt(r"\$|usd\b"), "inr_or_rupee": cnt(r"inr\b|rs\.?\s?\d|₹")}}
    write(aud_dir, "salary_quality_report.json", {
        "assumption": cfg["quality"]["salary"]["assumption"], "floor": cfg["quality"]["salary"]["floor"], "ceiling": cfg["quality"]["salary"]["ceiling"],
        "currency_field_in_source": False, "period_field_in_source": False,
        "overall_final": sal_block(final), "core_only": sal_block(core_fin), "by_role": {r: sal_block(fin_by_role[r]) for r in all_roles if r in fin_by_role},
        "locations_of_salaried_core": dict(Counter(r["location_country"] for r in core_fin if r["salary_present"])),
        "comparison_with_earlier_feasibility_figures": {"earlier_core_with_salary": 611, "earlier_core_valid": 532,
            "note": "Earlier figures were computed on the employer-capped audit set; this build is uncapped and de-duplicated across all runs"},
        "not_done": "No salary bands, no model, no currency or period normalisation was applied."})

    # ── quality report ───────────────────────────────────────────────
    def miss(rs):
        out = {}
        for c in COLUMNS:
            n = sum(1 for r in rs if r.get(c) in (None, "", []))
            out[c] = {"missing": n, "pct": round(100 * n / max(1, len(rs)), 1)}
        return out
    created = [parse_iso(r["created"]) for r in survivors]
    ws_dt, ref_dt = (parse_iso(window_start) if window_start else None), (parse_iso(collected_max) if collected_max else None)
    ref_tol = ref_dt + timedelta(hours=cfg["quality"]["future_tolerance_hours"]) if ref_dt else None
    dates_final = Counter(r["created_date"] for r in final)
    lens = [r["description_length"] for r in final]
    areas = Counter(r["location_country"] for r in final)
    chk = {
        "no_network_calls_in_pipeline": True,
        "raw_files_unchanged": None,
        "no_records_silently_dropped": (n_raw == len(final) + len(excluded) + len(near_removed) + id_report["duplicate_job_id_count"] + len(no_id)),
        "all_final_rows_have_job_id_and_title": all(r["job_id"] and not r["title_missing"] for r in final),
        "all_final_roles_in_scope": all(r["role_scope"] in ("core", "conditional", "adjacent_not_core") for r in final),
        "no_excluded_domain_roles_in_final": not any(r["role_scope"] == "excluded_domain" for r in final),
        "job_ids_unique": len({r["job_id"] for r in final}) == len(final),
        "created_all_within_window": all(parse_iso(r["created"]) >= ws_dt for r in final) if ws_dt else None,
        "no_future_created_beyond_tz_tolerance": all(parse_iso(r["created"]) <= ref_tol for r in final) if ref_tol else None,
        "no_empty_descriptions": all(r["description_length"] > 0 for r in final),
        "core_targets_all_met": all(sample_audit[r]["target_checks"]["all_targets_met_uncapped"] for r in core_roles),
        "core_roles_failing_targets": [r for r in core_roles if not sample_audit[r]["target_checks"]["all_targets_met_uncapped"]],
        "core_roles_failing_targets_capped_view": [r for r in core_roles if not sample_audit[r]["target_checks"]["all_targets_met_capped_view"]],
    }
    write(proc_dir, "quality_report.json", {
        "pipeline_counts": {"raw_records": n_raw, "after_id_dedup": len(recs), "after_near_dedup": len(survivors), "excluded_at_role_assignment": sum(1 for _, st, _ in excluded if st == "role_assignment"),
                            "excluded_at_quality_filter": sum(1 for _, st, _ in excluded if st == "quality_filter"), "final": len(final)},
        "exclusion_reasons": dict(sorted(Counter(f"{st}:{rs.split(':')[0]}" for _, st, rs in excluded).items())),
        "quality_filter_reason_counts_all_survivors": dict(qstats),
        "date_checks": {"survivors_checked": len(survivors), "parse_failures": sum(1 for c in created if c is None), "impossible_dates_before_2000_or_after_2100": sum(1 for c in created if c and (c.year < 2000 or c.year > 2100)),
                        "created_after_latest_collection_time_within_tz_tolerance": sum(1 for c in created if c and ref_dt and ref_dt < c <= ref_tol), "future_dates_beyond_tolerance": sum(1 for c in created if c and ref_tol and c > ref_tol), "outside_90_day_window": sum(1 for c in created if c and ws_dt and c < ws_dt),
                        "earliest_created_survivor": min((r["created"] for r in survivors if r["created"]), default=None),
                        "latest_created_minus_latest_collection_hours": round((max(c for c in created if c) - parse_iso(collected_max)).total_seconds() / 3600, 2) if collected_max else None, "created_timezone_note": cfg["quality"]["future_tolerance_note"], "final_earliest": min(r["created"] for r in final), "final_latest": max(r["created"] for r in final),
                        "final_distinct_created_dates": len(dates_final), "final_dates_with_more_than_one_posting": sum(1 for v in dates_final.values() if v > 1),
                        "final_max_postings_on_one_date": max(dates_final.values()), "window_start": window_start, "latest_collection_timestamp": collected_max},
        "location_checks": {"final_location_country_counts": dict(areas), "rows_without_location_display": sum(1 for r in final if not r["location_display"]),
                            "rows_with_empty_area": sum(1 for r in final if not r["location_area"]), "rows_with_region_level": sum(1 for r in final if r["location_has_region"]),
                            "rows_with_lat_long": sum(1 for r in final if r["latitude"] is not None), "non_india_country_rows": sum(1 for r in final if r["location_country"] not in (None, "India"))},
        "description_checks": {"final_length_distribution": quantiles(lens), "empty": sum(1 for l in lens if l == 0), "short_lt_200": sum(1 for r in final if r["description_short_flag"]),
                               "truncated_with_ellipsis": sum(1 for r in final if r["description_is_truncated"]), "truncated_pct": round(100 * sum(1 for r in final if r["description_is_truncated"]) / len(final), 1),
                               "non_english_suspected": sum(1 for r in final if r["language_flag"] == "non_english_suspected"),
                               "limitation": "Adzuna returns only a ~500-character snippet; any later skill frequency is a lower bound."},
        "employer_checks": {"missing_employer_rows": sum(1 for r in final if r["employer_missing"]), "unique_employers_final": len({r["employer_normalized"] for r in final if r["employer_normalized"]})},
        "missing_values_final": miss(final), "checks": chk})
    write(proc_dir, "schema.json", {"dataset": "career_market_dataset", "version": cfg["dataset_version"], "rows": len(final),
        "fields": [{"name": n, "origin": o, "description": d, "dtype": str(df[n].dtype), "missing_pct": round(100 * sum(1 for r in final if r.get(n) in (None, "", [])) / max(1, len(final)), 1)} for n, o, d in FIELD_SPEC],
        "origin_legend": {"SOURCE": "copied unchanged from the Adzuna raw record", "DERIVED": "computed deterministically by scripts/build_dataset.py", "PROVENANCE": "collector metadata attached at collection time (or derived from file names for the legacy pull)"},
        "fields_deliberately_not_carried": {"redirect_url": "embeds the API app id and tracking tokens; join back to raw by job_id if needed", "adref": "tracking token", "__CLASS__": "API internal"}})

    # ── raw immutability check ───────────────────────────────────────
    after = {os.path.relpath(f, ROOT): sha256_file(f) for f in [os.path.join(ROOT, i["path"]) for i in inventory]}
    unchanged = after == hashes_before
    chk["raw_files_unchanged"] = unchanged
    role_counts = {r: len(v) for r, v in sorted(fin_by_role.items())}
    manifest = {
        "dataset_version": cfg["dataset_version"], "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": "scripts/build_dataset.py", "python": platform.python_version(), "pandas": pd.__version__,
        "config_sha256": {"dataset_build.json": sha256_file(CFG_PATH), "roles.json": sha256_file(ROLES_PATH)},
        "source_runs": src_names, "source_file_count": len(inventory), "raw_record_count": n_raw, "malformed_records": len(malformed),
        "id_deduplicated_count": len(recs), "near_deduplicated_count": len(survivors),
        "mapped_count": sum(1 for r in survivors if r["role"] and r["role_scope"] in ("core", "conditional", "adjacent_not_core")),
        "excluded_count": len(excluded), "excluded_by_stage": dict(Counter(st for _, st, _ in excluded)), "final_count": len(final),
        "role_counts": role_counts, "core_total": len(core_fin),
        "unique_employers": len({r["employer_normalized"] for r in final if r["employer_normalized"]}),
        "salary_availability": {"present": sum(1 for r in final if r["salary_present"]), "valid_under_working_screen_period_unresolved": sum(1 for r in final if r["salary_passes_plausibility_screen"]),
                                "predicted": sum(1 for r in final if r["salary_is_predicted"] == "1"), "core_present": sum(1 for r in core_fin if r["salary_present"]),
                                "core_valid": sum(1 for r in core_fin if r["salary_passes_plausibility_screen"])},
        "quality_check_status": {"all_structural_checks_passed": all(v for k, v in chk.items() if k in ("no_network_calls_in_pipeline", "raw_files_unchanged", "no_records_silently_dropped", "all_final_rows_have_job_id_and_title", "all_final_roles_in_scope", "no_excluded_domain_roles_in_final", "job_ids_unique", "created_all_within_window", "no_future_created_beyond_tz_tolerance", "no_empty_descriptions")),
                                 "core_targets_all_met": chk["core_targets_all_met"], "core_roles_failing_targets": chk["core_roles_failing_targets"], "core_roles_failing_targets_capped_view": chk["core_roles_failing_targets_capped_view"], "overall": "PASS" if chk["core_targets_all_met"] else "CONDITIONAL"},
        "raw_files_unchanged_verified_by_sha256": unchanged, "raw_source_files": [{"path": i["path"], "records": i["records"], "bytes": i["bytes"], "sha256": i["sha256"]} for i in inventory],
        "dataset_content_sha256": content_sha, "output_files": {"parquet": "data/processed/adzuna/career_market_dataset.parquet", "csv": "data/processed/adzuna/career_market_dataset.csv (about 14 MB duplicate kept for human inspection; parquet, about 2.8 MB, is the primary)"},
        "reproducibility_check": "not yet run (python scripts/build_dataset.py --check-reproducible)",
    }
    qp = os.path.join(proc_dir, "quality_report.json")
    qr = json.load(open(qp, encoding="utf-8"))
    qr["checks"]["raw_files_unchanged"] = unchanged
    write(proc_dir, "quality_report.json", qr)
    write(proc_dir, "dataset_manifest.json", manifest)
    log(f"[done] final {len(final)} rows; core {len(core_fin)}; content sha256 {content_sha[:16]}...; raw unchanged: {unchanged}")
    return manifest


def check_reproducible():
    """Build twice into temporary directories in separate processes and compare content hashes."""
    res = []
    for k in range(2):
        tmp = tempfile.mkdtemp(prefix="cmi_build_")
        subprocess.run([sys.executable, os.path.abspath(__file__), "--output-root", tmp, "--quiet"], check=True)
        man = json.load(open(os.path.join(tmp, "data", "processed", "adzuna", "dataset_manifest.json")))
        aud = {n: sha256_file(os.path.join(tmp, "data", "audits", "dataset", n)) for n in sorted(os.listdir(os.path.join(tmp, "data", "audits", "dataset")))}
        aud["quality_report.json"] = sha256_file(os.path.join(tmp, "data", "processed", "adzuna", "quality_report.json"))
        aud["schema.json"] = sha256_file(os.path.join(tmp, "data", "processed", "adzuna", "schema.json"))
        pq = pd.read_parquet(os.path.join(tmp, "data", "processed", "adzuna", "career_market_dataset.parquet"))
        res.append({"content_sha256": man["dataset_content_sha256"], "rows": man["final_count"], "audit_file_hashes": aud,
                    "parquet_logical_hash": hashlib.sha256(pq.astype(str).to_csv(index=False).encode()).hexdigest()})
    same = res[0] == res[1]
    out = {"runs": 2, "identical_content_hash": res[0]["content_sha256"] == res[1]["content_sha256"], "identical_parquet_logical_hash": res[0]["parquet_logical_hash"] == res[1]["parquet_logical_hash"],
           "identical_audit_and_report_files": res[0]["audit_file_hashes"] == res[1]["audit_file_hashes"], "content_sha256": res[0]["content_sha256"],
           "rows": res[0]["rows"], "audit_files_compared": sorted(res[0]["audit_file_hashes"]), "result": "REPRODUCIBLE" if same else "NOT REPRODUCIBLE"}
    aud_dir = os.path.join(ROOT, "data", "audits", "dataset")
    json.dump(out, open(os.path.join(aud_dir, "reproducibility_check.json"), "w"), indent=1)
    mp = os.path.join(ROOT, "data", "processed", "adzuna", "dataset_manifest.json")
    if os.path.exists(mp):
        m = json.load(open(mp))
        m["reproducibility_check"] = {"result": out["result"], "runs": 2, "matches_main_build": m["dataset_content_sha256"] == out["content_sha256"], "detail": "data/audits/dataset/reproducibility_check.json"}
        json.dump(m, open(mp, "w"), indent=1, sort_keys=True, ensure_ascii=False)
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-root", default=ROOT, help="write data/processed and data/audits under this root (default: repository root)")
    ap.add_argument("--check-reproducible", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.check_reproducible:
        sys.exit(0 if check_reproducible()["result"] == "REPRODUCIBLE" else 1)
    run(a.output_root, verbose=not a.quiet)
