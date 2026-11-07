"use client";
import { useMemo, useState } from "react";
import Kpis from "@/components/Kpis";
import { EXAMPLES, Result, TEST, bagOf, score } from "@/lib/disclose";
import { pct0 } from "@/lib/format";

// the ten examples are shown in a fixed mixed order so the order does not give the answer away
const ORDER = [3, 8, 0, 6, 2, 9, 5, 1, 7, 4];

function Gauge({ r }: { r: Result }) {
  const pc = (v: number) => `${Math.max(0, Math.min(100, v * 100))}%`;
  return (
    <div className="gauge" role="img" aria-label={`Chance this posting states a salary: ${pct0(r.p)}. Typical posting: ${pct0(TEST.base_rate)}.`}>
      <div className="gtrack"><span className="gfill" style={{ width: pc(r.p) }} /><span className="gmark" style={{ left: pc(TEST.base_rate) }} title="share of postings that state a salary" /><span className="gthr" style={{ left: pc(TEST.threshold) }} title="decision threshold" /></div>
      <div className="gnote"><b>{pct0(r.p)}</b> chance this employer states a salary. Marks: the typical posting ({pct0(TEST.base_rate)}) and the cut-off the model uses to say "likely" ({pct0(TEST.threshold)}).</div>
    </div>
  );
}
const Words = ({ r }: { r: Result }) => (
  <div className="cols2">
    <p className="small"><b>Words pushing toward stating pay:</b> {r.up.map((d) => d.w).join(", ") || "none"}</p>
    <p className="small"><b>Words pushing toward silence:</b> {r.down.map((d) => d.w).join(", ") || "none"}</p>
  </div>
);

export default function DisclosureDemo() {
  const [cur, setCur] = useState(0), [revealed, setRevealed] = useState(false), [text, setText] = useState("");
  const ex = EXAMPLES[ORDER[cur]];
  const res = useMemo(() => score(ex.bag), [ex]);
  const bag2 = useMemo(() => bagOf(text), [text]);
  const res2 = useMemo(() => (Object.keys(bag2).length >= 12 ? score(bag2) : null), [bag2]);
  const likely = res.p >= TEST.threshold, right = likely === ex.states_salary;
  return (
    <section className="section" id="try">
      <h2>Will this employer state the pay?</h2>
      <p className="small" style={{ maxWidth: "68ch" }}>Pick a posting from companies the model never saw. It reads only the description, with any salary figure removed, and gives the chance that the employer states a salary. Then reveal what the employer did.</p>
      <Kpis items={[
        { value: pct0(TEST.auc), label: `ROC-AUC on ${TEST.n_test.toLocaleString("en-IN")} held-out postings (50% is guessing)` },
        { value: pct0(TEST.recall), label: "of postings that do state pay are caught at the model's cut-off" },
        { value: pct0(TEST.precision), label: `of postings it flags really state pay, against ${pct0(TEST.base_rate)} for a random posting` },
      ]} />
      <div className="hero" style={{ marginTop: 18 }}>
        <div>
          <p className="figtitle">Held-out postings</p>
          <ul className="postlist">
            {ORDER.map((k, i) => <li key={i}><button aria-current={i === cur} onClick={() => { setCur(i); setRevealed(false); }}><b>Posting {i + 1}</b>{EXAMPLES[k].company}, {EXAMPLES[k].role}</button></li>)}
          </ul>
        </div>
        <div key={cur} className="swap">
          <p className="est-meta" style={{ marginTop: 0 }}>{ex.company}. Asks for {ex.exp}. The employer tagged:</p>
          <div>{ex.tags.length ? ex.tags.map((s) => <span className="chip" key={s}>{s}</span>) : <span className="small">no skill tags</span>}</div>
          <p className="figtitle" style={{ margin: "14px 0 4px" }}>Job description, the text the model reads</p>
          <div className="jd" tabIndex={0} aria-label="Job description">{ex.description}{ex.description.length >= 1800 ? " …" : ""}</div>
          <Gauge r={res} />
          <Words r={res} />
          {revealed ? (
            <div className="slide"><div className={`verdict${right ? " ok" : ""}`}>
              This employer {ex.states_salary ? "states" : "does not state"} a salary. The model said {likely ? "likely" : "unlikely"} ({pct0(res.p)}), so it is {right ? "right" : "wrong"}.
            </div></div>
          ) : <p style={{ marginTop: 12 }}><button className="btn" onClick={() => setRevealed(true)}>Show what the employer did</button></p>}
        </div>
      </div>
      <h3 className="est-title" style={{ marginTop: 34, fontSize: "1.15rem" }}>Or paste a job description</h3>
      <p className="small" style={{ maxWidth: "68ch" }}>The text stays in your browser. Salary figures in it are ignored.</p>
      <textarea className="paste" value={text} onChange={(e) => setText(e.target.value)} rows={6} placeholder="Paste a few sentences of a job description here" aria-label="Job description to score" />
      {res2 ? <><Gauge r={res2} /><Words r={res2} /></> : <p className="small">{text.trim() ? "Add a few more sentences: the model needs at least a dozen words it knows." : "The chance appears here as you type."}</p>}
    </section>
  );
}
