"""
preprocessing.py
================
Member 1 -- Preprocessing pipeline
Career Market Intelligence Project

Input : data/processed/adzuna/career_market_core_analysis.csv
Output: data/processed/career_market_preprocessed.csv

Run:
    python scripts/preprocessing.py
"""

import re
import sys
import json
import logging
from pathlib import Path

import pandas as pd
import nltk
import spacy

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV  = ROOT / "data" / "processed" / "adzuna" / "career_market_core_analysis.csv"
OUTPUT_CSV = ROOT / "data" / "processed" / "career_market_preprocessed.csv"
LOG_JSON   = ROOT / "data" / "processed" / "preprocessing_audit.json"

# ---------------------------------------------------------------------------
# Columns to keep (Step 2)
# ---------------------------------------------------------------------------
KEEP_COLS = [
    "job_id", "title", "role", "domain", "employer", "description_raw",
    "location_country", "location_region", "created_date", "category_label",
    "contract_time", "salary_min", "salary_max", "salary_present",
    "salary_passes_plausibility_screen", "description_length",
]

# ---------------------------------------------------------------------------
# Seniority keyword mapping (Step 4)
# ---------------------------------------------------------------------------
SENIOR_KW = re.compile(
    r"\b(senior|sr\.?|lead|principal|head|manager|director)\b", re.IGNORECASE
)
ENTRY_KW = re.compile(
    r"\b(junior|jr\.?|graduate|trainee|intern|entry|associate)\b", re.IGNORECASE
)

# ---------------------------------------------------------------------------
# NLTK stopwords (negation-aware)
# ---------------------------------------------------------------------------
def get_stopwords():
    nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords
    sw = set(stopwords.words("english"))
    negations = {"not", "no", "nor", "never", "neither", "nothing", "nobody",
                 "nowhere", "none", "cannot", "n't"}
    return sw - negations


