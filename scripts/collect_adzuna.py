"""
Collects job postings from the Adzuna API and saves the raw, untouched
JSON responses — one file per category — into data/raw/adzuna/.

Setup:
1. Register for a free key at https://developer.adzuna.com/
2. Set your APP_ID and APP_KEY below (or as environment variables — see note at bottom)
3. Adjust COUNTRY, CATEGORIES, and RESULTS_PER_CATEGORY as needed
4. Run from inside your project root (see "Where to run" at the bottom of the chat message)
"""

import requests
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY = "in"  # Adzuna country code: in, gb, us, au, de, fr, etc.

# Role categories to pull — edit these to match your team's chosen 4-6 categories
CATEGORIES = [
    "data analyst",
    "software engineer",
    "digital marketing",
    "business analyst",
]

RESULTS_PER_CATEGORY = 625     # aim for total = RESULTS_PER_CATEGORY * len(CATEGORIES)
RESULTS_PER_PAGE = 50          # Adzuna's max per page
BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

# Output location — raw JSON, one file per category, tagged with pull date
OUTPUT_DIR = os.path.join("data", "raw", "adzuna")
# ─────────────────────────────────────────────────────────────────────


def fetch_category(category: str, country: str, target_count: int) -> list:
    """Pulls pages for one category until target_count is reached or results run out."""
    all_results = []
    page = 1

    while len(all_results) < target_count:
        url = BASE_URL.format(country=country, page=page)
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": RESULTS_PER_PAGE,
            "what": category,
            "content-type": "application/json",
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"  Stopped at page {page}: HTTP {response.status_code} — {response.text[:200]}")
            break

        data = response.json()
        results = data.get("results", [])

        if not results:
            print(f"  No more results after page {page - 1}.")
            break

        all_results.extend(results)
        print(f"  Page {page}: got {len(results)} results (running total: {len(all_results)})")
        page += 1

    return all_results[:target_count]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pull_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if APP_ID == "YOUR_APP_ID_HERE" or APP_KEY == "YOUR_APP_KEY_HERE":
        print("ERROR: Set your APP_ID and APP_KEY before running.")
        return

    summary = {"pull_date": pull_date, "country": COUNTRY, "categories": {}}

    for category in CATEGORIES:
        print(f"\nFetching category: '{category}'")
        results = fetch_category(category, COUNTRY, RESULTS_PER_CATEGORY)

        # Save raw, untouched response for this category
        safe_name = category.replace(" ", "_")
        filename = f"adzuna_{safe_name}_{pull_date}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"  Saved {len(results)} records -> {filepath}")
        summary["categories"][category] = len(results)

    # Save a pull log — this is what Task 2 (data documentation) reuses directly
    log_path = os.path.join(OUTPUT_DIR, f"pull_log_{pull_date}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    total = sum(summary["categories"].values())
    print(f"\nDone. Total records collected: {total}")
    print(f"Pull log saved -> {log_path}")


if __name__ == "__main__":
    main()

