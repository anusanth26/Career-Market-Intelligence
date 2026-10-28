"""Writes workbook/career_market.twb: five dashboards over the CSVs in extracts/.

    python tableau_dashboard/build_workbook.py

Filters are Tableau parameters (Role, Seniority, State, Contract, Salary range) feeding one boolean
calculated field, so one control updates every postings sheet on a page. Data sources are the .hyper extracts from build_hyper.py (Tableau Public only saves extracts). Open the .twb in Tableau Public.
"""
import os
from xml.sax.saxutils import escape, quoteattr

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(HERE, "extracts")
OUT = os.path.join(HERE, "workbook", "career_market.twb")
BLUE, DARK, PALE, INK, LINE, CANVAS = "#1F5FBF", "#0F2F66", "#9DB7DF", "#1B2A3A", "#D5DBE2", "#EEF1F4"
VER = "18.1"


def q(s):
    return quoteattr(str(s))


# ---------------------------------------------------------------- data sources
class DS:
    def __init__(self, key, csv):
        self.key, self.csv, self.id = key, csv, f"federated.{key}"
        df = pd.read_csv(os.path.join(EXT, csv))
        self.cols = {}
        for c, t in df.dtypes.items():
            self.cols[c] = ("date" if c.endswith("_date") or c == "date" else
                            "integer" if str(t).startswith("int") else "real" if str(t).startswith("float")
                            else "boolean" if t == bool else "string")
        self.calcs = {}  # caption -> dict(id, datatype, role, type, formula)

    def calc(self, caption, formula, datatype, role="measure", agg=False):
        cid = f"[Calculation_{self.key}_{len(self.calcs) + 1}]"
        self.calcs[caption] = dict(id=cid, datatype=datatype, role=role, formula=formula, agg=agg)
        return caption

    def xml(self):
        cols = "".join(f"<column datatype='{t}' name={q(c)} ordinal='{i}' />" for i, (c, t) in enumerate(self.cols.items()))
        calcs = ""
        for cap, c in self.calcs.items():
            typ = "quantitative" if c["datatype"] in ("integer", "real") else "nominal"
            calcs += (f"<column caption={q(cap)} datatype='{c['datatype']}' name={q(c['id'])} role='{c['role']}' type='{typ}'>"
                      f"<calculation class='tableau' formula={q(c['formula'])} /></column>")
        hy = os.path.join(EXT, "hyper", self.csv.replace(".csv", ".hyper"))
        return (f"<datasource caption={q(self.key)} inline='true' name={q(self.id)} version='{VER}'>"
                f"<connection class='federated'><named-connections><named-connection caption={q(self.key)} name='hyper.{self.key}'>"
                f"<connection authentication='auth-none' class='hyper' dbname={q(hy)} default-settings='yes' schema='Extract' sslmode='' tablename='Extract' username='' />"
                f"</named-connection></named-connections>"
                f"<relation connection='hyper.{self.key}' name='Extract' table='[Extract].[Extract]' type='table' /></connection>"
                f"<aliases enabled='yes' />{calcs}</datasource>")


class Params:
    """Parameters datasource. Each parameter is a list of strings or a numeric range."""

    def __init__(self):
        self.items = []  # (internal name, caption, datatype, default, members | (min, max, step))

    def add(self, caption, default, members=None, rng=None):
        name = f"[Parameter {len(self.items) + 1}]"
        self.items.append((name, caption, "string" if members else "real", default, members, rng))
        return f"[Parameters].{name}"

    def xml(self):
        out = ""
        for name, cap, dt, default, members, rng in self.items:
            v = f'"{default}"' if dt == "string" else str(float(default))
            dom = ("<members>" + "".join(f"<member value={q(chr(34) + m + chr(34))} />" for m in members) + "</members>") if members else \
                  f"<range granularity='{rng[2]}' max='{float(rng[1])}' min='{float(rng[0])}' />"
            out += (f"<column caption={q(cap)} datatype='{dt}' name='{name}' param-domain-type='{'list' if members else 'range'}' "
                    f"role='measure' type='{'nominal' if members else 'quantitative'}' value={q(v)}>"
                    f"<calculation class='tableau' formula={q(v)} />{dom}</column>")
        return f"<datasource hasconnection='false' inline='true' name='Parameters' version='{VER}'><aliases enabled='yes' />{out}</datasource>"

    def column_xml(self, name):
        for n, cap, dt, default, members, rng in self.items:
            if n == name:
                v = f'"{default}"' if dt == "string" else str(float(default))
                return (f"<column caption={q(cap)} datatype='{dt}' name='{n}' param-domain-type='{'list' if members else 'range'}' "
                        f"role='measure' type='{'nominal' if members else 'quantitative'}' value={q(v)}>"
                        f"<calculation class='tableau' formula={q(v)} /></column>")


