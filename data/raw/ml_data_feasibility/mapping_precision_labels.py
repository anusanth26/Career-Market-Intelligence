"""
Gate 4 labels + metrics. Reads samples.json (seed 20260930) produced by mapping_precision_sample.py.

LABELLING RUBRIC (fixed before labelling; judged against the role CONCEPT, not merely against our own synonym list):
  correct   : the title clearly names the role (any seniority, domain prefix, or documented exact synonym of the core job)
  ambiguous : matched via a documented synonym/variant that is a materially different or debatable job family
              (e.g. scrum master, ERP functional analyst, product owner, ML engineer), or a hybrid title, or a people-manager role
  incorrect : the title matched a pattern but the job is a different family (or is meant to be excluded)
Labels below were assigned MANUALLY by the reviewer (an AI assistant) - they are NOT produced or validated by the mapping code and
must be spot-checked by at least one team member (recommended: independent re-label of 15 titles per role, report agreement).
Anything not listed as ambiguous/incorrect below was judged correct. Reason codes allow sensitivity analysis.

    python data/raw/ml_data_feasibility/mapping_precision_labels.py
"""

import csv
import json
import os
from collections import Counter

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)))
samples = json.load(open(os.path.join(HERE, "mapping_precision", "samples.json")))

A, X = "ambiguous", "incorrect"


def many(label, code, idx):
    return {i: (label, code) for i in idx}


PRECISION_LABELS = {
    "Software Engineer": {**many(A, "application_developer_generic", [2, 5, 14]), 44: (A, "manager_role")},
    "Data Analyst": {10: (A, "hybrid_developer"), 27: (A, "security_analyst_domain"), 29: (A, "hybrid_programmer"),
                     37: (A, "hybrid_business_data"), 45: (A, "data_stewardship"), 49: (A, "data_stewardship"), 50: (A, "data_operations")},
    "Data Scientist": {**many(A, "family:ml_engineer", [1, 2, 4, 6, 7, 9, 11, 12, 24, 31, 32, 33, 34, 36, 41]), 35: (A, "hybrid_ai_engineer")},
    "Data Engineer": {2: (A, "manager_role"), 35: (A, "manager_role"), **many(A, "family:analytics_engineer", [3, 6, 25])},
    "DevOps / Cloud Engineer": {**many(A, "platform_engineer_generic", [19, 23, 25]), 37: (A, "sap_basis_admin")},
    "Business Analyst": {31: (X, "physical_security_systems"), 48: (X, "website_security_support"),
                         **many(A, "family:systems_functional_analyst", [1, 2, 3, 6, 7, 8, 10, 11, 13, 16, 17, 19, 20, 32, 34, 45, 47]),
                         **many(A, "family:product_analyst", [9, 12, 18])},
    "Product Manager": {**many(A, "family:product_owner", [1, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 22, 27, 38, 46]), 40: (A, "hybrid_customer_success")},
    "Project Manager": {8: (X, "service_delivery_manager"), 9: (X, "service_delivery_manager"), 43: (X, "interiors_construction_missed_by_exclude"),
                        **many(A, "family:program_manager", [11, 12, 13, 15, 19, 21, 25, 29, 30, 31, 33, 38, 39, 40, 41, 45, 46, 48, 49]),
                        **many(A, "family:delivery_manager", [2, 4, 7, 10, 14]), **many(A, "family:scrum_master", [3, 5, 6]),
                        **many(A, "construction_domain", [28, 47]), 36: (A, "npdi_engineering_analyst")},
    "Digital Marketing": {29: (A, "spam_like_posting"), 46: (A, "hybrid_outbound_monetization"), 49: (A, "hybrid_gtm_engineer")},
    "Graphic Designer": {**many(X, "motion_graphics_designer", [9, 21, 34]), **many(A, "hybrid_role", [5, 12, 25, 30, 31]),
                         **many(A, "creative_designer_generic", [15, 16]), **many(A, "visual_designer_ui_ux", [37, 41, 42]), 46: (A, "motion_graphics_hybrid")},
}
# Sensitivity: which ambiguous families a team could legitimately DEFINE as part of the role (a definitional decision, not evidence)
LENIENT_FAMILIES = {
    "Data Scientist": {"family:ml_engineer"}, "Product Manager": {"family:product_owner"},
    "Project Manager": {"family:program_manager", "family:delivery_manager"},
    "Business Analyst": {"family:systems_functional_analyst"}, "Data Engineer": {"family:analytics_engineer"},
}
# clear false negatives (title denotes the role but was UNMATCHED) and ambiguous unmatched, by sample index
UNMATCHED = {
    "Software Engineer": {"fn": [1, 3, 4, 8, 12, 13], "amb": [14]},
    "Data Analyst": {"fn": [17, 18, 21, 22], "amb": [3, 4, 15, 23, 24]},
    "Data Scientist": {"fn": [3, 9, 10, 11, 15], "amb": [7]},
    "Data Engineer": {"fn": [3, 8, 10, 15], "amb": [1, 13]},
    "DevOps / Cloud Engineer": {"fn": [2, 3, 7, 8, 15], "amb": [11, 14]},
    "Business Analyst": {"fn": [3, 9], "amb": [2, 12, 14, 15, 20]},
    "Product Manager": {"fn": [10, 14], "amb": []},
    "Project Manager": {"fn": [10, 13, 17, 20, 23, 28], "amb": [5, 7, 11, 12, 15, 18, 19, 22]},
    "Digital Marketing": {"fn": [1, 4, 8, 9, 13, 15], "amb": [3, 6, 10, 11, 14]},
    "Graphic Designer": {"fn": [1, 6, 12, 18, 19, 21, 22, 25, 29, 30], "amb": [5, 7, 13, 24, 26]},
}
FN_FIX = {"Software Engineer": "developer titles without the words 'software developer' (Backend/Sr./AI Developer, 'Software Cloud Developer', 'Software Engineering Lead')",
          "Data Analyst": "BI-reporting titles ('BI Reporting Analyst', 'Senior Insights Analyst - Power BI')",
          "Data Scientist": "'Data Science' noun forms ('Data Science Internship', 'Data Science & ML Senior Associate', 'Applied AI Scientist')",
          "Data Engineer": "'Data Engineering' noun forms, 'SSIS Developer (ETL)'",
          "DevOps / Cloud Engineer": "reordered forms ('Senior Engineer, DevOps', 'DevOps / Infrastructure Engineer', 'Cloud Services Engineer')",
          "Business Analyst": "'Business Process Analyst', 'Senior Analyst Business Systems'",
          "Product Manager": "'Digital Product Management - Associate'",
          "Project Manager": "'Project Management' noun forms ('Manager - Project Management', 'Project Management Specialist')",
          "Digital Marketing": "SEO titles other than 'SEO specialist/executive/analyst/manager' ('SEO Expert', 'SEO and Growth Specialist', 'Senior Marketing Executive, Digital Channels')",
          "Graphic Designer": "'Graphic Design ___' noun forms and 'Graphics Designer' (Graphic Design Intern/Specialist/Contractor/Consultant)"}

