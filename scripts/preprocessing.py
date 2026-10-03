"""
preprocessing.py — Career Market Intelligence (Member 1)
=========================================================
Reads  : data/final/career_market_core_analysis.csv  (7,184 rows, 49 cols)
Writes : data/processed/career_market_preprocessed.csv

Steps
-----
1  Load
2  Select columns (keep features/EDA, drop audit-only)
3  Build target  (salary_mid -> salary_band, has_salary flag)
4  Derive seniority_level from job title
5  Handle missing values
6  Clean text    (description_raw -> description_clean)
7  Standardise   (dates, casing, uniqueness check)
8  Validate & export

Run from the project root:
    python scripts/preprocessing.py
"""

import re
import warnings
import pandas as pd
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

warnings.filterwarnings("ignore")

# ── paths ──────────────────────────────────────────────────────────────────────
INPUT_PATH  = "data/final/career_market_core_analysis.csv"
OUTPUT_PATH = "data/processed/career_market_preprocessed.csv"

# ── column selection ───────────────────────────────────────────────────────────
KEEP_COLS = [
    "job_id", "title", "role", "domain", "employer",
    "description_raw", "location_country", "location_region",
    "created_date", "category_label", "contract_time",
    "salary_min", "salary_max", "salary_present",
    "salary_passes_plausibility_screen", "description_length",
]

# ── seniority keywords ─────────────────────────────────────────────────────────
SENIOR_KEYWORDS = r"\b(senior|sr\.?|lead|principal|head|manager|director)\b"
ENTRY_KEYWORDS  = r"\b(junior|jr\.?|graduate|trainee|intern|entry|associate)\b"

# ── spaCy model & stopwords ────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

NEGATIONS = {
    "not", "no", "nor", "neither", "never", "none", "nothing",
    "nowhere", "nobody", "without", "cannot",
}
STOP_WORDS_FILTERED = STOP_WORDS - NEGATIONS

# ── tech-token protection ──────────────────────────────────────────────────────
TECH_TOKENS = {
    "c++":      "__CPLUSPLUS__",
    "c#":       "__CSHARP__",
    ".net":     "__DOTNET__",
    "node.js":  "__NODEJS__",
    "vue.js":   "__VUEJS__",
    "react.js": "__REACTJS__",
    "asp.net":  "__ASPNET__",
}
TECH_RESTORE = {v.lower(): k for k, v in TECH_TOKENS.items()}


# ── helpers ────────────────────────────────────────────────────────────────────

def protect_tech_tokens(text: str) -> str:
    for token, placeholder in TECH_TOKENS.items():
        text = text.replace(token, placeholder)
    return text


def restore_tech_tokens(text: str) -> str:
    for placeholder, token in TECH_RESTORE.items():
        text = text.replace(placeholder, token)
    return text


def clean_description(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    # 1 strip HTML
    text = re.sub(r"<[^>]+>", " ", text)
    for ent, repl in [("&amp;","&"),("&lt;","<"),("&gt;",">"),("&nbsp;"," "),("&quot;",'"'),("&#39;","'")]:
        text = text.replace(ent, repl)
    # 2 remove URLs and emails
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    # 3 protect tech tokens then lowercase
    text = protect_tech_tokens(text.lower())
    # 4 remove special chars; keep letters, digits, spaces, underscores (for placeholders)
    text = re.sub(r"[^a-z0-9 _]", " ", text)
    # 5 spaCy: stopwords + lemmatize
    doc = nlp(text)
    tokens = [
        token.lemma_
        for token in doc
        if token.text not in STOP_WORDS_FILTERED
        and token.lemma_ not in STOP_WORDS_FILTERED
        and not token.is_space
        and token.text.strip()
    ]
    text = " ".join(tokens)
    # 6 restore tech tokens and collapse spaces
    text = restore_tech_tokens(text)
    return re.sub(r"\s+", " ", text).strip()


def clean_descriptions_batch(series: pd.Series) -> pd.Series:
    """Batch-clean descriptions using nlp.pipe for high throughput."""
    prepped = []
    for text in series:
        if not isinstance(text, str) or not text.strip():
            prepped.append("")
            continue
        # 1 strip HTML
        text = re.sub(r"<[^>]+>", " ", text)
        for ent, repl in [("&amp;","&"),("&lt;","<"),("&gt;",">"),("&nbsp;"," "),("&quot;",'"'),("&#39;","'")]:
            text = text.replace(ent, repl)
        # 2 remove URLs and emails
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"\S+@\S+\.\S+", " ", text)
        # 3 protect tech tokens then lowercase
        text = protect_tech_tokens(text.lower())
        # 4 remove special chars
        text = re.sub(r"[^a-z0-9 _]", " ", text)
        prepped.append(text)

    cleaned = []
    for doc in nlp.pipe(prepped, batch_size=512):
        tokens = [
            token.lemma_
            for token in doc
            if token.text not in STOP_WORDS_FILTERED
            and token.lemma_ not in STOP_WORDS_FILTERED
            and not token.is_space
            and token.text.strip()
        ]
        text = " ".join(tokens)
        text = restore_tech_tokens(text)
        cleaned.append(re.sub(r"\s+", " ", text).strip())
    return pd.Series(cleaned, index=series.index)


