"""
Small evenly-spaced row sample from Hugging Face datasets-server (rows API) to estimate India presence,
salary/currency mix and description length. Stores ONLY aggregate statistics and a few titles, never
descriptions or embeddings. The accessible range is the server's "partial" window (first part of the
dataset), so results describe that window only, not the whole dataset.

    python data/raw/ml_data_feasibility/hf_sample_probe.py
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections import Counter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_sample_probe.json")
PROBES = {
    "edwarddgao/open-apply-jobs": {"total_rows_reported": 41472031, "accessible_rows_partial": 653597},
    "Yigit-Karaman/open-jobs-daily": {"total_rows_reported": 3077836, "accessible_rows_partial": 530884},
}
N_OFFSETS, LENGTH = 24, 25
INDIA = re.compile(r"\bindia\b|bengaluru|bangalore|hyderabad|mumbai|pune|chennai|gurgaon|gurugram|noida|delhi|kolkata", re.I)


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cmi-feasibility"}), timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 - report and retry
            err = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    return {"error": err}


def main():
    result = {}
    for ds, info in PROBES.items():
        span = info["accessible_rows_partial"]
        rows, errors = [], []
        for i in range(N_OFFSETS):
            off = int(i * (span - LENGTH) / (N_OFFSETS - 1))
            q = urllib.parse.urlencode({"dataset": ds, "config": "default", "split": "train", "offset": off, "length": LENGTH})
            d = get("https://datasets-server.huggingface.co/rows?" + q)
            if "rows" in d:
                rows += [r["row"] for r in d["rows"]]
            else:
                errors.append(str(d)[:200])
            time.sleep(1)
        n = len(rows)
        loc_key = "locations" if ds.startswith("edwarddgao") else "location"
        desc_key = "description_html" if ds.startswith("edwarddgao") else "jd"

        def loc_text(r):
            v = r.get(loc_key)
            return " ".join(v) if isinstance(v, list) else (v or "")
        india = [r for r in rows if INDIA.search(loc_text(r))]
        res = {**info, "sampled_rows": n, "sample_errors": errors[:3], "sample_design": f"{N_OFFSETS} evenly spaced offsets x {LENGTH} rows inside the partial window",
               "india_like_location_rows": len(india), "india_like_pct": round(100 * len(india) / n, 2) if n else None,
               "description_len_chars": sorted(len(r.get(desc_key) or "") for r in rows)[n // 2] if n else None,
               "sample_india_titles": [r.get("title") for r in india[:8]]}
        if ds.startswith("edwarddgao"):
            sal = [r for r in rows if r.get("salary_min") is not None or r.get("salary_max") is not None]
            res.update({"salary_present_pct": round(100 * len(sal) / n, 2) if n else None,
                        "salary_currency_counts": dict(Counter(r.get("salary_currency") for r in sal)),
                        "salary_period_counts": dict(Counter(r.get("salary_period") for r in sal)),
                        "source_counts": dict(Counter(r.get("source") for r in rows) if rows and "source" in rows[0] else {}),
                        "posted_at_min_max": [min((r.get("posted_at") or "~")[:10] for r in rows), max((r.get("posted_at") or "")[:10] for r in rows)] if rows else None,
                        "distinct_ids": len({r.get("id") for r in rows}),
                        "distinct_source_slug": len({r.get("source_slug") for r in rows})})
        else:
            res.update({"ats_counts": dict(Counter(r.get("ats") for r in rows).most_common(8)),
                        "jd_at_4000_char_cap_pct": round(100 * sum(1 for r in rows if len(r.get("jd") or "") >= 4000) / n, 1) if n else None,
                        "salary_field_present": any("salary" in k for k in (rows[0] if rows else {}))})
        result[ds] = res
    json.dump(result, open(OUT, "w"), indent=2)
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
