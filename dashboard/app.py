import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

st.set_page_config(page_title="Salary Band Predictor", layout="centered")

# --- Load Model ---
@st.cache_resource
def load_model():
    # Adjust path if running from dashboard/ directory
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'salary_band_model.joblib')
    return joblib.load(model_path)

model_data = load_model()
model = model_data['model']
scaler = model_data['scaler']
feature_columns = model_data['feature_columns']
numeric_cols = model_data['numeric_cols']
classes = model_data['classes']

st.title("💼 Salary Band Predictor")
st.markdown("Enter the job posting characteristics below to predict the expected salary band.")

# --- Inputs ---
st.header("Job Characteristics")

col1, col2 = st.columns(2)

with col1:
    roles = [
        "Data Analyst", "Data Engineer", "Data Scientist", 
        "Devops / Cloud Engineer", "Digital Marketing", 
        "Graphic Designer", "Product Manager", 
        "Project Manager", "Software Engineer"
    ]
    selected_role = st.selectbox("Role Category", roles)
    
    locations = [
        "Karnataka", "Maharashtra", "Telangana", 
        "Uttar Pradesh", "Tamil Nadu", "Gujarat", 
        "Unknown", "other"
    ]
    selected_location = st.selectbox("Location Bucket", locations)
    
    is_full_time = st.checkbox("Is Full Time?", value=True)

with col2:
    seniority_levels = {
        "Unknown": 0, "Entry Level": 1, "Mid Level": 2, 
        "Senior": 3, "Lead": 4, "Executive": 5
    }
    selected_seniority = st.selectbox("Seniority Level", list(seniority_levels.keys()))
    
    available_skills = [
        'python', 'sql', 'communication', 'azure', 
        'machine_learning', 'agile', 'aws', 'linux', 
        'java', 'sap', 'docker'
    ]
    selected_skills = st.multiselect("Key Skills", available_skills)


# --- Prediction Logic ---
if st.button("Predict Salary Band", type="primary"):
    # 1. Initialize an empty row with zeros for all feature columns
    input_data = {col: 0 for col in feature_columns}
    
    # 2. Populate standard features
    input_data['is_full_time'] = int(is_full_time)
    input_data['seniority_ordinal'] = seniority_levels[selected_seniority]
    input_data['skill_count'] = len(selected_skills)
    
    # 3. Populate one-hot encoded roles and locations
    role_col = f"role_{selected_role}"
    if role_col in input_data:
        input_data[role_col] = 1
        
    location_col = f"location_bucket_{selected_location}"
    if location_col in input_data:
        input_data[location_col] = 1
        
    # 4. Populate one-hot encoded skills
    for skill in selected_skills:
        skill_col = f"skill_{skill}"
        if skill_col in input_data:
            input_data[skill_col] = 1
            
    # Create DataFrame
    df_input = pd.DataFrame([input_data])[feature_columns]
    
    # 5. Scale numeric columns
    df_input[numeric_cols] = scaler.transform(df_input[numeric_cols])
    
    # 6. Predict
    prediction = model.predict(df_input)[0]
    probabilities = model.predict_proba(df_input)[0]
    
    # Map probabilities to classes
    prob_dict = {classes[i]: probabilities[i] for i in range(len(classes))}
    confidence = prob_dict[prediction] * 100
    
    # --- Display Results ---
    st.divider()
    
    st.subheader("Prediction Result")
    
    # Color coding based on prediction
    color = "blue"
    if prediction == "high": color = "green"
    elif prediction == "low": color = "red"
    
    st.markdown(f"### Predicted Band: :{color}[{prediction.upper()}]")
    st.progress(confidence / 100.0)
    st.markdown(f"**Confidence:** `{confidence:.1f}%`")
    
    with st.expander("View All Probabilities"):
        for cls, prob in prob_dict.items():
            st.write(f"- **{cls.title()}**: {prob*100:.1f}%")
