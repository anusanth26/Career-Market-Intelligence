import pandas as pd
import numpy as np
import requests
import re
import os
import json
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

# We'll reuse the feature engineering logic for consistency
def extract_seniority(title):
    t = str(title).lower()
    if re.search(r'\b(vp|chief|director|head|principal|architect)\b', t): return 'Executive/Principal'
    elif re.search(r'\b(senior|sr|lead|manager|staff)\b', t): return 'Senior'
    elif re.search(r'\b(junior|jr|entry|intern|trainee|fresher|graduate)\b', t): return 'Junior/Entry'
    return 'Mid-Level'

def extract_years_experience(text):
    text = str(text).lower()
    match = re.search(r'(\d+)\s*(?:-|to|\+)?\s*(\d+)?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)', text)
    if match: return int(match.group(1))
    return np.nan

def clean_html(raw_html):
    if pd.isna(raw_html): return ""
    return BeautifulSoup(raw_html, "lxml").get_text(separator=" ", strip=True)

def main():
    print("Fetching live data from Remotive API (Web/API Collection)...")
    url = "https://remotive.com/api/remote-jobs?category=software-dev,data"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        jobs = data.get('jobs', [])
        print(f"Successfully retrieved {len(jobs)} live jobs from Remotive API.")
    except Exception as e:
        print(f"Failed to fetch from Remotive API: {e}")
        return

    # Map to our standard schema
    records = []
    for j in jobs:
        records.append({
            'job_id': 'REMOTIVE_' + str(j.get('id')),
            'title': j.get('title'),
            'employer_normalized': str(j.get('company_name')).lower(),
            'description_raw': clean_html(j.get('description')),
            'location_display': j.get('candidate_required_location', 'Remote'),
            'salary_raw': j.get('salary', ''),
            'source': 'Remotive API'
        })
    
    df = pd.DataFrame(records)
    
    # 1. Engineer standard features
    df['seniority_level'] = df['title'].apply(extract_seniority)
    df['years_experience_required'] = df['description_raw'].apply(extract_years_experience)
    df['work_arrangement'] = 'Remote' # All remotive jobs are remote
    
    # Parse Salary if available (Remotive gives strings like "$80k - $120k")
    def parse_salary(s):
        s = str(s).lower().replace(',', '')
        nums = re.findall(r'(\d+)(k)?', s)
        vals = []
        for n, k in nums:
            val = int(n)
            if k == 'k' or val < 1000:
                val *= 1000
            vals.append(val)
        if len(vals) >= 2:
            return (vals[0] + vals[1]) / 2
        elif len(vals) == 1:
            return vals[0]
        return np.nan

    df['salary_midpoint'] = df['salary_raw'].apply(parse_salary)
    
    output_path = 'data/processed/adzuna/remotive_api_dataset.csv'
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} Remotive API records to {output_path}")

if __name__ == '__main__':
    main()
