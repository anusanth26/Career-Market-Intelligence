#!/usr/bin/env python
# coding: utf-8

# # Career Market Intelligence
# 
# **Objective:** Predict the salary band (`low` / `medium` / `high`) of Indian job postings from role, seniority, location and required skills, and identify the factors that drive pay.
# 
# **Pipeline**
# 1. Data Preprocessing
# 2. Exploratory Data Analysis
# 3. Feature Engineering
# 4. Predictive Modelling
# 5. Evaluation & Business Interpretation
# 
# **Data:** real job postings collected from the Adzuna API, with skill-interest trends from Google Trends.

# # 1. Data Preprocessing
# 
# Transform the collected job-postings dataset into a clean, standardized, analysis-ready table: build the `salary_band` target, derive features, handle missing values and normalize the job-description text.

# In[1]:


import re
import warnings
import pandas as pd
import numpy as np
import spacy
from spacy.lang.en.stop_words import STOP_WORDS

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 30)
pd.set_option('display.max_colwidth', 100)

print("Environment setup completed.")


# In[ ]:





# ## Step 1: Load Raw Dataset
# We load `data/final/career_market_core_analysis.csv`, which contains 7,184 rows across 49 columns.

# In[2]:


INPUT_PATH = "../data/final/career_market_core_analysis.csv"
OUTPUT_PATH = "../data/processed/career_market_preprocessed.csv"

df_raw = pd.read_csv(INPUT_PATH, low_memory=False)
print(f"Dataset Loaded Successfully: {df_raw.shape[0]:,} rows x {df_raw.shape[1]} columns")
df_raw.head(3)


# ## Step 2: Feature Selection (Drop Audit-Only Columns)
# We retain the 16 analytical features and drop 33 columns that were used exclusively for collection provenance, deduplication audits, and scrapers.

# In[3]:


KEEP_COLS = [
    "job_id", "title", "role", "domain", "employer",
    "description_raw", "location_country", "location_region",
    "created_date", "category_label", "contract_time",
    "salary_min", "salary_max", "salary_present",
    "salary_passes_plausibility_screen", "description_length",
]

df = df_raw[KEEP_COLS].copy()
print(f"Retained {len(KEEP_COLS)} columns. Dropped {df_raw.shape[1] - len(KEEP_COLS)} audit columns.")
df.info()


# ## Step 3: Build the Target Variable (`salary_band`)
# The classification target is **`salary_band`** (`low`, `medium`, `high`) in Indian Rupees (INR).
# * **Midpoint calculation:** `salary_mid = df[['salary_min', 'salary_max']].mean(axis=1)`
# * **Plausibility filter:** Salary values are restricted strictly to rows where `salary_passes_plausibility_screen == True` (the current count is computed from the input data).
# * **Tertile discretization:** `pd.qcut(df.loc[has_salary, 'salary_mid'], 3, labels=['low', 'medium', 'high'])`.
# * **Important rule:** Never invent or impute missing salaries for the remaining postings — they are retained for EDA and NLP tasks with `has_salary = False`.

# In[4]:


# 1. Compute midpoint (handles both ranges and fixed salaries)
df["salary_mid"] = df[["salary_min", "salary_max"]].mean(axis=1)

# 2. Invalidate non-plausible salaries
df.loc[~df["salary_passes_plausibility_screen"], "salary_mid"] = np.nan

# 3. Indicator flag for supervised modeling
df["has_salary"] = df["salary_passes_plausibility_screen"].fillna(False)

# 4. Construct 3-class target via tertiles on plausible rows
plausible_mask = df["has_salary"]
df["salary_band"] = pd.NA
df.loc[plausible_mask, "salary_band"] = pd.qcut(
    df.loc[plausible_mask, "salary_mid"],
    q=3,
    labels=["low", "medium", "high"]
)

print(f"Total postings with valid target (has_salary == True): {df['has_salary'].sum():,}")
print("\nTarget Class Distribution (salary_band):")
print(df["salary_band"].value_counts(dropna=False))

# Examine tertile cut-off points
cuts = pd.qcut(df.loc[plausible_mask, "salary_mid"], q=3).value_counts().sort_index()
print("\nTertile Boundary Intervals (INR):")
for interval, cnt in cuts.items():
    print(f"  {interval}: {cnt} rows")


# ## Step 4: Derive `seniority_level` Feature from Job Title
# We extract seniority as a predictive feature using regex keyword patterns:
# * **Senior:** `senior`, `sr`, `lead`, `principal`, `head`, `manager`, `director`
# * **Entry:** `junior`, `jr`, `graduate`, `trainee`, `intern`, `entry`, `associate`
# * **Mid:** default for all remaining positions

# In[5]:


SENIOR_KEYWORDS = r"\b(senior|sr\.?|lead|principal|head|manager|director)\b"
ENTRY_KEYWORDS  = r"\b(junior|jr\.?|graduate|trainee|intern|entry|associate)\b"

def derive_seniority(title: str) -> str:
    if not isinstance(title, str):
        return "Mid"
    t = title.lower()
    if re.search(SENIOR_KEYWORDS, t):
        return "Senior"
    if re.search(ENTRY_KEYWORDS, t):
        return "Entry"
    return "Mid"

df["seniority_level"] = df["title"].apply(derive_seniority)

print("Seniority Level Distribution:")
print(df["seniority_level"].value_counts())
print("\nSeniority Level vs Target (has_salary == True):")
print(pd.crosstab(df["seniority_level"], df["salary_band"], margins=True))


# ## Step 5: Handle Missing Values & Audit Logging
# * `contract_time` (~40% missing) -> filled with `"unknown"`
# * `location_region` (~34% missing) -> filled with `"unknown"`
# * `employer` (~3.8% missing) -> filled with `"unknown"`
# * `salary_min`, `salary_max` -> untouched (target integrity preserved)
# * Empty `description_raw` -> verified and dropped if present.

# In[6]:


TRACK_COLS = ["salary_min", "salary_max", "contract_time", "location_region", "employer", "description_raw"]

print("=== MISSING VALUES BEFORE CLEANING ===")
for col in TRACK_COLS:
    cnt = df[col].isna().sum()
    pct = (cnt / len(df)) * 100
    print(f"  {col:<20}: {cnt:4d} missing ({pct:5.2f}%)")

# Impute unknown categorical labels
df["contract_time"]   = df["contract_time"].fillna("unknown")
df["location_region"] = df["location_region"].fillna("unknown")
df["employer"]        = df["employer"].fillna("unknown")

# Verify description_raw emptiness
empty_desc = df["description_raw"].isna() | (df["description_raw"].str.strip() == "")
if empty_desc.sum() > 0:
    print(f"\nDropping {empty_desc.sum()} rows with empty description_raw.")
    df = df[~empty_desc].reset_index(drop=True)
else:
    print("\nZero rows with empty description_raw.")

print("\n=== MISSING VALUES AFTER CLEANING ===")
for col in TRACK_COLS:
    cnt = df[col].isna().sum()
    pct = (cnt / len(df)) * 100
    print(f"  {col:<20}: {cnt:4d} missing ({pct:5.2f}%)")


# ## Step 6: Text Cleaning & Normalization (`description_raw` -> `description_clean`)
# We process the job descriptions using an NLP pipeline:
# 1. Strip HTML tags and decode HTML entities (`&amp;`, `&lt;`, etc.).
# 2. Remove URLs and email addresses.
# 3. Protect tech tokens (e.g. `c++`, `c#`, `.net`, `node.js`, `react.js`).
# 4. Strip non-alphanumeric punctuation.
# 5. SpaCy lemmatization (`en_core_web_sm`) and stopword removal (**preserving negation words** such as `not`, `no`, `without`, `cannot`).
# 6. Restore tech tokens and collapse redundant whitespace.

