"""
Manual labels for the mapping spot-check (reviewer: AI assistant; NOT independently verified by a human).
Rubric (fixed before labelling), same as the earlier audit:
  correct = title clearly names the role; ambiguous = documented synonym/variant that is a materially different or debatable job,
  hybrid title, or people-manager role; incorrect = matched a pattern but the job is a different family.
Anything not listed below was judged correct. Run:  python data/audits/dataset/mapping_spotcheck/make_labels.py
"""
import csv, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
A, X = "ambiguous", "incorrect"
def m(label, code, idx): return {i: (label, code) for i in idx}
LABELS = {  # current samples.json (seed 20261001)
 "Software Engineer": {1: (A, "system_software_hybrid")},
 "Data Analyst": {3: (A, "hybrid_operations_manager")},
 "Data Scientist": m(A, "family:ml_engineer", [1, 4, 5, 6, 15, 17, 18]),
 "Data Engineer": {7: (A, "family:analytics_engineer")},
 "DevOps / Cloud Engineer": {7: (A, "hybrid_backend_cloud"), 9: (A, "data_platform_engineer"), 10: (A, "platform_engineer_generic"), 17: (A, "platform_engineer_generic"), 19: (A, "platform_engineer_generic")},
 "Business Analyst": {4: (X, "security_operations_analyst"), **m(A, "family:product_analyst", [1, 2, 5]), **m(A, "family:systems_functional_analyst", [7, 15])},
 "Product Manager": m(A, "family:product_owner", [1, 3, 4, 5, 6, 11, 12, 13, 18]),
 "Project Manager": {1: (A, "hybrid_delivery_project_manager"), 13: (A, "unclear_domain"), 15: (A, "industrial_construction_domain"), 17: (A, "hybrid_change_specialist"),
                     33: (A, "npdi_engineering_analyst"), 36: (A, "hybrid_portfolio"), 37: (A, "infrastructure_construction_domain"), 45: (A, "heavy_engineering_domain")},
 "Digital Marketing": {2: (X, "teaching_role_faculty"), 15: (X, "sales_role_mentions_digital_marketing"), 7: (A, "content_strategist_agency"), 10: (A, "creative_operations_manager"), 18: (A, "hybrid_developer_seo")},
 "Graphic Designer": {2: (A, "visual_designer_digital"), 10: (A, "hybrid_video"), 15: (A, "creative_designer_generic"), 20: (A, "visual_designer_generic")},
}
# Graphic Designer sample drawn BEFORE the motion-graphics exclusion (samples_pre_gd_fix.json); kept as the evidence for that rule
GD_PRE_FIX = {14: (X, "motion_graphics_designer"), 17: (X, "motion_graphics_designer"), 18: (X, "motion_graphics_designer"),
              **m(A, "hybrid_role", [5, 13]), 2: (A, "visual_designer_digital"), 8: (A, "visual_designer_product"), 12: (A, "visual_designer_product")}
def write(samples, labels, path, only=None):
    rows = []
    for role, items in samples["roles"].items():
        if only and role != only: continue
        for it in items:
            lab, code = labels.get(role, {}).get(it["i"], ("correct", ""))
            rows.append({"role": role, "sample_index": it["i"], "job_id": it["job_id"], "title": it["title"], "mapping_tier": it["tier"], "label": lab, "reason_code": code})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return len(rows)
cur = json.load(open(os.path.join(HERE, "samples.json")))
pre = json.load(open(os.path.join(HERE, "samples_pre_gd_fix.json")))
print(write(cur, LABELS, os.path.join(HERE, "labels.csv")), "labels written")
print(write(pre, {"Graphic Designer": GD_PRE_FIX}, os.path.join(HERE, "labels_graphic_designer_pre_fix.csv"), only="Graphic Designer"), "pre-fix GD labels written")