def derive_seniority(title: str) -> str:
    if not isinstance(title, str):
        return "Mid"
    t = title.lower()
    if re.search(SENIOR_KEYWORDS, t):
        return "Senior"
    if re.search(ENTRY_KEYWORDS, t):
        return "Entry"
    return "Mid"


# ── main pipeline ──────────────────────────────────────────────────────────────

def run_preprocessing() -> pd.DataFrame:

    # Step 1 — Load ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("STEP 1 — Load dataset")
    print("=" * 60)
    df = pd.read_csv(INPUT_PATH, low_memory=False)
    print(f"  Loaded: {df.shape[0]:,} rows x {df.shape[1]} cols")
    assert df.shape == (7184, 49), f"Unexpected shape: {df.shape}"

    # Step 2 — Select columns ──────────────────────────────────────────────────
    print("\nSTEP 2 — Select columns")
    df = df[KEEP_COLS].copy()
    print(f"  Retained {len(KEEP_COLS)} columns; dropped {49 - len(KEEP_COLS)} audit-only columns.")

    # Step 3 — Build target ────────────────────────────────────────────────────
    print("\nSTEP 3 — Build target (salary_mid, salary_band, has_salary)")
    df["salary_mid"] = df[["salary_min", "salary_max"]].mean(axis=1)
    df.loc[~df["salary_passes_plausibility_screen"], "salary_mid"] = float("nan")
    df["has_salary"] = df["salary_passes_plausibility_screen"].fillna(False)

    plausible_mask = df["has_salary"]
    df["salary_band"] = pd.NA
    df.loc[plausible_mask, "salary_band"] = pd.qcut(
        df.loc[plausible_mask, "salary_mid"], 3, labels=["low", "medium", "high"]
    )
    print(f"  has_salary==True  : {plausible_mask.sum():,}")
    print(f"  salary_band dist  :\n{df['salary_band'].value_counts().to_string()}")

    # Step 4 — Seniority ───────────────────────────────────────────────────────
    print("\nSTEP 4 — Derive seniority_level from title")
    df["seniority_level"] = df["title"].apply(derive_seniority)
    print(f"  Distribution:\n{df['seniority_level'].value_counts().to_string()}")

    # Step 5 — Missing values ──────────────────────────────────────────────────
    print("\nSTEP 5 — Handle missing values")
    TRACK = ["salary_min", "salary_max", "contract_time", "location_region", "employer"]
    n = len(df)
    print("\n  BEFORE:")
    for col in TRACK:
        miss = df[col].isna().sum()
        print(f"    {col:35s}: {miss:4d} ({miss/n*100:.1f}%)")
    desc_empty = df["description_raw"].isna().sum() + (df["description_raw"].str.strip() == "").sum()
    print(f"    {'description_raw (empty)':35s}: {desc_empty:4d} ({desc_empty/n*100:.1f}%)")

    # apply fixes
    df["contract_time"]   = df["contract_time"].fillna("unknown")
    df["location_region"] = df["location_region"].fillna("unknown")
    df["employer"]        = df["employer"].fillna("unknown")

    empty_desc_mask = df["description_raw"].isna() | (df["description_raw"].str.strip() == "")
    n_dropped = empty_desc_mask.sum()
    if n_dropped:
        df = df[~empty_desc_mask].reset_index(drop=True)
        print(f"\n  Dropped {n_dropped} rows with empty description_raw.")

    n = len(df)
    print("\n  AFTER:")
    for col in TRACK:
        miss = df[col].isna().sum()
        print(f"    {col:35s}: {miss:4d} ({miss/n*100:.1f}%)")

    # Step 6 — Clean text ──────────────────────────────────────────────────────
    print(f"\nSTEP 6 — Clean description text ...")
    df["description_clean"] = clean_descriptions_batch(df["description_raw"])
    print(f"  Done. Sample comparison (row 0):")
    print(f"    RAW  : {str(df['description_raw'].iloc[0])[:120]!r}")
    print(f"    CLEAN: {str(df['description_clean'].iloc[0])[:120]!r}")

    # Step 7 — Standardise ─────────────────────────────────────────────────────
    print("\nSTEP 7 — Standardise")
    df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")
    for col in ["role", "location_region", "location_country", "category_label"]:
        df[col] = df[col].str.strip().str.title()

    dup_count = df["job_id"].duplicated().sum()
    print(f"  job_id duplicates : {dup_count}  (expect 0)")
    assert dup_count == 0, "Duplicate job_ids found!"
    print(f"  created_date dtype: {df['created_date'].dtype}")

    # Step 8 — Validate & export ───────────────────────────────────────────────
    print("\nSTEP 8 — Validate & export")
    assert df["job_id"].is_unique

    final_cols = KEEP_COLS + ["salary_mid", "salary_band", "has_salary",
                              "seniority_level", "description_clean"]
    df = df[final_cols]

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"  Total rows        : {len(df):,}")
    print(f"  has_salary==True  : {df['has_salary'].sum():,}")
    print(f"  salary_band dist  :\n{df['salary_band'].value_counts().to_string()}")
    print(f"\n  Saved to: {OUTPUT_PATH}")
    print(f"  Final shape: {df.shape}")
    return df


if __name__ == "__main__":
    df_out = run_preprocessing()
    print("\nPreprocessing complete.")
