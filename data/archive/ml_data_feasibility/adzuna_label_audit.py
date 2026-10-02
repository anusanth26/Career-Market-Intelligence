"""
Read-only audit of the CLEAN Adzuna India postings for ML-target feasibility.
No model is trained. Reuses the project's own mapping and dedup code, so the "clean" set is the
same one reported in report/clean_coverage_results.md.

    python data/raw/ml_data_feasibility/adzuna_label_audit.py
Writes data/raw/ml_data_feasibility/adzuna_label_audit.json
"""

import json
import math
import os
import re
import statistics as st
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from analyze_coverage import dedupe_and_cap, norm_text, read_jsonl  # noqa: E402
from role_mapping import compile_rules, map_title  # noqa: E402

RUNS = os.path.join(ROOT, "data", "raw", "adzuna", "runs")
FEAS = "20260929T174139Z_4496f922_feasibility"
DEEP = "20260929T175840Z_b181dc01_deepen"
SEC = "20260929T180809Z_8ad616c4_security_full"

CORE = ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer",
        "Business Analyst", "Product Manager", "Project Manager", "Digital Marketing", "Graphic Designer"]
CONDITIONAL = ["UX Designer", "Financial Analyst"]
SECURITY = ["Security Engineer", "Information Security Analyst", "Cybersecurity Engineer",
            "Information Security Engineer", "Cybersecurity Analyst"]
# which run supplies each role (the run that pulled it completely)
SOURCE_RUN = {**{r: FEAS for r in CORE + ["UX Designer"]}, "Data Analyst": DEEP, "Financial Analyst": DEEP,
              **{r: SEC for r in SECURITY}}

# "manager"/"architect" are ROLE words (Product Manager, Project Manager), not seniority, so they are excluded
SENIOR = r"\b(senior|sr|lead|principal|staff|head|director|vp|vice president|associate director)\b"
JUNIOR = r"\b(junior|jr|intern|internship|trainee|fresher|entry level|graduate|apprentice)\b"
YEARS = re.compile(r"(\d{1,2})\s*(?:\+|plus)?\s*(?:-|to|–)?\s*(\d{1,2})?\s*\+?\s*(?:years|yrs|year)\b", re.I)
BOILER = re.compile(r"(this job is with|inclusive employer|mygwork|please do not contact the recruiter|"
                    r"equal opportunity|we are an? (?:equal|inclusive)|about (?:us|the company|the role))", re.I)
SKILLS = """sql python excel power bi tableau java javascript typescript react angular node.js aws azure gcp docker
kubernetes terraform jenkins git linux spark hadoop kafka airflow snowflake databricks etl tensorflow pytorch
scikit-learn pandas numpy machine learning deep learning nlp statistics sas spss looker qlik salesforce sap oracle
jira agile scrum seo sem google analytics google ads facebook ads photoshop illustrator figma sketch indesign
after effects premiere canva html css c++ c# .net spring django flask rest api microservices ci/cd devops
mongodb postgresql mysql nosql data modeling data warehouse power query dax vba tableau prep alteryx
stakeholder communication leadership roadmap product management project management pmp prince2 budgeting
forecasting financial modeling""".replace("\n", " ").split()
MULTI = ["power bi", "google analytics", "google ads", "facebook ads", "machine learning", "deep learning",
         "after effects", "data modeling", "data warehouse", "power query", "financial modeling", "product management",
         "project management", "ci/cd"]


def skill_list():
    text, out = " ".join(SKILLS), []
    for m in MULTI:
        if m in text:
            out.append(m)
            text = text.replace(m, " ")
    return out + [t for t in text.split() if t]


