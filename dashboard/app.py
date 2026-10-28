import os
import re

import altair as alt
import joblib
import pandas as pd
import streamlit as st
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..")
EXTRACTS = os.path.join(ROOT, "tableau_dashboard", "extracts")

INK, MUTED, LINE, CANVAS = "#1B2A3A", "#5B6B7B", "#D5DBE2", "#EEF1F4"
BLUE, AMBER, GREEN = "#1F5FBF", "#D9930D", "#1F8A70"
BAND_COLORS = {"low": "#9DB7DF", "medium": BLUE, "high": "#0F2F66"}

st.set_page_config(page_title="Career Market Intelligence", page_icon=None, layout="wide")

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Public Sans', system-ui, sans-serif; color: {INK}; }}
:root, html, body {{ color-scheme: light only; }}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: {CANVAS} !important; color: {INK}; }}
[data-testid="stHeader"] {{ background: {CANVAS} !important; }}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {{ background: #FFFFFF !important; }}
[data-baseweb="select"] > div, [data-baseweb="input"], textarea, .stTextInput input {{ background: #FFFFFF !important; color: {INK} !important; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding: 1.4rem 2rem 2rem; max-width: 1500px; }}
section[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {LINE}; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}
h1 {{ font-size: 1.55rem; font-weight: 700; margin: 0; letter-spacing: -0.01em; }}
h2, h3 {{ font-weight: 600; letter-spacing: -0.005em; }}
.sub {{ color: {MUTED}; font-size: 0.92rem; margin: 0.15rem 0 1rem; }}
.kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 1rem; }}
.kpi {{ background: #fff; border: 1px solid {LINE}; border-radius: 6px; padding: 12px 16px; }}
.kpi .v {{ font-size: 1.9rem; font-weight: 700; line-height: 1.15; font-variant-numeric: tabular-nums; }}
.kpi .l {{ color: {MUTED}; font-size: 0.82rem; margin-top: 2px; }}
[class*="st-key-panel"] {{ background: #fff; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; }}
.ptitle {{ font-size: 0.98rem; font-weight: 600; margin-bottom: 2px; }}
.note {{ color: {MUTED}; font-size: 0.82rem; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ height: 42px; padding: 0 16px; font-weight: 500; color: {MUTED}; }}
.stTabs [aria-selected="true"] {{ color: {BLUE}; font-weight: 600; }}
.result {{ padding: 6px 4px 10px; }}
.result .big {{ font-size: 2.2rem; font-weight: 700; }}
@media (max-width: 900px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
""",
    unsafe_allow_html=True,
)


def themed(chart, height=300):
    return (
        chart.properties(height=height)
        .configure(autosize=alt.AutoSizeParams(type="pad", contains="padding"), background="#FFFFFF").configure_view(stroke=None)
        .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#E6EAEF", domainColor=LINE, tickColor=LINE,
                        labelFont="Public Sans", titleFont="Public Sans", titleFontWeight=500, labelLimit=140)
        .configure_legend(labelColor=INK, titleColor=MUTED, labelFont="Public Sans")
    )


CUR = None  # the card the next charts are drawn into
_cards = 0


def show(chart, height=300):
    (CUR or st).altair_chart(themed(chart, height), width="stretch")


def panel(title, note=None):
    global CUR, _cards
    _cards += 1
    CUR = st.container(border=True, key=f"panel{_cards}")
    CUR.markdown(f'<div class="ptitle">{title}</div>' + (f'<div class="note">{note}</div>' if note else ""), unsafe_allow_html=True)
    return CUR


def lakh(v):
    return f"₹{v / 1e5:.1f}L"


@st.cache_data
def load(name):
    return pd.read_csv(os.path.join(EXTRACTS, name))


postings = load("postings.csv")
postings["created_date"] = pd.to_datetime(postings["created_date"])
postings["location_region"] = postings["location_region"].fillna("Unknown")
postings["seniority_level"] = postings["seniority_level"].fillna("Unknown")

# ---------------- model helpers ----------------
@st.cache_resource
def load_joblib(name):
    path = os.path.join(ROOT, "models", name)
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
        text = " ".join(tok.lemma_ for tok in nlp(text[:100000]) if not tok.is_space)
    return re.sub(r"\s+", " ", text).strip()


def build_structured_input(columns, role, location, full_time, seniority, skills):
    values = {col: 0 for col in columns}
    values["is_full_time"] = int(full_time)
    values["seniority_ordinal"] = seniority
    values["skill_count"] = len(skills)
    for key in (f"role_{role}", f"location_bucket_{location}"):
        if key in values:
            values[key] = 1
    for skill in skills:
        if f"skill_{skill}" in values:
            values[f"skill_{skill}"] = 1
    return values


def predict_standard(model_data, structured):
    row = pd.DataFrame([structured])[model_data["feature_columns"]]
    row[model_data["numeric_cols"]] = model_data["scaler"].transform(row[model_data["numeric_cols"]])
    probs = model_data["model"].predict_proba(row)[0]
    return dict(zip(model_data["classes"], probs)), None


def predict_text(text_data, structured, job_title, job_description):
    from scipy.sparse import csr_matrix, hstack
    row = pd.DataFrame([structured])[text_data["feature_columns"]].astype(float)
    features = hstack([csr_matrix(row.values),
                       text_data["title_vectorizer"].transform([job_title.lower()]),
                       text_data["description_vectorizer"].transform([clean_description(job_description)])]).tocsr()
    b, s = text_data["band_model"], text_data["binary_model"]
    return dict(zip(b.classes_, b.predict_proba(features)[0])), dict(zip(s.classes_, s.predict_proba(features)[0]))


def predict_svd(svd_data, job_description):
    cleaned = clean_description(job_description)
    b, s = svd_data["band_model"], svd_data["binary_model"]
    return dict(zip(b.classes_, b.predict_proba([cleaned])[0])), dict(zip(s.classes_, s.predict_proba([cleaned])[0]))


def prob_chart(probs, colors=None):
    df = pd.DataFrame({"label": [k.title() for k in probs], "p": list(probs.values()), "key": list(probs)})
    c = alt.Chart(df).mark_bar(size=22).encode(
        x=alt.X("p:Q", axis=alt.Axis(format="%", title=None), scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("label:N", sort=["Low", "Medium", "High"], title=None),
        color=alt.Color("key:N", scale=alt.Scale(domain=list((colors or BAND_COLORS)), range=list((colors or BAND_COLORS).values())), legend=None),
        tooltip=["label", alt.Tooltip("p:Q", format=".1%")])
    show(c, 130)


# ---------------- header + filters ----------------
st.markdown("<h1>Career Market Intelligence</h1>", unsafe_allow_html=True)
st.markdown('<div class="sub">Adzuna job postings in India, July to October 2026. Ten roles, text-mined skills, and salary models.</div>',
            unsafe_allow_html=True)

with st.sidebar:
    st.markdown("**Filters**")
    st.caption("Apply to Overview and Salary.")
    roles_sel = st.multiselect("Role", sorted(postings.role.unique()))
    sen_sel = st.multiselect("Seniority", ["Entry", "Mid", "Senior"])
    states = postings.location_region.value_counts().index.tolist()
    state_sel = st.multiselect("State", states)
    contract_sel = st.multiselect("Contract", sorted(postings.contract_time.dropna().unique()))
    lo, hi = float(postings.salary_mid.min()), float(postings.salary_mid.max())
    sal_range = st.slider("Salary (₹ lakh per year)", lo / 1e5, hi / 1e5, (lo / 1e5, hi / 1e5), step=0.5,
                          help="Only postings that state a salary have one. Others are kept unless you narrow this.")
    st.caption("Salary is a number from Adzuna with no currency or period field. ₹ per year is an assumption.")

f = postings
if roles_sel:
    f = f[f.role.isin(roles_sel)]
if sen_sel:
    f = f[f.seniority_level.isin(sen_sel)]
if state_sel:
    f = f[f.location_region.isin(state_sel)]
if contract_sel:
    f = f[f.contract_time.isin(contract_sel)]
if (sal_range[0], sal_range[1]) != (lo / 1e5, hi / 1e5):
    f = f[f.salary_mid.between(sal_range[0] * 1e5, sal_range[1] * 1e5)]
fs = f[f.salary_mid.notna()]

tab_over, tab_sal, tab_skill, tab_pred, tab_model = st.tabs(
    ["Overview", "Salary", "Skills", "Predict salary", "Model results"])

# ---------------- Overview ----------------
with tab_over:
    med = lakh(fs.salary_mid.median()) if len(fs) else "–"
    share = f"{len(fs) / len(f):.0%}" if len(f) else "–"
    st.markdown(
        f'<div class="kpis">'
        f'<div class="kpi"><div class="v">{len(f):,}</div><div class="l">Postings</div></div>'
        f'<div class="kpi"><div class="v">{f.role.nunique()}</div><div class="l">Roles</div></div>'
        f'<div class="kpi"><div class="v">{f.employer.nunique():,}</div><div class="l">Employers</div></div>'
        f'<div class="kpi"><div class="v">{share}</div><div class="l">Postings with a stated salary</div></div>'
        f'<div class="kpi"><div class="v">{med}</div><div class="l">Median salary per year</div></div></div>',
        unsafe_allow_html=True)
    if f.empty:
        st.warning("No postings match these filters. Clear a filter in the sidebar.")
    else:
        c1, c2 = st.columns([1.1, 1])
        with c1:
            panel("Postings by role")
            d = f.role.value_counts().rename_axis("role").reset_index(name="postings")
            show(alt.Chart(d).mark_bar(color=BLUE).encode(
                x=alt.X("postings:Q", title=None), y=alt.Y("role:N", sort="-x", title=None),
                tooltip=["role", "postings"]), 330)
        with c2:
            panel("Postings by week created", "The last week is partial.")
            d = f.set_index("created_date").resample("W").size().rename("postings").reset_index()
            show(alt.Chart(d).mark_area(color=BLUE, opacity=0.18, line={"color": BLUE}).encode(
                x=alt.X("created_date:T", title=None), y=alt.Y("postings:Q", title=None),
                tooltip=[alt.Tooltip("created_date:T", title="Week of"), "postings"]), 330)
        c3, c4 = st.columns(2)
        with c3:
            panel("Top states")
            d = f.location_region.value_counts().head(10).rename_axis("state").reset_index(name="postings")
            show(alt.Chart(d).mark_bar(color=BLUE).encode(
                x=alt.X("postings:Q", title=None), y=alt.Y("state:N", sort="-x", title=None),
                tooltip=["state", "postings"]), 300)
        with c4:
            panel("Seniority mix by role")
            d = f.groupby(["role", "seniority_level"]).size().rename("postings").reset_index()
            show(alt.Chart(d).mark_bar().encode(
                x=alt.X("postings:Q", stack="normalize", title=None, axis=alt.Axis(format="%")),
                y=alt.Y("role:N", title=None, sort="-x"),
                color=alt.Color("seniority_level:N", title="Seniority",
                                scale=alt.Scale(domain=["Entry", "Mid", "Senior", "Unknown"],
                                                range=["#9DB7DF", BLUE, "#0F2F66", LINE])),
                tooltip=["role", "seniority_level", "postings"]), 300)

# ---------------- Salary ----------------
with tab_sal:
    st.caption(f"Salary is stated in {len(fs):,} of {len(f):,} filtered postings. Groups with fewer than 10 salaries are hidden.")
    if len(fs) < 10:
        st.warning("Fewer than 10 postings with a salary match these filters. Widen the filters to see salary charts.")
    else:
        c1, c2 = st.columns(2)

        def grouped(col):
            g = fs.groupby(col).salary_mid.agg(median="median", n="size").reset_index()
            return g[g.n >= 10]

        with c1:
            panel("Median salary by role (₹ per year)")
            g = grouped("role")
            show(alt.Chart(g).mark_bar(color=BLUE).encode(
                x=alt.X("median:Q", title=None, axis=alt.Axis(labelExpr="'₹' + format(datum.value / 100000, ',.1~f') + 'L'")), y=alt.Y("role:N", sort="-x", title=None),
                tooltip=["role", alt.Tooltip("median:Q", format=",.0f"), alt.Tooltip("n:Q", title="Salaries")]), 320)
        with c2:
            panel("Salary range by seniority")
            show(alt.Chart(fs[fs.seniority_level.isin(["Entry", "Mid", "Senior"])]).mark_boxplot(color=BLUE, extent="min-max").encode(
                x=alt.X("seniority_level:N", sort=["Entry", "Mid", "Senior"], title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("salary_mid:Q", title=None, axis=alt.Axis(labelExpr="'₹' + format(datum.value / 100000, ',.1~f') + 'L'"))), 320)
        c3, c4 = st.columns(2)
        with c3:
            panel("Salary bands by role", "Bands are thirds of all salaries in the dataset.")
            d = fs.groupby(["role", "salary_band"]).size().rename("postings").reset_index()
            show(alt.Chart(d).mark_bar().encode(
                x=alt.X("postings:Q", stack="normalize", title=None, axis=alt.Axis(format="%")),
                y=alt.Y("role:N", title=None),
                color=alt.Color("salary_band:N", title="Band", scale=alt.Scale(domain=list(BAND_COLORS), range=list(BAND_COLORS.values()))),
                tooltip=["role", "salary_band", "postings"]), 320)
        with c4:
            panel("Median salary by state (₹ per year)")
            g = grouped("location_region")
            show(alt.Chart(g).mark_bar(color=BLUE).encode(
                x=alt.X("median:Q", title=None, axis=alt.Axis(labelExpr="'₹' + format(datum.value / 100000, ',.1~f') + 'L'")), y=alt.Y("location_region:N", sort="-x", title=None),
                tooltip=["location_region", alt.Tooltip("median:Q", format=",.0f"), alt.Tooltip("n:Q", title="Salaries")]), 320)
        panel("Postings with a stated salary")
        CUR.dataframe(fs[["title", "role", "employer", "location_region", "seniority_level", "salary_min", "salary_max", "salary_band"]]
                     .sort_values("salary_max", ascending=False), width="stretch", hide_index=True, height=300)

# ---------------- Skills ----------------
with tab_skill:
    demand, pairs, trends = load("skill_demand.csv"), load("skill_cooccurrence.csv"), load("trends_long.csv")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        panel("Share of postings that mention each skill", "Text-mined from job descriptions. Percent of each role's postings.")
        show(alt.Chart(demand).mark_rect().encode(
            x=alt.X("skill:N", title=None, axis=alt.Axis(labelAngle=-60, labelFontSize=10, labelOverlap=False)), y=alt.Y("role:N", title=None),
            color=alt.Color("pct_of_role_postings:Q", title="% of postings", scale=alt.Scale(scheme="blues")),
            tooltip=["role", "skill", alt.Tooltip("pct_of_role_postings:Q", title="% of postings")]), 400)
    with c2:
        panel("Skills that appear together", "Lift above 1 means the pair co-occurs more than chance.")
        top = pairs.assign(pair=pairs.skill_a + " + " + pairs.skill_b).nlargest(12, "lift")
        show(alt.Chart(top).mark_bar(color=BLUE).encode(
            x=alt.X("lift:Q", title=None), y=alt.Y("pair:N", sort="-x", title=None),
            tooltip=["pair", "together", "lift", "jaccard"]), 400)
    panel("Search interest over time (Google Trends, India)", "Scaled 0 to 100 per skill; pick skills to compare.")
    default = [s for s in ["SQL", "Python", "Power BI"] if s in set(trends.skill)]
    pick = CUR.multiselect("Skills", sorted(trends.skill.unique()), default=default)
    if pick:
        d = trends[trends.skill.isin(pick)].assign(date=lambda x: pd.to_datetime(x.date))
        show(alt.Chart(d).mark_line().encode(
            x=alt.X("date:T", title=None), y=alt.Y("interest:Q", title=None),
            color=alt.Color("skill:N", title=None, scale=alt.Scale(range=[BLUE, AMBER, GREEN, "#7A4EAB", "#C8452B", "#555F6B"])),
            tooltip=["skill", alt.Tooltip("date:T"), alt.Tooltip("interest:Q", format=".1f")]), 300)
    else:
        CUR.info("Select at least one skill to draw the trend.")

# ---------------- Predict ----------------
with tab_pred:
    std, text_data, svd_data = load_joblib("salary_band_model.joblib"), load_joblib("salary_text_models.joblib"), load_joblib("salary_tfidf_svd_models.joblib")
    labels = {"std": "Structured features", "text": "Structured + title and description", "svd": "Description only (TF-IDF + SVD)"}
    options = ["std"] + (["text"] if text_data else []) + (["svd"] if svd_data else [])
    left, right = st.columns([1, 1])
    with left:
        with panel("Describe the posting"):
            kind = st.radio("Model", options, format_func=labels.get, horizontal=True)
            off = kind == "svd"
            if off:
                st.caption("This model reads only the description. Role, state, seniority and skills are not used.")
            a, b = st.columns(2)
            role = a.selectbox("Role", sorted(postings.role.unique()), disabled=off)
            loc = b.selectbox("State", ["Karnataka", "Maharashtra", "Telangana", "Delhi", "Uttar Pradesh", "Tamil Nadu", "Gujarat", "Unknown", "other"], disabled=off)
            sen = a.selectbox("Seniority", ["Entry", "Mid", "Senior"], index=1, disabled=off)
            full = b.checkbox("Full time", value=True, disabled=off)
            skills = st.multiselect("Skills", ["python", "sql", "communication", "azure", "machine_learning", "agile", "aws", "linux", "java", "sap", "docker"],
                                    format_func=lambda s: s.replace("_", " "), disabled=off)
            title = desc = ""
            if kind in ("text", "svd"):
                if kind == "text":
                    title = st.text_input("Job title", placeholder="Senior Data Engineer")
                desc = st.text_area("Job description", height=140, placeholder="Paste the description here")
            go = st.button("Predict", type="primary")
    with right:
        with panel("Prediction"):
            if not go:
                st.info("Fill in the posting on the left and select Predict.")
            elif kind == "svd" and not desc.strip():
                st.warning("Paste a job description to use this model.")
            else:
                structured = build_structured_input(std["feature_columns"], role, loc, full, {"Entry": 0, "Mid": 1, "Senior": 2}[sen], skills)
                if kind == "std":
                    band, side = predict_standard(std, structured)
                elif kind == "text":
                    structured = build_structured_input(text_data["feature_columns"], role, loc, full, {"Entry": 0, "Mid": 1, "Senior": 2}[sen], skills)
                    band, side = predict_text(text_data, structured, title, desc)
                else:
                    band, side = predict_svd(svd_data, desc)
                top = max(band, key=band.get)
                st.markdown(f'<div class="result"><div class="note">Most likely salary band</div><div class="big">{top.title()}</div>'
                            f'<div class="note">{band[top]:.0%} confidence. Each band is a third of salaries in the dataset.</div></div>', unsafe_allow_html=True)
                prob_chart(band)
                if side:
                    above = side.get("above", 0)
                    med = (svd_data if kind == "svd" else text_data)["median_salary"]
                    st.markdown(f"**Above the median salary ({lakh(med)})?** {above:.0%} likely")
                    prob_chart({"below": side.get("below", 0), "above": above}, {"below": "#9DB7DF", "above": "#0F2F66"})
            st.caption("These models predict a band, not an exact figure. See Model results for how much to trust them.")

# ---------------- Model results ----------------
with tab_model:
    res, cm, fi = load("model_results.csv"), load("confusion_matrix.csv"), load("feature_importance.csv")
    g = res[res.evaluation == "employer_grouped_cv"].set_index("task")
    st.markdown(
        f'<div class="kpis" style="grid-template-columns:repeat(4,1fr)">'
        f'<div class="kpi"><div class="v">{g.loc["band", "accuracy"]:.1%}</div><div class="l">Band accuracy, unseen employers (guessing: {g.loc["band", "majority_baseline_accuracy"]:.1%})</div></div>'
        f'<div class="kpi"><div class="v">{g.loc["binary", "accuracy"]:.1%}</div><div class="l">Above/below median accuracy (guessing: {g.loc["binary", "majority_baseline_accuracy"]:.1%})</div></div>'
        f'<div class="kpi"><div class="v">{int(g.loc["band", "n_scored"]):,}</div><div class="l">Salary-labelled postings scored</div></div>'
        f'<div class="kpi"><div class="v">{postings.employer.nunique():,}</div><div class="l">Employers in the dataset</div></div></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        panel("Accuracy against guessing the most common class",
              "Unseen: a company never sits in both training and test. Holdout shares companies, so it runs higher. Band = low/medium/high; above/below = median salary.")
        long = res.melt(id_vars=["task", "evaluation"], value_vars=["accuracy", "majority_baseline_accuracy"], var_name="measure", value_name="value")
        long["measure"] = long.measure.map({"accuracy": "Model", "majority_baseline_accuracy": "Guessing"})
        long["test"] = long.task.map({"band": "Band", "binary": "Above/below"}) + "|" + long.evaluation.map({"employer_grouped_cv": "unseen", "holdout": "holdout"})
        order = ["Band|unseen", "Band|holdout", "Above/below|unseen", "Above/below|holdout"]
        show(alt.Chart(long).mark_bar().encode(
            x=alt.X("test:N", title=None, sort=order, axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, '|')", labelLimit=0, labelOverlap=False, labelFontSize=11)),
            xOffset=alt.XOffset("measure:N"), y=alt.Y("value:Q", title=None, axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("measure:N", title=None, scale=alt.Scale(domain=["Guessing", "Model"], range=["#B8C2CE", BLUE]), legend=alt.Legend(orient="top")),
            tooltip=["test", "measure", alt.Tooltip("value:Q", format=".1%")]), 360)
    with c2:
        task = st.radio("Show details for", ["band", "binary"], format_func={"band": "Salary band", "binary": "Above/below median"}.get, horizontal=True)
        panel("Where the model gets it right and wrong", "Rows are the true class, columns what the model predicted. Unseen employers.")
        d = cm[cm.task == task]
        base = alt.Chart(d).encode(x=alt.X("predicted:N", title="Predicted", axis=alt.Axis(labelAngle=0)), y=alt.Y("actual:N", title="Actual"))
        show(base.mark_rect().encode(color=alt.Color("count:Q", scale=alt.Scale(scheme="blues"), legend=None)) +
             base.mark_text(fontWeight=600).encode(text="count:Q", color=alt.condition(alt.datum["count"] > d["count"].max() / 2, alt.value("white"), alt.value(INK))), 300)
        panel("Most influential features", "Random forest importance for the chosen task.")
        t = fi[fi.task == task].nlargest(10, "importance").assign(feature=lambda x: x.feature.str.replace("location_bucket_", "State: ").str.replace("role_", "Role: ").str.replace("skill_", "Skill: ").str.replace("_", " "))
        show(alt.Chart(t).mark_bar(color=BLUE).encode(
            x=alt.X("importance:Q", title=None), y=alt.Y("feature:N", sort="-x", title=None),
            tooltip=["feature", "importance"]), 280)
    st.caption("Standard-model numbers come from scripts/model_results.py on the 1,153 salary-labelled postings. "
               "Pay for the same role and seniority varies widely, so no model on this data should be treated as precise. "
               "Text-model scores (about 49% to 51% band, 71% to 72% above/below median, unseen employers) come from the notebook and were not recomputed.")