PARAMS = Params()
postings, skills, pairs, trends = DS("postings", "postings.csv"), DS("skill_demand", "skill_demand.csv"), DS("skill_pairs", "skill_cooccurrence.csv"), DS("trends", "trends_long.csv")
modlong, confusion, importance, preds = (DS("model_long", "model_results_long.csv"), DS("confusion", "confusion_matrix.csv"),
                                         DS("importance", "feature_importance_top10.csv"), DS("predictions", "predictions.csv"))
ALL_DS = [postings, skills, pairs, trends, modlong, confusion, importance, preds]
DSMAP = {d.id: d for d in ALL_DS}

df_p = pd.read_csv(os.path.join(EXT, "postings.csv"))
roles = sorted(df_p.role.unique())
states = ["Karnataka", "Maharashtra", "Telangana", "Delhi", "Uttar Pradesh", "Tamil Nadu", "Gujarat", "Unknown", "other"]
all_states = ["All"] + df_p.location_region.fillna("Unknown").value_counts().index.tolist()
pm_role = PARAMS.add("Role", "All", ["All"] + roles)
pm_sen = PARAMS.add("Seniority", "All", ["All", "Entry", "Mid", "Senior"])
pm_state = PARAMS.add("State", "All", all_states)
pm_con = PARAMS.add("Contract", "All", ["All"] + sorted(df_p.contract_time.dropna().unique()))
pm_lo = PARAMS.add("Salary from (₹ lakh)", 1.0, rng=(1, 50, 0.5))
pm_hi = PARAMS.add("Salary to (₹ lakh)", 50.0, rng=(1, 50, 0.5))
pm_skill = PARAMS.add("Skill", "SQL", sorted(pd.read_csv(os.path.join(EXT, "trends_long.csv")).skill.unique()))
pm_task = PARAMS.add("Details for", "band", ["band", "binary"])
pm_prole = PARAMS.add("Role (what-if)", "Data Analyst", roles)
pm_psen = PARAMS.add("Seniority (what-if)", "Mid", ["Entry", "Mid", "Senior"])
pm_pstate = PARAMS.add("State (what-if)", "Karnataka", states)
pm_pcon = PARAMS.add("Contract (what-if)", "Full time", ["Full time", "Other contract"])
pm_pskill = PARAMS.add("Skills (what-if)", "Python + SQL", ["No listed skills", "Python + SQL", "Python + SQL + AWS", "Cloud stack (AWS, Azure, Docker, Linux)"])

def sel(param, field, extra=""):
    return f"(({param}='All') OR ({field}={param}))"

postings.calc("Keep", " AND ".join([
    sel(pm_role, "[role]"), sel(pm_sen, "[seniority_level]"), sel(pm_state, "[location_region]"), sel(pm_con, "[contract_time]"),
    f"(ISNULL([salary_mid]) OR ([salary_mid] >= {pm_lo} * 100000 AND [salary_mid] <= {pm_hi} * 100000))"]), "boolean", "dimension")