LEX = skill_list()
LEX_RE = [(s, re.compile(r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])", re.I)) for s in LEX]


def build_clean():
    """Rebuild the clean per-role postings exactly as analyze_coverage.py does (official strict rules)."""
    clean_by_role, cache = {}, {}
    for run in {FEAS, DEEP, SEC}:
        d = os.path.join(RUNS, run)
        manifest = json.load(open(os.path.join(d, "run_manifest.json")))
        cfg = manifest["config_snapshot"]
        rules, settings = compile_rules(cfg["roles"]), cfg["settings"]
        window = manifest["window_start"][:10] + "T00:00:00Z"
        rows, order = [], 0
        for q in read_jsonl(os.path.join(d, "queries.jsonl")):
            for rec in read_jsonl(os.path.join(d, q["records_file"])):
                raw, col = rec["raw"], rec["collection"]
                m = map_title(raw.get("title", ""), rules)
                emp = (raw.get("company") or {}).get("display_name") or ""
                rows.append({
                    "order": order, "id": str(raw.get("id")), "title": raw.get("title", ""),
                    "description": raw.get("description", ""), "created": raw.get("created"),
                    "employer": emp, "employer_norm": norm_text(emp),
                    "salary_min": raw.get("salary_min"), "salary_max": raw.get("salary_max"),
                    "salary_pred": str(raw.get("salary_is_predicted", "")), "variant": col["query_variant"],
                    "query_role": col["query_role"], "mapped_role": m["role"], "in_window": bool(raw.get("created"))
                    and raw["created"] >= window, "location": (raw.get("location") or {}).get("area", []),
                    "contract_time": raw.get("contract_time"), "category": (raw.get("category") or {}).get("label"),
                })
                order += 1
        cache[run] = (rows, settings)
    for role, run in SOURCE_RUN.items():
        rows, settings = cache[run]
        pool = [r for r in rows if r["mapped_role"] == role and r["in_window"]]
        for r in pool:
            r["vkey"] = r["variant"]
        clean, _ = dedupe_and_cap(pool, settings, role, [], defaultdict(Counter))
        clean_by_role[role] = [{**r, "role": role} for r in clean]
    return clean_by_role, cache[FEAS][1]


def quantiles(vals, qs=(0.05, 0.25, 0.5, 0.75, 0.95)):
    if not vals:
        return {}
    v = sorted(vals)
    return {f"p{int(q * 100)}": v[min(len(v) - 1, int(q * len(v)))] for q in qs} | {"min": v[0], "max": v[-1], "n": len(v)}


def main():
    clean_by_role, settings = build_clean()
    core_rows = [r for role in CORE for r in clean_by_role[role]]
    cond_rows = [r for role in CONDITIONAL for r in clean_by_role[role]]
    # security merged family: dedupe again across the five title families
    sec_pool = [r for role in SECURITY for r in clean_by_role[role]]
    sec_rows = list({r["id"]: r for r in sec_pool}.values())
    for r in sec_rows:
        r["role"] = "Security (merged)"
    all_rows = core_rows + cond_rows + sec_rows
    out = {"definition": "clean postings = official strict title rules, dedup, 5% employer cap; India; 90-day window",
           "runs_used": {"core+UX": FEAS, "Data Analyst/Financial Analyst": DEEP, "security families": SEC}}

    # ── A. class distribution and employer structure ─────────────────
    by_role = defaultdict(list)
    for r in all_rows:
        by_role[r["role"]].append(r)
    dist = {}
    for role, rs in by_role.items():
        emp = Counter(r["employer_norm"] for r in rs if r["employer_norm"])
        dist[role] = {"n": len(rs), "distinct_employers": len(emp),
                      "top_employer_share": round(max(emp.values()) / len(rs), 3) if emp else None,
                      "missing_employer": sum(1 for r in rs if not r["employer_norm"])}
    n_core = len(core_rows)
    out["A_class_distribution"] = {
        "per_role": dist, "core_10_total": n_core, "with_conditional_total": len(all_rows),
        "majority_class_share_core": round(max(dist[r]["n"] for r in CORE) / n_core, 3),
        "imbalance_ratio_core_max_over_min": round(max(dist[r]["n"] for r in CORE) / min(dist[r]["n"] for r in CORE), 2),
        "distinct_employers_core": len({r["employer_norm"] for r in core_rows if r["employer_norm"]}),
        "ids_shared_between_roles": len(core_rows) - len({r["id"] for r in core_rows}),
    }

    # ── B. role classification: how circular is it? ──────────────────
    rules = {r["role"]: r for r in compile_rules(json.load(open(os.path.join(ROOT, "config", "roles.json")))["roles"])}
    circ = {}
    for role in CORE:
        rs, rx = by_role[role], rules[role]["_match"]
        hit_desc = sum(1 for r in rs if any(p.search(norm_text(r["description"])) for p in rx))
        title_in_desc = sum(1 for r in rs if norm_text(r["title"]) and norm_text(r["title"]) in norm_text(r["description"]))
        circ[role] = {"n": len(rs), "snippet_matches_own_title_rule_pct": round(100 * hit_desc / len(rs), 1),
                      "full_title_appears_in_snippet_pct": round(100 * title_in_desc / len(rs), 1)}
    tot = len(core_rows)
    out["B_role_classification_circularity"] = {
        "per_role": circ,
        "overall_snippet_matches_own_title_rule_pct": round(sum(c["snippet_matches_own_title_rule_pct"] * c["n"] for c in circ.values()) / tot, 1),
        "overall_full_title_in_snippet_pct": round(sum(c["full_title_appears_in_snippet_pct"] * c["n"] for c in circ.values()) / tot, 1),
        "note": "Labels are a deterministic function of the title (100% by construction). A title-blind model is only "
                "valid if title tokens are removed from the features and the snippet does not restate the title.",
    }

    # ── C. salary ────────────────────────────────────────────────────
    def mid(r):
        vals = [v for v in (r["salary_min"], r["salary_max"]) if v is not None]
        return sum(vals) / len(vals) if vals else None
    sal_all = [r for r in all_rows if mid(r) is not None]
    floor, ceil_ = settings["salary_floor"], settings["salary_ceiling"]
    valid = [r for r in sal_all if floor <= mid(r) <= ceil_ and (r["salary_min"] or 0) >= floor]
    core_sal = [r for r in core_rows if mid(r) is not None]
    core_valid = [r for r in core_sal if r in valid]
    spread = [r["salary_max"] / r["salary_min"] for r in valid if r["salary_min"] and r["salary_max"] and r["salary_max"] != r["salary_min"]]
    per_role_sal = {role: sum(1 for r in by_role[role] if r in valid) for role in by_role}
    emp_sal = Counter(r["employer_norm"] for r in core_valid if r["employer_norm"])
    top5 = sum(v for _, v in emp_sal.most_common(5))
    vals = sorted(mid(r) for r in core_valid)
    bands = {}
    for k in (3, 4):
        cuts = [vals[int(len(vals) * i / k)] for i in range(1, k)] if vals else []
        cnt = Counter(sum(1 for c in cuts if mid(r) >= c) for r in core_valid)
        bands[f"{k}_quantile_bands"] = {"cutpoints": cuts, "class_counts": dict(sorted(cnt.items()))}
    # period/currency sanity: descriptions that mention monthly / LPA / lakh among salaried rows
    txt = [r["description"].lower() for r in core_sal]
    out["C_salary"] = {
        "core_10_clean": len(core_rows), "core_salary_any": len(core_sal), "core_salary_valid_after_floor_ceiling": len(core_valid),
        "core_salary_presence_pct": round(100 * len(core_sal) / len(core_rows), 1),
        "all_13_salary_valid": len(valid), "salary_valid_per_role": per_role_sal,
        "roles_with_at_least_30_salary_labels": sorted(r for r, n in per_role_sal.items() if n >= 30),
        "roles_with_fewer_than_30": sorted(r for r, n in per_role_sal.items() if n < 30),
        "predicted_flag_1_count": sum(1 for r in all_rows if r["salary_pred"] == "1"),
        "salary_mid_quantiles_core_valid": quantiles(vals),
        "range_width_max_over_min_quantiles": quantiles(spread),
        "point_salary_share_pct": round(100 * sum(1 for r in core_valid if r["salary_min"] == r["salary_max"]) / max(1, len(core_valid)), 1),
        "distinct_employers_among_salaried_core": len(emp_sal),
        "top5_employers_share_of_salaried_core_pct": round(100 * top5 / max(1, len(core_valid)), 1),
        "band_class_counts": bands,
        "snippets_mentioning_monthly_pct": round(100 * sum(1 for t in txt if re.search(r"per month|monthly|/month", t)) / max(1, len(txt)), 1),
        "snippets_mentioning_lpa_or_lakh_pct": round(100 * sum(1 for t in txt if re.search(r"\blpa\b|lakh|lac\b", t)) / max(1, len(txt)), 1),
        "currency_field_in_api": False,
        "location_consistency": dict(Counter(r["location"][0] if r["location"] else "?" for r in core_sal)),
    }
    # is salary presence random? compare salary presence between seniority cues and top employer groups
    sen_sal = Counter()
    for r in core_rows:
        c = "senior" if re.search(SENIOR, r["title"].lower()) else "junior" if re.search(JUNIOR, r["title"].lower()) else "unspecified"
        sen_sal[(c, mid(r) is not None)] += 1
    out["C_salary"]["presence_by_title_seniority_cue"] = {
        c: round(100 * sen_sal[(c, True)] / max(1, sen_sal[(c, True)] + sen_sal[(c, False)]), 1) for c in ("senior", "junior", "unspecified")}

    # ── D. seniority (derived from title) ────────────────────────────
    lab, yrs, agree = Counter(), 0, Counter()
    for r in core_rows:
        t = r["title"].lower()
        c = "senior_or_lead" if re.search(SENIOR, t) else "junior_or_entry" if re.search(JUNIOR, t) else "no_title_cue"
        lab[c] += 1
        m = YEARS.search(r["description"])
        if m:
            yrs += 1
            y = int(m.group(1))
            yb = "0-2y" if y <= 2 else "3-6y" if y <= 6 else "7y+"
            agree[(c, yb)] += 1
    out["D_seniority"] = {
        "native_seniority_field_in_adzuna": False,
        "title_cue_distribution_core": dict(lab),
        "title_cue_share_pct": {k: round(100 * v / n_core, 1) for k, v in lab.items()},
        "snippets_with_years_of_experience_pct": round(100 * yrs / n_core, 1),
        "title_cue_vs_years_in_snippet_crosstab": {f"{a}|{b}": v for (a, b), v in sorted(agree.items())},
        "note": "Any seniority label here is derived from the title or snippet, i.e. not a ground-truth field.",
    }

    # ── E. snippet limits / skill detection ──────────────────────────
    per_role_skill = {}
    all_counts = []
    for role in CORE:
        cnts = [sum(1 for _, p in LEX_RE if p.search(r["description"])) for r in by_role[role]]
        all_counts += cnts
        per_role_skill[role] = {"mean_distinct_skills_in_snippet": round(st.mean(cnts), 2),
                                "pct_zero_skills": round(100 * sum(1 for c in cnts if c == 0) / len(cnts), 1),
                                "pct_three_or_more": round(100 * sum(1 for c in cnts if c >= 3) / len(cnts), 1)}
    lens = [len(r["description"]) for r in core_rows]
    out["E_snippet_and_skills"] = {
        "lexicon_size": len(LEX), "per_role": per_role_skill,
        "overall_pct_zero_skills": round(100 * sum(1 for c in all_counts if c == 0) / len(all_counts), 1),
        "overall_pct_three_or_more": round(100 * sum(1 for c in all_counts if c >= 3) / len(all_counts), 1),
        "description_length": quantiles(lens), "truncated_pct": round(100 * sum(1 for r in core_rows if r["description"].rstrip().endswith("…")) / n_core, 1),
        "boilerplate_phrase_in_snippet_pct": round(100 * sum(1 for r in core_rows if BOILER.search(r["description"])) / n_core, 1),
        "boilerplate_in_first_200_chars_pct": round(100 * sum(1 for r in core_rows if BOILER.search(r["description"][:200])) / n_core, 1),
        "caveat": "Lexicon detection recall on full postings is NOT measurable from Adzuna alone (no full text, no gold labels).",
    }

    # ── F. leakage structure for splitting ───────────────────────────
    fam = Counter((r["employer_norm"], norm_text(r["title"])) for r in core_rows if r["employer_norm"])
    in_repeat = sum(v for v in fam.values() if v > 1)
    days = Counter((r["created"] or "")[:10] for r in core_rows)
    weeks = Counter()
    for d, n in days.items():
        weeks[d[:7] + "-w" + str((int(d[8:10]) - 1) // 7 + 1)] += n
    emp_all = Counter(r["employer_norm"] for r in core_rows if r["employer_norm"])
    out["F_leakage_structure"] = {
        "rows_in_repeated_employer_title_families_pct": round(100 * in_repeat / n_core, 1),
        "employers_with_more_than_10_core_postings": sum(1 for v in emp_all.values() if v > 10),
        "largest_employer_share_of_core_pct": round(100 * max(emp_all.values()) / n_core, 2),
        "distinct_employers_core": len(emp_all),
        "created_date_range": [min(days), max(days)], "postings_by_calendar_week": dict(sorted(weeks.items())),
        "share_of_postings_in_last_30_days_of_window_pct": round(100 * sum(v for d, v in days.items() if d >= "2026-08-30") / n_core, 1),
    }
    p = os.path.join(os.path.dirname(__file__), "adzuna_label_audit.json")
    json.dump(out, open(p, "w"), indent=2, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
