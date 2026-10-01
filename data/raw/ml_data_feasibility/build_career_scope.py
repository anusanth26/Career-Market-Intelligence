"""
Builds config/career_scope.json (the dataset-design specification) from:
  - config/roles.json                                         (mapping rules already used in the audits)
  - data/raw/ml_data_feasibility/design_support_audit.json    (measured per-role facts)
  - data/raw/ml_data_feasibility/adzuna_label_audit.json      (salary / seniority / snippet facts)
  - the coverage_results.csv files of the 2026-09-29 runs     (per-variant marginal clean counts)
Measured numbers are copied programmatically, never typed by hand. Design decisions (definitions, dropped
variants, thresholds) are declared below with their justification.

    python data/raw/ml_data_feasibility/build_career_scope.py
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "data", "raw", "adzuna", "runs")

roles_cfg = {r["role"]: r for r in json.load(open(os.path.join(ROOT, "config", "roles.json")))["roles"]}
support = json.load(open(os.path.join(HERE, "design_support_audit.json")))
labels = json.load(open(os.path.join(HERE, "adzuna_label_audit.json")))

# ── design decisions (each carries its evidence) ─────────────────────────────────────────────
DEFS = {
    "Software Engineer": {
        "definition": "Builds and maintains software applications or services. Any seniority.",
        "ambiguous_examples": ["Software Engineer in Test / SDET (excluded by rule)", "Security Software Engineer", "Embedded Software Engineer"],
        "drop": {"software development engineer": "0 new clean postings in the audit (all duplicates of 'software engineer'); the SDE title still maps via the regex when returned by another query"},
        "medium_confidence_variants": ["application developer"],
    },
    "Data Analyst": {
        "definition": "Analyses data to produce reports and insights. Titles 'data analyst', 'BI analyst', 'business intelligence analyst'.",
        "ambiguous_examples": ["Data Analyst / Business Analyst (ambiguous_multi)", "Analyst - Data Analytics (unmatched)", "Senior Data Management Analyst (unmatched)"],
        "drop": {"reporting analyst": "adds 2 clean postings for 6 API calls; returns Regulatory/Tax/Record-to-Report analysts (manual title inspection)"},
        "medium_confidence_variants": [],
    },
    "Data Scientist": {
        "definition": "Builds statistical / machine-learning models. Includes machine learning engineer and applied scientist titles.",
        "ambiguous_examples": ["Lead Machine Learning Engineer (MLOps) (engineering-leaning)", "Data Scientist/Digitalization Engineer"],
        "drop": {},
        "medium_confidence_variants": ["machine learning engineer"],
    },
    "Data Engineer": {
        "definition": "Builds data pipelines and platforms (ETL, warehouses, big data).",
        "ambiguous_examples": ["Data Engineering [T500-...] (unmatched, role name not a title)", "Senior Analytics Engineer"],
        "drop": {},
        "medium_confidence_variants": ["analytics engineer"],
    },
    "DevOps / Cloud Engineer": {
        "definition": "Builds and operates cloud infrastructure, CI/CD and reliability tooling.",
        "ambiguous_examples": ["AI Platform Engineer", "Cloud Engineer-II", "Data Platform Engineer (unmatched)"],
        "drop": {},
        "medium_confidence_variants": ["platform engineer"],
    },
    "Business Analyst": {
        "definition": "Elicits requirements and analyses business processes/systems. Includes IT business analyst titles.",
        "ambiguous_examples": ["Workday HCM Functional Analyst (ERP-functional)", "Finance Systems Analyst (D365)", "Vice President, Product Analyst"],
        "drop": {},
        "medium_confidence_variants": ["systems analyst", "functional analyst", "product analyst"],
    },
    "Product Manager": {
        "definition": "Owns product strategy and roadmap. Includes product owner titles.",
        "ambiguous_examples": ["Data & Analytics Sales Product Owner", "Product Marketing Manager (unmatched)"],
        "drop": {},
        "medium_confidence_variants": ["product owner"],
    },
    "Project Manager": {
        "definition": "Plans and delivers projects/programmes. Includes programme manager, delivery manager and scrum master titles.",
        "ambiguous_examples": ["Scrum Master (agile role, not a manager of projects)", "Project Manager - Construction (excluded by rule)", "Digital Marketing Project Manager (ambiguous_multi)"],
        "drop": {},
        "medium_confidence_variants": ["program manager", "delivery manager", "scrum master"],
    },
    "Digital Marketing": {
        "definition": "Plans and runs online marketing (SEO, paid, performance, social).",
        "ambiguous_examples": ["Senior Marketing Executive, Digital Channels (unmatched)", "Creative Designer (Performance Marketing) (ambiguous_multi)"],
        "drop": {},
        "medium_confidence_variants": [],
    },
    "Graphic Designer": {
        "definition": "Produces visual/graphic design work. Includes visual designer and creative designer titles.",
        "ambiguous_examples": ["Motion Graphic Designer (video/motion; see added exclude)", "UI/UX & Graphic Designer (ambiguous_multi)"],
        "drop": {},
        "medium_confidence_variants": ["creative designer"],
        "add_exclude": ["\\bmotion graphics? designer\\b"],
        "add_exclude_reason": "manual sample showed 'Motion Graphic Designer' entering the role; motion/video design has a different skill set",
    },
    "UX Designer": {
        "definition": "Designs user experience / interfaces for digital products. Includes product designer titles.",
        "ambiguous_examples": ["Product Design Engineer (unmatched)", "Product Designer (may be industrial design)"],
        "drop": {},
        "medium_confidence_variants": ["product designer"],
    },
    "Financial Analyst": {
        "definition": "Financial planning, reporting and analysis. Includes FP&A and investment analyst titles.",
        "ambiguous_examples": ["Financial Plan & Analysis Analyst (unmatched by strict rule; matched in the sensitivity config)", "Financial Reporting Analyst (unmatched)"],
        "drop": {"finance analyst": "Adzuna stems finance~financial: returned the identical 587 postings, 0 new clean"},
        "medium_confidence_variants": ["investment analyst"],
    },
}
SECURITY_FAMILY = ["Security Engineer", "Information Security Analyst", "Cybersecurity Engineer", "Information Security Engineer", "Cybersecurity Analyst"]

CORE = ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer",
        "Business Analyst", "Product Manager", "Project Manager", "Digital Marketing", "Graphic Designer"]
DOMAIN_OF = {r: roles_cfg[r]["domain"] for r in roles_cfg}
SOURCE_RUN = {r: support["per_role"][r]["source_run"] for r in support["per_role"]}

# variant-level marginal clean counts from the audit runs
variant_clean = {}
for run in set(SOURCE_RUN.values()):
    for row in csv.DictReader(open(os.path.join(RUNS, run, "analysis", "coverage_results.csv"))):
        if row["level"] == "variant":
            variant_clean[(run, row["canonical_role"], row["query_variant"])] = {
                "api_count": row["api_count"], "raw": row["raw_count"], "title_matched": row["title_match_count"],
                "marginal_clean": row["clean_count"]}


def variants_for(role):
    d = DEFS.get(role, {})
    med = set(d.get("medium_confidence_variants", []))
    out = []
    for v in roles_cfg[role]["variants"]:
        q = v if isinstance(v, str) else v["query"]
        if q in d.get("drop", {}):
            continue
        out.append({"query": q, "search_param": "title_only", "confidence_tier": "medium" if q in med else "canonical",
                    "measured_2026-09-29": variant_clean.get((SOURCE_RUN[role], role, q))})
    return out


def dropped_for(role):
    d = DEFS.get(role, {})
    return [{"query": q, "reason": why, "measured_2026-09-29": variant_clean.get((SOURCE_RUN[role], role, q))}
            for q, why in d.get("drop", {}).items()]


def role_entry(role, status):
    c, s = roles_cfg[role], support["per_role"][role]
    d = DEFS[role]
    exclude = c["exclude"] + d.get("add_exclude", [])
    sal = labels["C_salary"]["salary_valid_per_role"].get(role)
    return {
        "role": role, "domain": c["domain"], "status": status, "country": "in",
        "definition": d["definition"],
        "query_variants": variants_for(role), "dropped_variants": dropped_for(role),
        "include_patterns": {"canonical_pattern": c["match"][0], "synonym_patterns": c["match"][1:]},
        "exclude_patterns": exclude, "exclude_patterns_added_vs_roles_json": d.get("add_exclude", []),
        "added_exclude_reason": d.get("add_exclude_reason"),
        "ambiguous_title_examples": d["ambiguous_examples"],
        "measured_baseline_2026_09_29": {
            "source_run": s["source_run"], "api_count_primary_variant": s["api_count_primary_variant"],
            "raw_rows_own_queries": s["raw_rows_own_queries"], "title_matched_rows": s["title_matched_rows"],
            "clean": s["clean"], "yield_clean_per_raw": s["yield_clean_per_raw"],
            "near_dup_rate_of_unique_ids_pct": s["near_dup_rate_of_unique_ids_pct"],
            "distinct_employers": s["distinct_employers"], "top_employer_share_pct": s["top_employer_share_pct"],
            "effective_number_of_employers": s["effective_number_of_employers_1_over_sum_share_sq"],
            "canonical_title_share_pct": s["mapping_tier_canonical_title_pct"],
            "canonical_title_clean_n": round(s["clean"] * s["mapping_tier_canonical_title_pct"] / 100),
            "description_ge_200_chars_pct": s["description_ge_200_chars_pct"],
            "salary_valid_labels": sal, "last_7_days_inflow_lower_bound": s["last_7_days_inflow_clean_lower_bound"],
            "pages_used": s["pages_used_to_collect"], "variants_capped_by_record_limit": s["variants_capped_by_record_limit"],
            "note": "Counts are for the official STRICT rules in config/roles.json (before the exclude/variant edits in this spec)",
        },
    }


spec = {
    "spec_version": "1.0-draft", "created": "2026-09-30", "status": "DESIGN - awaiting team acknowledgement; no production collection started",
    "generated_by": "data/raw/ml_data_feasibility/build_career_scope.py from measured audits",
    "rubric_constraint": "Primary dataset must be collected by the team via API/scraping. No pre-built datasets (Kaggle/UCI/GitHub/Hugging Face) as a primary source.",
    "sources": {
        "adzuna_api": {"role": "current employer demand (job postings)", "raw_dir": "data/raw/adzuna/"},
        "google_trends": {"role": "temporal search-interest signal", "raw_dir": "data/raw/trends/", "never_mixed_into_adzuna_records": True},
        "onet_esco": {"role": "reference taxonomies for skill/occupation normalisation only (not job-posting data)",
                      "licences": {"O*NET 31.0": "CC BY 4.0 (onetcenter.org/license_db.html)", "ESCO v1.2.1": "content licensed CC BY 4.0 (esco.ec.europa.eu copyright notice)"}},
    },
    "collection_rules": {
        "country": "in", "search_param": "title_only", "max_days_old_baseline": 90, "max_days_old_incremental": 7,
        "sort_by": "date", "results_per_page": 50, "window": "whole calendar days (verified 2026-09-29)",
        "role_label_source": "posting title only (config mapping rules), never the query and never the description",
        "raw_fields": ["id", "title", "description", "company.display_name", "location.display_name", "location.area", "created",
                       "salary_min", "salary_max", "salary_is_predicted", "contract_type", "contract_time", "category.label", "category.tag",
                       "redirect_url", "latitude", "longitude", "adref"],
        "collector_added_provenance": ["run_id", "collected_at", "source", "country", "query_variant", "query_role", "page", "position"],
        "api_limits_from_terms_of_service": {"per_minute": 25, "per_day": 250, "per_week": 1000, "per_month": 2500,
                                             "self_imposed_pace_seconds_between_calls": 2.6},
    },
    "domains": [
        {"domain": "Technology & Data", "status": "core", "roles": ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer"]},
        {"domain": "Business, Finance & Management", "status": "core", "roles": ["Business Analyst", "Product Manager", "Project Manager", "Digital Marketing"]},
        {"domain": "Media & Design", "status": "core", "roles": ["Graphic Designer"],
         "caveat": "One firm role; domain-level conclusions are weak until UX Designer is promoted"},
    ],
    "roles": [role_entry(r, "core") for r in CORE],
    "conditional_roles": [role_entry("UX Designer", "conditional"), role_entry("Financial Analyst", "conditional")],
    "conditional_family": {
        "name": "Security (merged title families)", "status": "conditional", "domain": "Technology & Data",
        "members": [{"role": r, "query_variants": variants_for(r), "include_patterns": roles_cfg[r]["match"],
                     "overlap_group": roles_cfg[r].get("overlap_group"), "priority": roles_cfg[r].get("priority"),
                     "measured_clean": support["per_role"][r]["clean"], "api_count": support["per_role"][r]["api_count_primary_variant"]} for r in SECURITY_FAMILY],
        "merged_clean_measured": 510, "note": "No single family reaches 400 (best 374). Merging is a team decision, not applied automatically.",
    },
    "promotion_rule_conditional_to_core": {
        "rule": "A conditional role is promoted only when, after incremental collection and the same QC gates, clean >= 400 AND canonical-title clean >= 300 AND mapping precision >= 90% on the manual sample.",
        "evidence_path": "Weekly inflow lower bounds measured 2026-09-29: UX Designer 68/week, Financial Analyst 67/week (clean, before dedup).",
    },
    "excluded_domains": {
        "Engineering": "Mechanical 256 / Electrical 210 / Quality 269 clean (exhausted); recall-tolerant sensitivity 396 / 373 / 266 - none reaches 400",
        "Architecture & Construction": "'architect' count is 72.1% IT architects, 2.5% likely building architects",
        "Healthcare": "India title counts 5-154 for 5 of 6 roles (feasibility_analysis.md)",
        "Logistics / Transport / Supply Chain": "India title counts 20-107 (feasibility_analysis.md)",
        "Energy / Environment": "India title counts 4-32 (feasibility_analysis.md)",
    },
    "mapping_rules": {
        "normalisation": "lowercase, strip accents, non-alphanumerics -> single space (scripts/role_mapping.py normalize_title)",
        "statuses": ["matched", "excluded_by_rule", "ambiguous_multi", "unmatched"],
        "confidence_tiers": {
            "high": "title matches the role's canonical pattern (first include pattern)",
            "medium": "title matches a synonym pattern (e.g. product owner, delivery manager, systems analyst)",
            "none": "unmatched / ambiguous_multi / excluded_by_rule are NEVER assigned a role",
        },
        "overlap": "only inside a declared overlap_group (security) by priority; any other multi-role match is ambiguous_multi",
        "unmatched_handling": "kept in raw, listed in variant_title_inspection.csv for periodic review; never forced into a role",
        "language_rule": "flag (do not delete) postings whose description is not predominantly English (one Korean title found in a 12-title sample); decide inclusion at processing time",
        "circularity_guard": "role label = f(title). Any later ML feature set must exclude title tokens and must be checked for the role phrase in the snippet (48.1% of snippets contain the role rule; 27.7% restate the full title)",
    },
    "deduplication": {
        "order": ["exact adzuna id (across queries AND runs)", "near-duplicate key = normalised title + normalised employer + first 150 normalised description chars", "employer cap"],
        "employer_cap_fraction_of_role": 0.05, "cap_applies_after_near_dup": True, "missing_employer_never_capped": True,
        "cross_query": "a posting returned by several title variants is one posting; keep earliest collected_at and record all query_variants that returned it",
        "cross_run": "id seen in a later weekly increment is not new; reposts (new id, same near-dup key) count once, first created date kept",
        "logging": "every removal written with role, employer, reason, kept id",
    },
    "minimum_sample_requirements": {
        "clean_per_core_role_min": 400, "clean_per_role_skill_frequency_floor": 300,
        "canonical_title_clean_min": 300, "distinct_employers_min": 100, "effective_number_of_employers_min": 50,
        "top_employer_share_max_pct": 6, "near_dup_rate_of_unique_ids_max_pct": 20,
        "description_nonempty_min_pct": 99, "description_ge_200_chars_min_pct": 95,
        "mapping_precision_min_pct_on_manual_sample": 90, "manual_precision_sample_size_per_role": 50,
        "salary_descriptive_min_valid_per_role": 30, "salary_model_min_valid_pooled": 750,
        "salary_model_min_per_class": 250, "adzuna_snapshots_min_for_freshness_view": 4,
        "trends_min_weekly_points_per_skill": 260, "trends_min_nonzero_week_share": 0.8,
        "skill_min_postings": 20, "skill_min_share_of_role_pct": 2,
        "justification_file": "report/dataset_design.md section 8",
        "measured_gaps": {"salary_valid_core_now": labels["C_salary"]["core_salary_valid_after_floor_ceiling"],
                          "roles_below_30_salary_labels": labels["C_salary"]["roles_with_fewer_than_30"]},
    },
    "collection_plan": {
        "baseline": {"status": "already collected 2026-09-29 (runs/ directory)", "core_clean": labels["A_class_distribution"]["core_10_total"],
                     "core_pages_used": support["api_budget"]["pages_for_10_core_roles_full_baseline"]},
        "incremental_weekly": {"weeks": 3, "max_days_old": 7, "estimated_calls_per_week": "60-75", "purpose": "fresh postings, salary-label growth, conditional-role promotion"},
        "skill_prevalence_count_probe": {"calls_per_snapshot": "~300 (10 roles x 30 skills, 90-day window)", "snapshots": 2,
                                         "role": "validation/recall signal beside snippet mining; NOT a replacement (title_only denominators include non-role titles)"},
        "requires_before_starting": "written confirmation from Adzuna that academic use may continue beyond the 14-day trial (terms of service)",
    },
}
json.dump(spec, open(os.path.join(ROOT, "config", "career_scope.json"), "w"), indent=2, ensure_ascii=False)
print("wrote config/career_scope.json;", len(spec["roles"]), "core roles,", len(spec["conditional_roles"]), "conditional roles + security family")
