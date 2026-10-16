"""
Rescales Google Trends batches to a common scale using the shared anchor term, so skills collected in
different requests become comparable. Google scales every request 0-100 WITHIN that request only; the
anchor (default 'SQL') appears in every batch and is used to align them.

Method: pick the first batch as reference. For every batch, factor = ref_anchor_mean / batch_anchor_mean;
multiply that batch's non-anchor skill columns by the factor. Merge all skills on date.

Output (shareable, committed): data/processed/trends_rescaled_<GEO>.csv  (columns: date, <skills...>)

Usage:
    python scripts/rescale_trends.py            # geo IN (default)
    python scripts/rescale_trends.py --geo US
"""

import argparse
import glob
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRENDS_DIR = os.path.join(ROOT, "data", "raw", "trends")
OUT_DIR = os.path.join(ROOT, "data", "processed")
ANCHOR = "SQL"


def load_batch(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")  # handles ISO and other formats
    df = df.dropna(subset=["date"]).sort_values("date")
    if "isPartial" in df.columns:
        # drop the trailing partial week if present (incomplete data)
        partial = df["isPartial"].astype(str).str.upper().eq("TRUE")
        df = df[~partial].drop(columns=["isPartial"])
    return df.set_index("date")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", default="IN")
    args = ap.parse_args()

    all_paths = glob.glob(os.path.join(TRENDS_DIR, f"trends_{args.geo}_batch*.csv"))
    if not all_paths:
        raise SystemExit(f"No trends batches found for geo={args.geo} in {TRENDS_DIR}")
    # Use only the most recent pull date (filename suffix _YYYY-MM-DD.csv) to avoid mixing pulls.
    def _pull_date(p: str) -> str:
        m = re.search(r"_(\d{4}-\d{2}-\d{2})\.csv$", p)
        return m.group(1) if m else ""
    latest = max(_pull_date(p) for p in all_paths)
    paths = sorted(p for p in all_paths if _pull_date(p) == latest)
    print(f"Using pull date {latest}: {len(paths)} batch file(s)")

    ref = load_batch(paths[0])
    if ANCHOR not in ref.columns:
        raise SystemExit(f"Anchor '{ANCHOR}' missing from reference batch {paths[0]}")
    ref_anchor_mean = ref[ANCHOR].astype(float).mean()

    merged = pd.DataFrame(index=ref.index)
    merged[ANCHOR] = ref[ANCHOR].astype(float)

    for path in paths:
        batch = load_batch(path)
        if ANCHOR not in batch.columns:
            print(f"  skip (no anchor): {os.path.basename(path)}")
            continue
        batch_anchor_mean = batch[ANCHOR].astype(float).mean()
        factor = ref_anchor_mean / batch_anchor_mean if batch_anchor_mean else 1.0
        for col in batch.columns:
            if col == ANCHOR or col in merged.columns:
                continue
            merged[col] = batch[col].astype(float) * factor

    merged = merged.sort_index()
    out_path = os.path.join(OUT_DIR, f"trends_rescaled_{args.geo}.csv")
    merged.reset_index().to_csv(out_path, index=False)

    # Sanity check: percent change first-year vs last-year per skill.
    weeks = np.arange(len(merged))
    changes = {}
    for col in merged.columns:
        y = merged[col].values
        first, last = y[:52].mean(), y[-52:].mean()
        changes[col] = 100 * (last - first) / first if first else 0.0

    print(f"Batches merged : {len(paths)} (geo={args.geo})")
    print(f"Skills (incl. anchor): {len(merged.columns)}")
    print(f"Weeks          : {len(merged)}")
    print(f"Output         : {out_path}")
    print("\nFirst-year vs last-year % change:")
    for k, v in sorted(changes.items(), key=lambda kv: kv[1]):
        print(f"  {k:<18} {v:+.1f}%")
    declining = sum(1 for v in changes.values() if v < -10)
    if declining == len(changes):
        print("\n[WARNING] Every skill declines — this usually means the rescaling or anchor is wrong.")
        print("          Re-check the anchor term before presenting these trends.")


if __name__ == "__main__":
    main()
