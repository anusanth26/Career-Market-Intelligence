"use client";
import { scaleLinear } from "d3-scale";

type Row = { skill: string; class: string; pct_change: number; low_volume: boolean; mk_trend: string; trend_confirmed: boolean };

function ma(v: number[], k = 8) {
  return v.map((_, i) => { const a = v.slice(Math.max(0, i - k + 1), i + 1); return a.reduce((s, x) => s + x, 0) / a.length; });
}

const COLOR: Record<string, string> = { rising: "var(--c3)", declining: "var(--c2)", stable: "var(--ink3)" };

/** One small line chart per skill, each on its own scale, coloured by the trend label. */
export default function Sparks({ dates, series, rows }: { dates: string[]; series: Record<string, number[]>; rows: Row[] }) {
  const W = 220, H = 74, pad = 4;
  const x = scaleLinear().domain([0, dates.length - 1]).range([pad, W - pad]);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "18px 22px" }}>
      {rows.map((r) => {
        const v = ma(series[r.skill]);
        const y = scaleLinear().domain([Math.min(...v), Math.max(...v)]).range([H - pad, pad + 6]);
        const d = v.map((q, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(q).toFixed(1)}`).join("");
        const col = r.low_volume ? "var(--ink3)" : COLOR[r.class];
        return (
          <figure key={r.skill} style={{ margin: 0 }}>
            <figcaption style={{ fontFamily: "var(--font-ui)", fontSize: 13.5, display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 2 }}>
              <b style={{ fontWeight: 620 }}>{r.skill}</b>
              <span className="num" style={{ color: col, fontWeight: 600 }}>{r.pct_change >= 0 ? "+" : "−"}{Math.abs(r.pct_change).toFixed(0)}%</span>
            </figcaption>
            <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${r.skill}: ${r.class}, ${r.pct_change.toFixed(0)} percent over five years${r.low_volume ? ", volume too small to rely on" : ""}`}>
              <line x1={pad} x2={W - pad} y1={H - pad} y2={H - pad} stroke="var(--rule)" />
              <path d={d} fill="none" stroke={col} strokeWidth={2} strokeLinejoin="round" strokeDasharray={r.low_volume ? "3 3" : undefined} opacity={r.low_volume ? 0.8 : 1} />
            </svg>
            <div style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--ink3)", marginTop: 1 }}>
              {r.low_volume ? "volume too small to judge" : `${r.class}${r.trend_confirmed ? ", confirmed by test" : ", test disagrees"}`}
            </div>
          </figure>
        );
      })}
    </div>
  );
}
