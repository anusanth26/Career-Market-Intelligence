"use client";
import * as Plot from "@observablehq/plot";
import { scaleLog } from "d3-scale";
import { useEffect, useMemo, useState } from "react";
import { Fig } from "@/components/Block";
import Kpis from "@/components/Kpis";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { CALC, predict } from "@/lib/calc";
import { logBins, median, midpoint, quantile, rankOf } from "@/lib/stats";
import { Tokens } from "@/lib/tokens";
import { f3, inr, lk, pct0, sgnPct } from "@/lib/format";
import { ALL, useFilters } from "@/lib/filters";
import D from "@/data/dataset.json";
import S from "@/data/salary.json";
import T from "@/data/textmining.json";

const ROWS = (D.rows as any[]).map((r) => ({ ...r, mid: midpoint(r), exp: (r.exp_min + r.exp_max) / 2 }));
const OPT = CALC.options;
const premium = (skill: string) => (T.premiums as any[]).find((p) => p.skill === skill);
const RS: Record<string, any[]> = (T as any).role_skills ?? {};

function RangeScale({ lo, est, hi, offer }: { lo: number; est: number; hi: number; offer?: number }) {
  const W = 760, H = 150, x = scaleLog().domain([1.5, 80]).range([18, W - 18]).clamp(true);
  const L = (v: number) => Math.round(x(v) * 10) / 10;
  return (
    <svg className="scale" viewBox={`0 0 ${W} ${H}`} width="100%" style={{ width: "100%", height: "auto", aspectRatio: `${W} / ${H}` }} role="img"
      aria-label={`Expected ${lk(est)}, 80 percent range ${lk(lo)} to ${lk(hi)}${offer != null ? `, offer ${lk(offer)}` : ""}`}>
      <line x1={18} x2={W - 18} y1={92} y2={92} stroke="var(--rule)" />
      {[2, 5, 10, 25, 50].map((t) => <g key={t}><line x1={L(t)} x2={L(t)} y1={86} y2={98} stroke="var(--ink3)" /><text x={L(t)} y={116} textAnchor="middle">{`₹${t} L`}</text></g>)}
      <rect x={L(lo)} width={Math.max(2, L(hi) - L(lo))} y={52} height={30} rx={3} fill="var(--c1)" />
      <line x1={L(est)} x2={L(est)} y1={42} y2={88} stroke="var(--ink)" strokeWidth={3} />
      <text className="lbl" x={L(est)} y={32} textAnchor="middle">expected</text>
      <text x={L(lo)} y={46} textAnchor="middle">{lk(lo)}</text><text x={L(hi)} y={46} textAnchor="middle">{lk(hi)}</text>
      {offer != null ? <g><line x1={L(offer)} x2={L(offer)} y1={56} y2={104} stroke="var(--c2)" strokeWidth={4} /><text className="lbl" x={L(offer)} y={138} textAnchor="middle" style={{ fill: "var(--c2)" }}>your offer {lk(offer)}</text></g> : null}
    </svg>
  );
}

function Presets({ items }: { items: { label: string; on: () => void }[] }) {
  return <div className="presets"><span>Try an example:</span>{items.map((p) => <button key={p.label} onClick={p.on}>{p.label}</button>)}</div>;
}

