# Tableau dashboard (local demo)

Open Tableau Public, connect to the CSVs in `extracts/` (Text file). Rebuild them with
`python tableau_dashboard/build_extracts.py` and `python scripts/model_results.py`.
`postings.csv` has no job descriptions on purpose.

## Data sources and joins
- `postings.csv` is the main source (7,240 rows; salary on 1,153: filter `has_salary` for salary charts and say so in a caption).
- `skill_demand.csv`, `skill_cooccurrence.csv`, `topics_by_role.csv`, `trends_long.csv`, `model_results.csv`,
  `confusion_matrix.csv`, `feature_importance.csv`: separate sources, no joins. Join on `role` only where noted.

## Pages (set the dashboard size to your projector, e.g. 1920 x 1080)
1. **Overview:** KPIs = COUNTD(job_id), COUNTD(role), COUNTD(employer), median salary_mid, % has_salary. Role bar, created_date line, state map (latitude/longitude).
2. **Salary:** box plot salary_mid by role; bar of median salary_mid by seniority_level; salary_band mix by role (stacked 100%); table of postings.
3. **Skills:** heat map `skill_demand` (role x skill, colour = pct_of_role_postings); bar of `skill_cooccurrence` by lift; `trends_long` lines with a skill parameter.
4. **Model results:** bar of `model_results` accuracy by evaluation with `majority_baseline_accuracy` as a reference line; confusion matrix heat map (task parameter); top-10 `feature_importance`.

## Interactions to wire up
Global filters on postings sheets: role, seniority_level, location_region, contract_time, salary_mid range, created_date.
Dashboard actions: click a role bar to filter every postings sheet; click a state on the map to filter the Salary page.
Parameters: skill picker (page 3), task picker band/binary (page 4), top-N skills.

## Demo order (about 5 minutes)
1. Job seeker: Data Analyst, Entry, Karnataka -> top skills and salary range.
2. Career choice: compare roles by median salary and skill trend (SQL, Python).
3. Evaluator: model page; grouped CV 46.9% band / 65.5% binary against 33.6% / 49.3% baselines; explain why holdout runs higher.