cfg_scope = json.load(open(os.path.join(HERE, "..", "..", "..", "config", "career_scope.json")))
base = {r["role"]: r["measured_baseline_2026_09_29"] for r in cfg_scope["roles"]}

rows, summary = [], {}
for role, items in samples["precision"].items():
    lab = PRECISION_LABELS[role]
    c = Counter()
    by_tier = {"C": Counter(), "S": Counter()}
    for it in items:
        label, code = lab.get(it["i"], ("correct", ""))
        c[label] += 1
        by_tier[it["tier"]][label] += 1
        rows.append({"role": role, "sample_index": it["i"], "adzuna_id": it["id"], "title": it["title"], "mapping_tier": it["tier"],
                     "retrieved_by": it["retrieved_by"], "label": label, "reason_code": code})
    n = sum(c.values())
    correct, amb, inc = c["correct"], c["ambiguous"], c["incorrect"]
    lenient_extra = sum(1 for i, (l, code) in lab.items() if l == A and code in LENIENT_FAMILIES.get(role, set()))
    b = base[role]
    prec = correct / (correct + inc) if correct + inc else None
    tier_prec = {t: (round(100 * v["correct"] / (v["correct"] + v["incorrect"]), 1) if v["correct"] + v["incorrect"] else None) for t, v in by_tier.items()}
    um = UNMATCHED[role]
    pool = samples["unmatched"][role]["pool_distinct_unmatched_titles"]
    ns = len(samples["unmatched"][role]["sample"])
    summary[role] = {
        "sample_n": n, "correct": correct, "ambiguous": amb, "incorrect": inc,
        "precision_pct": round(100 * prec, 1), "ambiguity_rate_pct": round(100 * amb / n, 1),
        "strict_precision_pct_ambiguous_as_incorrect": round(100 * correct / n, 1),
        "lenient_precision_pct_if_team_defines_family_as_in_role": round(100 * (correct + lenient_extra) / (correct + lenient_extra + inc), 1) if lenient_extra else None,
        "lenient_families": sorted(LENIENT_FAMILIES.get(role, [])),
        "precision_by_tier_pct": {"canonical": tier_prec["C"], "synonym": tier_prec["S"]},
        "tier_counts": {"canonical_n": sum(by_tier["C"].values()), "synonym_n": sum(by_tier["S"].values())},
        "ci95_precision_wilson_pct": None,
        "unmatched_sample_n": ns, "unmatched_pool_distinct_titles": pool,
        "unmatched_clear_false_negatives": len(um["fn"]), "unmatched_ambiguous": len(um["amb"]),
        "unmatched_fn_rate_in_sample_pct": round(100 * len(um["fn"]) / ns, 1),
        "est_distinct_false_negative_titles_in_pool": round(pool * len(um["fn"]) / ns),
        "false_negative_pattern": FN_FIX[role],
        "clean_n": b["clean"], "canonical_clean_n": b["canonical_title_clean_n"],
        "gate_precision_ge_90": prec >= 0.90, "gate_clean_ge_400": b["clean"] >= 400, "gate_canonical_ge_300": b["canonical_title_clean_n"] >= 300,
    }
    # Wilson interval for precision
    k, m = correct, correct + inc
    if m:
        z = 1.96
        p = k / m
        d = 1 + z * z / m
        centre = (p + z * z / (2 * m)) / d
        half = z * ((p * (1 - p) / m + z * z / (4 * m * m)) ** 0.5) / d
        summary[role]["ci95_precision_wilson_pct"] = [round(100 * (centre - half), 1), round(100 * (centre + half), 1)]
    summary[role]["passes_all_three"] = all(summary[role][g] for g in ("gate_precision_ge_90", "gate_clean_ge_400", "gate_canonical_ge_300"))
    summary[role]["false_positive_examples"] = [it["title"] for it in items if lab.get(it["i"], ("", ""))[0] == X][:4]
    summary[role]["ambiguous_examples"] = [it["title"] for it in items if lab.get(it["i"], ("", ""))[0] == A][:4]
    for k2, v2 in [("fn", "false_negative"), ("amb", "unmatched_ambiguous")]:
        for i in um[k2]:
            it = samples["unmatched"][role]["sample"][i - 1]
            rows.append({"role": role, "sample_index": f"U{i}", "adzuna_id": it["id"], "title": it["title"], "mapping_tier": "",
                         "retrieved_by": it["query"], "label": v2, "reason_code": ""})
