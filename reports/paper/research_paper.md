# What Indian Job Postings Say About Pay, Skills and Careers: Calibrated Salary Ranges, Skill Pay Associations and Pay-Disclosure Classification from Naukri Postings

**Team 03, 23CSE452 Business Analytics**

**Evidence status of this document.** Every number about our own work comes from the executed project notebooks (`career_market_intelligence`, `text_mining`, `combined_insight`, `method2_time_series`). Every number about other work comes from the abstract or a summary page that we read, not from the full paper, and is marked as such in Section 2. Metrics differ across studies, so the benchmark tables say plainly where a comparison is direct and where it is only a reference point.

---

## Abstract

Job boards publish what employers want and, sometimes, what they will pay, but in India little published work turns that into numbers a job seeker, recruiter or trainer can act on. We study 14,085 full-text postings from Naukri, of which 10,780 map to one of ten business and technology roles and 1,358 state a usable yearly salary range. We ask five questions. (1) How accurately can a posting's pay be estimated for employers the model has never seen, and how honest can the stated range be? (2) Which skills go with higher pay once role and experience are held fixed? (3) Can a description alone identify a role? (4) Can a description predict whether the employer states pay at all? (5) Which skills would move a posting from one role to another?

A tuned gradient-boosting model reaches a test R² of 0.767 and a mean error of ₹3.8 lakh on 257 postings from unseen employers (role median: 0.335 and ₹5.6 lakh); calibrated by conformalized quantile regression, an 80% range held the stated salary for 83.3% of those postings. Experience is the one input the model cannot lose (cross-validated R² falls by 0.109 without it), and the description adds about 0.02. Of 170 skills tested for a pay association, 17 survive false-discovery control, and their ranking is unstable on held-out employers (Spearman about 0.28). A linear model reads the role from the description with 0.90 accuracy (macro-F1 0.88) and from skills alone with 0.90, and a role-fit model run backwards moves 48.1% of postings to a chosen target role by adding five or fewer skills, and 84.3% by adding ten or fewer, using only skills the target role really asks for. Only 12.9% of role-matched postings state pay, 76.5% of postings come from employers that never do, and the description predicts disclosure with ROC-AUC 0.87 and F1 0.52. Inside a role, employers that stay silent do not clearly point to different pay (−3.6%, interval −7.2% to +2.4%). We release the notebooks, a dashboard and a benchmark against the closest prior work, and we state where our evidence is weak.

**Keywords:** job postings, salary prediction, conformal prediction, text mining, skill premiums, pay transparency, role fit, India.

---

## 1. Introduction

A job seeker asks what an offer should pay. A recruiter asks what a role costs in a city. A training institute asks which skills are worth teaching. Postings answer these questions in part, because they list skills and sometimes a salary, but three things make them hard to use. First, most postings do not state pay. Second, the stated pay is a range, and a single number hides how wide it is. Third, skill lists mix tools with filler, and correlations between skills and pay can simply reflect that better-paid roles ask for different things.

This project works on those three problems for one Indian job board. Its contributions are:

1. **A salary model with an honest range.** A boosted model with employer-grouped validation, and a conformal wrapper whose coverage is checked on employers it never saw, including where it fails (Section 5.1).
2. **A cautious skill-pay analysis.** Three estimators, false-discovery control, a placebo test and a stability test, which together show that most apparent premiums are not reliable (Section 5.2).
3. **Two classification tasks on the description.** Role identification, with checks that the model does not just read the title; and prediction of whether a posting states pay, which we did not find studied from posting wording (Sections 5.3 and 5.4).
4. **Career switch between roles.** A role-fit model used backwards to list the skills that move a posting toward another role, tested against a simple baseline and shown beside each skill's pay association (Section 5.5).
5. **Search interest set against demand and pay.** Twenty skills placed on three signals, plus a test of whether code skills lost search interest after AI coding assistants appeared (Section 5.6).
6. **A benchmark and gap analysis against prior work, and a working dashboard** (Sections 2, 6, 7 and 8).

---

## 2. Related work and benchmarking

We group the closest work by the question it answers. For each group we give what the study found, where we read it, and how directly it can be compared with ours.

### 2.1 Predicting pay from posting text

Bana (2022) fine-tunes BERT on the text of about 800,000 postings linked to salaries and tests it on the remaining 200,000, from the Greenwich.HR aggregator. A news summary reports that the model "accurately predicted the associated salaries 87% of the time" and that the words "explain 87% of the variation in salaries", against 69% when only titles and locations are used. The summary does not define accuracy, does not reconcile the two readings of 87%, and gives no error in rupees or dollars [S1, S2]. Marinescu and Wolthoff (2020), as cited in the same AEA abstract, find that titles and words explain a very large share of pay (a coefficient of determination close to 90%) [S1].

*Our comparison.* Our test R² is 0.767 and our cross-validated R² is 0.696 on 1,358 postings, about three orders of magnitude less data, with a metric that is defined (variance of log salary explained, on employers not seen in training). Text adds little for us: R² is 0.673 without it and 0.696 with a 50-component summary of the description. The qualitative result agrees (words help, and titles and places alone help less); the numbers are not comparable because Bana's metric is undefined in the source we read and the datasets differ in size, country and pay definition.

### 2.2 Skills and pay in postings

