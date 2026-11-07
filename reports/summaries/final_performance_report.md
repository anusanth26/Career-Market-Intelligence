# Final Model Performance Evaluation

Source: `scripts/model_results.py` (output in `tableau_dashboard/extracts/`). Standard models (31 structured features) retrained with the saved settings on the 1,153 salary-labelled postings from 497 employers.

| Task | Employer-grouped 5-fold CV | Majority baseline | Stratified 80/20 holdout | Majority baseline |
|---|---|---|---|---|
| Salary band (low / medium / high) | 46.9% (macro-F1 0.444) | 33.6% | 50.2% (macro-F1 0.480) | 36.8% |
| Above / below median | 65.5% (macro-F1 0.650) | 49.3% | 73.2% (macro-F1 0.732) | 48.5% |

The grouped CV keeps a company out of both train and test, so it is the fairer estimate for unseen postings. The holdout shares employers between train and test and runs optimistic.

An earlier version of this report (65.8% binary, 51.1% band) came from scripts that zeroed the seniority feature, matched skills inside other words, and scored on rows the model had trained on. Those numbers and the matching figures in `reports/eda/` should not be used.
