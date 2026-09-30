"""
Merges postings_structured.csv and postings_text.csv into a single master dataset
without any data loss or duplication.
"""

from pathlib import Path
import pandas as pd

def merge_clean_data():
    CLEANED_DIR = Path("data/cleaned")
    struct_path = CLEANED_DIR / "postings_structured.csv"
    text_path = CLEANED_DIR / "postings_text.csv"
    output_path = CLEANED_DIR / "postings_combined.csv"

    print(f"Reading structured data from: {struct_path}")
    df_struct = pd.read_csv(struct_path)
    print(f"  Structured shape: {df_struct.shape}")

    print(f"Reading text data from: {text_path}")
    df_text = pd.read_csv(text_path)
    print(f"  Text shape before deduplication: {df_text.shape}")

    # Deduplicate text data on unique job_id (original pull had 28 cross-role duplicates)
    df_text_dedup = df_text.drop_duplicates(subset=["job_id"], keep="first").copy()
    print(f"  Text shape after deduplication: {df_text_dedup.shape}")

    # Columns to bring from text dataset (including category_name so 100% of all attributes are preserved)
    text_cols = [
        "category_name",
        "description_original",
        "description_clean",
        "description_nostopwords",
        "description_lemmatized",
        "description_word_count",
    ]

    # Perform 1-to-1 inner merge on job_id
    df_combined = df_struct.merge(
        df_text_dedup[["job_id"] + text_cols],
        on="job_id",
        how="inner"
    )

    # Exhaustive verification and integrity checks
    assert len(df_combined) == len(df_struct) == 2472, f"Row count mismatch! Expected 2472, got {len(df_combined)}"
    assert df_combined["job_id"].nunique() == 2472, "Found duplicate job_id in combined dataset!"
    assert df_combined["job_id"].isnull().sum() == 0, "Found null job_id in combined dataset!"
    assert len(df_combined.columns) == 37, f"Expected 37 columns, got {len(df_combined.columns)}"
    assert (df_combined["category_name"] == df_combined["adzuna_category"]).all(), "Category alignment mismatch!"
    assert df_combined["description_original"].isnull().sum() == 0, "Found null in description_original!"
    assert (df_combined["description_word_count"] > 0).all(), "Found invalid word count <= 0!"

    # Save master file
    df_combined.to_csv(output_path, index=False)
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\nSuccessfully generated master dataset: {output_path}")
    print(f"  Total records: {len(df_combined)}")
    print(f"  Total columns: {len(df_combined.columns)} (100% attributes from both structured and text)")
    print(f"  File size    : {file_size_mb:.2f} MB")
    print(f"  Unique job_ids: {df_combined['job_id'].nunique()} (Zero duplicates, Zero data loss)")

if __name__ == "__main__":
    merge_clean_data()