Deming and Kahn (2018) link the skill requirements in US postings to wages within occupations and firms, and report that cognitive and social skill requirements go with higher pay [R1]. Ao, Horvath, Sheng, Song and Sun (2022) compare skill-categorisation methods on a UK dataset of over one million advertisements by how much wage variation each explains: three dictionary-based methods explain "only about 20%" and LDA topic modelling about 45% [S3].

*Our comparison.* In the same spirit, we compare skill measures by how much they add. Topic shares alone explain R² 0.366 (ridge) and 0.360 (XGBoost) of log salary on our data, and a 50-component summary of the text explains 0.52. These text-only figures include role and seniority wording, so they are an upper bound on what skills alone carry. Once experience and role are known, adding skills from employer tags or from the text lifts cross-validated R² by about 0.01 at most (0.012 for the random forest; Section 5.2). Direction agrees with Ao et al. (bottom-up text measures capture more than a skill list); magnitudes are not comparable because their regressions and data differ.

### 2.3 Pay transparency and selection in posted wages

Batra, Michaud and Mongey (2023, forthcoming in *Labour Economics*) use the universe of US online postings and report that about 14% contain any wage information (6% a point wage, 8% a range), that the average range spans about 28% of its midpoint, that disclosure follows the occupation-wage gradient, that high-wage firms are more opaque, and that none of the 20 largest posting firms states wages in more than 2% of its posts [S4]. A Minneapolis Fed note on the same data adds that middle-wage occupations are about twice as likely to state a wage and that over half of postings come from firms that never do [S5]. Hazell and Taska (2025, *American Economic Review*) build on posted wages to study how rigid pay for new hires is [R2].

*Our comparison.* This is the closest direct benchmark. In our role-matched data 12.9% of postings state a yearly range (12.1% of all scraped postings), close to the US 14%. Our ranges are wider: the median stated maximum is 1.67 times the minimum, which is a span of 50% of the midpoint against their 28%. Concentration is stronger: 76.5% of our postings come from employers that never state pay, and among employers with at least five postings 67.7% never do. The US studies document who discloses; they do not, in the sources we read, ask whether the wording of a posting predicts disclosure. That is the gap in Section 7.

### 2.4 Skill extraction and role or occupation classification

Skill extraction work such as SkillSpan and weak-supervision methods tags skill spans in postings [S6, S7]; a 2026 preprint uses contrastive learning on about 14 million Chinese vacancies to find explicit and implicit skills and map them to ESCO [S8]. Job-title normalisation (JobBERT, VacancySBERT) learns title representations from skills and descriptions [S9, S10]. A 2025 preprint classifies advertisements into UK and US standard occupation codes and reports about 61% accuracy at the finest tier and 72% at the next [S11].

*Our comparison.* We do not extract new skills; we match a fixed vocabulary of the 200 most common employer tags whole-word in the text and check the matching against the tags (the text pattern finds 79% to 89% of the postings an employer tagged for the eight most-asked skills). Our role task has ten coarse roles taken from the title, so our 0.90 accuracy and the 61% to 72% of the SOC study answer different questions: ours is ten broad classes, theirs hundreds of fine ones. They should not be compared.

### 2.5 Calibrated ranges

Conformalized quantile regression (Romano, Patterson and Candès, NeurIPS 2019) wraps any quantile regressor so that intervals have finite-sample coverage whatever the data distribution and adapt their width to the input; they report shorter intervals than competing conformal methods across eleven datasets [S12].

*Our comparison.* We apply it to interval-valued salary labels. At an 80% target the range held 83.3% of 257 test postings (95% Wilson interval 78.2% to 87.3%), the uncalibrated quantile bands held 70.4%, and a role-median baseline with a conformal band also held 83.3% but was about twice as wide (median top-to-bottom ratio 6.25 against 3.27). The guarantee is marginal; coverage by role runs from 58.8% (Software Engineer, 17 test postings) to 96.9% (Graphic Designer), which is what the theory allows.

### 2.6 Career switch and skill recourse

Actionable recourse in linear classification (Ustun, Spangher and Liu, 2019) asks for the lowest-cost change a person can make to flip a decision [S13]. A study of employability applies counterfactual explanations to a Flemish public-employment dataset of about 1.4 million rows, averaging 11 skills per position, and searches greedily for the skills a rejected applicant would need for a job [S14].

*Our comparison.* We apply the same idea to moves between ten roles, with a greedy search on a linear classifier of 200 skills, a measured flip rate, and a naive baseline, and we show each suggested skill's pay association. In the source we read, the employability study does not cover role-to-role moves or pay.

### 2.7 India

For India we found: a World Bank and CSAE working paper on Indian job adverts and artificial intelligence, 2010 to 2019, which measures AI demand and task content [S15]; a 2025 framework that mines CS and IT skill requirements from Indian job advertisements and reports no quantitative results in its abstract [S16]; and a 2021 student project on AI demand using Naukri postings. We did not find an India-specific study that predicts pay from full-text postings with employer-grouped validation, calibrated ranges, or an analysis of who states pay.

### 2.8 Summary of the benchmark

