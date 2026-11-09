"use client";
import { quantile } from "@/lib/stats";
import { lk } from "@/lib/format";

export type Group = { key: string; label: string; vals: number[] };
const LO = 1.5, HI = 70, W = 100;
const x = (v: number) => (Math.log(Math.max(v, LO) / LO) / Math.log(HI / LO)) * W;

/** Pay by group as a ranked list: whisker 10th to 90th percentile, bar middle half, tick median. Clicking a row picks that group. */
export default function RankList({ groups, selected, onPick, empty = "No postings match.", keepOrder = false }: { groups: Group[]; selected: string; onPick: (k: string) => void; empty?: string; keepOrder?: boolean }) {
  const rows = groups.map((g) => ({ ...g, n: g.vals.length, p10: quantile(g.vals, 0.1), p25: quantile(g.vals, 0.25), med: quantile(g.vals, 0.5), p75: quantile(g.vals, 0.75), p90: quantile(g.vals, 0.9) })).filter((r) => r.n > 0);
  if (!keepOrder) rows.sort((a, b) => b.med - a.med);
  if (!rows.length) return <p className="small">{empty}</p>;
  return (
    <ul className="ranklist" role="listbox" aria-label="Pay by group, click to filter">
      {rows.map((r) => (
        <li key={r.key}>
          <button role="option" aria-selected={selected === r.key} onClick={() => onPick(r.key)} title={`${r.label}: median ${lk(r.med)}, middle half ${lk(r.p25)} to ${lk(r.p75)}, ${r.n} postings`}>
            <span className="rl-name">{r.label}</span>
            <svg viewBox={`0 0 ${W} 14`} preserveAspectRatio="none" className="rl-svg" aria-hidden>
              <line x1={x(r.p10)} x2={x(r.p90)} y1={7} y2={7} stroke="var(--ink3)" strokeWidth={1.2} vectorEffect="non-scaling-stroke" />
              <rect x={x(r.p25)} width={Math.max(0.8, x(r.p75) - x(r.p25))} y={2} height={10} fill="var(--c1)" />
              <line x1={x(r.med)} x2={x(r.med)} y1={0} y2={14} stroke="var(--bg)" strokeWidth={2} vectorEffect="non-scaling-stroke" />
            </svg>
            <span className="rl-med">{lk(r.med)}</span>
            <span className="rl-n">{r.n}</span>
          </button>
        </li>
      ))}
      <li className="rl-axis" aria-hidden><span /> <span className="rl-ticks">{[2, 5, 10, 20, 40].map((t) => <i key={t} style={{ left: `${x(t)}%` }}>{t}</i>)}</span><span className="rl-med">median</span><span className="rl-n">n</span></li>
    </ul>
  );
}
