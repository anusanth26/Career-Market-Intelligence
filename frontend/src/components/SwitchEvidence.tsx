"use client";
import { useState } from "react";
import DataDetails from "@/components/DataDetails";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { barsH, dumbbell, heat } from "@/lib/charts";
import { CLASSES, METRICS, MIN_SHARE, OVERALL, PAIRS, PREM, TOP } from "@/lib/switch";
import { f2, inr, pct0, sgnPct } from "@/lib/format";
import R from "@/data/roles.json";

/** Median skills to add for every move between two roles. */
export function SwitchHeat() {
  const hard = [...PAIRS].sort((x, y) => x.flip_5 - y.flip_5).slice(0, 8);
  const dm = PAIRS.find((p) => p.from === "Digital Marketing" && p.to === "DevOps / Cloud Engineer")!;
  return (
    <div className="duo">
      <div>
        <p className="figtitle">Median skills to add, by current role (row) and target role (column)</p>
        <p className="figsub">Blank: fewer than half of the postings reach the target within ten skills.</p>
        <PlotFigure label="Median number of skills to add to be read as another role" minHeight={440} build={heat({ data: PAIRS.filter((p) => p.median_added != null && p.flip_10 >= 0.5).map((p) => ({ from: p.from, to: p.to, v: p.median_added })), x: "to", y: "from", v: "v", fmt: (v) => String(Math.round(v)), xDomain: CLASSES, yDomain: CLASSES, domain: [0, 8], marginLeft: 170, marginBottom: 120, textMin: 0 })} />
      </div>
      <div className="small">
        <p><strong>Neighbouring roles are about three skills apart:</strong> Product Manager and Business Analyst, Product Manager and Project Manager, DevOps and Software Engineer.</p>
        <p><strong>Distant roles take six or seven</strong> and about half or fewer flip within ten (Digital Marketing to DevOps / Cloud: {pct0(dm.flip_10)} do).</p>
        <p>Across all 90 moves, {pct0(OVERALL.flip_5)} reach the target within 5 added skills, against {pct0(OVERALL.naive_flip_5)} for simply adding the target role's most common skills. Suggestions are limited to skills at least {pct0(MIN_SHARE)} of the target role's postings ask for, so none is a rare skill that happens to flip the classifier.</p>
        <DataDetails summary="The eight hardest moves" rows={hard} cols={[{ key: "from", label: "From" }, { key: "to", label: "To" }, { key: "flip_5", label: "Within 5", right: true, fmt: pct0 }, { key: "flip_10", label: "Within 10", right: true, fmt: pct0 }, { key: "median_added", label: "Median", right: true, fmt: (v: any) => (v == null ? "n/a" : String(Math.round(v))) }]} />
      </div>
    </div>
  );
}

/** The skills the search adds first on the way between two roles. */
export function SwitchBridge() {
  const [a, setA] = useState("Data Analyst"), [b, setB] = useState("Data Engineer");
  const rows = TOP[`${a}|${b}`] ?? [];
  const pair = PAIRS.find((p) => p.from === a && p.to === b);
  return (
    <div>
      <div className="controls" style={{ marginTop: 0 }}>
        <label className="field">From<select value={a} onChange={(e) => setA(e.target.value)}>{CLASSES.map((c) => <option key={c}>{c}</option>)}</select></label>
        <label className="field">To<select value={b} onChange={(e) => setB(e.target.value)}>{CLASSES.filter((c) => c !== a).map((c) => <option key={c}>{c}</option>)}</select></label>
      </div>
      {pair ? <p className="small">{pct0(pair.flip_5)} of {a} postings reach {b} within 5 added skills, {pct0(pair.flip_10)} within 10; median {pair.median_added == null ? "n/a" : Math.round(pair.median_added)}.</p> : null}
      <div className="tablewrap"><table><thead><tr><th>Skill</th><th className="r">Picked</th><th className="r">Asked by {b}</th><th className="r">Asked by {a}</th><th>Pay association</th></tr></thead>
        <tbody>{rows.map((r) => { const p = PREM[r.skill]; return <tr key={r.skill}><td>{r.skill}</td><td className="r">{pct0(r.pick)}</td><td className="r">{pct0(r.share_to)}</td><td className="r">{pct0(r.share_from)}</td><td className="small">{p ? `${sgnPct(p.pct)}, ${p.clear ? "clear" : "not clear"}` : "not estimated"}</td></tr>; })}</tbody></table></div>
      <p className="small">Picked: share of {a} postings that got the skill in their first five additions. A good bridge skill is asked far more by the target role than the current one.</p>
    </div>
  );
}

/** How well the wording of a posting identifies its role. */
export function SwitchAccuracy() {
  const models = [...(R.models as any[])].sort((x, y) => y.macro_F1 - x.macro_F1).map((m) => ({ ...m, base: m.model === "Majority class" }));
  const per = [...(R.per_role as any[])].sort((x, y) => x["F1 full text"] - y["F1 full text"]);
  const full = (R.final as any[]).find((x) => x.model === "full text");
  return (
    <div className="duo">
      <div>
        <p className="figtitle">Which model reads a description best</p>
        <p className="figsub">Macro-F1 over ten roles, five-fold cross-validation by company.</p>
        <PlotFigure label="Macro-F1 for ten role-fit models" minHeight={340} build={barsH({ data: models, label: "model", value: "macro_F1", sd: "F1_sd", fmt: (v) => v.toFixed(3), domain: [0, 1], color: (d, t) => (d.base ? t.ink3 : t.cat[0]), marginLeft: 220 })} />
      </div>
      <div>
        <p className="figtitle">F1 for each role on the test postings</p>
        <p className="figsub">Joined dots: what removing the title's own words does.</p>
        <Legend items={[{ color: "var(--c2)", label: "full text", shape: "dot" }, { color: "var(--c1)", label: "title words removed", shape: "dot" }]} />
        <PlotFigure label="F1 by role, full text against title words removed" minHeight={340} build={dumbbell({ data: per, label: "role", a: "F1 full text", b: "F1 title words removed", aName: "full text", bName: "title words removed", fmt: f2, marginLeft: 160, domain: [0.4, 1] })} />
        <p className="small">On {inr(R.n_test)} test postings from unseen companies the description alone names the role {pct0(full.accuracy)} of the time ({pct0(0.198)} for guessing the biggest role). Skills alone get {pct0(METRICS.accuracy)}.</p>
      </div>
    </div>
  );
}
