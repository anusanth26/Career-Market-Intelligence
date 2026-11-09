"use client";
import * as Plot from "@observablehq/plot";
import { useMemo, useState } from "react";
import Kpis from "@/components/Kpis";
import PlotFigure from "@/components/PlotFigure";
import { CLASSES, POPULAR, PREM, probsOf, recourse, shareOf, typical } from "@/lib/switch";
import { Tokens } from "@/lib/tokens";
import { pct0, sgnPct } from "@/lib/format";

export default function SwitchDemo() {
  const [from, setFrom] = useState(CLASSES.indexOf("Data Analyst")), [target, setTarget] = useState(CLASSES.indexOf("Data Engineer"));
  const [have, setHave] = useState<Set<string>>(() => new Set(typical(CLASSES.indexOf("Data Analyst"), 5)));
  const [q, setQ] = useState("");
  const probs = useMemo(() => probsOf(have), [have]);
  const order = probs.map((p, i) => ({ p, i })).sort((a, b) => b.p - a.p);
  const top = order[0].i;
  const plan = useMemo(() => recourse(have, target), [have, target]);
  const toggle = (s: string) => setHave((h) => { const n = new Set(h); if (n.has(s)) n.delete(s); else n.add(s); return n; });
  const start = (r: number) => { setFrom(r); setHave(new Set(typical(r, 5))); };
  const shown = POPULAR.filter((s) => !q.trim() || s.includes(q.trim().toLowerCase())).slice(0, 60);
  const curve = [{ n: 0, p: probs[target] }, ...plan.steps.map((s, i) => ({ n: i + 1, p: s.pTarget }))];
  const buildCurve = (t: Tokens): Plot.PlotOptions => ({
    height: 200, marginLeft: 46, marginBottom: 40,
    x: { label: "skills added, in this order", labelAnchor: "left", ticks: curve.map((d) => d.n), tickFormat: (d: number) => String(d) }, y: { domain: [0, 1], label: `chance of reading as ${CLASSES[target]}`, grid: true, tickFormat: (d: number) => `${Math.round(d * 100)}%` },
    marks: [Plot.line(curve, { x: "n", y: "p", stroke: t.cat[0], strokeWidth: 2.5 }), Plot.dot(curve, { x: "n", y: "p", r: 4, fill: t.cat[0] }), Plot.ruleY([0.5], { stroke: t.ink3, strokeDasharray: "4 3" }),
      Plot.tip(curve, Plot.pointerX({ x: "n", y: "p", title: (d: any) => `${d.n} skills added\n${pct0(d.p)}` }))],
  });
  return (
    <section className="section" id="try">
      <h2>Which skills would make you read as another role?</h2>
      <p className="small" style={{ maxWidth: "68ch" }}>Start from the typical skills of a role, or tick your own. Pick the role you want to move toward. The model that reads skills says how you read now, then adds the skills that move you toward the target fastest, shown with what each one has gone with in pay. Only skills at least 10% of the target role's postings ask for are suggested, and never a role name.</p>
      <div className="controls" style={{ alignItems: "flex-end" }}>
        <label className="field">Start from the typical skills of<select value={from} onChange={(e) => start(+e.target.value)}>{CLASSES.map((c, i) => <option key={c} value={i}>{c}</option>)}</select></label>
        <label className="field">Move toward<select value={target} onChange={(e) => setTarget(+e.target.value)}>{CLASSES.map((c, i) => <option key={c} value={i}>{c}</option>)}</select></label>
        <button className="btn ghost" onClick={() => setHave(new Set())}>Clear skills</button>
      </div>
      <Kpis items={[
        { value: have.size ? CLASSES[top] : "no skills yet", label: have.size ? `how you read now, ${pct0(order[0].p)} sure` : "tick skills below" },
        { value: pct0(probs[target]), label: `chance of reading as ${CLASSES[target]} now` },
        { value: plan.flipped ? (plan.steps.length ? String(plan.steps.length) : "0") : "10+", label: plan.flipped ? (plan.steps.length ? "skills to add before the target is the top role" : `you already read as ${CLASSES[target]}`) : "skills added without reaching the target, so it is a long way off" },
      ]} />
      <div className="hero" style={{ marginTop: 18 }}>
        <div>
          <p className="figtitle">Your skills ({have.size})</p>
          <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find a skill" aria-label="Find a skill" style={{ width: "100%", marginBottom: 8 }} />
          <div className="skillpick" role="group" aria-label="Skills you have" style={{ maxHeight: 340, overflow: "auto" }}>
            {shown.map((s) => <button key={s} className="chip" aria-pressed={have.has(s)} onClick={() => toggle(s)}>{s}</button>)}
          </div>
        </div>
        <div>
          <p className="figtitle">How you read now</p>
          <ol className="probbars" aria-label="Role probabilities for your skills">
            {order.slice(0, 4).map(({ p, i }) => (
              <li key={CLASSES[i]} className={i === top && have.size ? "top" : ""}><span className="nm">{CLASSES[i]}</span><span className="trk"><span className="fill" style={{ width: `${Math.max(0.5, p * 100)}%` }} /></span><span className="pc">{p < 0.005 ? "<1%" : pct0(p)}</span></li>
            ))}
          </ol>
          <p className="figtitle" style={{ marginTop: 18 }}>Skills to add toward {CLASSES[target]}</p>
          <p className="small" style={{ margin: "0 0 6px" }}>Chance after: chance of reading as {CLASSES[target]} once the skill is added. Target asks: share of {CLASSES[target]} postings that ask for it. You ask: share of {CLASSES[top]} postings that do. Pay: its market-wide pay association.</p>
          {plan.steps.length === 0 ? <p className="small">{plan.flipped ? `Nothing to add: your skills already read as ${CLASSES[target]}.` : "No skill moves you closer. Add some skills first."}</p> : (
            <div className="tablewrap"><table><thead><tr><th>Add</th><th className="r">Chance after</th><th className="r">Target asks</th><th className="r">You ask</th><th>Pay</th></tr></thead>
              <tbody>{plan.steps.map((s, i) => { const pr = PREM[s.skill]; return (
                <tr key={s.skill}><td><button className="chip" style={{ margin: 0 }} onClick={() => toggle(s.skill)} title="Add this skill to your profile">{i + 1}. {s.skill}</button></td><td className="r">{pct0(s.pTarget)}</td><td className="r">{pct0(shareOf(target, s.skill))}</td><td className="r">{pct0(shareOf(top, s.skill))}</td>
                  <td className="small">{pr ? `${sgnPct(pr.pct)}, ${pr.clear ? "clear" : "not clear"}` : "not estimated"}</td></tr>); })}</tbody></table></div>
          )}
          {plan.steps.length ? <p style={{ marginTop: 10 }}><button className="btn" onClick={() => setHave((h) => new Set([...h, ...plan.steps.map((s) => s.skill)]))}>Add all of them</button></p> : null}
          {plan.steps.length ? <PlotFigure label="Chance of reading as the target role as skills are added" build={buildCurve} minHeight={200} /> : null}
          <p className="small" style={{ maxWidth: "62ch" }}>This shows how a posting's wording changes the reading, not whether you would be hired. A pay association is the market-wide average for that skill, marked clear only where it survives the false-discovery correction.</p>
        </div>
      </div>
    </section>
  );
}
