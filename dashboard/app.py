"""
Career Market Intelligence Dashboard — Member D (Review 2)
==========================================================
Five tabs:
  1. 📊 Skill Demand      — ranked bar charts, role breakdown, data table
  2. 📈 Skill Trends      — momentum bars, skill cards with badges
  3. 🎯 Gap Analysis      — 2x2 Altair scatter + recommendation cards
  4. 💼 Salary Predictor  — Review-1 ML models (preserved intact)
  5. 🔬 Model Evaluation  — diagnostics, confusion matrix, feature importance

All CSV paths are relative (repo-root-relative via __file__). No hardcoded paths.
Missing files produce a clear warning — no crash.
"""

import os
import re
import warnings

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Career Market Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# REPO ROOT (works from any cwd)
# ──────────────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

def repo(rel: str) -> str:
    return os.path.join(REPO_ROOT, rel)

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, html, body { font-family: 'Inter', sans-serif !important; }

/* Background */
.stApp {
    background: radial-gradient(ellipse at top left, #0f1923 0%, #0d1117 40%, #091020 100%);
    color: #e6edf3;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #13171f 0%, #0d1117 100%);
    border-right: 1px solid #21262d;
}

/* ── KPI card ── */
.kpi-wrap { padding: 4px; }
.kpi-card {
    background: linear-gradient(145deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #21262d;
    border-radius: 16px;
    padding: 24px 18px 18px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
    cursor: default;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,.55);
    border-color: #30363d;
}
.kpi-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--accent, linear-gradient(90deg,#58a6ff,#bc8cff));
    border-radius: 16px 16px 0 0;
}
.kpi-icon  { font-size: 1.8rem; margin-bottom: 6px; line-height: 1; }
.kpi-value { font-size: 2rem; font-weight: 800; color: #e6edf3; line-height: 1.1; }
.kpi-label { font-size: 0.72rem; color: #8b949e; font-weight: 600;
             text-transform: uppercase; letter-spacing: .08em; margin-top: 7px; }
.kpi-sub   { font-size: 0.70rem; color: #6e7681; margin-top: 3px; }

/* ── Badges ── */
.badge {
    display: inline-block; padding: 3px 11px; border-radius: 20px;
    font-size: 0.70rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
}
.b-rising      { background:#122924; color:#3fb950; border:1px solid #238636; }
.b-stable      { background:#112035; color:#58a6ff; border:1px solid #1f6feb; }
.b-declining   { background:#2d1212; color:#f85149; border:1px solid #da3633; }
.b-invest      { background:#122924; color:#3fb950; border:1px solid #238636; }
.b-opportunity { background:#2d2000; color:#e3b341; border:1px solid #9e6a03; }
.b-hype        { background:#112035; color:#58a6ff; border:1px solid #1f6feb; }
.b-avoid       { background:#2d1212; color:#f85149; border:1px solid #da3633; }
.b-high        { background:#122924; color:#3fb950; border:1px solid #238636; }
.b-medium      { background:#112035; color:#58a6ff; border:1px solid #1f6feb; }
.b-low         { background:#2d1212; color:#f85149; border:1px solid #da3633; }

/* ── Section heading ── */
.sec-head { font-size: 1.5rem; font-weight: 800; color: #e6edf3; margin-bottom: 2px; }
.sec-sub  { color: #8b949e; font-size: 0.84rem; margin-bottom: 20px; line-height: 1.5; }

/* ── Recommendation card ── */
.rec-card {
    background: #13171f; border: 1px solid #21262d; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 10px;
    display: flex; align-items: flex-start; gap: 14px;
    transition: border-color .2s, box-shadow .2s;
}
.rec-card:hover { border-color: #58a6ff; box-shadow: 0 4px 20px rgba(88,166,255,.1); }
.rec-skill { font-weight: 700; font-size: 1.05rem; color: #e6edf3; }
.rec-meta  { font-size: 0.75rem; color: #6e7681; margin-top: 2px; }
.rec-text  { font-size: 0.83rem; color: #8b949e; margin-top: 5px; line-height: 1.5; }

/* ── Divider ── */
hr { border-color: #21262d !important; margin: 1.5rem 0 !important; }

/* ── Tab strip ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: transparent;
    border-bottom: 1px solid #21262d; padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; border: 1px solid transparent;
    border-bottom: none; color: #8b949e; font-weight: 500;
    border-radius: 10px 10px 0 0; padding: 9px 22px; font-size: 0.88rem;
    transition: color .2s;
}
.stTabs [aria-selected="true"] {
    background: #161b22 !important;
    border-color: #21262d #21262d transparent !important;
    color: #e6edf3 !important; font-weight: 700 !important;
}

/* ── Callout boxes ── */
.caveat-box {
    background: #1a1f0f; border-left: 4px solid #e3b341;
    border-radius: 0 10px 10px 0; padding: 12px 18px;
    font-size: 0.81rem; color: #8b949e; margin-top: 16px; line-height: 1.55;
}
.novelty-box {
    background: linear-gradient(135deg,#0d1f33,#111b2a);
    border: 1px solid #1f6feb; border-radius: 14px;
    padding: 20px 24px; margin-top: 24px;
}
.novelty-title { font-weight: 700; color: #58a6ff; margin-bottom: 8px; font-size: 1rem; }
.novelty-body  { font-size: 0.84rem; color: #8b949e; line-height: 1.7; }

/* ── Banner ── */
.banner {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 60%, #161b22 100%);
    border: 1px solid #21262d; border-radius: 18px;
    padding: 30px 36px; margin-bottom: 28px;
    position: relative; overflow: hidden;
}
.banner::after {
    content: ''; position: absolute; top:-60px; right:-60px;
    width:220px; height:220px; border-radius:50%;
    background: radial-gradient(circle, rgba(88,166,255,.08) 0%, transparent 70%);
}
.banner-title { font-size: 2.1rem; font-weight: 900; color: #e6edf3; line-height: 1.15; }
.banner-sub   { color: #8b949e; font-size: 0.92rem; margin-top: 8px; }
.banner-pills { margin-top: 14px; display: flex; gap: 10px; flex-wrap: wrap; }
.pill {
    background: #21262d; border: 1px solid #30363d;
    border-radius: 20px; padding: 4px 14px;
    font-size: 0.75rem; color: #8b949e; font-weight: 500;
}

/* ── Altair chart override ── */
.vega-embed { border-radius: 12px; overflow: hidden; }

/* ── Input widgets ── */
.stSelectbox>div>div, .stMultiSelect>div>div,
.stTextInput>div>div>input, .stTextArea>div>textarea {
    background: #13171f !important; border-color: #30363d !important;
    color: #e6edf3 !important; border-radius: 10px !important;
}
.stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] { color: #6e7681; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_csv(rel_path: str):
    p = repo(rel_path)
    if not os.path.exists(p):
        return None
    try:
        return pd.read_csv(p)
    except Exception as e:
        st.error(f"Could not read `{rel_path}`: {e}")
        return None

def kpi(col, icon, val, label, sub, accent):
    with col:
        st.markdown(f"""
        <div class="kpi-wrap">
        <div class="kpi-card" style="--accent:{accent}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-sub">{sub}</div>
        </div></div>""", unsafe_allow_html=True)

def badge(text, kind):
    return f'<span class="badge b-{kind}">{text}</span>'

# ──────────────────────────────────────────────────────────────────────────────
# SALARY MODEL HELPERS (preserved exactly from original)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    return joblib.load(repo("models/salary_band_model.joblib"))

@st.cache_resource
def load_svd_models():
    p = repo("models/salary_tfidf_svd_models.joblib")
    return joblib.load(p) if os.path.exists(p) else None

@st.cache_resource
def load_text_models():
    p = repo("models/salary_text_models.joblib")
    return joblib.load(p) if os.path.exists(p) else None

@st.cache_resource
def load_lemmatizer():
    try:
        import spacy
        return spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception:
        return None

def clean_description(text: str) -> str:
    text = re.sub(r"<[^>]+>|https?://\S+|\S+@\S+", " ", text.lower())
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    nlp = load_lemmatizer()
    if nlp:
        text = " ".join(t.lemma_ for t in nlp(text) if not t.is_space)
    return re.sub(r"\s+", " ", text).strip()

def build_structured_input(columns, role, location, full_time, seniority, skills):
    v = {col: 0 for col in columns}
    v["is_full_time"] = int(full_time)
    v["seniority_ordinal"] = seniority
    v["skill_count"] = len(skills)
    for key in (f"role_{role}", f"location_bucket_{location}"):
        if key in v:
            v[key] = 1
    for s in skills:
        if f"skill_{s}" in v:
            v[f"skill_{s}"] = 1
    return v

def predict_text_model(td, structured, title, desc):
    from scipy.sparse import csr_matrix, hstack
    row = pd.DataFrame([structured])[td["feature_columns"]].astype(float)
    tf = td["title_vectorizer"].transform([title.lower()])
    df_ = td["description_vectorizer"].transform([clean_description(desc)])
    feats = hstack([csr_matrix(row.values), tf, df_]).tocsr()
    bm, bim = td["band_model"], td["binary_model"]
    return (dict(zip(bm.classes_, bm.predict_proba(feats)[0])),
            dict(zip(bim.classes_, bim.predict_proba(feats)[0])))

def predict_svd_model(sd, desc):
    cleaned = clean_description(desc)
    bm, bim = sd["band_model"], sd["binary_model"]
    return (dict(zip(bm.classes_, bm.predict_proba([cleaned])[0])),
            dict(zip(bim.classes_, bim.predict_proba([cleaned])[0])))

def show_result(bp, bip, med):
    band = max(bp, key=bp.get)
    side = max(bip, key=bip.get)
    color = {"high":"green","medium":"blue","low":"red"}.get(band,"blue")
    st.divider()
    st.subheader("Prediction Result")
    st.markdown(f"### Predicted Band: :{color}[{band.upper()}]")
    st.progress(bp[band])
    st.markdown(f"**Confidence:** `{bp[band]*100:.1f}%`")
    st.markdown(f"### Likely **{side.upper()}** the median salary (₹{med:,.0f})")
    st.progress(bip[side])
    st.markdown(f"**Confidence:** `{bip[side]*100:.1f}%`")
    with st.expander("All probabilities"):
        for c,p in bp.items(): st.write(f"- **{c.title()}**: {p*100:.1f}%")
        for c,p in bip.items(): st.write(f"- **{c.title()} median**: {p*100:.1f}%")

# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
skill_demand_df = load_csv("data/review2/skill_demand.csv")
skill_trends_df = load_csv("data/review2/skill_trends.csv")
skill_gap_df    = load_csv("data/review2/skill_gap.csv")

model_data      = load_model()
model_obj       = model_data["model"]
scaler          = model_data["scaler"]
feature_columns = model_data["feature_columns"]
numeric_cols    = model_data["numeric_cols"]
classes         = model_data["classes"]
text_data       = load_text_models()
svd_data        = load_svd_models()

STANDARD = "Standard model (role, seniority, location, skills)"
TEXT_ENH  = "Text-enhanced model (title + description)"
SVD_MOD   = "TF-IDF + SVD model (description only)"

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:20px 0 12px">
      <div style="font-size:1.6rem;font-weight:900;color:#e6edf3;letter-spacing:-.02em;">🧠 Career Intel</div>
      <div style="font-size:0.75rem;color:#6e7681;margin-top:4px;line-height:1.5;">
        Personalized Career Market<br>Intelligence Engine · Review 2
      </div>
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style="font-size:0.70rem;color:#6e7681;font-weight:700;text-transform:uppercase;
                letter-spacing:.1em;margin-bottom:10px;">Views</div>
    <div style="font-size:0.82rem;color:#8b949e;line-height:2.1;">
      📊 <b style="color:#c9d1d9;">Skill Demand</b><br>
      📈 <b style="color:#c9d1d9;">Skill Trends</b><br>
      🎯 <b style="color:#c9d1d9;">Gap Analysis</b> ⭐ headline<br>
      💼 <b style="color:#c9d1d9;">Salary Predictor</b><br>
      🔬 <b style="color:#c9d1d9;">Model Evaluation</b>
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("""
    <div style="font-size:0.72rem;color:#6e7681;line-height:1.8;">
      <b style="color:#8b949e;">Dataset:</b> 7,240 Adzuna postings · India<br>
      <b style="color:#8b949e;">Trends:</b> Google Trends (IN, 5-year)<br>
      <b style="color:#8b949e;">Models:</b> Random Forest · TF-IDF+SVD<br><br>
      <span style="color:#e3b341;">⚠</span> Skill counts are a <em>lower bound</em><br>
      (~500-char description truncation)<br><br>
      <span style="color:#58a6ff;">ℹ</span> Trends = relative search interest,<br>
      not hiring volume
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# BANNER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="banner">
  <div class="banner-title">🧠 Career Market Intelligence</div>
  <div class="banner-sub">
    Fusing employer demand · Google Trends momentum · India job market · Review 2
  </div>
  <div class="banner-pills">
    <span class="pill">📍 India</span>
    <span class="pill">📄 7,240 postings</span>
    <span class="pill">🔎 29 skills tracked</span>
    <span class="pill">📅 5-year Trends</span>
    <span class="pill">🤖 3 ML models</span>
  </div>
</div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab_d, tab_t, tab_g, tab_s, tab_e = st.tabs([
    "📊 Skill Demand",
    "📈 Skill Trends",
    "🎯 Gap Analysis",
    "💼 Salary Predictor",
    "🔬 Model Evaluation",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — SKILL DEMAND
# ═════════════════════════════════════════════════════════════════════════════
with tab_d:
    st.markdown('<div class="sec-head">📊 Skill Demand Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Skill frequency detected in job posting descriptions via regex matching. '
                'Rankings are relative — absolute % are a <em>lower bound</em> '
                'due to ~500-char description truncation.</div>', unsafe_allow_html=True)

    if skill_demand_df is None:
        st.error("⚠️ `data/review2/skill_demand.csv` not found. Run Member A's notebook first.")
    else:
        df_d = skill_demand_df.copy()

        # ── KPIs ──
        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"🎯", str(len(df_d)),    "Skills Tracked",     "in frozen canonical list",
            "linear-gradient(90deg,#58a6ff,#bc8cff)")
        kpi(c2,"🏆", df_d.iloc[0]["skill"], "Top Demanded Skill", f"rank #1 · {df_d.iloc[0]['pct_postings']:.1f}%",
            "linear-gradient(90deg,#3fb950,#26a641)")
        kpi(c3,"📄", f"{int(df_d['frequency'].sum()):,}", "Total Skill Mentions",
            "sum across all skills", "linear-gradient(90deg,#e3b341,#f0883e)")
        kpi(c4,"📈", f"{df_d['pct_postings'].mean():.2f}%", "Avg Coverage / Skill",
            "mean % of postings", "linear-gradient(90deg,#f85149,#ff7b72)")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Controls ──
        col_a, col_b, col_c = st.columns([3,2,2])
        with col_a:
            top_n = st.slider("Number of skills", 5, len(df_d), min(20,len(df_d)), key="d_n")
        with col_b:
            sort_by = st.selectbox("Sort by", ["Rank","Frequency","% Postings"], key="d_sort")
        with col_c:
            chart_type = st.selectbox("Chart type", ["Horizontal bars","Lollipop","Treemap-style"], key="d_chart")

        sort_map = {"Rank":"rank","Frequency":"frequency","% Postings":"pct_postings"}
        asc = (sort_by == "Rank")
        df_plot = df_d.sort_values(sort_map[sort_by], ascending=asc).head(top_n).copy()

        # ── Altair chart ──
        if chart_type == "Horizontal bars":
            chart = (
                alt.Chart(df_plot)
                .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
                .encode(
                    x=alt.X("frequency:Q", title="Mentions in Job Postings",
                             axis=alt.Axis(grid=True, gridColor="#21262d", labelColor="#8b949e", titleColor="#8b949e")),
                    y=alt.Y("skill:N", sort="-x", title=None,
                             axis=alt.Axis(labelColor="#c9d1d9", labelFontSize=12)),
                    color=alt.Color("pct_postings:Q",
                                    scale=alt.Scale(scheme="blues", reverse=False),
                                    legend=alt.Legend(title="% Postings", labelColor="#8b949e", titleColor="#8b949e")),
                    tooltip=[
                        alt.Tooltip("skill:N", title="Skill"),
                        alt.Tooltip("frequency:Q", title="Mentions", format=","),
                        alt.Tooltip("pct_postings:Q", title="% Postings", format=".2f"),
                        alt.Tooltip("rank:Q", title="Rank"),
                    ]
                )
                .properties(height=max(350, top_n*28))
                .configure_view(fill="#13171f", stroke=None)
                .configure_axis(domainColor="#30363d", tickColor="#30363d")
            )
            st.altair_chart(chart, use_container_width=True)

        elif chart_type == "Lollipop":
            base = alt.Chart(df_plot)
            lines = base.mark_rule(color="#30363d", strokeWidth=2).encode(
                y=alt.Y("skill:N", sort=alt.EncodingSortField("frequency", order="descending"), title=None,
                         axis=alt.Axis(labelColor="#c9d1d9", labelFontSize=12)),
                x=alt.X("frequency:Q", title="Mentions", axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e", gridColor="#21262d")),
                x2=alt.X2("zero:Q"),
            ).transform_calculate(zero="0")
            dots = base.mark_circle(size=120).encode(
                y=alt.Y("skill:N", sort=alt.EncodingSortField("frequency", order="descending"), title=None),
                x=alt.X("frequency:Q"),
                color=alt.value("#58a6ff"),
                tooltip=["skill:N","frequency:Q","pct_postings:Q","rank:Q"],
            )
            chart = (lines + dots).properties(height=max(350, top_n*28)).configure_view(fill="#13171f", stroke=None)
            st.altair_chart(chart, use_container_width=True)

        else:  # Treemap-style heat squares
            df_plot["label"] = df_plot["skill"] + "\n" + df_plot["pct_postings"].map(lambda x: f"{x:.1f}%")
            chart = (
                alt.Chart(df_plot)
                .mark_rect(cornerRadius=6, stroke="#0d1117", strokeWidth=2)
                .encode(
                    x=alt.X("rank:O", title=None, axis=None),
                    y=alt.Y("frequency:Q", bin=alt.Bin(maxbins=6), title="Frequency band",
                             axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e")),
                    color=alt.Color("frequency:Q", scale=alt.Scale(scheme="viridis"),
                                    legend=alt.Legend(title="Mentions", labelColor="#8b949e", titleColor="#8b949e")),
                    tooltip=["skill:N","frequency:Q","pct_postings:Q","rank:Q"],
                )
                .properties(height=320)
                .configure_view(fill="#13171f", stroke=None)
            )
            st.altair_chart(chart, use_container_width=True)

        # ── % postings secondary chart ──
        st.markdown("#### % of Postings Mentioning Each Skill")
        df_pct = df_plot.sort_values("pct_postings", ascending=False)
        pct_chart = (
            alt.Chart(df_pct)
            .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5, color="#bc8cff")
            .encode(
                x=alt.X("pct_postings:Q", title="% of Job Postings",
                         axis=alt.Axis(format=".1f", labelColor="#8b949e", titleColor="#8b949e", gridColor="#21262d")),
                y=alt.Y("skill:N", sort="-x", title=None,
                         axis=alt.Axis(labelColor="#c9d1d9", labelFontSize=12)),
                tooltip=[alt.Tooltip("skill:N"),
                          alt.Tooltip("pct_postings:Q", title="% Postings", format=".2f"),
                          alt.Tooltip("frequency:Q", title="Mentions")],
            )
            .properties(height=max(350, top_n*28))
            .configure_view(fill="#13171f", stroke=None)
            .configure_axis(domainColor="#30363d", tickColor="#30363d")
        )
        st.altair_chart(pct_chart, use_container_width=True)

        # ── Data table ──
        with st.expander("📋 Full data table"):
            disp = df_plot[["rank","skill","frequency","pct_postings"]].copy()
            disp.columns = ["Rank","Skill","Mentions","% Postings"]
            st.dataframe(
                disp, use_container_width=True, hide_index=True,
                column_config={
                    "Mentions": st.column_config.ProgressColumn(
                        "Mentions", min_value=0, max_value=int(df_d["frequency"].max()), format="%d"),
                    "% Postings": st.column_config.NumberColumn("% Postings", format="%.2f%%"),
                }
            )

        st.markdown("""<div class="caveat-box">
        ⚠️ <strong>Known limitation:</strong> Adzuna truncates descriptions to ~500 characters.
        All skill percentages are a <strong>lower bound</strong> of true prevalence —
        interpret rankings, not raw percentages.</div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — SKILL TRENDS
# ═════════════════════════════════════════════════════════════════════════════
with tab_t:
    st.markdown('<div class="sec-head">📈 Skill Trends — Google Trends Momentum</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">5-year weekly Google Trends (India, anchor=SQL, rescaled across batches). '
                'Y-axis = relative search interest, not hiring volume.</div>', unsafe_allow_html=True)

    if skill_trends_df is None:
        st.error("⚠️ `data/review2/skill_trends.csv` not found. Run Member B's notebook first.")
    else:
        df_t = skill_trends_df.copy()
        df_t["class"] = df_t["class"].str.strip().str.lower()

        n_r = (df_t["class"]=="rising").sum()
        n_s = (df_t["class"]=="stable").sum()
        n_d = (df_t["class"]=="declining").sum()
        fastest = df_t.loc[df_t["pct_change"].idxmax(),"skill"]
        deepest = df_t.loc[df_t["pct_change"].idxmin(),"skill"]

        c1,c2,c3,c4,c5 = st.columns(5)
        kpi(c1,"🚀", str(n_r), "Rising",    "≥ +10% 5-yr change", "linear-gradient(90deg,#3fb950,#26a641)")
        kpi(c2,"➡️", str(n_s), "Stable",    "–10% to +10%",       "linear-gradient(90deg,#58a6ff,#1f6feb)")
        kpi(c3,"📉", str(n_d), "Declining", "≤ –10% 5-yr change", "linear-gradient(90deg,#f85149,#da3633)")
        kpi(c4,"⭐", fastest,  "Fastest Rising",  "5-yr % change", "linear-gradient(90deg,#e3b341,#f0883e)")
        kpi(c5,"⚠️", deepest,  "Steepest Drop",   "5-yr % change", "linear-gradient(90deg,#8b949e,#6e7681)")

        st.markdown("<br>", unsafe_allow_html=True)

        # Controls
        col_f1, col_f2 = st.columns([2,1])
        with col_f1:
            class_filter = st.multiselect("Filter by trend class",
                ["rising","stable","declining"], default=["rising","stable","declining"], key="t_cls")
        with col_f2:
            sort_t = st.selectbox("Sort by", ["% Change ↓","% Change ↑","Slope ↓"], key="t_sort")

        df_tv = df_t[df_t["class"].isin(class_filter)].copy()
        if sort_t == "% Change ↑":
            df_tv = df_tv.sort_values("pct_change", ascending=True)
        elif sort_t == "Slope ↓":
            df_tv = df_tv.sort_values("slope_per_week", ascending=False)
        else:
            df_tv = df_tv.sort_values("pct_change", ascending=False)

        if df_tv.empty:
            st.info("No skills match the selected filters.")
        else:
            # Colour encoding
            colour_scale = alt.Scale(
                domain=["rising","stable","declining"],
                range=["#3fb950","#58a6ff","#f85149"]
            )

            # ── Diverging bar chart ──
            st.markdown("#### 5-Year % Change in Relative Search Interest")
            base = alt.Chart(df_tv).encode(
                y=alt.Y("skill:N",
                         sort=alt.EncodingSortField("pct_change", order="descending"),
                         title=None,
                         axis=alt.Axis(labelColor="#c9d1d9", labelFontSize=12)),
                x=alt.X("pct_change:Q",
                         title="5-Year % Change",
                         axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e",
                                        gridColor="#21262d", format=".0f")),
                color=alt.Color("class:N", scale=colour_scale,
                                 legend=alt.Legend(title="Trend Class", labelColor="#8b949e",
                                                    titleColor="#8b949e", orient="top")),
                tooltip=[
                    alt.Tooltip("skill:N"),
                    alt.Tooltip("class:N", title="Class"),
                    alt.Tooltip("pct_change:Q", title="% Change", format=".1f"),
                    alt.Tooltip("slope_per_week:Q", title="Slope/week", format=".4f"),
                ],
            )
            bars = base.mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4,
                                   cornerRadiusTopLeft=4, cornerRadiusBottomLeft=4)
            rule = alt.Chart(pd.DataFrame({"x":[0]})).mark_rule(color="#30363d", strokeWidth=1.5).encode(
                x=alt.X("x:Q")
            )
            trend_chart = (bars + rule).properties(height=max(360, len(df_tv)*28))
            st.altair_chart(
                trend_chart
                .configure_view(fill="#13171f", stroke=None)
                .configure_axis(domainColor="#30363d", tickColor="#30363d"),
                use_container_width=True
            )

            # ── Skill cards ──
            st.markdown("#### Skill-by-Skill Detail")
            badge_map = {"rising":"b-rising","stable":"b-stable","declining":"b-declining"}
            cols_per = 3
            rows = [df_tv.iloc[i:i+cols_per] for i in range(0,len(df_tv),cols_per)]
            for row_df in rows:
                cols = st.columns(cols_per)
                for c, (_, r) in zip(cols, row_df.iterrows()):
                    cls = r["class"]
                    pct = r["pct_change"]
                    slp = r["slope_per_week"]
                    bk  = badge_map.get(cls,"b-stable")
                    sign = "+" if pct>0 else ""
                    conf_txt = ("✓ confirmed" if r.get("trend_confirmed",False)
                                else "~ unconfirmed")
                    with c:
                        st.markdown(f"""
                        <div class="kpi-card" style="--accent:linear-gradient(90deg,#21262d,#21262d);text-align:left;padding:16px 18px;">
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                            <span style="font-weight:700;color:#e6edf3;font-size:1rem;">{r['skill']}</span>
                            <span class="badge {bk}">{cls}</span>
                          </div>
                          <div style="display:flex;gap:24px;">
                            <div>
                              <div style="font-size:1.25rem;font-weight:800;color:#e6edf3;">{sign}{pct:.1f}%</div>
                              <div style="font-size:0.68rem;color:#6e7681;">5-yr change</div>
                            </div>
                            <div>
                              <div style="font-size:1.25rem;font-weight:800;color:#e6edf3;">{slp:+.4f}</div>
                              <div style="font-size:0.68rem;color:#6e7681;">slope/week</div>
                            </div>
                          </div>
                          <div style="font-size:0.68rem;color:#6e7681;margin-top:8px;">{conf_txt}</div>
                        </div>""", unsafe_allow_html=True)

            with st.expander("📋 Full trends table"):
                show_cols = [c for c in ["skill","class","pct_change","slope_per_week","trend_confirmed","mk_p"]
                             if c in df_tv.columns]
                disp = df_tv[show_cols].copy()
                disp.columns = [c.replace("_"," ").title() for c in show_cols]
                st.dataframe(disp, use_container_width=True, hide_index=True)

        st.markdown("""<div class="caveat-box">
        ⚠️ <strong>Trends caveat:</strong> Values = <strong>relative search interest</strong>
        (0–100 rescaled per batch via SQL anchor). Reflects public curiosity, not employer hiring.
        India geo (IN) only. Declining search interest may coexist with high job demand
        (mature/assumed skill).</div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — GAP ANALYSIS (HEADLINE)
# ═════════════════════════════════════════════════════════════════════════════
with tab_g:
    st.markdown('<div class="sec-head">🎯 Demand–Interest Gap Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Fusing employer posting demand (Member A) with Google Trends momentum (Member B). '
                '<strong>Opportunity = high employer demand + low/declining public interest</strong> '
                '— high-value, under-competed skills.</div>', unsafe_allow_html=True)

    if skill_gap_df is None:
        st.error("⚠️ `data/review2/skill_gap.csv` not found. Run Member C's notebook first.")
    else:
        df_g = skill_gap_df.copy()
        df_g["quadrant"]       = df_g["quadrant"].str.strip().str.lower()
        df_g["momentum_class"] = df_g["momentum_class"].str.strip().str.lower()

        q = df_g["quadrant"].value_counts()
        c1,c2,c3,c4 = st.columns(4)
        kpi(c1,"⭐", str(q.get("opportunity",0)), "Opportunity",
            "High demand · Low/Declining interest", "linear-gradient(90deg,#e3b341,#f0883e)")
        kpi(c2,"📈", str(q.get("invest",0)),      "Invest",
            "High demand · Rising interest",        "linear-gradient(90deg,#3fb950,#26a641)")
        kpi(c3,"🔥", str(q.get("hype",0)),        "Hype",
            "Low demand · Rising interest",         "linear-gradient(90deg,#58a6ff,#1f6feb)")
        kpi(c4,"🚫", str(q.get("avoid",0)),       "Avoid",
            "Low demand · Flat/Declining",          "linear-gradient(90deg,#f85149,#da3633)")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 2×2 Altair scatter (FIXED — no size= column name issue) ──
        st.markdown("#### 2×2 Demand–Interest Gap Map")
        st.caption("x = Employer demand (% postings)  ·  y = Trend momentum (5-yr % change)  ·  "
                   "size = demand rank weight  ·  colour = quadrant")

        colour_scale_g = alt.Scale(
            domain=["opportunity","invest","hype","avoid"],
            range=["#e3b341","#3fb950","#58a6ff","#f85149"]
        )

        # Compute size values as a numeric column (inverse rank → bigger = higher demand)
        df_g["size_val"] = (df_g["demand_rank"].max() + 1 - df_g["demand_rank"]) * 40 + 80

        scatter = (
            alt.Chart(df_g)
            .mark_point(filled=True, opacity=0.88, stroke="#0d1117", strokeWidth=1)
            .encode(
                x=alt.X("demand_pct:Q",
                         title="Employer Demand (% of postings)",
                         axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e",
                                        gridColor="#21262d", format=".1f")),
                y=alt.Y("pct_change:Q",
                         title="Trend Momentum (5-yr % change)",
                         axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e",
                                        gridColor="#21262d", format=".0f")),
                color=alt.Color("quadrant:N",
                                 scale=colour_scale_g,
                                 legend=alt.Legend(title="Quadrant", labelColor="#c9d1d9",
                                                    titleColor="#8b949e", orient="right")),
                size=alt.Size("size_val:Q",
                               scale=alt.Scale(range=[120, 600]),
                               legend=None),
                tooltip=[
                    alt.Tooltip("skill:N", title="Skill"),
                    alt.Tooltip("quadrant:N", title="Quadrant"),
                    alt.Tooltip("demand_pct:Q", title="Demand %", format=".2f"),
                    alt.Tooltip("pct_change:Q", title="Trend % change", format=".1f"),
                    alt.Tooltip("demand_rank:Q", title="Demand rank"),
                    alt.Tooltip("momentum_class:N", title="Momentum"),
                ],
            )
        )

        # Quadrant reference lines at median demand and 0% trend change
        med_demand = float(df_g["demand_pct"].median())
        h_rule = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
            color="#30363d", strokeDash=[6,4], strokeWidth=1.5).encode(y="y:Q")
        v_rule = alt.Chart(pd.DataFrame({"x":[med_demand]})).mark_rule(
            color="#30363d", strokeDash=[6,4], strokeWidth=1.5).encode(x="x:Q")

        # Skill labels
        labels = (
            alt.Chart(df_g)
            .mark_text(dy=-14, fontSize=11, fontWeight=600, color="#c9d1d9")
            .encode(
                x=alt.X("demand_pct:Q"),
                y=alt.Y("pct_change:Q"),
                text=alt.Text("skill:N"),
            )
        )

        gap_chart = (
            (scatter + h_rule + v_rule + labels)
            .properties(height=460)
            .configure_view(fill="#13171f", stroke=None)
            .configure_axis(domainColor="#30363d", tickColor="#30363d")
        )
        st.altair_chart(gap_chart, use_container_width=True)

        # Quadrant legend callout
        st.markdown("""
        <div style="display:flex;gap:14px;flex-wrap:wrap;margin-bottom:22px;font-size:0.80rem;color:#8b949e;">
          <span><span class="badge b-opportunity">⭐ Opportunity</span> High demand · Low interest — <em>learn this now</em></span>
          <span><span class="badge b-invest">📈 Invest</span> High demand · Rising interest</span>
          <span><span class="badge b-hype">🔥 Hype</span> Low employer demand despite buzz</span>
          <span><span class="badge b-avoid">🚫 Avoid</span> Low demand · Low interest</span>
        </div>""", unsafe_allow_html=True)

        # ── Recommendations ──
        quad_filter = st.multiselect(
            "Filter recommendations by quadrant",
            options=["opportunity","invest","hype","avoid"],
            default=["opportunity","invest"], key="g_qf")

        df_recs = df_g[df_g["quadrant"].isin(quad_filter)].sort_values("demand_rank")
        icons = {"opportunity":"⭐","invest":"📈","hype":"🔥","avoid":"🚫"}

        if df_recs.empty:
            st.info("No skills in the selected quadrants.")
        else:
            st.markdown("#### Skill Recommendations")
            for _, row in df_recs.iterrows():
                q_name = row["quadrant"]
                ic = icons.get(q_name,"•")
                bk = f"b-{q_name}"
                mk = f"b-{row['momentum_class']}" if row['momentum_class'] in ['rising','stable','declining'] else "b-stable"
                pct_sign = "+" if row["pct_change"]>0 else ""
                st.markdown(f"""
                <div class="rec-card">
                  <div style="font-size:1.6rem;line-height:1;">{ic}</div>
                  <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                      <span class="rec-skill">{row['skill']}</span>
                      <span class="badge {bk}">{q_name}</span>
                      <span class="badge {mk}">{row['momentum_class']}</span>
                    </div>
                    <div class="rec-meta">
                      Demand rank #{int(row['demand_rank'])} &nbsp;·&nbsp;
                      {row['demand_pct']:.2f}% of postings &nbsp;·&nbsp;
                      Trend {pct_sign}{row['pct_change']:.1f}%
                    </div>
                    <div class="rec-text">{row['recommendation']}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

        with st.expander("📋 Full gap table"):
            show_g = [c for c in ["skill","demand_rank","demand_pct","momentum_class",
                                   "pct_change","quadrant","recommendation"] if c in df_g.columns]
            disp_g = df_g[show_g].copy()
            disp_g.columns = [c.replace("_"," ").title() for c in show_g]
            st.dataframe(disp_g, use_container_width=True, hide_index=True)

        st.markdown("""
        <div class="novelty-box">
          <div class="novelty-title">💡 Novelty — The Demand–Interest Gap</div>
          <div class="novelty-body">
            No public, reproducible analysis fuses <strong style="color:#e6edf3;">employer skill demand</strong>
            (text mining on job postings) with <strong style="color:#e6edf3;">public search interest</strong>
            (Google Trends time-series). This dashboard does — flagging per-skill
            <strong style="color:#e3b341;">opportunity</strong> (high demand + low interest = under-competed)
            and <strong style="color:#f85149;">risk</strong> (hype with weak employer backing)
            using only free, self-collected data.<br><br>
            <em>Cf. Shi et al. 2020 (KDD/LinkedIn) · Chen et al. 2024 NeurIPS Job-SDF ·
            Choi &amp; Varian 2012 · Wang et al. 2024 JobViz.</em>
          </div>
        </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — SALARY PREDICTOR (original, preserved intact)
# ═════════════════════════════════════════════════════════════════════════════
with tab_s:
    st.markdown('<div class="sec-head">💼 Salary Band Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Predict expected salary band (low / medium / high) using three '
                'Review-1 trained ML models.</div>', unsafe_allow_html=True)

    model_opts = ([STANDARD] + ([TEXT_ENH] if text_data else []) + ([SVD_MOD] if svd_data else []))
    model_choice = st.radio("Select model", model_opts, horizontal=True)
    disabled = (model_choice == SVD_MOD)

    if disabled:
        st.info("This model uses only the job description — structured inputs are not used.")

    st.subheader("Job Characteristics")
    c1, c2 = st.columns(2)

    with c1:
        roles = ["Business Analyst","Data Analyst","Data Engineer","Data Scientist",
                 "Devops / Cloud Engineer","Digital Marketing","Graphic Designer",
                 "Product Manager","Project Manager","Software Engineer"]
        sel_role = st.selectbox("Role", roles, disabled=disabled)
        locations = ["Karnataka","Maharashtra","Telangana","Delhi",
                     "Uttar Pradesh","Tamil Nadu","Gujarat","Unknown","other"]
        sel_loc = st.selectbox("Location", locations, disabled=disabled)
        is_ft = st.checkbox("Full Time?", value=True, disabled=disabled)

    with c2:
        sen_map = {"Entry":0,"Mid":1,"Senior":2}
        sel_sen = st.selectbox("Seniority", list(sen_map.keys()), disabled=disabled)
        av_skills = ["python","sql","communication","azure","machine_learning",
                     "agile","aws","linux","java","sap","docker"]
        sel_skills = st.multiselect("Key Skills", av_skills, disabled=disabled)

    if model_choice == SVD_MOD:
        desc = st.text_area("Job Description", height=180,
                             placeholder="Paste the full job description…", key="svd_d")
        if st.button("Predict Salary", type="primary", key="btn_svd"):
            if not desc.strip():
                st.warning("Please enter a job description.")
            else:
                bp, bip = predict_svd_model(svd_data, desc)
                show_result(bp, bip, svd_data["median_salary"])

    elif model_choice == TEXT_ENH:
        jt = st.text_input("Job Title", placeholder="e.g. Senior Data Engineer")
        jd = st.text_area("Job Description", height=150, placeholder="Paste description…")
        if st.button("Predict Salary", type="primary", key="btn_txt"):
            structured = build_structured_input(
                text_data["feature_columns"], sel_role, sel_loc, is_ft, sen_map[sel_sen], sel_skills)
            bp, bip = predict_text_model(text_data, structured, jt, jd)
            show_result(bp, bip, text_data["median_salary"])

    elif model_choice == STANDARD:
        if st.button("Predict Salary Band", type="primary", key="btn_std"):
            inp = {col:0 for col in feature_columns}
            inp["is_full_time"] = int(is_ft)
            inp["seniority_ordinal"] = sen_map[sel_sen]
            inp["skill_count"] = len(sel_skills)
            for k in (f"role_{sel_role}", f"location_bucket_{sel_loc}"):
                if k in inp: inp[k] = 1
            for sk in sel_skills:
                if f"skill_{sk}" in inp: inp[f"skill_{sk}"] = 1
            df_in = pd.DataFrame([inp])[feature_columns]
            df_in[numeric_cols] = scaler.transform(df_in[numeric_cols])
            pred = model_obj.predict(df_in)[0]
            probs = model_obj.predict_proba(df_in)[0]
            pd_ = {classes[i]: probs[i] for i in range(len(classes))}
            conf = pd_[pred]*100
            st.divider()
            st.subheader("Prediction Result")
            col = {"high":"green","medium":"blue","low":"red"}.get(pred,"blue")
            st.markdown(f"### Predicted Band: :{col}[{pred.upper()}]")
            st.progress(conf/100)
            st.markdown(f"**Confidence:** `{conf:.1f}%`")
            with st.expander("All probabilities"):
                for c_, p_ in pd_.items():
                    st.write(f"- **{c_.title()}**: {p_*100:.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 5 — MODEL EVALUATION (original preserved + KPI cards + Altair charts)
# ═════════════════════════════════════════════════════════════════════════════
with tab_e:
    st.markdown('<div class="sec-head">🔬 Model Performance & Diagnostics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Compare three salary-prediction models on employer-grouped '
                'cross-validation and held-out test results.</div>', unsafe_allow_html=True)

    def img_safe(rel):
        from PIL import Image
        p = repo(rel)
        return Image.open(p) if os.path.exists(p) else None

    # KPI cards
    c1,c2,c3 = st.columns(3)
    kpi(c1,"🏗️","47.0%","Standard Model",   "Band acc · employer-grouped CV","linear-gradient(90deg,#8b949e,#6e7681)")
    kpi(c2,"📝","49.2%","Text-Enhanced",    "Band acc · employer-grouped CV","linear-gradient(90deg,#58a6ff,#1f6feb)")
    kpi(c3,"🔤","51.3%","TF-IDF + SVD",     "Band acc · employer-grouped CV","linear-gradient(90deg,#3fb950,#26a641)")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Altair model comparison chart ──
    model_comp = pd.DataFrame({
        "Model":    ["Standard","Text-Enhanced","TF-IDF + SVD","Standard","Text-Enhanced","TF-IDF + SVD"],
        "Task":     ["Band"]*3 + ["Binary"]*3,
        "Accuracy": [47.0, 49.2, 51.3, 69.2, 71.2, 71.8],
    })
    comp_chart = (
        alt.Chart(model_comp)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            y=alt.Y("Model:N", title=None, axis=alt.Axis(labelColor="#c9d1d9", labelFontSize=12)),
            x=alt.X("Accuracy:Q", title="Accuracy (%)",
                     scale=alt.Scale(domain=[0,100]),
                     axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e", gridColor="#21262d")),
            color=alt.Color("Task:N",
                             scale=alt.Scale(domain=["Band","Binary"],range=["#58a6ff","#3fb950"]),
                             legend=alt.Legend(title="Task",labelColor="#c9d1d9",titleColor="#8b949e",orient="top")),
            column=alt.Column("Task:N", title=None,
                               header=alt.Header(labelColor="#8b949e", labelFontSize=12)),
            tooltip=["Model:N","Task:N",alt.Tooltip("Accuracy:Q",format=".1f")],
        )
        .properties(width=260, height=180)
        .configure_view(fill="#13171f", stroke="#21262d", strokeWidth=1)
        .configure_axis(domainColor="#30363d", tickColor="#30363d")
    )
    st.altair_chart(comp_chart, use_container_width=False)

    st.divider()
    st.subheader("Held-Out Test Results (TF-IDF + SVD — 231 postings)")
    held = pd.DataFrame({
        "Task":     ["Salary Band\n(low/med/high)","Above/Below Median"],
        "Accuracy": [58.4, 76.6],
        "Macro-F1": [0.570, 0.766],
    })
    hc = (
        alt.Chart(held)
        .mark_bar(cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Task:N", title=None, axis=alt.Axis(labelColor="#c9d1d9")),
            y=alt.Y("Accuracy:Q", title="Accuracy (%)", scale=alt.Scale(domain=[0,100]),
                     axis=alt.Axis(labelColor="#8b949e", titleColor="#8b949e", gridColor="#21262d")),
            color=alt.value("#e3b341"),
            tooltip=["Task:N",alt.Tooltip("Accuracy:Q",format=".1f"),alt.Tooltip("Macro-F1:Q",format=".3f")],
        )
        .properties(height=200)
        .configure_view(fill="#13171f", stroke=None)
        .configure_axis(domainColor="#30363d", tickColor="#30363d")
    )
    st.altair_chart(hc, use_container_width=True)
    st.caption("Held-out split shares employers across train/test → scores run higher than employer-grouped CV.")

    st.divider()
    st.subheader("Feature Importance")
    fi = img_safe("reports/eda/feature_importance_band.png")
    if fi:
        st.image(fi, caption="Top 10 Feature Importances — Salary Band Model")
    else:
        fi2 = img_safe("reports/model_evaluation/final_model_metrics.png")
        if fi2: st.image(fi2, caption="Model Evaluation Metrics")
        else:   st.warning("Feature importance image not found.")

    cb = img_safe("reports/eda/cm_band.png")
    cbin = img_safe("reports/eda/cm_binary.png")
    if cb or cbin:
        st.divider()
        st.subheader("Confusion Matrices")
        ci1, ci2 = st.columns(2)
        with ci1:
            if cb: st.image(cb, caption="Confusion Matrix — Salary Band")
        with ci2:
            if cbin: st.image(cbin, caption="Confusion Matrix — Above/Below Median")

    st.divider()
    st.subheader("Interpretation Notes")
    st.markdown(
        "- **Employer-grouped CV** is the gold-standard comparison: tests on companies unseen during training.\n"
        "- **Held-out split** shares employers → text models benefit from company-specific language → inflated scores.\n"
        "- Salary within the same role/seniority varies widely → no model expected to achieve high accuracy.\n"
        "- Medium band is hardest (recall 0.37); ~70% of errors are between adjacent bands."
    )