postings.calc("Postings", "COUNTD([job_id])", "integer", agg=True)
postings.calc("Roles", "COUNTD([role])", "integer", agg=True)
postings.calc("Employers", "COUNTD([employer])", "integer", agg=True)
postings.calc("Share with salary", "STR(ROUND(COUNT([salary_mid]) / COUNT([job_id]) * 100, 0)) + '%'", "string", agg=True)
postings.calc("Median salary", "'₹' + STR(ROUND(MEDIAN([salary_mid]) / 100000, 1)) + 'L'", "string", agg=True)
postings.calc("Median salary (₹ lakh)", "MEDIAN([salary_mid]) / 100000", "real", agg=True)
postings.calc("Salaries known", "COUNT([salary_mid])", "integer", agg=True)
postings.calc("Seniority known", "[seniority_level] <> 'Unknown'", "boolean", "dimension")
trends.calc("Keep skill", f"[skill] = {pm_skill}", "boolean", "dimension")
confusion.calc("Keep task", f"[task] = {pm_task}", "boolean", "dimension")
importance.calc("Keep task", f"[task] = {pm_task}", "boolean", "dimension")
pairs.calc("Pair", "[skill_a] + ' + ' + [skill_b]", "string", "dimension")
modlong.calc("Grouped band accuracy", "STR(ROUND(SUM(IF [task]='band' AND [evaluation]='employer_grouped_cv' AND [measure]='Model' THEN [value] END) * 100, 1)) + '%'", "string", agg=True)
modlong.calc("Grouped binary accuracy", "STR(ROUND(SUM(IF [task]='binary' AND [evaluation]='employer_grouped_cv' AND [measure]='Model' THEN [value] END) * 100, 1)) + '%'", "string", agg=True)
modlong.calc("Guess band", "STR(ROUND(SUM(IF [task]='band' AND [evaluation]='employer_grouped_cv' AND [measure]='Guessing' THEN [value] END) * 100, 1)) + '%'", "string", agg=True)
modlong.calc("Guess binary", "STR(ROUND(SUM(IF [task]='binary' AND [evaluation]='employer_grouped_cv' AND [measure]='Guessing' THEN [value] END) * 100, 1)) + '%'", "string", agg=True)
preds.calc("Keep profile", " AND ".join([f"[role] = {pm_prole}", f"[seniority] = {pm_psen}", f"[state] = {pm_pstate}",
                                         f"[contract] = {pm_pcon}", f"[skill_profile] = {pm_pskill}"]), "boolean", "dimension")
for b in ("low", "medium", "high"):
    preds.calc(f"P {b}", f"STR(ROUND(AVG([p_{b}]) * 100, 0)) + '%'", "string", agg=True)
preds.calc("Predicted band", "ATTR(UPPER(LEFT([predicted_band], 1)) + MID([predicted_band], 2))", "string", agg=True)
preds.calc("Confidence", "STR(ROUND(AVG([top_probability]) * 100, 0)) + '% confidence'", "string", agg=True)
PARAM_CAPS = {n: c for n, c, *_ in PARAMS.items}

# ---------------------------------------------------------------- worksheets
DER = {"none": ("None", "nk"), "sum": ("Sum", "qk"), "avg": ("Avg", "qk"), "med": ("Median", "qk"), "cnt": ("Count", "qk"),
       "ctd": ("CountD", "qk"), "usr": ("User", "nk"), "wk": ("Week-Trunc", "qk"), "attr": ("Attribute", "nk")}
ABBR = {"none": "none", "sum": "sum", "avg": "avg", "med": "med", "cnt": "cnt", "ctd": "ctd", "usr": "usr", "wk": "twk", "attr": "attr"}