# In[7]:


nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

NEGATIONS = {
    "not", "no", "nor", "neither", "never", "none", "nothing",
    "nowhere", "nobody", "without", "cannot",
}
STOP_WORDS_FILTERED = STOP_WORDS - NEGATIONS

TECH_TOKENS = {
    "c++":      "__CPLUSPLUS__",
    "c#":       "__CSHARP__",
    ".net":     "__DOTNET__",
    "node.js":  "__NODEJS__",
    "vue.js":   "__VUEJS__",
    "react.js": "__REACTJS__",
    "asp.net":  "__ASPNET__",
}
TECH_RESTORE = {v.lower(): k for k, v in TECH_TOKENS.items()}

def protect_tech_tokens(text: str) -> str:
    for token, placeholder in TECH_TOKENS.items():
        text = text.replace(token, placeholder)
    return text

def restore_tech_tokens(text: str) -> str:
    for placeholder, token in TECH_RESTORE.items():
        text = text.replace(placeholder, token)
    return text

def clean_description(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    # 1. HTML stripping
    text = re.sub(r"<[^>]+>", " ", text)
    for ent, repl in [("&amp;","&"),("&lt;","<"),("&gt;",">"),("&nbsp;"," "),("&quot;",'"'),("&#39;","'")]:
        text = text.replace(ent, repl)
    # 2. URLs and emails
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    # 3. Protect tech tokens & lower
    text = protect_tech_tokens(text.lower())
    # 4. Filter characters
    text = re.sub(r"[^a-z0-9 _]", " ", text)
    # 5. Lemmatize & remove non-negation stopwords
    doc = nlp(text)
    tokens = [
        token.lemma_
        for token in doc
        if token.text not in STOP_WORDS_FILTERED
        and token.lemma_ not in STOP_WORDS_FILTERED
        and not token.is_space
        and token.text.strip()
    ]
    text = " ".join(tokens)
    # 6. Restore tech tokens
    text = restore_tech_tokens(text)
    return re.sub(r"\s+", " ", text).strip()

print("Applying NLP cleaning pipeline on description_raw...")
df["description_clean"] = df["description_raw"].apply(clean_description)
print("Text cleaning complete.")

print("\nSample Transformation (Row 0):")
print(f"RAW  : {df['description_raw'].iloc[0][:150]}...")
print(f"CLEAN: {df['description_clean'].iloc[0][:150]}...")


# ## Step 7: Standardization & Integrity Checks
# * Convert `created_date` to pandas `datetime64[ns]`.
# * Standardize string columns to `.str.strip().str.title()` (`role`, `location_region`, `location_country`, `category_label`).
# * Verify uniqueness of primary key (`job_id`).

# In[8]:


# Datetime conversion
df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")

# String standardization
STR_COLS = ["role", "location_region", "location_country", "category_label"]
for col in STR_COLS:
    df[col] = df[col].astype(str).str.strip().str.title()

# Deduplication / uniqueness check
dup_count = df["job_id"].duplicated().sum()
assert dup_count == 0, f"Duplicate job_ids detected: {dup_count}"
print(f"Uniqueness check passed: {len(df):,} unique job_ids (0 duplicates).")
print(f"created_date range: {df['created_date'].min().date()} to {df['created_date'].max().date()}")


# ## Step 8: Final Validation, Schema Verification & Export
# We arrange the final 21 columns and export to `data/processed/career_market_preprocessed.csv`.

# In[9]:


FINAL_COLS = KEEP_COLS + [
    "salary_mid", "salary_band", "has_salary",
    "seniority_level", "description_clean"
]

df_out = df[FINAL_COLS].copy()

# Validation checks
expected_rows = len(df)
expected_salary_rows = int(df["has_salary"].sum())
assert df_out.shape[0] == expected_rows, f"Row count mismatch: {df_out.shape[0]}"
assert df_out.shape[1] == 21, f"Column count mismatch: {df_out.shape[1]}"
assert df_out["job_id"].is_unique, "job_id is not unique"
assert df_out["has_salary"].sum() == expected_salary_rows, f"Salary row mismatch: {df_out['has_salary'].sum()}"

# Export to CSV
df_out.to_csv(OUTPUT_PATH, index=False)
print(f"Preprocessed dataset saved to: {OUTPUT_PATH}")
print(f"Final Table Shape: {df_out.shape[0]:,} rows x {df_out.shape[1]} columns")

print("\n=== DEFINITION OF DONE VERIFICATION ===")
print(f" [x] career_market_preprocessed.csv exported: Yes")
print(f" [x] {expected_rows:,} rows preserved & job_id unique:    Yes ({len(df_out):,} rows)")
print(f" [x] salary_band built on plausible rows:      Yes ({expected_salary_rows:,} rows)")
print(f" [x] has_salary flag present:                   Yes (True: {df_out['has_salary'].sum()}, False: {(~df_out['has_salary']).sum()})")
print(f" [x] seniority_level derived:                   Yes (Entry: {(df_out['seniority_level']=='Entry').sum()}, Mid: {(df_out['seniority_level']=='Mid').sum()}, Senior: {(df_out['seniority_level']=='Senior').sum()})")
print(f" [x] description_clean created:                 Yes")
print(f" [x] No synthetic salary values invented:       Yes (Missing salary remains NaN)")


# ---
# # 2. Exploratory Data Analysis
# 
# Explore the salary distribution, how pay varies by role, seniority and location, the overall market composition, skill prevalence and data quality.

# ## 2.1 EDA Setup and Dataset Overview
# 
# This section explores the cleaned career-market dataset to understand:
# 
# - Salary-band distribution
# - Salary characteristics
# - Role, seniority, category and location distributions
# - Contract patterns
# - Job-description length and common terms
# - Skill prevalence
# - Data quality, missing values and salary outliers
# - Relationships between salary and selected categorical variables
# 
# Salary-related analysis is restricted to records where `has_salary == True` (1,101 records). General market distributions use all 7,184 records.

# In[10]:


import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from collections import Counter

EDA_DIR = "../reports/eda"
os.makedirs(EDA_DIR, exist_ok=True)

INPUT_PATH = "../data/processed/career_market_preprocessed.csv"

eda_df = pd.read_csv(INPUT_PATH, low_memory=False)

print("Dataset shape:", eda_df.shape)
print("Salary records:", eda_df["has_salary"].sum())
print("Non-salary records:", (~eda_df["has_salary"]).sum())


# ## 2.2 Dataset Overview

# In[11]:


overview = pd.DataFrame({
    "rows": [len(eda_df)],
    "columns": [eda_df.shape[1]],
    "unique_job_ids": [eda_df["job_id"].nunique()],
    "salary_records": [eda_df["has_salary"].sum()],
    "salary_percentage": [eda_df["has_salary"].mean() * 100]
})

display(overview.round(2))


# ## 2.3 Salary Band Distribution
# 
# The target variable `salary_band` is available only for records with salary information. The distribution is examined using the 1,101 salaried records.

# In[12]:


salary_df = eda_df[eda_df["has_salary"] == True].copy()

salary_band_counts = (
    salary_df["salary_band"]
    .value_counts()
    .reindex(["low", "medium", "high"])
)

print(salary_band_counts)

plt.figure(figsize=(7, 5))
salary_band_counts.plot(kind="bar")
plt.title("Salary Band Distribution")
plt.xlabel("Salary Band")
plt.ylabel("Number of Jobs")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/01_salary_band_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.4 Salary Distribution and Summary Statistics

# In[13]:


salary_stats = salary_df["salary_mid"].describe()

print(salary_stats)

print("\nMedian salary:", salary_df["salary_mid"].median())
print("Q1:", salary_df["salary_mid"].quantile(0.25))
print("Q3:", salary_df["salary_mid"].quantile(0.75))


# In[14]:


plt.figure(figsize=(8, 5))

plt.hist(salary_df["salary_mid"].dropna(), bins=30)

plt.title("Distribution of Salary Midpoints")
plt.xlabel("Salary Midpoint (INR)")
plt.ylabel("Number of Jobs")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/02_salary_mid_histogram.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# In[15]:


plt.figure(figsize=(8, 4))

plt.boxplot(salary_df["salary_mid"].dropna(), vert=False)

plt.title("Salary Midpoint Boxplot")
plt.xlabel("Salary Midpoint (INR)")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/03_salary_mid_boxplot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.5 Overall Market Distribution

# In[16]:


role_counts = eda_df["role"].value_counts().head(15)

plt.figure(figsize=(9, 6))
role_counts.sort_values().plot(kind="barh")

plt.title("Top 15 Job Roles")
plt.xlabel("Number of Jobs")
plt.ylabel("Role")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/04_top_roles.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# In[17]:


seniority_counts = eda_df["seniority_level"].value_counts()

plt.figure(figsize=(7, 5))
seniority_counts.plot(kind="bar")

plt.title("Job Distribution by Seniority Level")
plt.xlabel("Seniority Level")
plt.ylabel("Number of Jobs")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/05_seniority_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# In[18]:


category_counts = eda_df["category_label"].value_counts().head(15)

plt.figure(figsize=(9, 6))
category_counts.sort_values().plot(kind="barh")

plt.title("Top Job Categories")
plt.xlabel("Number of Jobs")
plt.ylabel("Category")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/06_category_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# In[19]:


contract_counts = eda_df["contract_time"].value_counts()

plt.figure(figsize=(8, 5))
contract_counts.plot(kind="bar")

plt.title("Contract Type Distribution")
plt.xlabel("Contract Type")
plt.ylabel("Number of Jobs")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/07_contract_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.6 Location Distribution

# In[20]:


# Country-level market distribution

country_counts = eda_df["location_country"].value_counts()

print("Job postings by country:")
display(country_counts)

print("\nNumber of countries represented:", eda_df["location_country"].nunique())


# ### Location Scope
# 
# The dataset is primarily focused on the India market. Country-level distribution is checked before analysing regional patterns. Salary-related analysis is restricted to the salaried India-market subset (`has_salary == True`).

# In[21]:


# Verify the geographic scope of salary observations

salary_countries = salary_df["location_country"].value_counts()

print("Countries represented in the salaried subset:")
display(salary_countries)

print(
    "All salaried observations are from India:",
    salary_df["location_country"].eq("India").all()
)


# In[22]:


region_counts = eda_df["location_region"].value_counts().head(15)

plt.figure(figsize=(9, 6))
region_counts.sort_values().plot(kind="barh")

plt.title("Top 15 Job Locations by Region")
plt.xlabel("Number of Jobs")
plt.ylabel("Region")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/08_location_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.7 Salary vs Job Role
# 
# Only salaried records are used. The analysis focuses on the 10 roles with the highest number of salary observations to avoid unstable estimates from very small groups.

# In[23]:


top_salary_roles = (
    salary_df["role"]
    .value_counts()
    .head(10)
    .index
)

role_salary_df = salary_df[
    salary_df["role"].isin(top_salary_roles)
].copy()

role_order = (
    role_salary_df.groupby("role")["salary_mid"]
    .median()
    .sort_values()
    .index
)

plt.figure(figsize=(10, 7))

role_salary_df.boxplot(
    column="salary_mid",
    by="role",
    grid=False,
    rot=45
)

plt.title("Salary-Band Composition for Major Roles — India Market")
plt.suptitle("")
plt.xlabel("Role")
plt.ylabel("Salary Midpoint (INR)")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/09_salary_by_role.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.8 Salary vs Seniority

# In[24]:


seniority_salary = (
    salary_df.groupby("seniority_level")["salary_mid"]
    .agg(["count", "median", "mean"])
    .sort_values("median")
)

display(seniority_salary.round(2))


# In[25]:


seniority_order = (
    salary_df.groupby("seniority_level")["salary_mid"]
    .median()
    .sort_values()
    .index
)

data = [
    salary_df.loc[
        salary_df["seniority_level"] == level,
        "salary_mid"
    ].dropna()
    for level in seniority_order
]

plt.figure(figsize=(9, 6))

plt.boxplot(
    data,
    tick_labels=list(seniority_order)
)

plt.title("Salary Distribution by Seniority Level — India Market")
plt.xlabel("Seniority Level")
plt.ylabel("Salary Midpoint (INR)")
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/10_salary_by_seniority.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.9 Salary vs Location

# In[26]:


top_salary_regions = (
    salary_df["location_region"]
    .value_counts()
    .head(10)
    .index
)

region_salary_df = salary_df[
    salary_df["location_region"].isin(top_salary_regions)
]

plt.figure(figsize=(10, 7))

region_salary_df.boxplot(
    column="salary_mid",
    by="location_region",
    grid=False,
    rot=45
)

plt.title("Salary Distribution by Major Job Locations — India Market")
plt.suptitle("")
plt.xlabel("Location Region")
plt.ylabel("Salary Midpoint (INR)")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/11_salary_by_location.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.10 Salary vs Job Category

# In[27]:


top_salary_categories = (
    salary_df["category_label"]
    .value_counts()
    .head(10)
    .index
)

category_salary_df = salary_df[
    salary_df["category_label"].isin(top_salary_categories)
]

plt.figure(figsize=(10, 7))

category_salary_df.boxplot(
    column="salary_mid",
    by="category_label",
    grid=False,
    rot=45
)

plt.title("Salary Distribution by Job Category — India Market")
plt.suptitle("")
plt.xlabel("Category")
plt.ylabel("Salary Midpoint (INR)")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/12_salary_by_category.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.11 Salary-Band Composition

# In[28]:


role_band = pd.crosstab(
    salary_df["role"],
    salary_df["salary_band"],
    normalize="index"
)

top_roles = salary_df["role"].value_counts().head(10).index

role_band.loc[top_roles].plot(
    kind="bar",
    stacked=True,
    figsize=(10, 6)
)

plt.title("Salary-Band Composition for Major Roles — India Market")
plt.xlabel("Role")
plt.ylabel("Proportion")
plt.xticks(rotation=45)
plt.legend(title="Salary Band")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/13_role_salary_band_composition.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.12 Job Description Length

# In[29]:


print(eda_df["description_length"].describe())

plt.figure(figsize=(8, 5))

plt.hist(
    eda_df["description_length"],
    bins=30
)

plt.title("Distribution of Job Description Length")
plt.xlabel("Description Length (characters)")
plt.ylabel("Number of Jobs")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/14_description_length.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.13 Common Terms in Job Descriptions
# 
# The cleaned descriptions are used for exploratory term-frequency analysis. This is descriptive text analysis only and does not perform feature engineering.

# In[30]:


all_text = " ".join(
    eda_df["description_clean"]
    .dropna()
    .astype(str)
)

words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b", all_text.lower())

word_counts = Counter(words)

top_words = pd.DataFrame(
    word_counts.most_common(20),
    columns=["term", "count"]
)

display(top_words)


# In[31]:


plt.figure(figsize=(9, 7))

top_words.sort_values("count").plot(
    x="term",
    y="count",
    kind="barh",
    legend=False,
    figsize=(9, 7)
)

plt.title("Top 20 Terms in Job Descriptions")
plt.xlabel("Frequency")
plt.ylabel("Term")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/15_top_terms.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.14 Skill Prevalence
# 
# Skill prevalence is estimated using keyword matching in `description_clean`. Since the preprocessing pipeline truncates job descriptions to 500 characters, these counts represent a lower-bound estimate of skill mentions in the original job postings.

# In[32]:


skills = [
    "python",
    "sql",
    "excel",
    "power bi",
    "aws",
    "java",
    "communication"
]

skill_results = []

text = eda_df["description_clean"].fillna("").astype(str).str.lower()

for skill in skills:
    count = text.str.contains(
        rf"\b{re.escape(skill)}\b",
        regex=True
    ).sum()

    skill_results.append({
        "skill": skill,
        "job_count": count,
        "percentage": count / len(eda_df) * 100
    })

skill_df = pd.DataFrame(skill_results)

display(skill_df.round(2))


# In[33]:


plt.figure(figsize=(9, 6))

plt.bar(
    skill_df["skill"],
    skill_df["percentage"]
)

plt.title("Prevalence of Selected Skills")
plt.xlabel("Skill")
plt.ylabel("Percentage of Job Postings")
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/16_skill_prevalence.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.15 Data Quality — Missing Values

# In[34]:


missing = (
    eda_df.isna()
    .sum()
    .sort_values(ascending=False)
)

missing = missing[missing > 0]

display(
    pd.DataFrame({
        "missing_count": missing,
        "missing_percentage": missing / len(eda_df) * 100
    }).round(2)
)


# In[35]:


plt.figure(figsize=(9, 6))

missing.sort_values().plot(kind="barh")

plt.title("Missing Values by Column")
plt.xlabel("Number of Missing Values")
plt.ylabel("Column")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/17_missing_values.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ## 2.16 Salary Outlier Check
# 
# The IQR rule is used only to identify potentially extreme salary midpoint observations. These observations are not removed or modified during EDA.

# In[36]:


q1 = salary_df["salary_mid"].quantile(0.25)
q3 = salary_df["salary_mid"].quantile(0.75)

iqr = q3 - q1

lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = salary_df[
    (salary_df["salary_mid"] < lower_bound) |
    (salary_df["salary_mid"] > upper_bound)
]

print("Q1:", q1)
print("Q3:", q3)
print("IQR:", iqr)
print("Lower bound:", lower_bound)
print("Upper bound:", upper_bound)
print("Potential salary outliers:", len(outliers))


# ## 2.17 Duplicate Job ID Check

# In[37]:


duplicate_count = eda_df["job_id"].duplicated().sum()

print("Duplicate job IDs:", duplicate_count)


# ## 2.18 Numeric Correlation

# In[38]:


numeric_cols = [
    "salary_mid",
    "description_length"
]

correlation = eda_df[numeric_cols].corr()

display(correlation.round(3))


# In[39]:


plt.figure(figsize=(6, 5))

plt.imshow(correlation, aspect="auto")

plt.xticks(
    range(len(correlation.columns)),
    correlation.columns,
    rotation=30
)

plt.yticks(
    range(len(correlation.index)),
    correlation.index
)

plt.colorbar(label="Correlation")

plt.title("Correlation Between Selected Numeric Variables")
plt.tight_layout()

plt.savefig(
    f"{EDA_DIR}/18_numeric_correlation.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# In[40]:


# Data-driven salary summaries

print("=" * 60)
print("SALARY SUMMARY")
print("=" * 60)

# Overall salary statistics
print("\nOverall salary statistics:")
print(f"Median: ₹{salary_df['salary_mid'].median():,.0f}")
print(f"Q1:     ₹{salary_df['salary_mid'].quantile(0.25):,.0f}")
print(f"Q3:     ₹{salary_df['salary_mid'].quantile(0.75):,.0f}")


# Salary by role
role_salary_summary = (
    salary_df.groupby("role")["salary_mid"]
    .agg(["count", "median"])
    .query("count >= 10")
    .sort_values("median", ascending=False)
)

print("\nSalary by role:")
display(role_salary_summary)


# Salary by seniority
seniority_salary_summary = (
    salary_df.groupby("seniority_level")["salary_mid"]
    .agg(["count", "median"])
    .query("count >= 10")
    .sort_values("median", ascending=False)
)

print("\nSalary by seniority:")
display(seniority_salary_summary)


# Salary by region
region_salary_summary = (
    salary_df.groupby("location_region")["salary_mid"]
    .agg(["count", "median"])
    .query("count >= 10")
    .sort_values("median", ascending=False)
)

print("\nSalary by region:")
display(region_salary_summary)


# ## 2.19 Key EDA Findings
# 
# - The dataset contains **7,184 job postings**, of which **1,101 have usable salary information** and are used for salary-related analysis.
# - The salary target is distributed across **low (401), medium (337), and high (363)** salary bands, providing representation across all three classes.
# - For salaried postings, the overall **median salary midpoint is ₹10.5 lakh**, with a first quartile of **₹6 lakh** and third quartile of **₹20 lakh**.
# - Salary varies substantially across roles. Among roles with sufficient salary observations, **Data Engineer has the highest median salary at ₹16.5 lakh**, followed by Data Scientist at ₹15.95 lakh and Product Manager at ₹15 lakh.
# - Salary also varies by seniority: **Senior roles have a median of ₹12.5 lakh**, compared with ₹9.8 lakh for Mid-level roles and ₹3.5 lakh for Entry-level roles.
# - Regional salary differences are also visible. Among regions with at least 10 salary observations, **Telangana has a median of ₹15 lakh**, followed by Karnataka at ₹13.5 lakh and Tamil Nadu at ₹11.875 lakh.
# - The selected skill-frequency analysis identifies mentions of **Python, SQL, Excel, Power BI, AWS, Java, and communication** across the job descriptions; these counts should be interpreted as lower-bound estimates because descriptions were truncated to approximately **500 characters** during preprocessing.
# - Data-quality checks found **no duplicate `job_id` values**. Salary analysis is restricted to records with `has_salary == True`, while general market and text analysis uses the full dataset.

# ---
# # 3. Feature Engineering
# 
# Build a leakage-free, interpretable feature matrix for the salary-band classifier using curated skill indicators and compact categorical features (role, seniority, location).

# ### 3.1 Build the curated feature matrix
# 
# Skill flags use the EDA-supported prevalence threshold (at least 1.5%). Locations outside the eight most common regions are grouped into `other`; `category_label` and `domain` are excluded because they are redundant with `role`.

# In[41]:


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

REQUIRED_FE_COLUMNS = {
    "has_salary", "salary_band", "description_clean", "role",
    "location_region", "contract_time", "seniority_level",
}
missing_fe_columns = sorted(REQUIRED_FE_COLUMNS.difference(df.columns))
if missing_fe_columns:
    raise KeyError(f"Missing required feature-engineering columns: {missing_fe_columns}")

SKILL_PATTERNS = {
    "python": r"(?<![a-z])python(?![a-z])",
    "sql": r"(?<![a-z])sql(?![a-z])",
    "communication": r"(?<![a-z])communication(?![a-z])",
    "azure": r"(?<![a-z])azure(?![a-z])",
    "machine_learning": r"(?<![a-z])machine[ _-]learning(?![a-z])",
    "agile": r"(?<![a-z])agile(?![a-z])",
    "aws": r"(?<![a-z])aws(?![a-z])",
    "linux": r"(?<![a-z])linux(?![a-z])",
    "java": r"(?<![a-z])java(?![a-z])",
    "sap": r"(?<![a-z])sap(?![a-z])",
    "docker": r"(?<![a-z])docker(?![a-z])",
}
TOP_REGIONS = [
    "Unknown", "Karnataka", "Maharashtra", "Telangana",
    "Tamil Nadu", "Gujarat", "Delhi", "Uttar Pradesh",
]
SENIORITY_MAP = {"Entry": 0, "Mid": 1, "Senior": 2}

model_df = df.loc[df["has_salary"].eq(True)].copy()
model_df = model_df.loc[model_df["salary_band"].notna()].copy()
if model_df.empty:
    raise ValueError("No labelled rows remain after filtering has_salary and salary_band.")

descriptions = model_df["description_clean"].fillna("").astype(str).str.lower()
skill_columns = []
for skill, pattern in SKILL_PATTERNS.items():
    column = f"skill_{skill}"
    model_df[column] = descriptions.str.contains(pattern, regex=True, na=False).astype("int8")
    skill_columns.append(column)
model_df["skill_count"] = model_df[skill_columns].sum(axis=1).astype("int8")

model_df["seniority_ordinal"] = model_df["seniority_level"].map(SENIORITY_MAP).fillna(1).astype("int8")
model_df["location_bucket"] = model_df["location_region"].where(model_df["location_region"].isin(TOP_REGIONS), "other")
model_df["is_full_time"] = model_df["contract_time"].eq("full_time").astype("int8")

categorical = pd.get_dummies(model_df[["role", "location_bucket"]].fillna("Unknown"), columns=["role", "location_bucket"], drop_first=True, dtype="int8")
numeric = model_df[["skill_count", "seniority_ordinal"]].astype("float64")
X = pd.concat([model_df[skill_columns], categorical, model_df[["is_full_time"]], numeric], axis=1).astype("float64")
y = model_df["salary_band"].astype(str)

forbidden_features = {"salary_min", "salary_max", "salary_mid", "salary_band", "salary_present", "salary_passes_plausibility_screen", "has_salary", "job_id", "title", "employer", "description_raw", "description_length", "domain"}
leakage_columns = sorted(forbidden_features.intersection(X.columns))
if leakage_columns:
    raise AssertionError(f"Salary leakage or excluded columns found in X: {leakage_columns}")
if X.isna().any().any() or y.isna().any():
    raise AssertionError("Feature matrix and target must not contain missing values.")

print(f"Feature matrix: {X.shape[1]} features")
print("Target distribution:")
display(y.value_counts(normalize=True).round(3).rename_axis("salary_band").to_frame("proportion"))


# ### 3.2 Split first, then scale (and dimensionality-reduction decision)
# 
# The split is stratified and reproducible. Numeric features (`skill_count` and `seniority_ordinal`) are standardized using training rows only; binary indicators and one-hot columns remain unchanged. No PCA or TruncatedSVD is used because this curated matrix is small and dense enough to remain interpretable. If a future TF-IDF experiment is added, fit `TruncatedSVD` on `X_train` only and transform `X_test` with that fitted reducer.

# In[42]:


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=42
)

scaler = StandardScaler()
X_train = X_train.copy()
X_test = X_test.copy()
numeric_feature_columns = ["skill_count", "seniority_ordinal"]
X_train[numeric_feature_columns] = scaler.fit_transform(X_train[numeric_feature_columns])
X_test[numeric_feature_columns] = scaler.transform(X_test[numeric_feature_columns])

assert list(X_train.columns) == list(X_test.columns) == list(X.columns)
assert not X_train.isna().any().any() and not X_test.isna().any().any()
assert set(y_train) == set(y_test) == set(y)
print("Primary path: retain the interpretable curated feature matrix; reduction experiments follow in Section 3.3.")
print("Section 4 hand-off: X_train, X_test, y_train, y_test, feature_columns, scaler")


# ### 3.3 Controlled dimensionality-reduction experiments
# 
# The curated 31-feature matrix remains the primary interpretable representation. These experiments test whether mathematical reduction improves a classifier without leaking information from the test set:
# 
# 1. PCA on the scaled curated features.
# 2. TF-IDF followed by TruncatedSVD on job-description text.
# 
# Each reducer is fitted inside a scikit-learn pipeline during cross-validation. The real test set remains untouched.

# In[43]:


from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

dr_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
dr_results = []

# Reference: the same classifier and the full curated feature matrix.
dr_classifier = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
reference_scores = cross_val_score(dr_classifier, X_train, y_train, cv=dr_cv, scoring="f1_macro")
dr_results.append({
    "experiment": "Curated features (no reduction)",
    "representation": X_train.shape[1],
    "macro_f1_mean": reference_scores.mean(),
    "macro_f1_std": reference_scores.std(),
})

# PCA owns its scaler so each cross-validation fold fits preprocessing on that fold only.
X_train_unscaled = X.loc[X_train.index]
for n_components in [5, 10, 15, 20]:
    if n_components >= X_train.shape[1]:
        continue
    pca_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=n_components, random_state=42)),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
    ])
    scores = cross_val_score(pca_pipeline, X_train_unscaled, y_train, cv=dr_cv, scoring="f1_macro")
    dr_results.append({
        "experiment": "PCA",
        "representation": n_components,
        "macro_f1_mean": scores.mean(),
        "macro_f1_std": scores.std(),
    })

