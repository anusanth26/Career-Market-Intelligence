import * as Plot from "@observablehq/plot";
import { Tokens } from "./tokens";

type Row = Record<string, any>;
export type Build = (t: Tokens, w: number) => Plot.PlotOptions;

/** Horizontal bars with a value label at the end, optional error whiskers and a reference line. */
export function barsH(o: {
  data: Row[]; label: string; value: string; fmt: (v: number) => string; color?: (d: Row, t: Tokens) => string;
  domain?: [number, number]; xLabel?: string; sd?: string; ref?: number; base?: number; marginLeft?: number; ticks?: number[]; tickFmt?: (v: number) => string; rowH?: number;
}): Build {
  return (t) => {
    const base = o.base ?? 0;
    return {
      height: 48 + o.data.length * (o.rowH ?? 30), marginLeft: o.marginLeft ?? 170, marginRight: 64, marginTop: 8, marginBottom: 44,
      x: { domain: o.domain, label: o.xLabel ?? null, labelAnchor: "left", grid: true, ticks: o.ticks, tickFormat: o.tickFmt, line: false },
      y: { label: null, tickSize: 0, domain: o.data.map((d) => d[o.label]) },
      marks: [
        Plot.barX(o.data, { y: o.label, x1: base, x2: o.value, fill: (d: Row) => (o.color ? o.color(d, t) : t.cat[0]), insetTop: 4, insetBottom: 4 }),
        o.sd ? Plot.ruleY(o.data, { y: o.label, x1: (d: Row) => d[o.value] - d[o.sd!], x2: (d: Row) => d[o.value] + d[o.sd!], stroke: t.ink, strokeWidth: 1.4 }) : null,
        Plot.text(o.data.filter((d) => d[o.value] >= base), { y: o.label, x: (d: Row) => d[o.value] + (o.sd ? d[o.sd] : 0), text: (d: Row) => o.fmt(d[o.value]), dx: 7, textAnchor: "start", fill: t.ink }),
        Plot.text(o.data.filter((d) => d[o.value] < base), { y: o.label, x: (d: Row) => d[o.value] - (o.sd ? d[o.sd] : 0), text: (d: Row) => o.fmt(d[o.value]), dx: -7, textAnchor: "end", fill: t.ink }),
        o.ref != null ? Plot.ruleX([o.ref], { stroke: t.ink, strokeDasharray: "4 3" }) : Plot.ruleX([base], { stroke: t.ink3 }),
        Plot.tip(o.data, Plot.pointerY({ y: o.label, x: o.value, title: (d: Row) => `${d[o.label]}\n${o.fmt(d[o.value])}${o.sd ? ` (±${d[o.sd].toFixed(3)} across folds)` : ""}` })),
      ].filter(Boolean) as Plot.Markish[],
    };
  };
}

/** Two values per row joined by a line. */
export function dumbbell(o: {
  data: Row[]; label: string; a: string; b: string; aName: string; bName: string; fmt: (v: number) => string; xLabel?: string; marginLeft?: number; domain?: [number, number];
}): Build {
  return (t) => ({
    height: 66 + o.data.length * 30, marginLeft: o.marginLeft ?? 170, marginRight: 30, marginTop: 24, marginBottom: 44,
    x: { label: o.xLabel ?? null, labelAnchor: "left", grid: true, domain: o.domain }, y: { label: null, tickSize: 0, domain: o.data.map((d) => d[o.label]) },
    marks: [
      Plot.ruleY(o.data, { y: o.label, x1: o.a, x2: o.b, stroke: t.ink3, strokeWidth: 2 }),
      Plot.dot(o.data, { y: o.label, x: o.a, r: 6, fill: t.cat[1], stroke: t.bg, strokeWidth: 2 }),
      Plot.dot(o.data, { y: o.label, x: o.b, r: 6, fill: t.cat[0], stroke: t.bg, strokeWidth: 2 }),
      Plot.tip(o.data, Plot.pointerY({ y: o.label, x: o.b, title: (d: Row) => `${d[o.label]}\n${o.aName}: ${o.fmt(d[o.a])}\n${o.bName}: ${o.fmt(d[o.b])}` })),
    ],
  });
}

