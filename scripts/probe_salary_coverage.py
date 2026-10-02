"""
Salary-coverage probe for the Adzuna API (READ-ONLY, non-destructive).

Purpose
-------
Before committing to a full re-pull, this script measures how many *real* salaried
job postings Adzuna can give us for the India market, per role. It does NOT modify any
existing raw data, dataset, or run folders. It only:
    1. Asks Adzuna, per role, how many postings exist WITH a salary (salary_min filter).
    2. Asks how many exist in total (no salary filter) -> salary disclosure rate.
    3. Samples page 1 and confirms salary_min/salary_max are actually populated.
    4. Writes one small JSON report to data/raw/adzuna/salary_probe_<date>.json.

Setup
-----
1. Put ADZUNA_APP_ID and ADZUNA_APP_KEY in a .env file (git-ignored) at the project root:
       ADZUNA_APP_ID=your_id
       ADZUNA_APP_KEY=your_key
2. Run from the project root:
       python scripts/probe_salary_coverage.py --dry-run     # show planned calls, no API hits
       python scripts/probe_salary_coverage.py                # probe all roles
       python scripts/probe_salary_coverage.py --roles "Data Analyst,Software Engineer"

Reading the output
------------------
    salaried_available = Adzuna 'count' with salary_min filter  -> the real ceiling of new salaried rows
    total_available    = Adzuna 'count' with no salary filter
    disclosure_rate    = salaried_available / total_available
    salary_on_page1    = of the 50 sampled results, how many actually carry salary_min & salary_max
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

CONFIG_PATH = os.path.join("config", "roles.json")
OUTPUT_DIR = os.path.join("data", "raw", "adzuna")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
COUNTRY = "in"  # all existing salary data is India; keep the probe single-market for comparability
SALARY_MIN_FILTER = 1  # salary_min=1 makes Adzuna return only postings that carry a salary


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text) -> str:
    text = str(text)
    for secret in (APP_ID, APP_KEY):
        if secret:
            text = text.replace(secret, "***")
    return re.sub(r"(app_(?:id|key)=)[^&\s'\"]+", r"\1***", text)


def load_roles(role_filter):
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    settings = cfg["settings"]
    roles = []
    for role in cfg["roles"]:
        if not role.get("enabled", True):
            continue
        if role_filter and role["role"] not in role_filter:
            continue
        if COUNTRY not in role.get("countries", []):
            continue
        # use the first (canonical) title variant as the probe query
        first = role["variants"][0]
        query = first if isinstance(first, str) else first["query"]
        roles.append({"role": role["role"], "query": query})
    return settings, roles


def call(session, params, settings):
    """Single GET with credentials attached. Returns (json_or_None, error_or_None)."""
    try:
        r = session.get(
            BASE_URL.format(country=COUNTRY),
            params={**params, "app_id": APP_ID, "app_key": APP_KEY},
            timeout=settings["request_timeout_seconds"],
        )
        if r.status_code == 200:
            return r.json(), None
        return None, f"HTTP {r.status_code}: {redact(r.text[:200])}"
    except (requests.Timeout, requests.ConnectionError) as e:
        return None, redact(f"{type(e).__name__}: {e}")


def probe_role(session, role, settings):
    base = {
        "results_per_page": settings["page_size"],
        "title_only": role["query"],
        "max_days_old": settings["max_days_old"],
    }
    # 1. total postings (no salary filter)
    total_data, total_err = call(session, base, settings)
    time.sleep(settings["min_interval_seconds"])
    # 2. salaried postings only
    sal_data, sal_err = call(session, {**base, "salary_min": SALARY_MIN_FILTER}, settings)
    time.sleep(settings["min_interval_seconds"])

    total = (total_data or {}).get("count")
    salaried = (sal_data or {}).get("count")
    results = (sal_data or {}).get("results", [])
    on_page1 = sum(1 for x in results if x.get("salary_min") and x.get("salary_max"))

    disclosure = round(salaried / total, 4) if (total and salaried is not None) else None
    return {
        "role": role["role"],
        "query": role["query"],
        "total_available": total,
        "salaried_available": salaried,
        "disclosure_rate": disclosure,
        "salary_on_page1_of_50": on_page1,
        "errors": [e for e in (total_err, sal_err) if e] or None,
    }


def main():
    ap = argparse.ArgumentParser(description="Probe Adzuna salary coverage for India (read-only).")
    ap.add_argument("--roles", help="Comma-separated role names to probe (default: all India roles).")
    ap.add_argument("--dry-run", action="store_true", help="Print planned calls without hitting the API.")
    args = ap.parse_args()

    role_filter = [r.strip() for r in args.roles.split(",")] if args.roles else None
    settings, roles = load_roles(role_filter)

    if not roles:
        print("No matching India roles found in config/roles.json.")
        sys.exit(1)

    if args.dry_run:
        print(f"DRY RUN — would probe {len(roles)} roles in country '{COUNTRY}':")
        for r in roles:
            print(f"  - {r['role']:28s} title_only='{r['query']}' (2 calls: total + salaried)")
        print(f"\nEstimated API calls: {len(roles) * 2} "
              f"(~{len(roles) * 2 * settings['min_interval_seconds']:.0f}s with rate limiting)")
        return

    if not APP_ID or not APP_KEY:
        print("ERROR: ADZUNA_APP_ID / ADZUNA_APP_KEY not set. Add them to a .env file at the project root.")
        sys.exit(1)

    session = requests.Session()
    rows = []
    print(f"Probing {len(roles)} roles (country={COUNTRY})...\n")
    print(f"{'role':28s} {'total':>8s} {'salaried':>9s} {'disclose':>9s} {'pg1/50':>7s}")
    print("-" * 65)
    for role in roles:
        row = probe_role(session, role, settings)
        rows.append(row)
        disc = f"{row['disclosure_rate']*100:.1f}%" if row["disclosure_rate"] is not None else "n/a"
        print(f"{row['role']:28s} {str(row['total_available']):>8s} "
              f"{str(row['salaried_available']):>9s} {disc:>9s} {str(row['salary_on_page1_of_50']):>7s}")
        if row["errors"]:
            print(f"    ! {row['errors']}")

    total_salaried = sum(r["salaried_available"] or 0 for r in rows)
    report = {
        "probe_timestamp": iso_now(),
        "country": COUNTRY,
        "salary_min_filter": SALARY_MIN_FILTER,
        "max_days_old": settings["max_days_old"],
        "existing_salaried_rows_in_dataset": 599,
        "total_salaried_available_now": total_salaried,
        "roles": rows,
        "note": "Adzuna 'count' is an API-side estimate of matches, not a guarantee of retrievable rows "
                "(free-tier pagination is limited). Use as an upper-bound indicator.",
    }
    out_path = os.path.join(OUTPUT_DIR, f"salary_probe_{datetime.now():%Y-%m-%d}.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("-" * 65)
    print(f"Total salaried postings available now (India, all probed roles): {total_salaried}")
    print("You currently have 599 salaried rows in the dataset.")
    print(f"\nReport written to: {out_path}")


if __name__ == "__main__":
    main()
