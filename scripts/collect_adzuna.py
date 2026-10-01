"""
Collects job postings from the Adzuna API and saves the raw, untouched API records plus
reproducibility metadata. One directory per run, never overwritten:

    data/raw/adzuna/runs/<run_id>/
        run_manifest.json          config snapshot, CLI args, timestamps, environment
        queries.jsonl              one line per (country, role, title variant): API count + pull stats
        attempts.jsonl             every FAILED HTTP attempt (status, error text with credentials redacted)
        records_<...>.jsonl        one line per posting: {"collection": {...}, "raw": {<unmodified API record>}}

Setup:
1. Put ADZUNA_APP_ID and ADZUNA_APP_KEY in .env (git-ignored) or in the environment.
2. Edit config/roles.json (roles, title variants, countries, enabled flag, thresholds).
3. Run from the project root:
       python scripts/collect_adzuna.py --dry-run
       python scripts/collect_adzuna.py --roles "Data Analyst,Graphic Designer" --max-records 100
       python scripts/collect_adzuna.py

Every query sends title_only, max_days_old and sort_by=date (see config/roles.json settings).
A query is NOT a role label: role assignment is done later from the actual title
(scripts/role_mapping.py, scripts/analyze_coverage.py). `query_role` below only records which
config entry asked for the posting.
"""

import argparse
import hashlib
import json
import math
import os
import platform
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

DEFAULT_CONFIG = os.path.join("config", "roles.json")
DEFAULT_OUTPUT_ROOT = os.path.join("data", "raw", "adzuna", "runs")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"