/** Heat map from long rows. */
export function heat(o: {
  data: Row[]; x: string; y: string; v: string; fmt: (v: number) => string; xDomain: string[]; yDomain: string[]; domain?: [number, number]; diverging?: boolean;
  marginLeft?: number; marginBottom?: number; cellH?: number; textMin?: number; xLabelRotate?: number; xOnTop?: boolean;
}): Build {
  return (t, w) => {
    const [lo, hi] = o.domain ?? [0, Math.max(...o.data.map((d) => d[o.v]))];
    const range = o.diverging ? [t.neg, t.mid, t.pos] : t.seq;
    const dom = o.diverging ? [lo, 0, hi] : t.seq.map((_, i) => lo + ((hi - lo) * i) / (t.seq.length - 1));
    const mid = lo + (hi - lo) * 0.5;
    return {
      height: (o.marginBottom ?? 90) + 24 + o.yDomain.length * (o.cellH ?? 30), marginLeft: o.marginLeft ?? 150, marginBottom: o.marginBottom ?? 90, marginTop: o.xOnTop ? 90 : 10, marginRight: 8,
      x: { domain: o.xDomain, label: null, tickRotate: o.xLabelRotate ?? -40, tickSize: 0, axis: o.xOnTop ? "top" : "bottom" }, y: { domain: o.yDomain, label: null, tickSize: 0 },
      color: { type: "linear", domain: dom, range, clamp: true },
      marks: [
        Plot.cell(o.data, { x: o.x, y: o.y, fill: o.v, inset: 1 }),
        Plot.text(o.data, { x: o.x, y: o.y, text: (d: Row) => (Math.abs(d[o.v]) >= (o.textMin ?? 0) ? o.fmt(d[o.v]) : ""), fill: (d: Row) => { if (o.diverging) return t.ink; const f = (d[o.v] - lo) / (hi - lo || 1); const cellIsDark = t.dark ? f <= 0.55 : f > 0.55; return cellIsDark ? "#ffffff" : "#16212b"; }, fontSize: 11 }),
        Plot.tip(o.data, Plot.pointer({ x: o.x, y: o.y, title: (d: Row) => `${d[o.y]}, ${d[o.x]}\n${o.fmt(d[o.v])}` })),
      ],
    };
  };
}

/** p10-p90 whisker, p25-p75 bar and median tick per group, salaries in lakh on a log axis. */
export function rangeBars(o: { data: Row[]; label: string; domain?: [number, number]; marginLeft?: number }): Build {
  const d = o.data.map((r) => ({ ...r, p10l: r.p10 / 1e5, p25l: r.p25 / 1e5, medl: r.median / 1e5, p75l: r.p75 / 1e5, p90l: r.p90 / 1e5 }));
  return (t) => ({
    height: 44 + d.length * 32, marginLeft: o.marginLeft ?? 150, marginRight: 70, marginTop: 8, marginBottom: 36,
    x: { type: "log", domain: o.domain ?? [1.5, 45], label: "salary, lakh per year (log scale)", labelAnchor: "left", grid: true, ticks: [2, 3, 5, 10, 20, 40], tickFormat: (v: number) => String(v) },
    y: { label: null, tickSize: 0, domain: d.map((r) => r[o.label]) },
    marks: [
      Plot.ruleY(d, { y: o.label, x1: "p10l", x2: "p90l", stroke: t.ink3, strokeWidth: 1.5 }),
      Plot.barX(d, { y: o.label, x1: "p25l", x2: "p75l", fill: t.cat[0], insetTop: 6, insetBottom: 6 }),
      Plot.tickX(d, { y: o.label, x: "medl", stroke: t.bg, strokeWidth: 2.5, insetTop: 4, insetBottom: 4 }),
      Plot.text(d, { y: o.label, x: "p90l", text: (r: Row) => `n ${r.n}`, dx: 8, textAnchor: "start", fill: t.ink3, fontSize: 11 }),
      Plot.tip(d, Plot.pointerY({ y: o.label, x: "medl", title: (r: Row) => `${r[o.label]}  (n ${r.n})\nmedian ₹${r.medl.toFixed(1)} L\nmiddle half ₹${r.p25l.toFixed(1)} to ${r.p75l.toFixed(1)} L\n80% of postings ₹${r.p10l.toFixed(1)} to ${r.p90l.toFixed(1)} L` })),
    ],
  });
}