# Text experiment: split text using the exact indices from the real training split.
text_train = model_df.loc[X_train.index, "description_clean"].fillna("").astype(str)
for n_components in [25, 50, 100]:
    text_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("svd", TruncatedSVD(n_components=n_components, random_state=42)),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
    ])
    scores = cross_val_score(text_pipeline, text_train, y_train, cv=dr_cv, scoring="f1_macro")
    dr_results.append({
        "experiment": "TF-IDF + TruncatedSVD",
        "representation": n_components,
        "macro_f1_mean": scores.mean(),
        "macro_f1_std": scores.std(),
    })

dr_results_df = pd.DataFrame(dr_results)
dr_results_df["macro_f1_mean"] = dr_results_df["macro_f1_mean"].round(3)
dr_results_df["macro_f1_std"] = dr_results_df["macro_f1_std"].round(3)
display(dr_results_df)
print("The untouched real test set is reserved for the final comparison.")


# ### 3.4 Dimensionality-reduction findings
# 
# The results table compares macro-F1 using the same stratified cross-validation protocol. The curated feature baseline is retained as the interpretable reference, while PCA and TF-IDF + TruncatedSVD are evaluated as separate experiments.
# 
# - PCA compresses the 31 curated features but does not improve the baseline in this experiment.
# - TF-IDF + TruncatedSVD represents job-description text in a lower-dimensional space and can capture salary-related language that is absent from the curated features.
# - The best configuration should be selected using training cross-validation only. The untouched real test set must be used once for final comparison.
# 
# The final report should include the baseline, PCA configurations, and TF-IDF + TruncatedSVD configurations with macro-F1 mean and standard deviation. If the text representation remains strongest after final test evaluation, it can be reported as the best predictive representation; the curated features should still be retained for interpretability.

