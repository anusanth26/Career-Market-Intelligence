import pandas as pd
import numpy as np
import re
import os

def extract_seniority(title):
    t = str(title).lower()
    if re.search(r'\b(vp|chief|director|head|principal|architect)\b', t): 
        return 'Executive/Principal'
    elif re.search(r'\b(senior|sr|lead|manager|staff)\b', t): 
        return 'Senior'
    elif re.search(r'\b(junior|jr|entry|intern|trainee|fresher|graduate)\b', t): 
        return 'Junior/Entry'
    else: 
        return 'Mid-Level'

def extract_years_experience(text):
    text = str(text).lower()
    match = re.search(r'(\d+)\s*(?:-|to|\+)?\s*(\d+)?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)', text)
    if match:
        return int(match.group(1))
    return np.nan

def extract_education(text):
    t = str(text).lower()
    if re.search(r'\b(phd|doctorate)\b', t): return 'PhD'
    elif re.search(r'\b(master|ms|msc|mba)\b', t): return 'Masters'
    elif re.search(r'\b(bachelor|bs|bsc|ba|btech|degree|undergrad)\b', t): return 'Bachelors'
    else: return 'Not Specified'

def extract_work_arrangement(text, loc):
    t = str(text).lower() + " " + str(loc).lower()
    if re.search(r'\b(remote|work from home|wfh)\b', t): return 'Remote'
    elif re.search(r'\b(hybrid)\b', t): return 'Hybrid'
    elif re.search(r'\b(on-site|onsite|in office)\b', t): return 'On-site'
    else: return 'Unspecified'

def extract_benefits(text):
    t = str(text).lower()
    return int(bool(re.search(r'\b(health insurance|medical|401k|pf|provident fund|equity|stock options|bonus)\b', t)))

def city_tier(loc):
    t = str(loc).lower()
    tier_1 = ['bangalore', 'bengaluru', 'mumbai', 'delhi', 'new delhi', 'ncr', 'gurugram', 'gurgaon', 'noida', 'pune', 'hyderabad', 'chennai', 'san francisco', 'new york', 'london', 'seattle']
    for city in tier_1:
        if city in t: return 'Tier 1'
    return 'Tier 2/3'

def extract_skills(df, text_col, skills):
    for skill in skills:
        col_name = f"skill_{skill.lower().replace(' ', '_').replace('.', '').replace('+', 'p').replace('#', 'sharp')}"
        if skill == 'c++':
            pattern = r'\bc\+\+\b'
        else:
            pattern = r'\b' + re.escape(skill) + r'\b'
        df[col_name] = df[text_col].str.contains(pattern, case=False, na=False).astype(int)
    return df

def main():
    print("Loading data...")
    input_path = 'data/processed/adzuna/career_market_core_analysis.csv'
    output_path = 'data/processed/adzuna/career_market_comprehensive_features.csv'
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
        
    df = pd.read_csv(input_path)
    print(f"Original shape: {df.shape}")
    
    print("Engineering PRODUCTION-GRADE features...")
    
    # 1. Job Role Characteristics
    df['seniority_level'] = df['title'].apply(extract_seniority)
    df['years_experience_required'] = df['description_raw'].apply(extract_years_experience)
    df['education_requirement'] = df['description_raw'].apply(extract_education)
    df['work_arrangement'] = df.apply(lambda row: extract_work_arrangement(row['description_raw'], row['location_display']), axis=1)
    df['offers_benefits'] = df['description_raw'].apply(extract_benefits)
    df['location_tier'] = df['location_display'].apply(city_tier)
    
    # 2. Comprehensive Skill Taxonomy (Technical, Soft, Tools, Cloud)
    tech_skills = [
        'Python', 'SQL', 'AWS', 'Azure', 'GCP', 'Java', 'C++', 'C#', 'JavaScript', 
        'TypeScript', 'React', 'Angular', 'Vue', 'Node', 'Docker', 'Kubernetes', 
        'Jenkins', 'CI/CD', 'Git', 'Linux', 'Spark', 'Hadoop', 'Kafka', 
        'Tableau', 'Power BI', 'Looker', 'Excel', 'Snowflake', 'Redshift', 
        'Machine Learning', 'Deep Learning', 'NLP', 'PyTorch', 'TensorFlow', 
        'Scikit-learn', 'Databricks', 'dbt', 'Airflow', 'MongoDB', 'PostgreSQL'
    ]
    soft_skills = [
        'Agile', 'Scrum', 'Leadership', 'Communication', 'Problem Solving', 
        'Teamwork', 'Mentoring', 'Client-facing', 'Stakeholder Management', 'Presentation'
    ]
    
    df = extract_skills(df, 'description_raw', tech_skills + soft_skills)
    
    # 3. Advanced Salary & Compensation Targets
    df['salary_midpoint'] = (df['salary_min'] + df['salary_max']) / 2
    valid_salary_mask = (df['salary_midpoint'] >= 100000) & (df['salary_passes_plausibility_screen'] == True)
    
    # Create finely tuned quantiles for multi-class classification
    df.loc[valid_salary_mask, 'salary_band'] = pd.qcut(
        df.loc[valid_salary_mask, 'salary_midpoint'], 
        q=4, 
        labels=['Entry', 'Lower-Mid', 'Upper-Mid', 'High']
    )
    df['salary_band'] = df['salary_band'].astype(str).replace('nan', np.nan)
    
    # Create binary high-earner flag for logistic regression
    threshold = df.loc[valid_salary_mask, 'salary_midpoint'].quantile(0.75)
    df['is_high_earner'] = (df['salary_midpoint'] >= threshold).astype(float)
    df.loc[~valid_salary_mask, 'is_high_earner'] = np.nan
    
    # 4. Employer Tiering (Top 1%, Top 5%, Long-tail)
    emp_counts = df['employer_normalized'].value_counts()
    top_1_pct = emp_counts.nlargest(int(len(emp_counts) * 0.01)).index
    top_5_pct = emp_counts.nlargest(int(len(emp_counts) * 0.05)).index
    
    def get_emp_tier(emp):
        if emp in top_1_pct: return 'Top 1% Volume'
        if emp in top_5_pct: return 'Top 5% Volume'
        return 'Long-tail'
        
    df['employer_tier'] = df['employer_normalized'].apply(get_emp_tier)
    
    print(f"Saving comprehensive model-ready data to {output_path}...")
    df.to_csv(output_path, index=False)
    print(f"Done! New shape: {df.shape}")

if __name__ == '__main__':
    main()