| Study (source) | Data | Task and their result | Ours | Comparable? |
|---|---|---|---|---|
| Bana 2022 [S1, S2] | US, about 1M postings, BERT | Salary from text; "87%" (undefined); titles and locations only, 69% | Salary R² 0.767 test, 0.696 CV; 1,358 postings, India | No: metric undefined, data three orders larger |
| Ao et al. 2022 [S3] | UK, >1M ads | Skill method judged by wage variation explained: dictionaries about 20%, LDA about 45% | Text-only R²: topics 0.36, 50-dim summary 0.52; skills add at most 0.01 over controls | Direction only |
| Batra et al. 2023 [S4] | US, all online posts | 14% state any wage; range span 28% of midpoint; firm concentration | 12.9% state a range; span 50% of midpoint; 76.5% of postings from never-disclosers | Yes, closest |
| Romano et al. 2019 [S12] | 11 benchmark datasets | Finite-sample coverage, adaptive width | 83.3% at an 80% target on 257 unseen-employer postings; by role 59% to 97% | Method yes, data no |
| Rony and Patman 2025 [S11] | UK/US job ads, SOC codes | Accuracy 61% (finest tier), 72% (next) | 0.90 accuracy, ten coarse roles | No: different granularity |
| Counterfactuals in employability [S14] | Flanders, about 1.4M rows | Skills to add to become suitable for a job | Role-to-role moves, 48.1% within five skills and 84.3% within ten, with pay | Idea yes, task differs |
| Deming and Kahn 2018 [R1] | US postings | Skill requirements associated with wages within occupation | 17 of 170 skills survive correction; rank stability about 0.28 | Direction only |

---

## 3. Data

**Source.** Full-text postings from the Naukri job board, collected with a commercial scraper. A posting has a title, company, location, work mode, experience range, employer-tagged skills, industry, the full description, and sometimes a salary field. Naukri's terms may restrict redistribution, so the raw postings are not published and the dashboard's data files are for local use only.

**Role.** One of ten roles (Software Engineer, Data Analyst, Data Scientist, Data Engineer, DevOps / Cloud Engineer, Business Analyst, Product Manager, Project Manager, Digital Marketing, Graphic Designer), assigned from the title alone by fixed rules. Titles that match two roles, an exclusion rule or no role are dropped.

**Funnel.** Two notebooks start from the same scrape and end at slightly different salaried sets, because the text-mining notebook also removes descriptions that repeat.

| Step | Salary notebook | Text-mining notebook |
|---|---|---|
| Scraped | 14,085 | 14,085 |
| Mapped to one of ten roles | 11,589 | 11,589 |
| With a real description (at least 50 characters), identical descriptions kept once | not applied | 10,780 |
| State a salary | 1,457 | 1,389 |
| After screens (see below) | 1,358 postings, 1,017 employers | 1,348 postings, 1,016 employers |

The screens are the same in both: a range that starts at 0 is open-ended and dropped, a midpoint under ₹100,000 a year looks monthly and is dropped, and repeated title, company and range are kept once. The 10,780 postings are the corpus for every text task (topics, role and disclosure classification, recourse).

**Labels.** *Pay* is the midpoint of the stated yearly range, modelled on the log scale; the range itself is the interval-valued label. *States pay* means the salary field holds a yearly range; 12,376 of 14,085 raw postings have none, of which 11,972 are marked "Not disclosed", 352 "Unpaid" and 52 show a monthly amount that we do not treat as a yearly range.

**Splits.** Every evaluation groups by employer so that no company is in both training and test: five-fold grouped cross-validation, and a held-out test of 257 postings from 204 companies against 1,101 training postings from 813 companies for the salary model, and 2,064 postings from companies not in training for the text tasks.

---

## 4. Methods

### 4.1 Text and skills

Descriptions are lower-cased, links and addresses removed, whitespace collapsed; nothing is stemmed. Skills are the 200 most common employer tags that appear in at least 20 postings, and a posting asks for a skill if the employer tagged it or the description names it with a whole-word pattern (short ambiguous tags such as `r`, `go` and `ml` count from the tag only). Features for models are TF-IDF word weights (unigrams, stop words removed, words in at least 5 and at most half of postings, sublinear counts, up to 5,000 words), a 50-component truncated SVD of those weights, eight LDA or NMF topic shares, K-means clusters, and six skill bundles found by Louvain community detection on a skill co-occurrence network built from lift (Blei et al. 2003; Blondel et al. 2008) [R3, R4].

### 4.2 Salary model and range

Log salary is regressed on role, seniority from the title, city group, work mode, industry, experience (midpoint, its square, span), skills, a text summary and employer attributes. Four models and two baselines are compared under identical folds: Ridge, random forest, XGBoost (Chen and Guestrin 2016), and a stack of the three, against a global and a role median [R5]. XGBoost is tuned by randomised search inside the training postings only. The range uses conformalized quantile regression: gradient-boosting quantile models at the 10th and 90th percentiles are fitted on a proper training part, and the conformal score from a separate calibration part (split by employer) widens them to the target coverage [S12].

### 4.3 Pay associations of skills

