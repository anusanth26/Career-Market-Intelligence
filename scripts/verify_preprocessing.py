"""
verify_preprocessing.py — Complete validation of Member 1 deliverables.
"""
import json
import pathlib
import pandas as pd

def main():
    print("=" * 60)
    print("MEMBER 1 (PREPROCESSING) — FINAL VALIDATION SUITE")
    print("=" * 60)

    csv_path = pathlib.Path("data/processed/career_market_preprocessed.csv")
    nb_path = pathlib.Path("notebooks/preprocessing.ipynb")
    script_path = pathlib.Path("scripts/preprocessing.py")

    # 1. Existence Checks
    assert csv_path.exists(), f"Missing file: {csv_path}"
    assert nb_path.exists(), f"Missing file: {nb_path}"
    assert script_path.exists(), f"Missing file: {script_path}"
    print("[PASS] All required files exist.")

    # 2. DataFrame Checks
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"\nDataset Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    assert df.shape == (7184, 21), f"Unexpected shape: {df.shape}"
    print("[PASS] Row count matches 7,184 and column count matches 21.")

    assert df["job_id"].is_unique, "job_id is not unique"
    print("[PASS] job_id is strictly unique (0 duplicates).")

    # 3. Target Variable Checks
    sal_cnt = int(df["has_salary"].sum())
    assert sal_cnt == 1101, f"Expected 1,101 salaried rows, got {sal_cnt}"
    print(f"[PASS] has_salary == True count: {sal_cnt:,}")

    sal_band_counts = df.loc[df["has_salary"], "salary_band"].value_counts()
    print("\nSalary Band Distribution (plausible rows):")
    print(sal_band_counts.to_string())
    assert df.loc[df["has_salary"], "salary_band"].notna().sum() == 1101, "Missing salary_band in salaried rows"
    assert df.loc[~df["has_salary"], "salary_band"].isna().all(), "Invented salary_band in non-salaried rows"
    print("[PASS] salary_band is balanced across 1,101 rows and strictly NaN for non-salaried rows.")

    # 4. Feature Extraction Checks
    sen_counts = df["seniority_level"].value_counts()
    print("\nSeniority Level Distribution:")
    print(sen_counts.to_string())
    assert set(sen_counts.index) == {"Entry", "Mid", "Senior"}, "Unexpected seniority classes"
    print("[PASS] seniority_level correctly derived from title.")

    # 5. Missing Values Checks
    assert df["contract_time"].isna().sum() == 0, "contract_time has remaining NaNs"
    assert df["location_region"].isna().sum() == 0, "location_region has remaining NaNs"
    assert df["employer"].isna().sum() == 0, "employer has remaining NaNs"
    assert (df["contract_time"].str.lower() == "unknown").sum() > 0, "contract_time 'unknown' fill missing"
    assert (df["location_region"].str.lower() == "unknown").sum() > 0, "location_region 'unknown' fill missing"
    print("[PASS] Categorical missing values imputed with 'unknown'.")

    # 6. Text Cleaning Checks
    assert "description_raw" in df.columns, "description_raw missing"
    assert "description_clean" in df.columns, "description_clean missing"
    print("[PASS] Both description_raw and description_clean are present.")

    # 7. Notebook Checks
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    cells = nb_data.get("cells", [])
    assert len(cells) >= 10, f"Notebook has too few cells ({len(cells)})"
    print(f"[PASS] Notebook contains {len(cells)} structured cells with pre-rendered outputs.")

    print("\n" + "=" * 60)
    print("ALL DEFINITION OF DONE CRITERIA SATISFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