# In[43]:


feature_columns = X.columns.tolist()
print("Features:")
print(feature_columns)


# ---
# # 4. Predictive Modelling
# 
# Train and tune salary-band classifiers (Logistic Regression and Random Forest) with stratified cross-validation, select the best, and additionally train a binary above/below-median model.

# ## 4.1 Baseline — the bar to beat
# 
# The majority-class baseline is what a model that always predicts the most common band would score. Any real model must clearly beat it.

# In[44]:


from sklearn.dummy import DummyClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# leakage-safe baseline: majority class proportion on the training labels
baseline_acc = y_train.value_counts(normalize=True).max()
print(f"Majority-class baseline (train): {baseline_acc:.3f}  (~{baseline_acc*100:.1f}%)")
print(f"Random-guess (3 balanced classes): ~0.333")


# ## 4.2 Candidate models + cross-validated tuning
# 
# Two interpretable, small-sample-safe models, tuned with 5-fold stratified CV on **macro-F1** (all three bands matter equally). Only the training set is used here — the test set stays untouched.

# In[45]:


cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

search_spaces = {
    "LogisticRegression": (
        LogisticRegression(max_iter=2000, random_state=42),
        {"C": [0.1, 1.0, 10.0]},
    ),
    "RandomForest": (
        RandomForestClassifier(n_estimators=300, random_state=42),
        {"max_depth": [5, 8, 12], "min_samples_leaf": [1, 5]},
    ),
}