For each of 170 skills with at least 25 salaried postings we estimate the log-salary difference for postings that ask for it, with role, experience, seniority, city, work mode and industry as controls, in three ways: (a) one skill at a time by least squares with company-clustered standard errors; (b) all skills together in one ridge regression with company-bootstrap intervals; (c) double machine learning by partialling out, with boosted models and five-fold company-grouped cross-fitting (Chernozhukov et al. 2018) [S17]. Significance is judged after Benjamini-Hochberg false-discovery control at 10% [R6]. A placebo test shuffles the skill flags; a stability test re-estimates on 80%, 70%, 60% and 50% of the companies and on the rest.

### 4.4 Role fit

Ten models, including a majority-class baseline, are compared (logistic regression, linear SVM, ridge classifier, SGD and naive Bayes on the description, and k-NN, random forest, XGBoost and a neural network on 70 compact text-mining features) by macro-F1 under grouped cross-validation, with representation, text length, class-weight and split-ratio ablations. Two controls check that the model is not reading the title: removing the words that name a role, and removing the title's own words.

### 4.5 Pay-disclosure classification

The label is whether the posting states a yearly range. Salary amounts and words such as "CTC", "LPA" and "salary" are removed from the text first (one run keeps them, to show it does not matter). Seven models and a "never states" baseline are compared by ROC-AUC, average precision, and accuracy, precision, recall and F1 for the stating class at a cut-off chosen on the other folds, because with 12.9% positives accuracy alone is uninformative. Words and phrases that separate the groups are ranked by the weighted log-odds ratio with an informative Dirichlet prior (Monroe, Colaresi and Quinn 2008) [R7]. A selection check estimates, for every posting, the pay the text points to using a ridge model fitted on the postings that state pay, and compares employers that state and do not state pay inside each role.

### 4.6 Career switch (skill recourse)

A multinomial logistic regression on the 200 skill indicators is trained on the training companies. For a posting and a target role, the search adds the unasked skill that most increases the target role's score lead over its closest rival, repeats, and stops when the target is the top role or after ten additions, following the idea of actionable recourse for linear classifiers [S13]. Only feasible additions are allowed: skills that at least 10% of the target role's postings ask for, and not skills that are role names (for example `data engineer`). We added this limit after seeing that the unrestricted search flips the classifier through rare, heavily weighted skills (for example `google analytics` on the way to Data Engineer, asked by 1% of Data Engineer postings), which no one could use as advice. It is evaluated on every test posting that the classifier reads as its own role, for all 90 ordered role pairs, against a baseline that adds the target role's most common skills the posting lacks.

### 4.7 Search interest and the combined view

Google Trends interest for India over five years is collected weekly for 20 skills, in batches of five with a shared anchor term so that batches can be put on one scale. Skills are labelled rising, stable or declining from the five-year change and a Mann-Kendall test; forecasts use naive, exponential smoothing, ARIMA and Holt-Winters with rolling-origin backtests and conformal intervals; seasonality uses STL [R8, R9, R10]. To test whether code skills lost interest after AI coding assistants appeared, five code skills are compared with seven tool, platform and SEO skills around the release date by interrupted time series and by a difference-in-differences whose p-value comes from all 792 ways of choosing five treated skills from twelve. The combined view places each skill by employer demand (share of postings), search-interest change, and pay association.

---

## 5. Results

### 5.1 Salary estimation and calibrated ranges

Cross-validated results on the training postings (five folds grouped by employer, R² on log salary):

| Model | R² | Mean error | Within 30% of stated |
|---|---|---|---|
| Stacking (Ridge + random forest + XGBoost) | 0.704 | ₹424,418 | 53.3% |
| XGBoost | 0.695 | ₹432,934 | 51.8% |
| Ridge | 0.671 | ₹460,377 | 47.5% |
| Random forest | 0.671 | ₹450,964 | 51.4% |
| Role median (baseline) | 0.372 | ₹588,538 | 35.7% |
| Global median (baseline) | −0.007 | ₹775,145 | 20.0% |

The fold-to-fold spread of R² is about 0.05, so stacking and XGBoost are tied and Ridge is only 0.03 behind: most of the signal is additive. Tuning XGBoost changed R² from 0.695 to 0.696. On the 257 held-out postings the tuned XGBoost model reaches R² 0.767, a mean error of ₹377,083 and 59.9% of estimates within 30% of the stated salary, against 0.335, ₹559,582 and 36.6% for the role median. Predictions are pulled toward the middle: the highest stated salaries are mostly under-predicted.

**What the model uses.** Removing experience lowers cross-validated R² by 0.109, the description by 0.023, skills by 0.006, and every other group by 0.003 or less. Shuffling a group on the test postings gives the same order (experience 0.61, description 0.23, everything else under 0.01). A 500-character limit costs 0.019 of R² (0.677 against 0.696 for the full text), and removing pay amounts from the text changes it by 0.002, so the text does not leak the answer.

**Ranges.** At an 80% target the conformalized range held 83.3% of test salaries, the uncalibrated quantile bands 70.4%, and a role-median band with a conformal width 83.3% at about twice the width (Table below). At a 90% target the conformalized range held 96.1%.

| 80% target | Coverage | Median top-to-bottom ratio |
|---|---|---|
| Conformalized quantile regression | 83.3% | 3.27 |
| Quantile bands without calibration | 70.4% | 2.34 |
| Role median plus conformal band | 83.3% | 6.25 |