class Sheet:
    def __init__(self, name, ds, rows=(), cols=(), mark="Bar", color=None, text=None, filters=(), title=None, fill=BLUE,
                 sort=None, label=False, cell=False):
        self.name, self.ds, self.rows, self.cols, self.mark = name, ds, list(rows), list(cols), mark
        self.color, self.text, self.filters, self.title, self.fill = color, text, list(filters), title or name, fill
        self.sort, self.label, self.cell = sort, label, cell

    def inst(self, spec):
        agg, field = spec.split(":", 1)
        d = self.ds
        if field in d.calcs:
            base = d.calcs[field]["id"]
            if d.calcs[field]["agg"]:
                agg = "usr"
        else:
            base = f"[{field}]"
        deriv, suf = DER[agg]
        if agg == "usr":
            typ = "quantitative" if d.calcs[field]["datatype"] in ("integer", "real") else "nominal"
            suf = "qk" if typ == "quantitative" else "nk"
        else:
            typ = "quantitative" if suf == "qk" else "nominal"
        name = f"[{ABBR[agg]}:{base.strip('[]')}:{suf}]"
        return dict(base=base, deriv=deriv, name=name, type=typ, field=field)

    def xml(self):
        d = self.ds
        specs = self.rows + self.cols + ([self.color] if self.color else []) + ([self.text] if self.text else []) + [f for f, _ in self.filters]
        insts = {s: self.inst(s) for s in specs}
        deps, seen, pdeps = "", set(), []
        for s, i in insts.items():
            field = i["field"]
            if field == "Number of Records" and field not in seen:
                seen.add(field)
                deps += "<column datatype='integer' name='[Number of Records]' role='measure' type='quantitative' user:auto-column='numrec'><calculation class='tableau' formula='1' /></column>"
            elif field in d.calcs and field not in seen:
                seen.add(field)
                c = d.calcs[field]
                typ = "quantitative" if c["datatype"] in ("integer", "real") else "nominal"
                deps += (f"<column caption={q(field)} datatype='{c['datatype']}' name={q(c['id'])} role='{c['role']}' type='{typ}'>"
                         f"<calculation class='tableau' formula={q(c['formula'])} /></column>")
                import re
                for pn in re.findall(r"\[Parameters\]\.(\[Parameter \d+\])", c["formula"]):
                    if pn not in pdeps:
                        pdeps.append(pn)
            elif field not in d.calcs and field not in seen and field != "Number of Records":
                seen.add(field)
                t = d.cols[field]
                role, typ = ("measure", "quantitative") if t in ("integer", "real") else ("dimension", "ordinal" if t == "date" else "nominal")
                deps += f"<column datatype='{t}' name={q('[' + field + ']')} role='{role}' type='{typ}' />"
        for s, i in insts.items():
            deps += f"<column-instance column={q(i['base'])} derivation='{i['deriv']}' name={q(i['name'])} pivot='key' type='{i['type']}' />"
        pdep_xml = (f"<datasource-dependencies datasource='Parameters'>" + "".join(PARAMS.column_xml(p) for p in pdeps) + "</datasource-dependencies>") if pdeps else ""
        flt = "".join(
            f"<filter class='categorical' column={q('[' + d.id + '].' + insts[spec]['name'])}>"
            f"<groupfilter function='member' level={q(insts[spec]['name'])} member={q(val)} user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />"
            f"</filter>" for spec, val in self.filters)
        slices = "<slices>" + "".join(f"<column>{escape('[' + d.id + '].' + insts[s]['name'])}</column>" for s, _ in self.filters) + "</slices>" if self.filters else ""
        ref = lambda s: f"[{d.id}].{insts[s]['name']}"
        enc = ""
        if self.color:
            enc += f"<color column={q(ref(self.color))} />"
        if self.text:
            enc += f"<text column={q(ref(self.text))} />"
        style = (f"<style><style-rule element='mark'><format attr='mark-color' value='{self.fill}' />"
                 + ("<format attr='mark-labels-show' value='true' />" if self.label else "") + "</style-rule></style>") if not self.color else \
                (("<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /></style-rule></style>") if self.label else "")
        if self.mark == "Text":
            style = "<style><style-rule element='cell'><format attr='text-format' value='*' /></style-rule></style>"
        sortx = ""
        if self.sort:
            dim, meas, direction = self.sort
            sortx = f"<sort class='computed' column={q('[' + d.id + '].' + insts[dim]['name'])} direction='{direction}' using={q('[' + d.id + '].' + insts[meas]['name'])} />"
        return (f"<worksheet name={q(self.name)}><layout-options><title><formatted-text><run bold='true' fontsize='11' fontcolor='{INK}'>{escape(self.title)}</run></formatted-text></title></layout-options>"
                f"<table><view><datasources><datasource caption={q(d.key)} name={q(d.id)} /></datasources>"
                f"<datasource-dependencies datasource={q(d.id)}>{deps}</datasource-dependencies>{pdep_xml}{flt}{sortx}{slices}<aggregation value='true' /></view>"
                f"<style />{'<panes><pane selection-relaxation-option=' + chr(39) + 'selection-relaxation-allow' + chr(39) + '><view><breakdown value=' + chr(39) + 'auto' + chr(39) + ' /></view>' + '<mark class=' + chr(39) + self.mark + chr(39) + ' />' + (f'<encodings>{enc}</encodings>' if enc else '') + style + '</pane></panes>'}"
                f"<rows>{' / '.join(ref(r) for r in self.rows) if self.rows else ''}</rows><cols>{' / '.join(ref(c) for c in self.cols) if self.cols else ''}</cols></table></worksheet>")


