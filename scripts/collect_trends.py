"""
Collects Google Trends interest-over-time for skills and saves raw output to data/raw/trends/.

Google Trends scales every request to 0-100 relative to the terms IN THAT REQUEST, so series from
different requests are not comparable. Fix: every batch of 4 skills also contains one shared ANCHOR
term; each batch is rescaled so the anchor matches its reference level (done in the notebooks,
not here — this script stores the raw batch output untouched, plus the anchor column).

Usage:
    python scripts/collect_trends.py                 # all skills, all geos
    python scripts/collect_trends.py --limit 1       # smoke test: first batch only
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone

import pandas as pd
from pytrends.request import TrendReq

# ── CONFIG (loaded from config/review2_skills.json — the frozen skill list) ──
_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "review2_skills.json"
)
with open(_CONFIG_PATH, encoding="utf-8") as _fh:
    _CFG = json.load(_fh)
ANCHOR = _CFG.get("anchor", "SQL")   # high-volume, stable, unambiguous skill present in every batch
_GEO = _CFG.get("geo", "IN")
GEOS = {_GEO: _GEO}                   # single geo focus (IN); add more only if needed
TIMEFRAME = _CFG.get("timeframe", "today 5-y")  # weekly data; separates trend from spikes
CATEGORY = 0                         # 0 = all; 31 = Programming can disambiguate tech terms
BATCH_SIZE = 4                       # + anchor = Google's limit of 5 terms per request
PAUSE = (8, 15)                      # seconds between requests (randomised); Trends throttles hard
MAX_RETRIES = 5
OUTPUT_DIR = os.path.join("data", "raw", "trends")

SKILLS = _CFG["skills"]              # frozen list, derived from real skill demand
# ─────────────────────────────────────────────────────────────────────


def fetch(pytrends: TrendReq, terms: list, geo: str) -> pd.DataFrame:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            pytrends.build_payload(terms, cat=CATEGORY, timeframe=TIMEFRAME, geo=geo)
            return pytrends.interest_over_time()
        except Exception as e:  # pytrends raises ResponseError on HTTP 429
            wait = 60 * attempt
            print(f"    attempt {attempt} failed ({e.__class__.__name__}); sleeping {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Gave up on {terms} geo={geo!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="max batches per geo (smoke test)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pull_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    skills = [s for s in SKILLS if s.lower() != ANCHOR.lower()]
    batches = [skills[i:i + BATCH_SIZE] for i in range(0, len(skills), BATCH_SIZE)][: args.limit]
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
    log = {"pull_date": pull_date, "timeframe": TIMEFRAME, "anchor": ANCHOR, "category": CATEGORY,
           "geos": GEOS, "batches": []}

    for geo_name, geo in GEOS.items():
        for n, batch in enumerate(batches, 1):
            terms = [ANCHOR] + batch
            print(f"[{geo_name}] batch {n}/{len(batches)}: {terms}")
            df = fetch(pytrends, terms, geo)
            fname = f"trends_{geo_name}_batch{n:02d}_{pull_date}.csv"
            df.to_csv(os.path.join(OUTPUT_DIR, fname))
            log["batches"].append({"geo": geo_name, "batch": n, "terms": terms,
                                   "file": fname, "rows": len(df)})
            time.sleep(random.uniform(*PAUSE))

    with open(os.path.join(OUTPUT_DIR, f"trends_pull_log_{pull_date}.json"), "w") as f:
        json.dump(log, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()