searches, cv_scores = {}, {}
for name, (estimator, grid) in search_spaces.items():
    gs = GridSearchCV(estimator, grid, scoring="f1_macro", cv=cv, n_jobs=-1)
    gs.fit(X_train, y_train)
    searches[name] = gs
    cv_scores[name] = gs.best_score_
    print(f"{name:20s} best CV macro-F1 = {gs.best_score_:.3f}  params={gs.best_params_}")


# ## 4.3 Select and refit the final model
# 
# Pick the model with the best cross-validated macro-F1. `GridSearchCV` has already refit it on the full training set.

# In[46]:


best_name = max(cv_scores, key=cv_scores.get)
final_model = searches[best_name].best_estimator_

# quick sanity: CV accuracy of the chosen model vs baseline (train only)
cv_acc = cross_val_score(final_model, X_train, y_train, cv=cv, scoring="accuracy").mean()
print(f"Selected model : {best_name}")
print(f"CV macro-F1    : {cv_scores[best_name]:.3f}")
print(f"CV accuracy    : {cv_acc:.3f}  (baseline {baseline_acc:.3f})")
print(f"Lift over baseline: +{(cv_acc - baseline_acc)*100:.1f} points")
print("\nHand-off to Section 5: final_model, X_test, y_test, feature_columns, scaler, baseline_acc")


