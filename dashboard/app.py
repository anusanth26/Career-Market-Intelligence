import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import re
from PIL import Image

st.set_page_config(page_title="Salary Band Predictor", layout="wide")

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

STANDARD_MODEL_LABEL = "Standard model (role, seniority, location, skills)"
TEXT_MODEL_LABEL = "Text-enhanced model (adds job title + description)"
SVD_MODEL_LABEL = "TF-IDF + SVD model (job description only)"


@st.cache_resource
def load_svd_models():
    path = os.path.join(os.path.dirname(__file__), '..', 'models', 'salary_tfidf_svd_models.joblib')
    return joblib.load(path) if os.path.exists(path) else None


@st.cache_resource
def load_text_models():
    path = os.path.join(os.path.dirname(__file__), '..', 'models', 'salary_text_models.joblib')
    return joblib.load(path) if os.path.exists(path) else None


@st.cache_resource
def load_lemmatizer():
    try:
        import spacy
        return spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception:
        return None


def clean_description(text):
    # Mirrors the notebook's cleaning; lemmatization is skipped if spaCy is unavailable.
    text = re.sub(r"<[^>]+>|https?://\S+|\S+@\S+", " ", text.lower())
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    nlp = load_lemmatizer()
    if nlp is not None:
        text = " ".join(tok.lemma_ for tok in nlp(text) if not tok.is_space)
    return re.sub(r"\s+", " ", text).strip()


def build_structured_input(columns, role, location, full_time, seniority, skills):
    values = {col: 0 for col in columns}
    values['is_full_time'] = int(full_time)
    values['seniority_ordinal'] = seniority
    values['skill_count'] = len(skills)
    for key in (f"role_{role}", f"location_bucket_{location}"):
        if key in values:
            values[key] = 1
    for skill in skills:
        if f"skill_{skill}" in values:
            values[f"skill_{skill}"] = 1
    return values


def predict_text_model(text_data, structured, job_title, job_description):
    from scipy.sparse import hstack, csr_matrix
    row = pd.DataFrame([structured])[text_data['feature_columns']].astype(float)
    title_features = text_data['title_vectorizer'].transform([job_title.lower()])
    desc_features = text_data['description_vectorizer'].transform([clean_description(job_description)])
    features = hstack([csr_matrix(row.values), title_features, desc_features]).tocsr()
    band_model, binary_model = text_data['band_model'], text_data['binary_model']
    band_probs = dict(zip(band_model.classes_, band_model.predict_proba(features)[0]))
    binary_probs = dict(zip(binary_model.classes_, binary_model.predict_proba(features)[0]))
    return band_probs, binary_probs


def show_text_result(band_probs, binary_probs, median_salary):
    band = max(band_probs, key=band_probs.get)
    side = max(binary_probs, key=binary_probs.get)
    colors = {"high": "green", "medium": "blue", "low": "red"}
    st.divider()
    st.subheader("Prediction Result")
    st.markdown(f"### Predicted Band: :{colors[band]}[{band.upper()}]")
    st.progress(band_probs[band])
    st.markdown(f"**Confidence:** `{band_probs[band] * 100:.1f}%`")
    st.markdown(f"### Likely **{side.upper()}** the median salary (₹{median_salary:,.0f})")
    st.progress(binary_probs[side])
    st.markdown(f"**Confidence:** `{binary_probs[side] * 100:.1f}%`")
    with st.expander("View All Probabilities"):
        for cls, prob in band_probs.items():
            st.write(f"- **{cls.title()}**: {prob * 100:.1f}%")
        for cls, prob in binary_probs.items():
            st.write(f"- **{cls.title()} median**: {prob * 100:.1f}%")


def predict_svd_model(svd_data, job_description):
    cleaned = clean_description(job_description)
    band_model, binary_model = svd_data['band_model'], svd_data['binary_model']
    band_probs = dict(zip(band_model.classes_, band_model.predict_proba([cleaned])[0]))
    binary_probs = dict(zip(binary_model.classes_, binary_model.predict_proba([cleaned])[0]))
    return band_probs, binary_probs


