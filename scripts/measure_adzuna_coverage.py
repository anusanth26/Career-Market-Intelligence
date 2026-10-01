"""
Measures Adzuna posting availability (the `count` field) per candidate role and country.
Uses 1 result per call, so it is cheap in bandwidth but still counts against rate limits.

Reads ADZUNA_APP_ID / ADZUNA_APP_KEY from the environment (.env is loaded if present).
Output: data/raw/adzuna/coverage_<date>.json
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRIES = ["in", "gb", "us"]
MAX_DAYS_OLD = 90
SLEEP_SECONDS = 2.6  # free tier is rate limited; stay well under ~25 calls/min

ROLES = {
    "Technology & Data": ["software engineer", "data analyst", "data scientist", "data engineer",
                          "machine learning engineer", "devops engineer", "cybersecurity analyst",
                          "cloud engineer"],
    "Business, Finance & Management": ["business analyst", "financial analyst", "accountant",
                                       "project manager", "product manager", "digital marketing",
                                       "human resources"],
    "Healthcare": ["registered nurse", "pharmacist", "physiotherapist", "radiographer",
                   "clinical research associate", "medical coder"],
    "Engineering": ["mechanical engineer", "electrical engineer", "civil engineer",
                    "chemical engineer", "quality engineer", "manufacturing engineer"],
    "Logistics, Transport & Supply Chain": ["supply chain analyst", "logistics coordinator",
                                            "warehouse manager", "procurement specialist",
                                            "transport planner"],
    "Energy & Environment": ["solar engineer", "environmental engineer", "energy analyst",
                             "sustainability analyst", "health and safety officer"],
    "Media, Design & Creative": ["graphic designer", "ux designer", "content writer",
                                 "video editor", "social media manager"],
    "Architecture & Construction": ["architect", "quantity surveyor", "site engineer",
                                    "bim modeller", "construction manager"],
}


def probe(country: str, title: str) -> dict:
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": 1,
              "title_only": title, "max_days_old": MAX_DAYS_OLD,
              "content-type": "application/json"}
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        return {"error": r.status_code, "body": r.text[:120]}
    d = r.json()
    return {"count": d.get("count"), "mean_salary": d.get("mean")}


def main():
    if not APP_ID or not APP_KEY:
        sys.exit("Set ADZUNA_APP_ID and ADZUNA_APP_KEY")
    out = {"pulled": datetime.now(timezone.utc).isoformat(), "max_days_old": MAX_DAYS_OLD,
           "query_type": "title_only", "results": []}
    for domain, roles in ROLES.items():
        for role in roles:
            row = {"domain": domain, "role": role}
            for c in COUNTRIES:
                row[c] = probe(c, role)
                time.sleep(SLEEP_SECONDS)
            print(domain, "|", role, "|", {c: row[c].get("count", row[c]) for c in COUNTRIES}, flush=True)
            out["results"].append(row)
    path = os.path.join("data", "raw", "adzuna", f"coverage_{datetime.now(timezone.utc):%Y-%m-%d}.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print("saved", path)


if __name__ == "__main__":
    main()
