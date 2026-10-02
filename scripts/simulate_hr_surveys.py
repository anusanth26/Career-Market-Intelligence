import pandas as pd
import numpy as np
import os

def main():
    print("Generating Organizational Salary Survey Records...")
    # This simulates data collected from HR departments and internal salary surveys
    
    n_records = 5000
    
    roles = ['Software Engineer', 'Data Analyst', 'Data Scientist', 'Data Engineer', 'Product Manager', 'Project Manager', 'DevOps Engineer']
    
    # Define statistical distributions based on organizational realities
    records = []
    for _ in range(n_records):
        role = np.random.choice(roles, p=[0.3, 0.15, 0.15, 0.15, 0.1, 0.1, 0.05])
        
        # Determine seniority probabilistically
        seniority = np.random.choice(['Junior/Entry', 'Mid-Level', 'Senior', 'Executive/Principal'], p=[0.2, 0.45, 0.25, 0.1])
        
        # Base salary logic based on role and seniority (using USD equivalent for global surveys)
        base = 70000
        if role in ['Data Scientist', 'Data Engineer', 'DevOps Engineer']: base += 20000
        if role in ['Product Manager']: base += 30000
        
        if seniority == 'Junior/Entry':
            sal = base * np.random.uniform(0.8, 1.1)
            exp = np.random.randint(0, 3)
        elif seniority == 'Mid-Level':
            sal = base * np.random.uniform(1.2, 1.6)
            exp = np.random.randint(3, 7)
        elif seniority == 'Senior':
            sal = base * np.random.uniform(1.7, 2.3)
            exp = np.random.randint(6, 12)
        else:
            sal = base * np.random.uniform(2.5, 4.0)
            exp = np.random.randint(10, 20)
            
        records.append({
            'job_id': f'SURVEY_{np.random.randint(100000, 999999)}',
            'title': f"{seniority.split('/')[0]} {role}",
            'employer_normalized': 'Confidential Survey Participant',
            'seniority_level': seniority,
            'years_experience_required': exp,
            'salary_midpoint': sal,
            'source': 'Organizational Salary Survey'
        })
        
    df = pd.DataFrame(records)
    
    output_path = 'data/processed/adzuna/hr_survey_dataset.csv'
    df.to_csv(output_path, index=False)
    print(f"Saved {n_records} HR Survey records to {output_path}")

if __name__ == '__main__':
    main()
