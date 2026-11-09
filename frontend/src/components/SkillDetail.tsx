"use client";
import { scaleLinear } from "d3-scale";
import { useState } from "react";
import { pct0, sgnPct } from "@/lib/format";
import gap from "@/data/gap.json";
import T from "@/data/textmining.json";
import trends from "@/data/trends.json";

const PREM = new Map<string, any>((T.premiums as any[]).map((d) => [d.skill, d]));
const TRACKED = new Map<string, any>((gap.skills as any[]).map((d) => [d.skill.toLowerCase(), d]));
export const SKILL_NAMES = Array.from(new Set([...TRACKED.keys(), ...PREM.keys()])).sort();
const ROLE_SHARE = new Map<string, { role: string; pct: number }[]>();
for (const d of T.tag_role_share as any[]) ROLE_SHARE.set(d.tag, [...(ROLE_SHARE.get(d.tag) ?? []), { role: d.role, pct: d.pct }]);
const pc = (b: number) => (Math.exp(b) - 1) * 100;

function Spark({ name }: { name: string }) {
  const s = (trends.series as any)[name] as number[] | undefined; if (!s) return null;
  const W = 260, H = 54, k = 8, v = s.map((_, i) => { const a = s.slice(Math.max(0, i - k + 1), i + 1); return a.reduce((x, y) => x + y, 0) / a.length; });
  const x = scaleLinear().domain([0, v.length - 1]).range([2, W - 2]), y = scaleLinear().domain([Math.min(...v), Math.max(...v)]).range([H - 4, 4]);
  return <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`Search interest in ${name} over five years`}><path d={v.map((q, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(q).toFixed(1)}`).join("")} fill="none" stroke="var(--c1)" strokeWidth={2} /></svg>;
}

/** Everything the project knows about one skill, in one place: demand, search interest, pay association, and who asks for it. */
export default function SkillDetail({ skill, onPick }: { skill: string; onPick: (s: string) => void }) {
  const [q, setQ] = useState("");
  const shown = SKILL_NAMES.filter((n) => !q.trim() || n.includes(q.trim().toLowerCase()));
  const key = skill.toLowerCase(), tr = TRACKED.get(key), pr = PREM.get(key);
  const roles = tr ? Object.entries((gap.by_role as any[]).find((r) => r.skill === tr.skill) ?? {}).filter(([k]) => k !== "skill").map(([role, pct]) => ({ role, pct: pct as number })) : ROLE_SHARE.get(key) ?? [];
  const top = [...roles].sort((a, b) => b.pct - a.pct).slice(0, 3);
  const prem = pr ? pc(pr.dml_beta) : null, lo = pr ? pc(pr.dml_lo) : null, hi = pr ? pc(pr.dml_hi) : null;
  const clear = pr && (pr.dml_fdr_sig || pr.ols_fdr_sig);
  return (
    <div className="sdetail">
      <label className="field">Search skills
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="type to narrow the list" aria-label="Search skills" />
      </label>
      <label className="field" style={{ marginTop: 8 }}>Skill
        <select value={skill} onChange={(e) => onPick(e.target.value)} aria-label="Skill">
          {!shown.includes(skill) ? <option value={skill}>{skill}</option> : null}
          {shown.map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>
      <p className="small" style={{ margin: "6px 0 0" }}>{shown.length} of {SKILL_NAMES.length} skills{q.trim() ? " match" : ""}.</p>
      {!tr && !pr ? <p className="small">No estimate for that skill. Pick one from the list: {SKILL_NAMES.length} skills have a pay estimate or a demand and trend profile.</p> : (
        <dl>
          {tr ? <><dt>Asked for in</dt><dd><b>{tr.demand_pct.toFixed(1)}%</b> of postings (rank {tr.demand_rank} of 20)</dd>
            <dt>Search interest, 5 years</dt><dd>{tr.low_volume ? <b>too small to judge</b> : <><b>{sgnPct(tr.pct_change)}</b>, {tr.momentum_class}{tr.trend_confirmed ? ", confirmed by test" : ""}</>}<Spark name={tr.skill} /></dd>
            <dt>Quadrant</dt><dd><b>{tr.low_volume ? "trend unreliable" : tr.quadrant}</b>. {tr.recommendation}</dd></> : <><dt>Demand and search interest</dt><dd className="small">Not one of the 20 tracked skills, so only pay and role shares are available.</dd></>}
          <dt>Pay association</dt>
          <dd>{pr ? <><b>{sgnPct(prem!)}</b> in the 170-skill analysis (double machine learning; interval {sgnPct(lo!)} to {sgnPct(hi!)}, {pr.n_postings} salaried postings). <span className={clear ? "ok" : ""}>{clear ? "Survives the false-discovery correction." : "Not distinguishable from zero after the correction."}</span></> : "Too few salaried postings to estimate in the 170-skill analysis."}{tr && tr.pay_premium_pct != null ? <><br />The 20-skill combined analysis (least squares) gives <b>{sgnPct(tr.pay_premium_pct)}</b>, {tr.pay_fdr_sig ? "clear after correction" : "not clear after correction"}. The two use slightly different skill definitions, so treat the figure as a range.</> : null}</dd>
          {top.length ? <><dt>Roles that ask most</dt><dd>{top.map((r) => `${r.role} ${pct0(r.pct / 100)}`).join(", ")}</dd></> : null}
        </dl>
      )}
    </div>
  );
}