By role, coverage is 58.8% for Software Engineer (n = 17), 63.6% for Data Scientist (n = 11), 72.2% for Product Manager (n = 18), 75.0% for Business Analyst (n = 16), and 96.9% for Graphic Designer (n = 32); by experience, 76.1% for 5 to 8 years and 78.7% for 8 to 12 years against 84.6% to 93.8% elsewhere. The marginal guarantee holds; the conditional one does not, and the small roles have too few test postings to say more.

### 5.2 Which skills go with pay

On controls alone, cross-validated R² is 0.666 to 0.671 across four learners. Adding employer tags, skills from the text, or both moves it by 0.012 at most (the random forest) and sometimes lowers it (ridge with tags: 0.666 to 0.633); adding topic shares or the 50-component text summary lifts it to 0.675 to 0.701 (the spread across folds is 0.064). On the held-out test, XGBoost scores 0.714 on controls alone, 0.723 with selected skills, 0.726 with skills from tags or text, and 0.714 with all text features; the differences are inside the noise.

Of 170 skills, 32 have a nominal p-value below 0.05 by least squares, about 8.5 expected by chance; 15 survive false-discovery control. Double machine learning finds 31 nominal and 8 after correction; the ridge intervals exclude zero for 25 (uncorrected). The three estimators rank skills similarly (Spearman 0.77 to 0.94) and agree on sign for 74%. In total 17 skills have a clear association in at least one estimator. The largest positive double-ML values are bash (+26%), product management (+25%), networking (+23%), performance marketing (+23%), analytical skills (+18%), scrum (+15%) and agile (+12%); the largest negative are off-page optimisation (−19%), graphic designer (−19%), CorelDraw (−18%), video editing (−16%), project planning (−12%) and SEO (−12%). Python (+8%) and SQL (+4%) are not distinguishable from zero: they are everywhere.

**How far to trust these.** A placebo test with shuffled flags produces about 0.2 false discoveries per run against 15 real ones. But estimating on a random 80% of companies and again on the other 20% gives a rank agreement of only about 0.28 and 75% to 80% sign agreement, so the exact percentages are unreliable and the direction is weakly supported. Raw gaps are mostly experience and role: video editing looks 99% lower with no controls and 16% lower with full controls.

### 5.3 Role fit from the description

On the 2,064 test postings from companies not in training, a linear model reads the role with accuracy 0.897 and macro-F1 0.881 (guessing the largest role: 0.198 and 0.033). Cross-validated macro-F1 is 0.890 for logistic regression and 0.889 for a linear SVM; the four models on compact text-mining features reach 0.839 to 0.874 and naive Bayes 0.829. The model is not reading the title: 94% of descriptions contain at least one word of their own title, yet removing the title's words leaves accuracy at 0.896 and macro-F1 at 0.881, and removing every role-naming word lowers cross-validated macro-F1 from 0.889 to 0.862. Length matters: the first 500 characters give 0.839 and the first 200 give lower still. The employer's skill tags alone reach macro-F1 0.80, so the description carries more. The roles that blur are Business Analyst with Data Analyst, Product Manager and Project Manager, and Software Engineer with Data Engineer and DevOps. In 367 of 10,780 postings (3.4%) a model that did not see the company puts at least 70% on a different role than the title names (8.3% of Business Analyst titles).

### 5.4 Who states the pay

Only 1,389 of 10,780 role-matched postings (12.9%) state a yearly range, so predicting "does not state" for every posting is 87.1% accurate and finds nothing.

| Model | ROC-AUC | Precision | Recall | F1 |
|---|---|---|---|---|
| Logistic regression, words and attributes | 0.882 | 0.415 | 0.688 | 0.518 |
| Logistic regression, words | 0.871 | 0.440 | 0.629 | 0.518 |
| Linear SVM, words | 0.863 | 0.435 | 0.598 | 0.504 |
| MLP on 100 SVD components | 0.851 | 0.404 | 0.623 | 0.490 |
| Complement naive Bayes, words | 0.839 | 0.399 | 0.546 | 0.461 |
| XGBoost, posting attributes | 0.819 | 0.351 | 0.575 | 0.435 |
| Logistic regression, role only | 0.593 | 0.157 | 0.649 | 0.253 |
| Always "does not state" | 0.500 | 0 | 0 | 0 |

On 2,064 held-out postings from unseen companies the word model scores ROC-AUC 0.871 and F1 0.552. Attributes add almost nothing to the words, and the representation hardly matters (F1 0.501 to 0.528 across nine variants, including bigrams, binary presence, vocabulary size and leaving salary figures in; compressing the words by 50, 100 or 200 SVD components first gives 0.509, 0.516 and 0.518). Length matters: the first 500 characters give F1 0.422 against 0.518 for the full text, because the cues sit in the closing boilerplate. Marketing and advertising vocabulary leans toward stating pay (the role effect: Digital Marketing postings state pay 19.5% of the time, Software Engineer postings 5.6%), and boilerplate such as "company website", "job posting" and "disclaimer" leans toward silence.

**It is largely an employer habit.** 76.5% of postings come from companies that never state a salary in these data, and 85.5% of the postings that do come from companies that state one in at least half of theirs; among the 260 companies with at least five postings, 67.7% never do and 8.5% usually do.