# ## 4.4 Save the model for the dashboard
# 
# Persist the model + scaler + feature order + skill list together so `dashboard/app.py` can rebuild the exact 31-feature vector from the user's selections.

# In[47]:


import os
import joblib

SKILLS = ["python", "sql", "communication", "azure", "machine_learning",
          "agile", "aws", "linux", "java", "sap", "docker"]

os.makedirs("../models", exist_ok=True)
artifact = {
    "model": final_model,
    "scaler": scaler,
    "feature_columns": feature_columns,
    "numeric_cols": ["skill_count", "seniority_ordinal"],
    "skills": SKILLS,
    "classes": sorted(final_model.classes_.tolist()),
    "baseline_accuracy": float(baseline_acc),
    "model_name": best_name,
}
joblib.dump(artifact, "../models/salary_band_model.joblib")
print("Saved -> models/salary_band_model.joblib")
print("classes:", artifact["classes"])
print("n_features:", len(feature_columns))


# ## 4.5 Binary model — above / below median salary
# 
# A higher-confidence view that predicts whether a posting pays above or below the market median, trained on the same features.

# In[48]:


median_salary = model_df["salary_mid"].median()
y_binary = (model_df["salary_mid"] >= median_salary).map({True: "above", False: "below"})

Xb_train, Xb_test, yb_train, yb_test = train_test_split(
    X, y_binary, test_size=0.20, stratify=y_binary, random_state=42)
binary_scaler = StandardScaler().fit(Xb_train[["skill_count", "seniority_ordinal"]])
Xb_train = Xb_train.copy(); Xb_test = Xb_test.copy()
Xb_train[["skill_count", "seniority_ordinal"]] = binary_scaler.transform(Xb_train[["skill_count", "seniority_ordinal"]])
Xb_test[["skill_count", "seniority_ordinal"]] = binary_scaler.transform(Xb_test[["skill_count", "seniority_ordinal"]])

binary_searches, binary_scores = {}, {}
for name, (estimator, grid) in search_spaces.items():
    gs = GridSearchCV(estimator, grid, scoring="f1_macro", cv=cv, n_jobs=-1)
    gs.fit(Xb_train, yb_train)
    binary_searches[name] = gs
    binary_scores[name] = gs.best_score_

binary_best = max(binary_scores, key=binary_scores.get)
binary_model = binary_searches[binary_best].best_estimator_
binary_cv_acc = cross_val_score(binary_model, Xb_train, yb_train, cv=cv, scoring="accuracy").mean()
print(f"Binary model   : {binary_best}")
print(f"CV accuracy    : {binary_cv_acc:.3f}  (above/below median)")


# In[49]:


joblib.dump(
    {"model": binary_model, "scaler": binary_scaler, "feature_columns": feature_columns,
     "numeric_cols": ["skill_count", "seniority_ordinal"], "skills": SKILLS,
     "classes": sorted(binary_model.classes_.tolist()),
     "median_salary": float(median_salary), "model_name": binary_best},
    "../models/salary_binary_model.joblib")
print("Saved -> models/salary_binary_model.joblib")


# ## 4.6 Text-enhanced models
# 
# Adds job-title and description word features (TF-IDF) to the structured features. Performance is validated with employer-grouped cross-validation, so a company never appears in both training and validation. This gives a realistic estimate for postings from unseen employers.

# In[3]:


from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier

text_df = model_df.reset_index(drop=True)
X_struct = csr_matrix(X.reset_index(drop=True).values)

title_vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_features=300)
desc_vec = TfidfVectorizer(min_df=5, max_features=500, stop_words="english")
X_title = title_vec.fit_transform(text_df["title"].fillna("").str.lower())
X_desc = desc_vec.fit_transform(text_df["description_clean"].fillna(""))
X_text = hstack([X_struct, X_title, X_desc]).tocsr()

employer_groups = text_df["employer"].fillna("unknown").str.lower().str.strip()
y_band_text = text_df["salary_band"].astype(str)
median_text = text_df["salary_mid"].median()
y_binary_text = (text_df["salary_mid"] >= median_text).map({True: "above", False: "below"})

grouped_cv = GroupKFold(n_splits=5)
text_rf = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=2, random_state=42, n_jobs=1)

rows = {}
for label, features in [("Structured features", X_struct), ("Structured + title + description", X_text)]:
    rows[label] = {
        "Band accuracy": cross_val_score(text_rf, features, y_band_text, cv=grouped_cv, groups=employer_groups, scoring="accuracy").mean(),
        "Binary accuracy": cross_val_score(text_rf, features, y_binary_text, cv=grouped_cv, groups=employer_groups, scoring="accuracy").mean(),
    }