KEEP = ("none:Keep", "true")
S = []
def add(*a, **k):
    s = Sheet(*a, **k); S.append(s); return s.name

def kpi(name, ds, calc, filters=()):
    return add(name, ds, mark="Text", text=f"usr:{calc}", filters=filters, title=name)

# Overview
k_post = kpi("KPI postings", postings, "Postings", [KEEP])
k_roles = kpi("KPI roles", postings, "Roles", [KEEP])
k_emp = kpi("KPI employers", postings, "Employers", [KEEP])
k_share = kpi("KPI salary share", postings, "Share with salary", [KEEP])
k_med = kpi("KPI median salary", postings, "Median salary", [KEEP])
o_role = add("Postings by role", postings, rows=["none:role"], cols=["ctd:job_id"], filters=[KEEP], sort=("none:role", "ctd:job_id", "DESC"), title="Software and cloud roles lead postings")
o_week = add("Postings by week", postings, rows=["ctd:job_id"], cols=["wk:created_date"], mark="Area", filters=[KEEP], title="Postings by week created (last week is partial)")
o_state = add("Postings by state", postings, rows=["none:location_region"], cols=["ctd:job_id"], filters=[KEEP], sort=("none:location_region", "ctd:job_id", "DESC"), title="Karnataka leads where a state is known")
o_sen = add("Seniority mix", postings, rows=["none:role"], cols=["ctd:job_id"], mark="Bar", color="none:seniority_level", filters=[KEEP], title="Seniority mix by role")
# Salary
s_role = add("Median salary by role", postings, rows=["none:role"], cols=["usr:Median salary (₹ lakh)"], filters=[KEEP], sort=("none:role", "usr:Median salary (₹ lakh)", "DESC"), label=True, title="Median salary by role (₹ lakh per year)")
s_sen = add("Median salary by seniority", postings, rows=["none:seniority_level"], cols=["usr:Median salary (₹ lakh)"], filters=[KEEP, ("none:Seniority known", "true")], label=True, title="Median salary by seniority (₹ lakh per year)")
s_band = add("Salary bands by role", postings, rows=["none:role"], cols=["ctd:job_id"], color="none:salary_band", filters=[KEEP], title="Salary bands by role (postings with a salary)")
s_state = add("Median salary by state", postings, rows=["none:location_region"], cols=["usr:Median salary (₹ lakh)"], filters=[KEEP], sort=("none:location_region", "usr:Median salary (₹ lakh)", "DESC"), label=True, title="Median salary by state (₹ lakh per year)")
s_n = kpi("KPI salaries known", postings, "Salaries known", [KEEP])
# Skills
k_heat = add("Skill heat map", skills, rows=["none:role"], cols=["none:skill"], mark="Square", color="sum:pct_of_role_postings", title="Share of each role's postings that mention a skill (%)")
k_pairs = add("Skill pairs", pairs, rows=["none:Pair"], cols=["sum:lift"], title="Skill pairs that appear together (lift)", sort=("none:Pair", "sum:lift", "DESC"))
k_trend = add("Skill trend", trends, rows=["avg:interest"], cols=["wk:date"], mark="Line", filters=[("none:Keep skill", "true")], title="Search interest over time (Google Trends, India)")
# Predict
p_band = kpi("Predicted band", preds, "Predicted band", [("none:Keep profile", "true")])
p_conf = kpi("Prediction confidence", preds, "Confidence", [("none:Keep profile", "true")])
p_low, p_med, p_high = (kpi(f"P {b}", preds, f"P {b}", [("none:Keep profile", "true")]) for b in ("low", "medium", "high"))
# Model results
m_band = kpi("KPI band accuracy", modlong, "Grouped band accuracy")
m_bin = kpi("KPI binary accuracy", modlong, "Grouped binary accuracy")
m_gb = kpi("KPI guess band", modlong, "Guess band")
m_gbin = kpi("KPI guess binary", modlong, "Guess binary")
m_acc = add("Accuracy vs guessing", modlong, rows=["sum:value"], cols=["none:test", "none:measure"], color="none:measure", title="Model accuracy against guessing the most common class")
m_cm = add("Confusion matrix", confusion, rows=["none:actual"], cols=["none:predicted"], mark="Square", color="sum:count", text="sum:count", filters=[("none:Keep task", "true")], title="Where the model is right and wrong (unseen employers)")
m_fi = add("Feature importance", importance, rows=["none:feature"], cols=["sum:importance"], filters=[("none:Keep task", "true")], sort=("none:feature", "sum:importance", "DESC"), title="Most influential features")