text_data = load_text_models()
svd_data = load_svd_models()

st.title("💼 Career Market Intelligence Dashboard")

# --- Tabs ---
tab1, tab2 = st.tabs(["🎯 Salary Predictor", "📊 Model Evaluation"])

# ==========================================
# TAB 1: SALARY PREDICTOR
# ==========================================
with tab1:
    st.markdown("Enter the job posting characteristics below to predict the expected salary band.")

    model_options = [STANDARD_MODEL_LABEL] + ([TEXT_MODEL_LABEL] if text_data else []) + ([SVD_MODEL_LABEL] if svd_data else [])
    model_choice = st.radio("Model", model_options, horizontal=True)
    structured_inputs_disabled = model_choice == SVD_MODEL_LABEL
    if structured_inputs_disabled:
        st.info("This model uses only the job description, so role, location, seniority and skills are not used.")
    
    st.header("Job Characteristics")
    col1, col2 = st.columns(2)
    
    with col1:
        roles = [
            "Business Analyst", "Data Analyst", "Data Engineer", "Data Scientist", 
            "Devops / Cloud Engineer", "Digital Marketing", 
            "Graphic Designer", "Product Manager", 
            "Project Manager", "Software Engineer"
        ]
        selected_role = st.selectbox("Role Category", roles, disabled=structured_inputs_disabled)
        
        locations = [
            "Karnataka", "Maharashtra", "Telangana", "Delhi", 
            "Uttar Pradesh", "Tamil Nadu", "Gujarat", 
            "Unknown", "other"
        ]
        selected_location = st.selectbox("Location Bucket", locations, disabled=structured_inputs_disabled)
        
        is_full_time = st.checkbox("Is Full Time?", value=True, disabled=structured_inputs_disabled)
    
    with col2:
        seniority_levels = {
            "Entry": 0, "Mid": 1, 
            "Senior": 2
        }
        selected_seniority = st.selectbox("Seniority Level", list(seniority_levels.keys()), disabled=structured_inputs_disabled)
        
        available_skills = [
            'python', 'sql', 'communication', 'azure', 
            'machine_learning', 'agile', 'aws', 'linux', 
            'java', 'sap', 'docker'
        ]
        selected_skills = st.multiselect("Key Skills", available_skills, disabled=structured_inputs_disabled)
    
    # --- TF-IDF + SVD model (description only) ---
    if model_choice == SVD_MODEL_LABEL:
        svd_description = st.text_area("Job Description", height=180, placeholder="Paste the job description here", key="svd_description")

        if st.button("Predict Salary", type="primary", key="predict_svd"):
            if not svd_description.strip():
                st.warning("Enter a job description to use this model.")
            else:
                band_probs, binary_probs = predict_svd_model(svd_data, svd_description)
                show_text_result(band_probs, binary_probs, svd_data['median_salary'])
    
    # --- Text-enhanced model ---
    if model_choice == TEXT_MODEL_LABEL:
        st.markdown("Adding the job title and description improves accuracy. Both fields are optional.")
        job_title = st.text_input("Job Title", placeholder="e.g. Senior Data Engineer")
        job_description = st.text_area("Job Description", height=150, placeholder="Paste the job description here")

        if st.button("Predict Salary", type="primary", key="predict_text"):
            structured = build_structured_input(
                text_data['feature_columns'], selected_role, selected_location,
                is_full_time, seniority_levels[selected_seniority], selected_skills)
            band_probs, binary_probs = predict_text_model(text_data, structured, job_title, job_description)
            show_text_result(band_probs, binary_probs, text_data['median_salary'])

    # --- Prediction Logic ---
    if model_choice == STANDARD_MODEL_LABEL and st.button("Predict Salary Band", type="primary"):
        input_data = {col: 0 for col in feature_columns}
        
        input_data['is_full_time'] = int(is_full_time)
        input_data['seniority_ordinal'] = seniority_levels[selected_seniority]
        input_data['skill_count'] = len(selected_skills)
        
        role_col = f"role_{selected_role}"
        if role_col in input_data:
            input_data[role_col] = 1
            
        location_col = f"location_bucket_{selected_location}"
        if location_col in input_data:
            input_data[location_col] = 1
            
        for skill in selected_skills:
            skill_col = f"skill_{skill}"
            if skill_col in input_data:
                input_data[skill_col] = 1
                
        df_input = pd.DataFrame([input_data])[feature_columns]
        df_input[numeric_cols] = scaler.transform(df_input[numeric_cols])
        
        prediction = model.predict(df_input)[0]
        probabilities = model.predict_proba(df_input)[0]
        
        prob_dict = {classes[i]: probabilities[i] for i in range(len(classes))}
        confidence = prob_dict[prediction] * 100
        
        st.divider()
        st.subheader("Prediction Result")
        
        color = "blue"
        if prediction == "high": color = "green"
        elif prediction == "low": color = "red"
        
        st.markdown(f"### Predicted Band: :{color}[{prediction.upper()}]")
        st.progress(confidence / 100.0)
        st.markdown(f"**Confidence:** `{confidence:.1f}%`")
        
        with st.expander("View All Probabilities"):
            for cls, prob in prob_dict.items():
                st.write(f"- **{cls.title()}**: {prob*100:.1f}%")