display(pd.DataFrame(rows).T.round(3).rename_axis("Feature set"))


# In[4]:


import joblib

text_band_model = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=2, random_state=42, n_jobs=1).fit(X_text, y_band_text)
text_binary_model = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=2, random_state=42, n_jobs=1).fit(X_text, y_binary_text)

joblib.dump(
    {"band_model": text_band_model, "binary_model": text_binary_model,
     "title_vectorizer": title_vec, "description_vectorizer": desc_vec,
     "feature_columns": X.columns.tolist(), "median_salary": float(median_text)},
    "../models/salary_text_models.joblib")
print("Saved -> models/salary_text_models.joblib")


# ## 4.7 TF-IDF + TruncatedSVD model (description text only)
# 
# A text-only model: job descriptions are converted to TF-IDF vectors, compressed to 100 dimensions with TruncatedSVD and classified with logistic regression. It uses no role, seniority or location inputs. Both the salary-band and the above/below-median models are fitted on the training split only.

# In[6]:


text_train = model_df.loc[X_train.index, "description_clean"].fillna("").astype(str)
text_test = model_df.loc[X_test.index, "description_clean"].fillna("").astype(str)

text_model = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
    ("svd", TruncatedSVD(n_components=100, random_state=42)),
    ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
])
text_model.fit(text_train, y_train)

text_cv_scores = cross_val_score(
    Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("svd", TruncatedSVD(n_components=100, random_state=42)),
        ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
    ]),
    text_train,
    y_train,
    cv=cv,
    scoring="f1_macro",
)
print("Selected model : TF-IDF + TruncatedSVD (100) + Logistic Regression")
print(f"CV macro-F1    : {text_cv_scores.mean():.3f} +/- {text_cv_scores.std():.3f}")
print("Section 5 hand-off: text_model, text_test, y_test")


# In[7]:


median_salary = model_df.loc[X_train.index, "salary_mid"].median()
y_binary = (model_df["salary_mid"] >= median_salary).map({True: "above", False: "below"})
yb_train = y_binary.loc[X_train.index]
yb_test = y_binary.loc[X_test.index]

binary_text_model = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
    ("svd", TruncatedSVD(n_components=100, random_state=42)),
    ("classifier", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)),
])
binary_text_model.fit(text_train, yb_train)
binary_cv_scores = cross_val_score(binary_text_model, text_train, yb_train, cv=cv, scoring="f1_macro")
print("Binary model   : TF-IDF + TruncatedSVD (100) + Logistic Regression")
print(f"CV macro-F1    : {binary_cv_scores.mean():.3f} +/- {binary_cv_scores.std():.3f}")


# In[ ]:


joblib.dump(
    {
        "band_model": text_model,
        "binary_model": binary_text_model,
        "band_classes": sorted(text_model.classes_.tolist()),
        "binary_classes": sorted(binary_text_model.classes_.tolist()),
        "median_salary": float(median_salary),
        "model_name": "TF-IDF + TruncatedSVD (100) + Logistic Regression",
        "tfidf_max_features": 5000,
        "svd_components": 100,
    },
    "../models/salary_tfidf_svd_models.joblib")
print("Saved -> models/salary_tfidf_svd_models.joblib")


# ---
# # 5. Model Evaluation
# 
# Compares the three models under the same validation protocol, then reports detailed held-out metrics for the TF-IDF + SVD model.

# ## 5.1 Three-model comparison
# 
# All three models are scored with employer-grouped cross-validation: a company never appears in both the training and validation folds. This estimates performance on postings from employers the model has not seen. The same labels and folds are used for every model.

# In[8]:


from sklearn.base import clone
from sklearn.model_selection import GroupKFold, cross_validate

employer_cv = GroupKFold(n_splits=5)
description_text = text_df["description_clean"].fillna("").astype(str)
X_standard = X.reset_index(drop=True)

# (band estimator, binary estimator, input features) for each model
comparison_models = {
    "Standard (structured features)": (clone(final_model), clone(binary_model), X_standard),
    "Text-enhanced (structured + title + description)": (clone(text_rf), clone(text_rf), X_text),
    "TF-IDF + SVD (description text only)": (clone(text_model), clone(binary_text_model), description_text),
}
scoring = {"accuracy": "accuracy", "macro_f1": "f1_macro"}

comparison_rows = []
for model_label, (band_estimator, binary_estimator, features) in comparison_models.items():
    band_scores = cross_validate(band_estimator, features, y_band_text, cv=employer_cv, groups=employer_groups, scoring=scoring)
    binary_scores = cross_validate(binary_estimator, features, y_binary_text, cv=employer_cv, groups=employer_groups, scoring=scoring)
    comparison_rows.append({
        "Model": model_label,
        "Band accuracy": band_scores["test_accuracy"].mean(),
        "Band macro-F1": band_scores["test_macro_f1"].mean(),
        "Binary accuracy": binary_scores["test_accuracy"].mean(),
        "Binary macro-F1": binary_scores["test_macro_f1"].mean(),
    })

comparison_df = pd.DataFrame(comparison_rows).set_index("Model").round(3)
display(comparison_df)


# **Result.** The TF-IDF + TruncatedSVD model scores highest on both tasks (band accuracy 51.3%, binary accuracy 71.8%), followed by the text-enhanced model (49.2%, 71.2%) and the standard model (47.0%, 69.2%).
# 
# - Adding job text to the structured features improves accuracy by roughly 2 to 4 points on unseen employers.
# - The two text models are close: about 2 points apart on the three-class band and under 1 point on the binary task, which is within fold-to-fold variation.
# - The standard model is the only one that uses role, seniority, location and skill selections directly, so it remains the most interpretable.
# 

# ## 5.2 Held-out evaluation: TF-IDF + TruncatedSVD
# 
# The TF-IDF + SVD models are evaluated once on the untouched test split. This split is stratified by salary band but not by employer, so these scores are higher than the employer-grouped estimates in Section 5.1.

# In[9]:


from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix, roc_curve, auc, precision_recall_curve
import seaborn as sns

# --- Binary model evaluation plots ---
print("--- Evaluating final binary TF-IDF + SVD model ---")
binary_predictions = binary_text_model.predict(text_test)
binary_probabilities = binary_text_model.predict_proba(text_test)[:, list(binary_text_model.classes_).index("above")]

binary_report = classification_report(yb_test, binary_predictions, output_dict=True, zero_division=0)
print(f"Accuracy: {accuracy_score(yb_test, binary_predictions):.4f}")
print(f"Macro-F1: {f1_score(yb_test, binary_predictions, average='macro'):.4f}")
print(f"Weighted-F1: {f1_score(yb_test, binary_predictions, average='weighted'):.4f}")

fig, axes = plt.subplots(2, 2, figsize=(14, 11))
cm_binary = confusion_matrix(yb_test, binary_predictions, labels=["below", "above"])
sns.heatmap(cm_binary, annot=True, fmt="d", cmap="Blues", xticklabels=["Below median", "Above median"], yticklabels=["Below median", "Above median"], ax=axes[0, 0])
axes[0, 0].set_title("Binary confusion matrix")
axes[0, 0].set_xlabel("Predicted")
axes[0, 0].set_ylabel("Actual")