# ---------------------------------------------------------------- dashboards
W, H = 1600, 1000
_zid = [10]
def zid():
    _zid[0] += 1
    return _zid[0]

def pct(v, total):
    return int(round(v / total * 100000))

ZSTYLE = f"<zone-style><format attr='border-color' value='{LINE}' /><format attr='border-style' value='solid' /><format attr='border-width' value='1' /><format attr='background-color' value='#FFFFFF' /></zone-style>"
def zone_sheet(name, x, y, w, h):
    return f"<zone h='{pct(h, H)}' id='{zid()}' name={q(name)} w='{pct(w, W)}' x='{pct(x, W)}' y='{pct(y, H)}'>{ZSTYLE}</zone>"
def zone_param(param, x, y, w, h):
    return f"<zone h='{pct(h, H)}' id='{zid()}' mode='compact' param={q(param)} type-v2='paramctrl' w='{pct(w, W)}' x='{pct(x, W)}' y='{pct(y, H)}' />"
def zone_text(text, x, y, w, h, size=22, bold=True, color=INK):
    return (f"<zone h='{pct(h, H)}' id='{zid()}' type-v2='text' w='{pct(w, W)}' x='{pct(x, W)}' y='{pct(y, H)}'><formatted-text>"
            f"<run bold='{str(bold).lower()}' fontcolor='{color}' fontsize='{size}'>{escape(text)}</run></formatted-text></zone>")

def dashboard(name, heading, sub, body, sheets):
    inner = zone_text(heading, 20, 8, 900, 40) + zone_text(sub, 20, 48, 1500, 24, 11, False, "#5B6B7B") + body
    vps = "".join(f"<viewpoint name={q(s)}><zoom type='entire-view' /></viewpoint>" for s in sheets)
    dash = (f"<dashboard name={q(name)}><style />"
            f"<size maxheight='{H}' maxwidth='{W}' minheight='{H}' minwidth='{W}' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='{zid()}' type-v2='layout-basic' w='100000' x='0' y='0'>{inner}<zone-style><format attr='background-color' value='{CANVAS}' /></zone-style></zone></zones></dashboard>")
    win = f"<window class='dashboard' name={q(name)}><viewpoints>{vps}</viewpoints><active id='-1' /></window>"
    return dash, win

def grid_filters(x, y, w):
    """Filter controls laid out in a row."""
    items = [pm_role, pm_sen, pm_state, pm_con, pm_lo, pm_hi]
    cw = w / len(items)
    return "".join(zone_param(p, x + i * cw, y, cw - 8, 50) for i, p in enumerate(items))

