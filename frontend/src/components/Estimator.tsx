"use client";
import { scaleLog } from "d3-scale";
import { useMemo, useState } from "react";
import { lk } from "@/lib/format";

type Posting = {
  title: string; company: string; location: string; work_mode: string; experience: string; exp_min: number; exp_max: number;
  industry: string; role: string; skills: string[]; stated_min: number; stated_max: number;
  low80: number; est: number; high80: number; low90: number; high90: number; whatif: number[][];
};
type Demo = { summary: { coverage80: number; test_r2: number; test_mae: number; n_test: number }; grid: number[]; postings: Posting[] };

const W = 760, H = 168, L0 = 1.5, L1 = 80;

export default function Estimator({ demo }: { demo: Demo }) {
  const [cur, setCur] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const p = demo.postings[cur];
  const start = Math.min(20, Math.round(p.exp_min));
  const [exp, setExp] = useState(start);
  const select = (i: number) => { setCur(i); setRevealed(false); setExp(Math.min(20, Math.round(demo.postings[i].exp_min))); };
  const atStart = exp === start;
  const [lo, est, hi] = atStart ? [p.low80, p.est, p.high80] : p.whatif[exp];
  const x = useMemo(() => scaleLog().domain([L0, L1]).range([18, W - 18]).clamp(true), []);
  const L = (v: number) => Math.round(x(v / 1e5) * 10) / 10;
  const statedMid = (p.stated_min + p.stated_max) / 2;
  const inside = statedMid >= lo && statedMid <= hi;
  const off = Math.round(Math.abs(est / statedMid - 1) * 100);
  const ticks = [2, 5, 10, 25, 50];

  return (
    <div className="hero">
      <div>
        <p className="figtitle">Ten held-out postings, one per role</p>
        <ul className="postlist">
          {demo.postings.map((q, i) => (
            <li key={i}><button aria-current={i === cur} onClick={() => select(i)}><b>{q.title}</b>{q.company}, {q.role}</button></li>
          ))}
        </ul>
      </div>
      <div key={cur} className="swap">
        <h3 className="est-title">{p.title}</h3>
        <p className="est-meta">{p.company}, {p.location}. {p.work_mode}. Asks for {p.experience}.</p>
        <div>{p.skills.slice(0, 9).map((s) => <span className="chip" key={s}>{s}</span>)}</div>
        <div className="bigfig" key={Math.round(est / 1e4)} aria-live="polite">{lk(est / 1e5, 1)}<small>a year, model estimate</small></div>
        <p className="small" style={{ margin: "0 0 6px" }}>
          Likely range {lk(lo / 1e5)} to {lk(hi / 1e5)}. In tests on {demo.summary.n_test} postings from employers the model had not seen, ranges built this way held the stated salary {Math.round(demo.summary.coverage80 * 100)}% of the time (the target was 80%).
        </p>
        <svg className="scale" viewBox={`0 0 ${W} ${H}`} width="100%" style={{ width: "100%", height: "auto", aspectRatio: `${W} / ${H}` }} role="img"
          aria-label={`Estimate ${lk(est / 1e5)}, 80 percent range ${lk(lo / 1e5)} to ${lk(hi / 1e5)}${revealed ? `, stated ${lk(p.stated_min / 1e5)} to ${lk(p.stated_max / 1e5)}` : ""}`}>
          <line x1={18} x2={W - 18} y1={98} y2={98} stroke="var(--rule)" />
          {ticks.map((t) => (
            <g key={t}><line x1={L(t * 1e5)} x2={L(t * 1e5)} y1={92} y2={104} stroke="var(--ink3)" /><text x={L(t * 1e5)} y={122} textAnchor="middle">{`₹${t} L`}</text></g>
          ))}
          <rect x={L(p.low90)} width={L(p.high90) - L(p.low90)} y={58} height={30} rx={3} fill="var(--seq0)" style={{ opacity: atStart ? 1 : 0, transition: "opacity .25s" }} />
          <rect x={L(lo)} width={Math.max(2, L(hi) - L(lo))} y={58} height={30} rx={3} fill="var(--c1)" />
          <line x1={L(est)} x2={L(est)} y1={46} y2={94} stroke="var(--ink)" strokeWidth={3} />
          <text className="lbl" x={L(est)} y={36} textAnchor="middle">estimate</text>
          <text x={L(lo)} y={50} textAnchor="middle">{lk(lo / 1e5)}</text>
          <text x={L(hi)} y={50} textAnchor="middle">{lk(hi / 1e5)}</text>
          {revealed ? (
            <g>
              <rect x={L(p.stated_min)} width={Math.max(3, L(p.stated_max) - L(p.stated_min))} y={104} height={9} rx={2} fill="var(--c2)" />
              <text className="lbl" x={(L(p.stated_min) + L(p.stated_max)) / 2} y={146} textAnchor="middle" style={{ fill: "var(--c2)" }}>stated by the employer</text>
            </g>
          ) : null}
        </svg>
        <p className="small" style={{ margin: "0 0 4px" }}>
          <span style={{ display: "inline-block", width: 12, height: 12, background: "var(--c1)", marginRight: 6, verticalAlign: "-1px" }} />80% range
          {atStart ? <><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--seq0)", margin: "0 6px 0 18px", verticalAlign: "-1px" }} />90% range</> : null}
          <span style={{ display: "inline-block", width: 3, height: 13, background: "var(--ink)", margin: "0 6px 0 18px", verticalAlign: "-2px" }} />estimate
          {revealed ? <><span style={{ display: "inline-block", width: 12, height: 9, background: "var(--c2)", margin: "0 6px 0 18px", verticalAlign: "0" }} />stated range</> : null}
        </p>
        {revealed ? (
          <div className="slide"><div className={`verdict${inside ? " ok" : ""}`}>
            The employer states {lk(p.stated_min / 1e5)} to {lk(p.stated_max / 1e5)}. The midpoint, {lk(statedMid / 1e5)}, is {inside ? "inside" : "outside"} the model's 80% range, and the estimate is {off}% {est >= statedMid ? "above" : "below"} it.
          </div></div>
        ) : (
          <p style={{ marginTop: 12 }}><button className="btn" onClick={() => setRevealed(true)}>Show the salary the employer stated</button></p>
        )}
        <div className="controls" style={{ marginTop: 18 }}>
          <label>Experience asked for: <b className="num">{exp} {exp === 1 ? "year" : "years"}</b>
            <input type="range" min={0} max={20} step={1} value={exp} onChange={(e) => setExp(+e.target.value)} aria-label="Years of experience asked for" />
          </label>
          {!atStart ? <button className="btn ghost" onClick={() => setExp(start)}>Reset to {start}</button> : null}
        </div>
        <p className="small">Changing the experience changes only that field. The wording of the posting and everything else stay as they are, so this shows how the model reads experience, not what an employer would offer.</p>
      </div>
    </div>
  );
}