**Does silence bias the salary results?** For every posting we estimate the pay its text points to. Inside the same role, employers that stay silent point to 3.6% lower pay, with a company-bootstrap interval from −7.2% to +2.4%, which includes zero. The overall medians differ (₹10.3 lakh silent, ₹8.8 lakh stating) only because the role mix differs. Weighting each stated salary by the inverse of its estimated probability of being stated moves role medians by 0% to 23%, but the effective sample falls from 1,348 to 734, so we treat this as a bound on the size of the problem, not a correction.

### 5.5 Career switch between roles

A classifier on 200 skill indicators places 90.3% of the 2,064 test postings in the right role (macro-F1 0.888), as many as the whole description and more than the employer tags alone (83.7%). Across all 90 role moves and 16,767 posting-moves, with additions limited to skills the target role really asks for, the search brings a posting to the target role within five added skills in 48.1% of cases and within ten in 84.3%, with a median of five skills. The baseline that adds the target's most common missing skills from the same list manages 29.2% and 61.7%, with a median of six. Without the feasibility limit the search reaches 64.7% and 93.1% (median four), but through rare skills; we report the limited version because its suggestions are ones a person could act on. Neighbouring roles are about three skills apart: Product Manager to Business Analyst flips within five skills in 92% of postings, Product Manager to Project Manager in 89%, Project Manager to Product Manager in 86% and DevOps / Cloud to Software Engineer in 82%. Data Analyst to Data Engineer takes a median of five (53% within five, 90% within ten), with suggestions such as big data, PySpark, CI/CD and ETL. Distant roles take six or seven skills and about half or fewer flip within ten (Digital Marketing to DevOps / Cloud: 50%). A flip means the classifier reads the posting as the target role; it says nothing about being hired.

### 5.6 Search interest, demand and pay

