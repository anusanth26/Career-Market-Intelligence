"""
Manual labels for the mapping spot-check of the BUILT dataset (samples.json, seed 20261002).
Reviewer: AI assistant (manual judgement). NOT independently verified by a human.

Rubric (fixed before labelling; same as the earlier audit):
  correct   = the title clearly names the role
  ambiguous = documented synonym/variant that is a materially different or debatable job, a hybrid title, or a people-manager role
  incorrect = matched a pattern but the job is a different family
Label sources:
  * exact repeated titles (same role, same normalised title) reuse the label given earlier under the same rubric   -> label_source = lookup
  * titles not seen before are labelled manually in MANUAL below                                                   -> label_source = manual
Anything the script cannot label raises an error (no silent defaults).
    python data/audits/dataset/mapping_spotcheck/make_labels.py
"""
import csv, json, os, re, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
A, X, C = "ambiguous", "incorrect", "correct"
def norm(t): return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize("NFKD", t or "").lower()).strip()
def m(label, code, idx): return {i: (label, code) for i in idx}
KNOWN = {}
for f in [os.path.join(ROOT, "data/raw/ml_data_feasibility/mapping_precision/labels.csv"), os.path.join(HERE, "superseded/labels.csv")]:
    for r in csv.DictReader(open(f, encoding="utf-8")):
        if str(r.get("sample_index", "")).startswith("U"): continue
        KNOWN[(r["role"], norm(r["title"]))] = (r["label"], r.get("reason_code", ""))
MANUAL = {  # index -> (label, reason) for titles not seen in earlier audits; unlisted-and-unknown indices are errors
 "Software Engineer": {**m(C, "", [1, 2, 4, 5, 7, 8, 9, 11, 12, 13, 17, 20]), 16: (A, "application_developer_generic_mainframe")},
 "Data Analyst": {**m(C, "", [2, 5, 6, 8, 10, 11, 14, 15, 16]), 17: (X, "data_annotation_crowd_work")},
 "Data Scientist": {**m(C, "", [2, 4, 6, 9, 10, 11, 13, 17, 19]), 7: (A, "family:ml_engineer")},
 "Data Engineer": m(C, "", [4, 5, 8, 11, 12, 15, 17, 18, 19, 20]),
 "DevOps / Cloud Engineer": {**m(C, "", [2, 5, 6, 9, 12, 13, 14, 15, 16, 20]), 1: (A, "manager_role"), 4: (A, "platform_engineer_generic"), 7: (A, "platform_engineer_generic"),
                             10: (X, "salesforce_data_cloud_not_cloud_infrastructure"), 18: (A, "sap_platform"), 19: (A, "manager_role")},
 "Business Analyst": {**m(C, "", [4, 7, 12, 15, 17, 18, 19, 20]), 1: (A, "hybrid_data_business_analyst"), 2: (A, "family:systems_functional_analyst"), 6: (A, "family:product_analyst"),
                      8: (A, "family:systems_functional_analyst"), 10: (A, "family:systems_functional_analyst"), 11: (A, "family:product_analyst"), 14: (A, "key_user_plant_controlling")},
 "Product Manager": {**m(C, "", [3, 4, 5, 7, 8, 14, 20]), **m(A, "family:product_owner", [6, 9, 10, 15, 16])},
 "Project Manager": {**m(C, "", [2, 9, 16, 17, 18, 24, 25, 26, 29, 32, 34, 35, 37, 43, 47]), 8: (A, "hybrid_program_project"), 22: (A, "workplace_facilities"), 30: (A, "energy_construction_domain"),
                     46: (A, "engineering_domain"), 49: (A, "hvac_construction_domain")},
 "Digital Marketing": {**m(C, "", [1, 2, 3, 4, 5, 8, 11, 14, 15, 17, 19, 20]), 9: (A, "account_management_sales"), 10: (A, "vague_ad_no_role"), 12: (A, "spam_like_training_hybrid"),
                       13: (X, "training_ad_not_a_job_title"), 16: (A, "vague_ad_no_role")},
 "Graphic Designer": {**m(C, "", [4, 7, 12]), 10: (A, "environmental_graphics_signage"), 11: (A, "hybrid_fashion"), 20: (A, "hybrid_ai_specialist")},
}
samples = json.load(open(os.path.join(HERE, "samples.json")))
rows, unknown = [], []
for role, items in samples["roles"].items():
    for it in items:
        k = (role, norm(it["title"]))
        if it["i"] in MANUAL.get(role, {}):
            lab, code = MANUAL[role][it["i"]]; src = "manual"
            if k in KNOWN and KNOWN[k][0] != lab: print("NOTE: manual label differs from earlier label for", k, KNOWN[k], (lab, code))
        elif k in KNOWN:
            (lab, code), src = KNOWN[k], "lookup"
        else:
            unknown.append((role, it["i"], it["title"])); continue
        rows.append({"role": role, "sample_index": it["i"], "job_id": it["job_id"], "title": it["title"], "mapping_tier": it["tier"], "label": lab, "reason_code": code, "label_source": src})
if unknown: raise SystemExit(f"UNLABELLED: {unknown}")
with open(os.path.join(HERE, "labels.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), "labels written;", dict(Counter(r["label_source"] for r in rows)))