# ---------------------------------------------------------------------------
# Text cleaning (Step 6)
# ---------------------------------------------------------------------------
def clean_text(text, stopwords, nlp):
    if not isinstance(text, str) or not text.strip():
        return ""

    # 1. Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = (text
            .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'"))
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)

    # 2. Lowercase
    text = text.lower()

    # Preserve tech tokens
    tech_subs = [
        (r"\bc\+\+", "cplusplus"),
        (r"\bnode\.js\b", "nodejs"),
        (r"\b\.net\b", "dotnet"),
        (r"\basp\.net\b", "aspnetdotnet"),
        (r"\bvue\.js\b", "vuejs"),
        (r"\breact\.js\b", "reactjs"),
        (r"\bangular\.js\b", "angularjs"),
        (r"\btensor\.?flow\b", "tensorflow"),
    ]
    for pat, repl in tech_subs:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    # Remove special characters (keep letters, digits, spaces)
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # 3. Remove stopwords
    tokens = text.split()
    tokens = [t for t in tokens if t not in stopwords]
    text = " ".join(tokens)

    # 4. Lemmatize with spaCy
    doc = nlp(text, disable=["parser", "ner"])
    lemmas = [token.lemma_ for token in doc if token.lemma_.strip()]
    text = " ".join(lemmas)

    # 5. Collapse spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main():
    audit = {}

    # Step 1: Load
    log.info("=== Step 1: Loading data ===")
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    log.info("Loaded shape: %s", df.shape)
    audit["input_shape"] = list(df.shape)

    # Step 2: Select columns
    log.info("=== Step 2: Selecting columns ===")
    missing_keep = [c for c in KEEP_COLS if c not in df.columns]
    if missing_keep:
        log.warning("Columns expected but not found: %s", missing_keep)
    keep = [c for c in KEEP_COLS if c in df.columns]
    df = df[keep].copy()
    log.info("Columns kept: %d", len(df.columns))

    # Step 3: Build target variable
    log.info("=== Step 3: Building target variable ===")
    df["salary_mid"] = (df["salary_min"] + df["salary_max"]) / 2
    mask = df["salary_passes_plausibility_screen"].fillna(False).astype(bool)
    df.loc[~mask, "salary_mid"] = float("nan")
    log.info("Plausible salary rows: %d", mask.sum())
    audit["salary_plausible_rows"] = int(mask.sum())

    df["salary_band"] = pd.NA
    df.loc[mask, "salary_band"] = pd.qcut(
        df.loc[mask, "salary_mid"], 3, labels=["low", "medium", "high"]
    )
    log.info("salary_band:\n%s", df["salary_band"].value_counts())
    df["has_salary"] = df["salary_passes_plausibility_screen"].fillna(False).astype(bool)
    log.info("has_salary==True: %d", df["has_salary"].sum())

    # Step 4: Seniority level
    log.info("=== Step 4: Deriving seniority_level ===")
    def classify_seniority(title):
        if not isinstance(title, str):
            return "Mid"
        if SENIOR_KW.search(title):
            return "Senior"
        if ENTRY_KW.search(title):
            return "Entry"
        return "Mid"
    df["seniority_level"] = df["title"].apply(classify_seniority)
    log.info("seniority_level:\n%s", df["seniority_level"].value_counts())

    # Step 5: Handle missing values
    log.info("=== Step 5: Handling missing values ===")
    missing_before = df.isnull().sum()
    audit["missing_before"] = missing_before.to_dict()
    log.info("Missing BEFORE:\n%s", missing_before[missing_before > 0].to_string())

    ct_fill = df["contract_time"].isna().sum()
    df["contract_time"] = df["contract_time"].fillna("unknown")
    log.info("contract_time filled 'unknown': %d", ct_fill)

    lr_fill = df["location_region"].isna().sum()
    df["location_region"] = df["location_region"].fillna("unknown")
    log.info("location_region filled 'unknown': %d", lr_fill)

    emp_fill = df["employer"].isna().sum()
    df["employer"] = df["employer"].fillna("unknown")
    log.info("employer filled 'unknown': %d", emp_fill)

    rows_before = len(df)
    df = df[df["description_raw"].notna() & (df["description_raw"].str.strip() != "")]
    rows_after = len(df)
    log.info("Rows dropped (empty desc): %d (was %d, now %d)", rows_before - rows_after, rows_before, rows_after)
    audit["rows_dropped_empty_desc"] = rows_before - rows_after

    missing_after = df.isnull().sum()
    audit["missing_after"] = missing_after.to_dict()
    log.info("Missing AFTER:\n%s", missing_after[missing_after > 0].to_string())

    # Step 6: Clean text
    log.info("=== Step 6: Cleaning descriptions ===")
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    stopwords = get_stopwords()
    total = len(df)
    log.info("Cleaning %d descriptions...", total)
    cleaned = []
    for i, text in enumerate(df["description_raw"], 1):
        cleaned.append(clean_text(text, stopwords, nlp))
        if i % 500 == 0:
            log.info("  %d / %d", i, total)
    df["description_clean"] = cleaned
    log.info("description_clean done. Non-empty: %d", (df["description_clean"] != "").sum())

    # Step 7: Standardize
    log.info("=== Step 7: Standardizing ===")
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    for col in ["role", "location_region", "location_country", "category_label"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
    dup_count = df["job_id"].duplicated().sum()
    log.info("Duplicate job_ids: %d", dup_count)
    audit["duplicate_job_ids"] = int(dup_count)

    # Step 8: Validate & export
    log.info("=== Step 8: Validate & Export ===")
    assert df["job_id"].is_unique, "job_id is NOT unique!"
    log.info("salary_band counts:\n%s", df["salary_band"].value_counts().to_string())
    log.info("has_salary True: %d", df["has_salary"].sum())
    log.info("Final shape: %s", df.shape)
    audit["output_shape"] = list(df.shape)
    audit["salary_band_counts"] = {str(k): int(v) for k, v in df["salary_band"].value_counts().items()}
    audit["has_salary_count"] = int(df["has_salary"].sum())
    audit["final_columns"] = list(df.columns)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    log.info("Saved -> %s", OUTPUT_CSV)

    def jsonify(obj):
        if isinstance(obj, dict):
            return {k: jsonify(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [jsonify(i) for i in obj]
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

    with open(LOG_JSON, "w") as f:
        json.dump(jsonify(audit), f, indent=2)
    log.info("Audit log saved -> %s", LOG_JSON)

    print("\n" + "="*60)
    print("DEFINITION OF DONE CHECKLIST")
    print("="*60)
    print(f"[{'OK' if OUTPUT_CSV.exists() else 'FAIL'}] career_market_preprocessed.csv exists")
    print(f"[{'OK' if df['job_id'].is_unique else 'FAIL'}] job_id unique")
    print(f"[{'OK' if 'salary_band' in df.columns else 'FAIL'}] salary_band present")
    print(f"[{'OK' if 'has_salary' in df.columns else 'FAIL'}] has_salary flag present")
    print(f"[{'OK' if 'seniority_level' in df.columns else 'FAIL'}] seniority_level derived")
    print(f"[{'OK' if 'description_clean' in df.columns else 'FAIL'}] description_clean created")
    print(f"[{'OK' if 'description_raw' in df.columns else 'FAIL'}] description_raw kept")
    print(f"  Total rows: {len(df)}")
    print(f"  has_salary=True: {df['has_salary'].sum()}")
    print(f"  salary_band distribution:")
    for band, count in df['salary_band'].value_counts().items():
        print(f"    {band}: {count}")
    print("="*60)
    log.info("=== PREPROCESSING COMPLETE ===")


if __name__ == "__main__":
    main()