# ==========================================
# TAB 2: MODEL EVALUATION
# ==========================================
with tab2:
    st.header("Model Performance & Diagnostics")
    st.markdown("Review the final performance metrics and confusion matrices to understand where the models succeed and misclassify.")
    
    # Helper to load images robustly
    def load_image(filename):
        path = os.path.join(os.path.dirname(__file__), '..', 'reports', 'eda', filename)
        if os.path.exists(path):
            return Image.open(path)
        return None

    # Binary Model Performance
    st.subheader("1. Tuned Binary Classifier (Above vs Below Median)")
    st.markdown("- **Accuracy:** 65.80%\n- **F1-Score:** 65.72%\n- **Improvement over Baseline:** +19.05 percentage points")
    
    cm_binary = load_image('cm_binary.png')
    if cm_binary:
        st.image(cm_binary, caption="Confusion Matrix: Binary Classifier")
    else:
        st.warning("Binary confusion matrix image not found.")

    st.divider()
    
    # Band Model Performance
    st.subheader("2. Salary Band Multi-Class Classifier (Low, Medium, High)")
    st.markdown("- **Accuracy:** 51.08%\n- **F1-Score:** 43.44%")
    
    cm_band = load_image('cm_band.png')
    if cm_band:
        st.image(cm_band, caption="Confusion Matrix: Salary Band Classifier")
    else:
        st.warning("Salary Band confusion matrix image not found.")

    st.divider()
    
    # Feature Importance
    st.subheader("3. Feature Importance (Key Drivers)")
    fi_band = load_image('feature_importance_band.png')
    if fi_band:
        st.image(fi_band, caption="Top 10 Feature Importances (Salary Band Model)")
    else:
        st.warning("Feature importance image not found.")

    st.divider()

    st.subheader("4. Model Comparison")
    st.markdown(
        "All three models scored with employer-grouped cross-validation (a company never appears in both "
        "training and validation), which estimates performance on unseen employers:\n\n"
        "| Model | Band accuracy | Binary accuracy |\n|---|---|---|\n"
        "| Standard (structured features) | 47.0% | 69.2% |\n"
        "| Text-enhanced (structured + title + description) | 49.2% | 71.2% |\n"
        "| TF-IDF + SVD (description only) | 51.3% | 71.8% |"
    )