with open(os.path.join(HERE, "mapping_precision", "labels.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
json.dump({"seed": samples["seed"], "rubric": __doc__, "summary": summary}, open(os.path.join(HERE, "mapping_precision", "summary.json"), "w"), indent=1)
print(f"{'role':26}{'n':>3}{'corr':>5}{'amb':>4}{'inc':>4}{'prec%':>7}{'CI95':>14}{'amb%':>6}{'strict%':>8}{'lenient%':>9}{'Ctier%':>7}{'Stier%':>7}  FNrate%  clean canon  pass")
for r, s in summary.items():
    print(f"{r:26}{s['sample_n']:>3}{s['correct']:>5}{s['ambiguous']:>4}{s['incorrect']:>4}{s['precision_pct']:>7}{str(s['ci95_precision_wilson_pct']):>14}{s['ambiguity_rate_pct']:>6}"
          f"{s['strict_precision_pct_ambiguous_as_incorrect']:>8}{str(s['lenient_precision_pct_if_team_defines_family_as_in_role']):>9}"
          f"{str(s['precision_by_tier_pct']['canonical']):>7}{str(s['precision_by_tier_pct']['synonym']):>7}  {s['unmatched_fn_rate_in_sample_pct']:>6}  {s['clean_n']:>5}{s['canonical_clean_n']:>6}  {s['passes_all_three']}")