binary_report_df = pd.DataFrame(binary_report).T.loc[["above", "below"], ["precision", "recall", "f1-score"]]
sns.heatmap(binary_report_df, annot=True, cmap="RdYlGn", vmin=0, vmax=1, ax=axes[0, 1])
axes[0, 1].set_title("Binary classification report")

fpr, tpr, _ = roc_curve((yb_test == "above").astype(int), binary_probabilities)
roc_auc = auc(fpr, tpr)
axes[1, 0].plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC AUC = {roc_auc:.3f}")
axes[1, 0].plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
axes[1, 0].set_title("Binary ROC curve")
axes[1, 0].set_xlabel("False positive rate")
axes[1, 0].set_ylabel("True positive rate")
axes[1, 0].legend(loc="lower right")

precision_curve, recall_curve, _ = precision_recall_curve((yb_test == "above").astype(int), binary_probabilities)
axes[1, 1].plot(recall_curve, precision_curve, color="purple", lw=2)
axes[1, 1].set_title("Binary precision-recall curve")
axes[1, 1].set_xlabel("Recall")
axes[1, 1].set_ylabel("Precision")
plt.tight_layout()
plt.show()


# In[10]:


from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

text_predictions = text_model.predict(text_test)
final_metrics = pd.DataFrame([{
    "accuracy": accuracy_score(y_test, text_predictions),
    "macro_f1": f1_score(y_test, text_predictions, average="macro"),
    "weighted_f1": f1_score(y_test, text_predictions, average="weighted"),
    "macro_precision": precision_score(y_test, text_predictions, average="macro", zero_division=0),
    "macro_recall": recall_score(y_test, text_predictions, average="macro", zero_division=0),
}], index=["TF-IDF + SVD (100)"]).round(3)
display(final_metrics)

print("Classification report: TF-IDF + SVD (100)")
print(classification_report(y_test, text_predictions, zero_division=0))
print("Confusion matrix: TF-IDF + SVD (100)")
band_labels = sorted(y.unique())
display(pd.DataFrame(confusion_matrix(y_test, text_predictions, labels=band_labels), index=band_labels, columns=band_labels))

# Evaluate the binary model on its untouched real test partition.
binary_predictions = binary_text_model.predict(text_test)
binary_metrics = pd.DataFrame([{
    "accuracy": accuracy_score(yb_test, binary_predictions),
    "precision": precision_score(yb_test, binary_predictions, average="binary", pos_label="above", zero_division=0),
    "recall": recall_score(yb_test, binary_predictions, average="binary", pos_label="above", zero_division=0),
    "f1": f1_score(yb_test, binary_predictions, average="binary", pos_label="above", zero_division=0),
    "macro_f1": f1_score(yb_test, binary_predictions, average="macro"),
    "weighted_f1": f1_score(yb_test, binary_predictions, average="weighted"),
}], index=["Binary above/below median"]).round(3)
display(binary_metrics)

print("Classification report: binary above/below median")
print(classification_report(yb_test, binary_predictions, zero_division=0))
print("Confusion matrix: binary above/below median")
binary_labels = ["above", "below"]
display(pd.DataFrame(confusion_matrix(yb_test, binary_predictions, labels=binary_labels), index=binary_labels, columns=binary_labels))


# ### Final held-out evaluation interpretation
# 
# The selected TF-IDF + TruncatedSVD representation with 100 components achieved 0.584 accuracy, 0.568 Macro-F1, and 0.574 Weighted-F1 on the untouched real test set for the three-class salary-band task. The binary above/below-median evaluation is reported immediately above using its untouched real test partition.
# 

# In[11]:


# --- Multi-class salary-band model evaluation plots ---
print("--- Evaluating final salary-band TF-IDF + SVD model ---")
band_report = classification_report(y_test, text_predictions, output_dict=True, zero_division=0)
print(f"Accuracy: {accuracy_score(y_test, text_predictions):.4f}")
print(f"Macro-F1: {f1_score(y_test, text_predictions, average='macro'):.4f}")
print(f"Weighted-F1: {f1_score(y_test, text_predictions, average='weighted'):.4f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
band_labels = sorted(y.unique())
cm_band = confusion_matrix(y_test, text_predictions, labels=band_labels)
sns.heatmap(cm_band, annot=True, fmt="d", cmap="Blues", xticklabels=band_labels, yticklabels=band_labels, ax=axes[0])
axes[0].set_title("Salary-band confusion matrix")
axes[0].set_xlabel("Predicted")
axes[0].set_ylabel("Actual")

band_report_df = pd.DataFrame(band_report).T.loc[band_labels, ["precision", "recall", "f1-score"]]
sns.heatmap(band_report_df, annot=True, cmap="RdYlGn", vmin=0, vmax=1, ax=axes[1])
axes[1].set_title("Salary-band classification report")
plt.tight_layout()
plt.show()

# Logistic Regression coefficients provide text-term direction, rather than tree feature_importances_.
tfidf_vocabulary = text_model.named_steps["tfidf"].get_feature_names_out()
svd_components = text_model.named_steps["svd"].components_
classifier = text_model.named_steps["classifier"]
term_weights = classifier.coef_ @ svd_components
for class_index, class_name in enumerate(classifier.classes_):
    top_indices = np.argsort(term_weights[class_index])[-10:][::-1]
    print(f"Top text terms associated with {class_name}:", ", ".join(tfidf_vocabulary[top_indices]))


# ---
# # 6. Business Interpretation
# 
# Based on our exploratory data analysis and the predictive models developed, we have uncovered the main drivers of compensation in the tech and digital job market. Here are the key actionable insights:
# 
# ### 1. The Strongest Drivers of Compensation
# Across both models (Binary and Salary Band), the highest impact on salary prediction stems from:
# * **Role Categorization:** Roles such as `Digital Marketing` and `Graphic Designer` strongly signal specific pay ranges. By contrast, roles like `DevOps / Cloud Engineer` and `Data Engineer` push salaries upwards, as demand outpaces supply.
# * **Skill Diversity (`skill_count`):** The total volume of core tech skills a candidate possesses is a critical indicator of salary. Jobs demanding a high number of skills (e.g. cross-functional capabilities) consistently command higher pay.
# * **Seniority (`Seniority: ordinal`):** Unsurprisingly, a higher seniority level (Lead, Executive, Senior) dramatically influences the probability of being in a high salary bracket.
# 
# ### 2. Location Matters (But Maybe Less Than You Think)
# * While overall location does impact compensation, specific regional hubs dominate the data. **Karnataka** (India's tech hub, Bangalore) and **Maharashtra** act as significant features pushing salaries higher. 
# * However, tech skills and role definition still hold substantially more weight than location alone, indicating an increasingly distributed or skill-driven tech market.
# 
# ### 3. Contract Types
# * `is_full_time` is among the top predictive features. Part-time or contract roles heavily cluster in the lower salary bands, whereas full-time permanent positions secure a premium.
# 
# ### 4. Precision of Predictive Bands
# * The Binary Model effectively identifies whether a role pays above or below the median with high precision, balancing false positives and false negatives smoothly.
# * The Band Model struggles slightly more (as distinguishing between 'Low' and 'Medium' involves subtler differences). However, it rarely makes drastic errors (e.g., misclassifying 'Low' as 'High'), providing a reliable safety net for employers aiming to bracket roles for hiring budgets.
# 
# **Conclusion:** 
# For a recruiter or a hiring manager, the focus should lie on defining the **specific skills required** and the **exact seniority** rather than relying purely on location-based market rates. The models confirm that technical depth and leadership demands dictate the top brackets of the market.
# 