# ── helpers ───────────────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text) -> str:
    """Remove credentials from any text that is about to be logged (requests errors embed URLs)."""
    text = str(text)
    for secret in (APP_ID, APP_KEY):
        if secret:
            text = text.replace(secret, "***")
    return re.sub(r"(app_(?:id|key)=)[^&\s'\"]+", r"\1***", text)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def append_jsonl(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def expand_queries(cfg: dict, role_filter=None, country_filter=None, max_records=None) -> list:
    """Flatten config into one entry per (country, role, title variant)."""
    default_cap = cfg["settings"]["default_max_records"]
    queries = []
    for role in cfg["roles"]:
        if not role.get("enabled", True):
            continue
        if role_filter and role["role"] not in role_filter:
            continue
        for country in role["countries"]:
            if country_filter and country not in country_filter:
                continue
            for variant in role["variants"]:
                v = {"query": variant} if isinstance(variant, str) else dict(variant)
                queries.append({
                    "domain": role["domain"], "role": role["role"], "tier": role.get("tier"),
                    "country": country, "query": v["query"],
                    "max_records": max_records or v.get("max_records", default_cap),
                })
    return queries


class RateLimiter:
    """Enforces a minimum gap between API calls. Adzuna's limit is not documented in what we
    could fetch, so this is a conservative self-imposed pace; observed behaviour goes in attempts.jsonl."""

    def __init__(self, min_interval: float):
        self.min_interval, self._last = min_interval, 0.0

    def wait(self):
        gap = time.monotonic() - self._last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last = time.monotonic()


def request_with_retry(session, url, params, ctx, settings, limiter, attempts_path, stats):
    """GET with exponential backoff. Returns parsed JSON dict, or None once retries are exhausted /
    the error is not retryable. Every failed attempt is logged; nothing is silently discarded."""
    retry_statuses = set(settings["retry_statuses"])
    for attempt in range(settings["max_retries"] + 1):
        limiter.wait()
        status, error, retry_after, data = None, None, None, None
        started = time.monotonic()
        try:
            r = session.get(url, params=params, timeout=settings["request_timeout_seconds"])
            status = r.status_code
            retry_after = r.headers.get("Retry-After")
            if status == 200:
                try:
                    data = r.json()
                except ValueError:
                    error = "200 but body was not valid JSON"
                    status = "bad_json"
                else:
                    if attempt:
                        append_jsonl(attempts_path, {**ctx, "attempt": attempt, "outcome": "recovered",
                                                     "at": iso(utcnow())})
                    return data
            else:
                error = redact(r.text[:200])
        except (requests.Timeout, requests.ConnectionError) as e:
            error = redact(f"{type(e).__name__}: {e}")

        stats["http_failures"] += 1
        retryable = status in retry_statuses or status in (None, "bad_json")
        last = attempt == settings["max_retries"]
        append_jsonl(attempts_path, {
            **ctx, "attempt": attempt, "status": status, "error": error, "retry_after": retry_after,
            "elapsed_s": round(time.monotonic() - started, 2), "will_retry": retryable and not last,
            "at": iso(utcnow()),
        })
        if not retryable:
            stats["stop_reason"] = f"non_retryable_http_{status}"
            return None
        if last:
            stats["stop_reason"] = "retries_exhausted"
            return None
        stats["retries"] += 1
        delay = min(settings["backoff_max_seconds"], settings["backoff_base_seconds"] * 2 ** attempt)
        if retry_after and str(retry_after).isdigit():
            delay = max(delay, min(int(retry_after), settings["backoff_max_seconds"]))
        time.sleep(delay + random.uniform(0, 1))
    return None


def fetch_query(session, q, settings, run_id, run_dir, limiter, window_start):
    """Pull pages for one (country, role, variant). Records are appended page by page so partial
    progress survives any failure. Returns the query-level metadata dict."""
    page_size = settings["page_size"]
    max_pages = math.ceil(q["max_records"] / page_size)
    records_name = f"records_{q['country']}_{slug(q['role'])}__{slug(q['query'])}.jsonl"
    records_path = os.path.join(run_dir, records_name)
    attempts_path = os.path.join(run_dir, "attempts.jsonl")

    request_params = {  # credentials deliberately excluded from what we record
        "results_per_page": page_size, "title_only": q["query"],
        "max_days_old": settings["max_days_old"], "sort_by": settings["sort_by"],
    }
    stats = {"http_failures": 0, "retries": 0, "stop_reason": None}
    meta = {
        "run_id": run_id, "source": settings["source"], "country": q["country"], "domain": q["domain"],
        "query_role": q["role"], "query": q["query"], "max_records": q["max_records"],
        "requested_page_size": page_size, "request_params": request_params,
        "pull_started": iso(utcnow()), "api_count": None, "api_count_min": None, "api_count_max": None,
        "pages_ok": 0, "raw_records": 0, "records_file": records_name,
    }
    ids, created = [], []
    ctx = {"run_id": run_id, "country": q["country"], "query": q["query"], "role": q["role"]}

    for page in range(1, max_pages + 1):
        url = BASE_URL.format(country=q["country"], page=page)
        data = request_with_retry(
            session, url, {**request_params, "app_id": APP_ID, "app_key": APP_KEY,
                           "content-type": "application/json"},
            {**ctx, "page": page}, settings, limiter, attempts_path, stats)
        if data is None:
            break
        count = data.get("count")
        if count is not None:
            if meta["api_count"] is None:
                meta["api_count"] = count
            meta["api_count_min"] = count if meta["api_count_min"] is None else min(meta["api_count_min"], count)
            meta["api_count_max"] = count if meta["api_count_max"] is None else max(meta["api_count_max"], count)
        results = data.get("results", [])
        if not results:
            stats["stop_reason"] = "no_more_results"
            break
        fetched_at = iso(utcnow())
        for pos, raw in enumerate(results):
            append_jsonl(records_path, {
                "collection": {
                    "run_id": run_id, "collected_at": fetched_at, "source": settings["source"],
                    "country": q["country"], "query_variant": q["query"], "query_role": q["role"],
                    "domain": q["domain"], "adzuna_id": str(raw.get("id")), "page": page, "position": pos,
                },
                "raw": raw,  # untouched API record
            })
            ids.append(str(raw.get("id")))
            created.append(raw.get("created"))
        meta["pages_ok"] += 1
        meta["raw_records"] += len(results)
        if meta["raw_records"] >= q["max_records"]:
            stats["stop_reason"] = "max_records_reached"
            break
        if len(results) < page_size:
            stats["stop_reason"] = "no_more_results"
            break
    else:
        stats["stop_reason"] = "max_records_reached"

    # Self-audit facts recorded with every query so a run can be verified without re-reading records
    valid = [c for c in created if c]
    meta.update({
        "pull_finished": iso(utcnow()), **stats,
        "status": "complete" if stats["stop_reason"] in ("max_records_reached", "no_more_results") else "partial",
        "capped_by_max_records": stats["stop_reason"] == "max_records_reached"
                                 and (meta["api_count"] or 0) > meta["raw_records"],
        "duplicate_ids_within_query": len(ids) - len(set(ids)),
        "created_min": min(valid) if valid else None, "created_max": max(valid) if valid else None,
        "created_sorted_desc": all(a >= b for a, b in zip(valid, valid[1:])),
        "records_older_than_window": sum(1 for c in valid if c < iso(window_start)),
    })
    return meta


# ── main ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--roles", help="comma-separated canonical role names to run (default: all enabled)")
    ap.add_argument("--countries", help="comma-separated country codes to run (default: as configured)")
    ap.add_argument("--max-records", type=int, help="override the per-query record cap (for smoke tests)")
    ap.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    ap.add_argument("--tag", default="", help="label appended to the run directory name")
    ap.add_argument("--dry-run", action="store_true", help="print the query plan and exit; no API calls")
    args = ap.parse_args()

    cfg = load_config(args.config)
    settings = cfg["settings"]
    queries = expand_queries(
        cfg, set(args.roles.split(",")) if args.roles else None,
        set(args.countries.split(",")) if args.countries else None, args.max_records)
    if not queries:
        sys.exit("No queries selected (check --roles spelling / enabled flags in the config).")

    est_calls = sum(math.ceil(q["max_records"] / settings["page_size"]) for q in queries)
    print(f"{len(queries)} queries, up to {est_calls} API calls "
          f"(~{est_calls * settings['min_interval_seconds'] / 60:.0f} min at the configured pace)")
    if args.dry_run:
        for q in queries:
            print(f"  [{q['country']}] {q['role']:<32} title_only={q['query']!r:<34} cap={q['max_records']}")
        return
    if not APP_ID or not APP_KEY:
        sys.exit("ERROR: set ADZUNA_APP_ID and ADZUNA_APP_KEY (in .env or the environment).")

    started = utcnow()
    cfg_hash = hashlib.sha256(json.dumps([cfg, [q for q in queries]], sort_keys=True).encode()).hexdigest()[:8]
    run_id = f"{started:%Y%m%dT%H%M%SZ}_{cfg_hash}" + (f"_{slug(args.tag)}" if args.tag else "")
    run_dir = os.path.join(args.output_root, run_id)
    os.makedirs(run_dir, exist_ok=False)  # never reuse or overwrite an existing run

    manifest = {"run_id": run_id, "started": iso(started), "argv": sys.argv[1:], "config_path": args.config,
                "config_snapshot": cfg, "queries_planned": queries, "python": platform.python_version(),
                "window_start": None}
    manifest_path = os.path.join(run_dir, "run_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    session, limiter = requests.Session(), RateLimiter(settings["min_interval_seconds"])
    # Adzuna's max_days_old works in whole calendar days (verified: all 8 boundary rows in the first full run
    # were created on the boundary date), so the window starts at 00:00 UTC of (run date - max_days_old).
    window_start = (started - timedelta(days=settings["max_days_old"])).replace(hour=0, minute=0, second=0, microsecond=0)
    manifest["window_start"] = iso(window_start)
    manifest["window_start_exact_timestamp"] = iso(started - timedelta(days=settings["max_days_old"]))
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Run {run_id}\n")
    consecutive_failed, abort_after = 0, settings.get("abort_after_consecutive_failed_queries", 3)
    try:
        for i, q in enumerate(queries, 1):
            meta = fetch_query(session, q, settings, run_id, run_dir, limiter, window_start)
            append_jsonl(os.path.join(run_dir, "queries.jsonl"), meta)
            print(f"[{i}/{len(queries)}] {q['country']} {q['role']} | {q['query']!r}: "
                  f"api_count={meta['api_count']} raw={meta['raw_records']} pages={meta['pages_ok']} "
                  f"fail={meta['http_failures']} retries={meta['retries']} status={meta['status']}", flush=True)
            # several queries in a row exhausting their retries usually means a quota/ban, not a blip
            consecutive_failed = consecutive_failed + 1 if meta["stop_reason"] in (
                "retries_exhausted", "non_retryable_http_401", "non_retryable_http_403") else 0
            if consecutive_failed >= abort_after:
                manifest["aborted"] = f"{consecutive_failed} consecutive queries failed after retries; stopped at {i}/{len(queries)}"
                print("ABORTING:", manifest["aborted"])
                break
    finally:  # even on Ctrl-C the manifest records how far we got
        manifest["finished"] = iso(utcnow())
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    print(f"\nDone. Run directory: {run_dir}")


if __name__ == "__main__":
    main()