/* 1: check an offer */
export function CheckOffer() {
  const { f: gf } = useFilters();
  const [role, setRole] = useState("Data Engineer"), [sen, setSen] = useState("Mid"), [city, setCity] = useState("Bengaluru"), [mode, setMode] = useState("Hybrid");
  const [years, setYears] = useState(6), [offer, setOffer] = useState(14);
  useEffect(() => { if (gf.role !== ALL) setRole(gf.role); if (OPT.city.includes(gf.city)) setCity(gf.city); if (OPT.work_mode.includes(gf.mode)) setMode(gf.mode); }, [gf.role, gf.city, gf.mode]);
  const p = useMemo(() => predict({ role, seniority: sen, city, work_mode: mode, years }), [role, sen, city, mode, years]);
  const sim = useMemo(() => {
    const near = ROWS.filter((r) => r.role === role && Math.abs(r.exp - years) <= 2);
    return near.length >= 15 ? { rows: near, scope: `${role} postings asking for ${Math.max(0, years - 2)} to ${years + 2} years` } : { rows: ROWS.filter((r) => r.role === role), scope: `all ${role} postings (too few near ${years} years)` };
  }, [role, years]);
  const mids = sim.rows.map((r) => r.mid), rank = rankOf(mids, offer);
  const status = offer < p.lo ? "below" : offer > p.hi ? "above" : "inside";
  const bins = useMemo(() => logBins(mids), [mids]);
  const buildHist = (t: Tokens): Plot.PlotOptions => ({
    height: 220, marginLeft: 46, marginBottom: 40,
    x: { type: "log", domain: [1, 70], label: "stated salary midpoint, lakh (log scale)", labelAnchor: "left", ticks: [1, 2, 5, 10, 20, 40, 70], tickFormat: (d: number) => String(d) }, y: { label: "postings", grid: true },
    marks: [Plot.rectY(bins, { x1: "lo", x2: "hi", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }), Plot.ruleX([offer], { stroke: t.cat[1], strokeWidth: 3 }),
      Plot.text([{ x: offer, y: Math.max(1, ...bins.map((b) => b.n)) }], { x: "x", y: "y", text: () => `your offer ${lk(offer)}`, dx: 8, textAnchor: "start", fill: t.cat[1], fontWeight: 650, stroke: t.bg, strokeWidth: 4 })],
  });
  const set = (r: string, s: string, c: string, m: string, y: number, o: number) => { setRole(r); setSen(s); setCity(c); setMode(m); setYears(y); setOffer(o); };
  return (
    <section className="section scenario" id="offer">
      <h2>A job seeker checks an offer</h2>
      <p className="small" style={{ maxWidth: "66ch" }}>Enter a profile and an offer. You get what the data says that profile should expect, where the offer falls in that range, and how it compares with similar postings.</p>
      <Presets items={[
        { label: "Data Engineer, 6 years, Bengaluru, ₹14 L", on: () => set("Data Engineer", "Mid", "Bengaluru", "Hybrid", 6, 14) },
        { label: "Digital Marketing, 3 years, Mumbai, ₹3 L", on: () => set("Digital Marketing", "Mid", "Mumbai", "Work from office", 3, 3) },
        { label: "Software Engineer, 9 years, Hyderabad, ₹35 L", on: () => set("Software Engineer", "Senior", "Hyderabad", "Work from office", 9, 35) },
      ]} />
      <div className="controls" style={{ alignItems: "flex-end" }}>
        <label className="field">Role<select value={role} onChange={(e) => setRole(e.target.value)}>{OPT.role.map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="field">Seniority in the title<select value={sen} onChange={(e) => setSen(e.target.value)}>{OPT.seniority.map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="field">City<select value={city} onChange={(e) => setCity(e.target.value)}>{OPT.city.map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="field">Work mode<select value={mode} onChange={(e) => setMode(e.target.value)}>{OPT.work_mode.map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="field">Years of experience: {years}<input type="range" min={0} max={25} value={years} onChange={(e) => setYears(+e.target.value)} aria-label="Years of experience" /></label>
        <label className="field">Offer, lakh per year<input type="number" min={0.5} max={100} step={0.5} value={offer} onChange={(e) => setOffer(Math.max(0.5, +e.target.value || 0.5))} style={{ width: 110 }} /></label>
      </div>
      <Kpis items={[
        { value: lk(p.est), label: "expected salary for this profile" },
        { value: `${lk(p.lo, 0)} to ${lk(p.hi, 0)}`, label: "80% range" },
        { value: status === "inside" ? "Inside" : status === "below" ? "Below" : "Above", label: status === "inside" ? "your offer sits within the range" : `your offer is ${status} the range, ${sgnPct((offer / p.est - 1) * 100)} against the expected salary` },
        { value: pct0(rank), label: `of the ${sim.rows.length} stated salaries in ${sim.scope} are at or below your offer` },
      ]} />
      <RangeScale lo={p.lo} est={p.est} hi={p.hi} offer={offer} />
      <Fig title="Where the offer falls among similar postings" sub={sim.scope}><PlotFigure label="Histogram of similar postings' stated salaries with the offer marked" build={buildHist} minHeight={220} /></Fig>
      <p className="small" style={{ maxWidth: "70ch" }}>How to read it: {status === "inside" ? "the offer is within what the data supports for this profile, so look at benefits and growth rather than only the number." : status === "below" ? "the offer is below the range the data supports for this profile. That is a reason to ask, not proof the offer is unfair: employers differ, and this model does not see the company." : "the offer is above the range the data supports, which happens for strong employers or senior profiles that the calculator reads as average."} The calculator uses only role, seniority, city, work mode and years, so it is weaker than the main model (R² {f3(CALC.cv_r2)}, typical error {lk(CALC.cv_mae_inr / 1e5)} in cross-validation, and its 80% range held {pct0(CALC.cv_coverage80)} of held-out salaries).</p>
    </section>
  );
}

/* 2: benchmark a role */
export function Benchmark() {
  const { f: gf } = useFilters();
  const [role, setRole] = useState("Data Analyst"), [city, setCity] = useState("All"), [y0, setY0] = useState(2), [y1, setY1] = useState(6);
  useEffect(() => { if (gf.role !== ALL) setRole(gf.role); setCity(OPT.city.includes(gf.city) ? gf.city : "All"); const bd: Record<string, [number, number]> = { "0-2 years": [0, 2], "2-5 years": [2, 5], "5-8 years": [5, 8], "8-12 years": [8, 12], "12+ years": [12, 30] }; if (bd[gf.band]) { setY0(bd[gf.band][0]); setY1(bd[gf.band][1]); } }, [gf.role, gf.city, gf.band]);
  const rows = useMemo(() => ROWS.filter((r) => r.role === role && (city === "All" || r.city === city) && r.exp >= y0 && r.exp <= y1), [role, city, y0, y1]);
  const mids = rows.map((r) => r.mid);
  const bins = useMemo(() => logBins(mids), [mids]);
  const reli = (S.cond_role as any[]).find((r) => r.role === role), err = (S.err_role as any[]).find((r) => r.role === role);
  const top = (RS[role] ?? []).slice(0, 4);
  const buildHist = (t: Tokens): Plot.PlotOptions => ({
    height: 240, marginLeft: 46, marginBottom: 40,
    x: { type: "log", domain: [1, 70], label: "stated salary midpoint, lakh (log scale)", labelAnchor: "left", ticks: [1, 2, 5, 10, 20, 40, 70], tickFormat: (d: number) => String(d) }, y: { label: "postings", grid: true },
    marks: [Plot.rectY(bins, { x1: "lo", x2: "hi", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }),
      mids.length ? Plot.ruleX([median(mids)], { stroke: t.ink, strokeDasharray: "4 3" }) : null, Plot.tip(bins, Plot.pointerX({ x: (d: any) => Math.sqrt(d.lo * d.hi), y: "n", title: (d: any) => `₹${d.lo.toFixed(1)} to ${d.hi.toFixed(1)} L\n${d.n} postings` }))].filter(Boolean) as Plot.Markish[],
  });
  return (
    <section className="section scenario" id="benchmark">
      <h2>A recruiter benchmarks a role</h2>
      <p className="small" style={{ maxWidth: "66ch" }}>Choose a role, an experience band and optionally a city. You get what comparable postings state, and how far to trust the model for that role.</p>
      <Presets items={[
        { label: "Data Analyst, 2 to 6 years", on: () => { setRole("Data Analyst"); setCity("All"); setY0(2); setY1(6); } },
        { label: "Product Manager, 8 to 14 years", on: () => { setRole("Product Manager"); setCity("All"); setY0(8); setY1(14); } },
        { label: "Graphic Designer, 0 to 3 years, Mumbai", on: () => { setRole("Graphic Designer"); setCity("Mumbai"); setY0(0); setY1(3); } },
      ]} />
      <div className="controls" style={{ alignItems: "flex-end" }}>
        <label className="field">Role<select value={role} onChange={(e) => setRole(e.target.value)}>{OPT.role.map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="field">City<select value={city} onChange={(e) => setCity(e.target.value)}>{["All", ...OPT.city].map((o) => <option key={o}>{o}</option>)}</select></label>
        <label className="field">Years asked, from<input type="number" min={0} max={30} value={y0} onChange={(e) => setY0(+e.target.value || 0)} style={{ width: 90 }} /></label>
        <label className="field">to<input type="number" min={0} max={30} value={y1} onChange={(e) => setY1(+e.target.value || 0)} style={{ width: 90 }} /></label>
      </div>
      <Kpis items={[
        { value: inr(rows.length), label: "comparable postings with a stated salary" },
        { value: rows.length ? lk(median(mids)) : "n/a", label: "median stated salary" },
        { value: rows.length >= 4 ? `${lk(quantile(mids, 0.25), 0)} to ${lk(quantile(mids, 0.75), 0)}` : "n/a", label: "middle half of postings" },
        { value: rows.length >= 10 ? `${lk(quantile(mids, 0.1), 0)} to ${lk(quantile(mids, 0.9), 0)}` : "n/a", label: "80% of postings" },
        { value: reli ? pct0(reli.coverage) : "n/a", label: `model's 80% range held the stated salary this often for ${role} (${reli?.n} test postings)` },
      ]} />
      {rows.length > 0 && rows.length < 15 ? <p className="small" style={{ marginTop: 6 }}>Only {rows.length} postings match, so treat the figures as indicative.</p> : null}
      <Fig title="Stated salaries of the comparable postings" sub="Dashed line: the median."><PlotFigure label="Histogram of stated salaries for the chosen role, experience band and city" build={buildHist} minHeight={240} /></Fig>
      <p className="small" style={{ maxWidth: "70ch" }}>For {role} the model's typical error on unseen postings is {lk(err.MAE_INR / 1e5)} against {lk(err.role_median_MAE / 1e5)} for the role median. {top.length ? `Employers in this role most often tag ${top.map((s: any) => s.skill).join(", ")}.` : ""} {reli && reli.coverage < 0.8 ? "Its range has been too narrow for this role, so give candidates more room than the range suggests." : "Its range has held up for this role."}</p>
    </section>
  );
}

/* 3: plan skills */
export function PlanSkills() {
  const { f: gf } = useFilters();
  const [role, setRole] = useState("Data Scientist");
  useEffect(() => { if (gf.role !== ALL) setRole(gf.role); }, [gf.role]);
  const skills = (RS[role] ?? []) as any[];
  const [have, setHave] = useState<Record<string, boolean>>({ python: true, sql: true });
  const rows = skills.map((s) => ({ ...s, have: !!have[s.skill], prem: premium(s.skill) }));
  const total = rows.reduce((a, r) => a + r.tag_pct, 0), covered = rows.filter((r) => r.have).reduce((a, r) => a + r.tag_pct, 0);
  const gaps = rows.filter((r) => !r.have);
  const build = (t: Tokens): Plot.PlotOptions => ({
    height: 44 + rows.length * 27, marginLeft: 170, marginRight: 60, marginBottom: 34, marginTop: 6,
    x: { domain: [0, Math.max(60, ...rows.map((r) => r.tag_pct + 6))], grid: true, label: "share of the role's postings that tag the skill", labelAnchor: "left", tickFormat: (d: number) => `${d}%` }, y: { domain: rows.map((r) => r.skill), label: null, tickSize: 0 },
    color: { domain: ["have", "gap"], range: [t.cat[0], t.cat[1]] },
    marks: [Plot.barX(rows, { y: "skill", x1: 0, x2: "tag_pct", fill: (r: any) => (r.have ? "have" : "gap"), insetTop: 4, insetBottom: 4 }),
      Plot.text(rows, { y: "skill", x: "tag_pct", text: (r: any) => `${Math.round(r.tag_pct)}%`, dx: 7, textAnchor: "start", fill: t.ink })],
  });
  const toggle = (s: string) => setHave((h) => ({ ...h, [s]: !h[s] }));
  const preset = (r: string, list: string[]) => { setRole(r); setHave(Object.fromEntries(list.map((s) => [s, true]))); };
  return (
    <section className="section scenario" id="skills">
      <h2>A student plans skills for a target role</h2>
      <p className="small" style={{ maxWidth: "66ch" }}>Pick the role you are aiming at and tick the skills you already have. You see what is missing, ranked by how often postings ask for it, with each skill's pay association where it could be estimated.</p>
      <Presets items={[
        { label: "Data Scientist, knows Python and SQL", on: () => preset("Data Scientist", ["python", "sql"]) },
        { label: "Software Engineer, knows Java", on: () => preset("Software Engineer", ["java"]) },
        { label: "Digital Marketing, complete beginner", on: () => preset("Digital Marketing", []) },
      ]} />
      <div className="controls" style={{ alignItems: "flex-end" }}>
        <label className="field">Target role<select value={role} onChange={(e) => setRole(e.target.value)}>{OPT.role.map((o) => <option key={o}>{o}</option>)}</select></label>
      </div>
      <fieldset style={{ border: 0, padding: 0, margin: "0 0 12px" }}>
        <legend className="small" style={{ marginBottom: 6, fontFamily: "var(--font-ui)" }}>Skills you have</legend>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 16px", fontFamily: "var(--font-ui)", fontSize: "0.9rem" }}>
          {skills.map((s) => <label key={s.skill} style={{ display: "flex", gap: 6, alignItems: "center" }}><input type="checkbox" checked={!!have[s.skill]} onChange={() => toggle(s.skill)} />{s.skill}</label>)}
        </div>
      </fieldset>
      <Kpis items={[
        { value: `${rows.filter((r) => r.have).length} of ${rows.length}`, label: `of the ${role}'s most tagged skills you have` },
        { value: pct0(total ? covered / total : 0), label: "of the weight of those skills, counting commonly asked skills more" },
        { value: gaps[0] ? gaps[0].skill : "none", label: "the most common skill you are missing" },
        { value: gaps.filter((g) => g.prem && (g.prem.dml_fdr_sig || g.prem.ols_fdr_sig)).length.toString(), label: "missing skills with a pay association that survives the correction" },
      ]} />
      <Legend items={[{ color: "var(--c1)", label: "you have it", shape: "bar" }, { color: "var(--c2)", label: "gap", shape: "bar" }]} />
      <Fig title={`What ${role} postings tag most`} sub="The 15 most tagged skills for the role."><PlotFigure label="Most tagged skills for the target role, coloured by whether you have them" build={build} minHeight={440} /></Fig>
      <div className="tablewrap"><table><thead><tr><th>Skill you are missing</th><th className="r">Tagged in</th><th className="r">Pay association</th><th>Reading</th></tr></thead>
        <tbody>{gaps.slice(0, 8).map((g) => { const pr = g.prem; const pc = pr ? (Math.exp(pr.dml_beta) - 1) * 100 : null; const sig = pr && (pr.dml_fdr_sig || pr.ols_fdr_sig);
          return <tr key={g.skill}><td>{g.skill}</td><td className="r">{Math.round(g.tag_pct)}% of postings</td><td className="r">{pc == null ? "not estimated" : sgnPct(pc)}</td><td className="small">{pc == null ? "Too few salaried postings to estimate." : sig ? "Clear association at the same experience and role." : "Not distinguishable from zero. Learn it for access to postings, not for pay."}</td></tr>; })}</tbody></table></div>
    </section>
  );
}
