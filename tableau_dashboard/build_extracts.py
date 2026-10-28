"""Builds the CSVs the Tableau workbook connects to. Read-only on the frozen dataset.

    python tableau_dashboard/build_extracts.py

Job descriptions are left out on purpose: the workbook does not need them and the Adzuna
terms on redistributing them are unclear (reports/report/repository_data_exposure.md).
"""
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tableau_dashboard", "extracts")


def p(*parts):
    return os.path.join(ROOT, *parts)


core = pd.read_csv(p("data/final/career_market_core_analysis.csv"))
pre = pd.read_csv(p("data/processed/career_market_preprocessed.csv"),
                  usecols=["job_id", "seniority_level", "salary_mid", "salary_band"])
assert core.job_id.is_unique and pre.job_id.is_unique
postings = core.merge(pre, on="job_id", how="left", validate="one_to_one")
assert len(postings) == len(core)

keep = ["job_id", "title", "role", "domain", "employer_normalized", "location_region", "latitude",
        "longitude", "created_date", "category_label", "contract_time", "seniority_level",
        "salary_min", "salary_max", "salary_mid", "salary_band", "description_length"]
postings = postings[keep].rename(columns={"employer_normalized": "employer"})
postings["has_salary"] = postings.salary_mid.notna()
postings.to_csv(os.path.join(OUT, "postings.csv"), index=False)

pd.read_csv(p("reports/text_mining/skill_demand_by_role.csv")).to_csv(os.path.join(OUT, "skill_demand.csv"), index=False)
pd.read_csv(p("reports/text_mining/cooccurrence_pairs.csv")).to_csv(os.path.join(OUT, "skill_cooccurrence.csv"), index=False)

topics = pd.read_csv(p("reports/text_mining/lda_topic_by_role.csv")).melt(
    id_vars="role", var_name="topic", value_name="pct_of_role")
topics.to_csv(os.path.join(OUT, "topics_by_role.csv"), index=False)

trends = pd.read_csv(p("data/processed/trends_rescaled_IN.csv")).melt(
    id_vars="date", var_name="skill", value_name="interest")
trends.to_csv(os.path.join(OUT, "trends_long.csv"), index=False)

# tidy copies of the model results so Tableau can chart them without pivoting
res = pd.read_csv(os.path.join(OUT, "model_results.csv"))
long = res.melt(id_vars=["task", "evaluation"], value_vars=["accuracy", "majority_baseline_accuracy"], var_name="measure", value_name="value")
long["measure"] = long.measure.map({"accuracy": "Model", "majority_baseline_accuracy": "Guessing"})
long["test"] = long.task.map({"band": "Band", "binary": "Above/below"}) + " - " + long.evaluation.map({"employer_grouped_cv": "unseen employers", "holdout": "holdout"})
long.to_csv(os.path.join(OUT, "model_results_long.csv"), index=False)
fi = pd.read_csv(os.path.join(OUT, "feature_importance.csv"))
fi = fi.sort_values(["task", "importance"], ascending=[True, False]).groupby("task").head(10)
fi["feature"] = fi.feature.str.replace("location_bucket_", "State: ").str.replace("role_", "Role: ").str.replace("skill_", "Skill: ").str.replace("_", " ")
fi.to_csv(os.path.join(OUT, "feature_importance_top10.csv"), index=False)

print(f"postings {postings.shape}, with salary {int(postings.has_salary.sum())}, "
      f"trends {trends.shape}, topics {topics.shape}")