Of 20 skills, 3 are rising (Deep Learning, Google Cloud, Machine Learning), 5 stable and 12 declining; six have trends too small to judge. Search interest is attention, not hiring. Python and SQL fell 34% and 56% in search interest yet are each asked for in about a quarter of postings, which fits skills becoming assumed knowledge; Machine Learning is the one skill high on all three signals (12.6% of postings, +40% search interest, +21% pay association by the combined notebook's definition, +14% by double ML). On the quadrant rule the combined view labels 1 skill hot, 7 opportunity, 6 avoid and 6 trend-unreliable.

No forecasting method beats the naive forecast on rolling-origin backtests (median MASE 1.035 for naive, 1.076 for exponential smoothing, 1.126 for ARIMA, 1.115 for Holt-Winters; the Wilcoxon p-values against naive are 0.40 to 0.88). Conformal intervals with a nominal 80% level covered 86.4% to 89.5% of 574 forecasts for naive, smoothing and ARIMA and 78.6% for Holt-Winters, against 81.8% for ARIMA's own interval.

**Did AI assistants lower interest in code skills?** After the November 2022 release, code skills lost about 0.32 log points (about 27%) more interest than the controls, and only 3 of 792 possible groupings give a gap that low or lower (p = 0.005). No skill drops sharply at the release; instead every code skill was rising before and bends down afterwards (slope changes of −35% to −56% a year), while some controls bend too. The gap is largest in 2025, not at the release, so the date is wrong for ChatGPT itself and the result is better read as a later or slower effect. It cannot separate AI from other causes.

---

## 6. Discussion against the benchmarks

**Agreement.** (i) Words help predict pay but add less than experience and role (Bana; Ao et al. in direction). (ii) Posted pay is scarce and concentrated in few employers, and mid-level and templated postings differ in who discloses (Batra et al.): our India shares are close to the US ones. (iii) Conformal calibration repairs under-covering quantile bands at the cost of width (Romano et al.), and the guarantee is marginal.

**Differences.** (i) Our ranges are wider than the US ranges (span 50% against 28% of the midpoint). (ii) Disclosure here is more concentrated by employer than the US picture, though our firm counts are small (260 firms with five or more postings). (iii) We find no reliable skill premium ranking on held-out employers, a weaker result than the headline of earlier skill-and-wage studies, which may reflect our sample size, employer-grouped validation, and the strict correction, not an absence of premiums.

**What our checks add.** Grouping by employer, a role-median baseline, a placebo test, and a stability test each reduced a result that would look stronger without it: random splits would score higher; uncorrected tests would flag twice as many skills (32 against 15); and an ungrouped coverage claim would hide that the range is too narrow for some roles.

---

## 7. Gaps and what this work contributes

Gaps are stated as what we did not find in the sources we read; that is not proof that nothing exists.

| # | Gap | Evidence | What we did | What remains |
|---|---|---|---|---|
| G1 | No India-focused study predicting pay from full-text postings with employer-grouped validation and a calibrated range | India sources found cover AI demand or skill mining without such pay models [S15, S16] | Salary model and conformalized range on Naukri, with coverage by role | One board, one snapshot, small test set (257) |
| G2 | Whether posting wording predicts pay disclosure is not studied in the pay-transparency papers we read | They report disclosure by occupation, wage level and firm [S4, S5] | Disclosure classifier, F1 0.52, ROC-AUC 0.87, with words and a selection check | Other boards and countries; causal reasons for silence |
| G3 | Interval-valued salary labels are rarely modelled as ranges with guaranteed coverage | Salary work reports point error [S1, S2] | Midpoint model with a conformal range, and its failure by role | Conditional coverage; modelling both ends of the range |
| G4 | Skill suggestions for moves between roles are not shown with their pay association | Employability counterfactuals target a job, not role moves or pay [S14] | Role recourse with flip rates, a baseline, and pay associations | Cost of learning a skill; validation with real career moves |
| G5 | Three signals (employer demand, search interest, pay) are rarely put on one map | Related work uses one or two | Quadrant view of 20 skills | Search interest is attention, not hiring; one snapshot |
| G6 | Skill-premium estimates are rarely stress-tested | Many studies report coefficients without placebo or stability checks | Three estimators, false-discovery control, placebo, stability | Rank agreement on held-out employers is only about 0.28 |

---

## 8. Practical use

| Who | Decision | Use of this work | Caution |
|---|---|---|---|
| Job seeker or student | Is this offer fair? Which skills to learn? Which role can I move to? | Estimate and 80% range for a profile; where an offer sits among similar postings; missing skills for a target role; skills that move a role | The range was too narrow for some roles; premiums are associations, not what a skill would add for one person |
| Recruiter or HR | What does this role pay here, and how reliable is the benchmark? | Median and spread for role, city and experience; coverage by role | Stated salaries come from a minority of employers; treat a benchmark as a sample and report its size |
| Training institute | Which skills to teach? | Bridge skills between neighbouring roles; skills with a clear association | The pay figures are rough; most skills have no clear association |
| Analyst or policy maker | How open is the market? | Disclosure rate by role and firm; search interest against demand | A salaried-posting count overstates openness; search interest is not hiring |

The accompanying dashboard (a Next.js application reading JSON files written by the notebooks) has five sections: an overview with shared filters (role, city, experience, work mode), a pay page (estimate a posting, check an offer, benchmark a role, model accuracy and range reliability), a skills page (demand, interest and pay on one map, pay associations, the skill network, a skill lookup and a skill planner), a careers page (the skill recourse tool and its evidence), and a data and method page (the dataset with the model's results on any slice, who states pay, and the method). Panels computed in the notebooks, such as premiums and trends, are tagged as not responding to the filters.

---

## 9. Threats to validity and limitations

- **One board, one snapshot.** Results describe postings on one Indian board at one time; changes over time cannot be studied. Search-interest data and postings cover different periods.
- **Selection.** Only 12.9% of postings state pay and they come from a minority of employers. The inverse-probability check corrects only for what the text and attributes show.
- **Labels from titles.** Roles come from rules on titles. In 3.4% of postings the description points elsewhere; title inflation and unusual titles are not modelled.
- **Associations are not causes.** Skill premiums, the AI break test and the recourse results describe patterns in wording and pay. Reading as a role is not being hired for it.
- **Small test sets.** 257 salary test postings give a coverage interval of about ±5 points and 11 to 33 postings per role; role-level results are noisy.
- **Unstable premiums.** Skill-premium ranks agree weakly between employer halves (about 0.28).
- **Skill matching.** Whole-word matching of a fixed vocabulary misses implicit skills and aliases not in the list; two notebooks differ for a few skills because their alias lists differ (Machine Learning +21% in one, +14% to +16% in the other).
- **Google Trends** returns a sample and was queried for broad terms; the original pulls used for the analysed series were not saved, so the validation was repeated on fresh pulls (the classes of 13 of 20 skills agree between plain-word and topic-ID queries, and the fresh topic-ID pull correlates 0.97 on median with the analysed series).
- **Data terms.** Scraped postings may be restricted by the board's terms. They are not redistributed here.
- **Benchmarks.** Prior-work figures come from abstracts and summaries; metrics differ; a number in Section 2 is a reference point unless marked comparable.

---

## 10. Future work

1. Repeat the collection over time to test whether premiums, disclosure and search interest are stable, and to replace the single-snapshot assumption.
2. Add other boards and a second country to test whether the disclosure results are an Indian feature.
3. Model both ends of the stated range, and test conditional coverage methods that adapt by role.
4. Learn skills from the text, not a fixed vocabulary, with a contrastive or span-based extractor, and compare with the dictionary approach.
5. Validate recourse with real career moves, where the cost and order of learning matter.
6. Replace the keyword match with embeddings for the title-versus-work comparison.

---

## 11. Conclusion

Postings can give an Indian job seeker or recruiter a pay estimate for an unseen employer that is within 30% for six in ten postings, with a range that held for about four in five, provided the range is read with its failures by role. Experience dominates; the description adds a little; most skill premiums are not reliable. The wording of a posting tells you a good deal about the role and also about whether the employer will state pay at all, which depends more on the employer than on the job. A few added skills separate neighbouring roles. These results sit beside, and mostly agree with, the closest prior work, and they leave open the questions in Section 7.

---

## Reproducibility

The four notebooks run in order; each writes the aggregates the dashboard reads. All models use a fixed seed (42), ties in skill counts are broken by name so column order does not depend on hash order, and every split groups by employer. The raw postings and the Google Trends pulls are not distributed. Required packages are in `requirements.txt`. Scripts: `scripts/collect_trends.py` (Google Trends, with a `--plain` option for plain-word queries), `scripts/role_mapping.py` (role rules from `config/roles.json`).

---

## References

**Sources read for the benchmark (abstract or summary page only)**

- [S1] Bana, S. (2022). *work2vec: Using Language Models to Understand Wage Premia.* AEA 2022 preliminary programme. https://www.aeaweb.org/conference/2022/preliminary/paper/6yd4YYky
- [S2] Stanford HAI (2022). *Words matter: text in online job postings can predict salaries.* https://hai.stanford.edu/news/words-matter-text-online-job-postings-can-predict-salaries
- [S3] Ao, Horvath, Sheng, Song and Sun (2022). *Skill requirements in job advertisements: a comparison of skill-categorization methods based on explanatory power in wage regressions.* arXiv:2207.12834. https://arxiv.org/abs/2207.12834
- [S4] Batra, H., Michaud, A. and Mongey, S. (2023). *Online Job Posts Contain Very Little Wage Information.* NBER Working Paper 31984; forthcoming in *Labour Economics*. https://www.nber.org/papers/w31984
- [S5] Federal Reserve Bank of Minneapolis (2026). *Sparse, vague and potentially selected: assessing wage data from online job listings.* https://www.minneapolisfed.org/article/2026/sparse-vague-and-potentially-selected-assessing-wage-data-from-online-job-listings
- [S6] (2022). *SkillSpan: Hard and Soft Skill Extraction from English Job Postings.* arXiv:2204.12811. https://arxiv.org/abs/2204.12811
- [S7] (2022). *Skill Extraction from Job Postings using Weak Supervision.* arXiv:2209.08071. https://arxiv.org/abs/2209.08071
- [S8] *Artificial Intelligence and Skills: Evidence from Contrastive Learning in Online Job Vacancies.* arXiv:2601.03558. https://arxiv.org/abs/2601.03558
- [S9] Decorte et al. (2021). *JobBERT: Understanding Job Titles through Skills.* arXiv:2109.09605. https://arxiv.org/abs/2109.09605
- [S10] *VacancySBERT: the approach for representation of titles and skills for semantic similarity search in the recruitment domain.* arXiv:2307.16638. https://arxiv.org/abs/2307.16638
- [S11] Rony and Patman (2025). *Standard Occupation Classifier: A Natural Language Processing Approach.* arXiv:2511.23057 (preprint). https://arxiv.org/abs/2511.23057
- [S12] Romano, Y., Patterson, E. and Candès, E. (2019). *Conformalized Quantile Regression.* NeurIPS. arXiv:1905.03222. https://arxiv.org/abs/1905.03222
- [S13] Ustun, B., Spangher, A. and Liu, Y. (2019). *Actionable Recourse in Linear Classification.* FAT*. arXiv:1809.06514. https://arxiv.org/abs/1809.06514
- [S14] *Unveiling the Potential of Counterfactuals Explanations in Employability.* arXiv:2305.10069. https://arxiv.org/abs/2305.10069
- [S15] Stapleton, K. *AI and Services-Led Growth: Evidence from Indian Job Adverts.* World Bank / CSAE working paper (slides and summary read only).
- [S16] Singh, Kanaujia and Singh (2025). *Data to Decisions: A Computational Framework to Identify Skill Requirements from Advertorial Data.* arXiv:2503.17424. https://arxiv.org/abs/2503.17424
- [S17] Chernozhukov, V. et al. (2018). *Double/Debiased Machine Learning for Treatment and Structural Parameters.* Econometrics Journal 21(1), C1-C68. arXiv:1608.00060. https://arxiv.org/abs/1608.00060

**Standard references (cited from the bibliographic record; check pages before formal submission)**

- [R1] Deming, D. and Kahn, L. B. (2018). Skill Requirements across Firms and Labor Markets: Evidence from Job Postings for Professionals. *Journal of Labor Economics* 36(S1), S337-S369.
- [R2] Hazell, J. and Taska, B. (2025). Downward Rigidity in the Wage for New Hires. *American Economic Review* 115(12).
- [R3] Blei, D., Ng, A. and Jordan, M. (2003). Latent Dirichlet Allocation. *Journal of Machine Learning Research* 3, 993-1022.
- [R4] Blondel, V. et al. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, P10008.
- [R5] Chen, T. and Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *KDD*.
- [R6] Benjamini, Y. and Hochberg, Y. (1995). Controlling the False Discovery Rate. *Journal of the Royal Statistical Society B* 57(1), 289-300.
- [R7] Monroe, B., Colaresi, M. and Quinn, K. (2008). Fightin' Words: Lexical Feature Selection and Evaluation for Identifying the Content of Political Conflict. *Political Analysis* 16(4), 372-403.
- [R8] Mann, H. (1945). Nonparametric tests against trend. *Econometrica* 13, 245-259; Kendall, M. (1975). *Rank Correlation Methods.*
- [R9] Cleveland, R. et al. (1990). STL: A Seasonal-Trend Decomposition Procedure Based on Loess. *Journal of Official Statistics* 6(1), 3-73.
- [R10] Hyndman, R. and Koehler, A. (2006). Another look at measures of forecast accuracy. *International Journal of Forecasting* 22(4), 679-688.
- [R11] Marinescu, I. and Wolthoff, R. (2020). Opening the Black Box of the Matching Function: The Power of Words. *Journal of Labor Economics* 38(2) (cited here as reported in [S1]).