SUB = "Adzuna job postings in India, July to October 2026. Filters apply to every chart on this page."
dashes = []
# 1 Overview
tiles = [k_post, k_roles, k_emp, k_share, k_med]
body = grid_filters(20, 80, 1560) + "".join(zone_sheet(t, 20 + i * 314, 140, 300, 90) for i, t in enumerate(tiles))
body += zone_sheet(o_role, 20, 245, 780, 350) + zone_sheet(o_week, 815, 245, 765, 350)
body += zone_sheet(o_state, 20, 610, 780, 370) + zone_sheet(o_sen, 815, 610, 765, 370)
dashes.append(dashboard("Overview", "Career Market Intelligence", SUB, body, tiles + [o_role, o_week, o_state, o_sen]))
# 2 Salary
body = grid_filters(20, 80, 1560) + zone_sheet(s_n, 20, 140, 300, 70)
body += zone_text("Salary is stated in a minority of postings (about 16%). Only those are charted here. ₹ per year is an assumption: Adzuna gives no currency or period.", 340, 150, 1240, 50, 11, False, "#5B6B7B")
body += zone_sheet(s_role, 20, 225, 780, 370) + zone_sheet(s_sen, 815, 225, 765, 370)
body += zone_sheet(s_band, 20, 610, 780, 370) + zone_sheet(s_state, 815, 610, 765, 370)
dashes.append(dashboard("Salary", "Salary", SUB, body, [s_n, s_role, s_sen, s_band, s_state]))
# 3 Skills
body = zone_text("Skill", 20, 90, 100, 20, 11, True) + zone_param(pm_skill, 20, 112, 260, 50)
body += zone_sheet(k_heat, 20, 175, 950, 460) + zone_sheet(k_pairs, 985, 175, 595, 460) + zone_sheet(k_trend, 20, 650, 1560, 330)
dashes.append(dashboard("Skills", "Skills in demand", "Skills are text-mined from job descriptions. The Skill control only changes the trend chart.", body, [k_heat, k_pairs, k_trend]))
# 4 Predict
ctrl = [pm_prole, pm_psen, pm_pstate, pm_pcon, pm_pskill]
body = "".join(zone_param(p, 20 + i * 312, 80, 296, 50) for i, p in enumerate(ctrl))
body += zone_sheet(p_band, 20, 150, 500, 140) + zone_sheet(p_conf, 540, 150, 500, 140)
body += "".join(zone_sheet(s, 20 + i * 520, 310, 500, 130) for i, s in enumerate([p_low, p_med, p_high]))
body += zone_text("Probability of each salary band for this posting profile, from the saved structured-features model (precomputed). Bands are thirds of all salaries in the dataset. These models predict a band, not an exact figure.", 20, 460, 1560, 60, 12, False, "#5B6B7B")
dashes.append(dashboard("Predict salary", "Predict a salary band", "Choose a posting profile. Results update immediately.", body, [p_band, p_conf, p_low, p_med, p_high]))
# 5 Model results
body = zone_sheet(m_band, 20, 90, 380, 90) + zone_sheet(m_gb, 410, 90, 380, 90) + zone_sheet(m_bin, 800, 90, 380, 90) + zone_sheet(m_gbin, 1190, 90, 390, 90)
body += zone_text("Details for", 1190, 195, 200, 20, 11, True) + zone_param(pm_task, 1190, 215, 390, 50)
body += zone_sheet(m_acc, 20, 195, 1150, 400) + zone_sheet(m_cm, 20, 610, 760, 370) + zone_sheet(m_fi, 800, 610, 780, 370)
dashes.append(dashboard("Model results", "Model results", "KPI tiles show accuracy on unseen employers and the accuracy of always guessing the most common class. Unseen employers = a company never sits in both training and test.", body, [m_band, m_gb, m_bin, m_gbin, m_acc, m_cm, m_fi]))

# ---------------------------------------------------------------- assemble
sheet_windows = "".join(f"<window class='worksheet' name={q(s.name)}><cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
                        f"<edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge></cards></window>"
                        for s in S)
xml = (f"<?xml version='1.0' encoding='utf-8' ?>\n<workbook original-version='{VER}' source-build='2026.2.2 (20262.26.0819.2015)' source-platform='mac' version='{VER}' xmlns:user='http://www.tableausoftware.com/xml/user'>"
       f"<datasources>{PARAMS.xml()}{''.join(d.xml() for d in ALL_DS)}</datasources>"
       f"<worksheets>{''.join(s.xml() for s in S)}</worksheets>"
       f"<dashboards>{''.join(d for d, _ in dashes)}</dashboards>"
       f"<windows source-height='30'>{''.join(w for _, w in dashes)}{sheet_windows}</windows></workbook>")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(xml)
print(f"wrote {OUT}: {len(S)} worksheets, {len(dashes)} dashboards, {len(PARAMS.items)} parameters")
