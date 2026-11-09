"use client";
import * as Plot from "@observablehq/plot";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { barsH, dumbbell } from "@/lib/charts";
import { Tokens } from "@/lib/tokens";
import { f3, pct0, sgn } from "@/lib/format";
import { ROWS } from "@/lib/filters";
import S from "@/data/salary.json";

const models = (S.models as any[]).map((m) => ({ ...m, base: m.model === "Global median" || m.model === "Role median" }));
const byR2 = [...models].sort((a, b) => b.R2_log - a.R2_log);
const byMae = [...models].sort((a, b) => a.MAE_INR - b.MAE_INR).map((m) => ({ ...m, mae_l: m.MAE_INR / 1e5 }));
const ref = (S.drop as any[]).find((d) => d.variant === "all groups (reference)");
const drop = (S.drop as any[]).filter((d) => d.variant !== "all groups (reference)").map((d) => ({ ...d, group: d.variant.replace("without ", ""), dR2: d.R2_log - ref.R2_log })).sort((a, b) => a.dR2 - b.dR2);
const imp = [...(S.importance as any[])].map((d) => ({ ...d, drop_in_R2: Math.max(0, d.drop_in_R2) })).sort((a, b) => b.drop_in_R2 - a.drop_in_R2);
const condR = [...(S.cond_role as any[])].sort((a, b) => a.coverage - b.coverage);
const condE = S.cond_exp as any[];
const err = [...(S.err_role as any[])].sort((a, b) => b.MAE_INR - a.MAE_INR).map((r) => ({ ...r, model_l: r.MAE_INR / 1e5, base_l: r.role_median_MAE / 1e5 }));

export const ModelR2 = () => <PlotFigure label="R-squared for four models and two baselines" minHeight={290} build={barsH({ data: byR2, label: "model", value: "R2_log", sd: "R2_sd", fmt: f3, domain: [-0.2, 0.8], color: (d, t) => (d.base ? t.ink3 : t.cat[0]), marginLeft: 190 })} />;
export const ModelErr = () => <PlotFigure label="Mean absolute error in lakh for four models and two baselines" minHeight={290} build={barsH({ data: byMae, label: "model", value: "mae_l", fmt: (v) => `₹${v.toFixed(1)} L`, color: (d, t) => (d.base ? t.ink3 : t.cat[0]), marginLeft: 190, domain: [0, 9] })} />;
export const DropChart = () => <PlotFigure label="Change in R-squared when each feature group is removed" minHeight={340} build={barsH({ data: drop, label: "group", value: "dR2", fmt: (v) => sgn(v), color: (d, t) => (d.dR2 < -0.01 ? t.cat[1] : t.ink3), domain: [-0.13, 0.02], marginLeft: 110, ticks: [-0.12, -0.08, -0.04, 0] })} />;
export const ImpChart = () => <PlotFigure label="Group permutation importance" minHeight={340} build={barsH({ data: imp, label: "group", value: "drop_in_R2", sd: "sd", fmt: (v) => v.toFixed(3), color: (d, t) => (d.drop_in_R2 > 0.05 ? t.cat[0] : t.ink3), domain: [0, 0.7], marginLeft: 110 })} />;
export const ErrChart = () => <><Legend items={[{ color: "var(--c2)", label: "guessing the role's median", shape: "dot" }, { color: "var(--c1)", label: "the model", shape: "dot" }]} /><PlotFigure label="Mean error by role, model against role median" minHeight={340} build={dumbbell({ data: err, label: "role", a: "base_l", b: "model_l", aName: "role median", bName: "model", fmt: (v) => `₹${v.toFixed(1)} L`, marginLeft: 150 })} /></>;
export function CovRole() {
  const build = (t: Tokens): Plot.PlotOptions => ({
    height: 70 + condR.length * 28, marginLeft: 160, marginRight: 80, marginBottom: 52,
    x: { domain: [0.4, 1], label: "share of the role's test postings inside the 80% range", labelAnchor: "left", grid: true, tickFormat: (v: number) => `${Math.round(v * 100)}%` }, y: { label: null, tickSize: 0, domain: condR.map((r) => r.role) },
    marks: [
      Plot.ruleY(condR, { y: "role", x1: 0.4, x2: "coverage", stroke: t.ink3 }),
      Plot.dot(condR, { y: "role", x: "coverage", r: (d: any) => 3 + Math.sqrt(d.n) * 0.9, fill: (d: any) => (d.coverage < 0.8 ? t.cat[1] : t.cat[0]), stroke: t.bg, strokeWidth: 1.5 }),
      Plot.text(condR, { y: "role", x: "coverage", text: (d: any) => `${pct0(d.coverage)}  (n ${d.n})`, dx: 16, textAnchor: "start", fill: t.ink, fontSize: 11.5 }),
      Plot.ruleX([0.8], { stroke: t.ink, strokeDasharray: "4 3" }),
    ],
  });
  return <><Legend items={[{ color: "var(--c1)", label: "at or above the 80% target", shape: "dot" }, { color: "var(--c2)", label: "below it", shape: "dot" }]} /><PlotFigure label="Coverage of the 80 percent range by role" minHeight={340} build={build} /></>;
}
export function CovExp() {
  const build = (t: Tokens): Plot.PlotOptions => ({
    height: 70 + condE.length * 30, marginLeft: 80, marginRight: 80, marginBottom: 52,
    x: { domain: [0.4, 1], label: "share inside the 80% range", labelAnchor: "left", grid: true, tickFormat: (v: number) => `${Math.round(v * 100)}%` }, y: { label: "years of experience", tickSize: 0, domain: condE.map((r) => r.band) },
    marks: [
      Plot.ruleY(condE, { y: "band", x1: 0.4, x2: "coverage", stroke: t.ink3 }),
      Plot.dot(condE, { y: "band", x: "coverage", r: (d: any) => 3 + Math.sqrt(d.n) * 0.9, fill: (d: any) => (d.coverage < 0.8 ? t.cat[1] : t.cat[0]), stroke: t.bg, strokeWidth: 1.5 }),
      Plot.text(condE, { y: "band", x: "coverage", text: (d: any) => `${pct0(d.coverage)}  (n ${d.n})`, dx: 16, textAnchor: "start", fill: t.ink, fontSize: 11.5 }),
      Plot.ruleX([0.8], { stroke: t.ink, strokeDasharray: "4 3" }),
    ],
  });
  return <><Legend items={[{ color: "var(--c1)", label: "at or above the 80% target", shape: "dot" }, { color: "var(--c2)", label: "below it", shape: "dot" }]} /><PlotFigure label="Coverage of the 80 percent range by experience" minHeight={240} build={build} /></>;
}

/** Share of log-salary variance each field explains on its own, adjusted for how many levels it has. */
const alone = (() => {
  const y = ROWS.map((r) => Math.log(r.mid)), n = y.length, my = y.reduce((a, b) => a + b, 0) / n, tot = y.reduce((a, b) => a + (b - my) ** 2, 0);
  const adj = (r2: number, k: number) => 1 - (1 - r2) * (n - 1) / (n - k);
  const oneWay = (key: (r: (typeof ROWS)[number]) => string) => {
    const g = new Map<string, number[]>(); ROWS.forEach((r, i) => g.set(key(r), [...(g.get(key(r)) ?? []), y[i]]));
    let within = 0; g.forEach((v) => { const m = v.reduce((a, b) => a + b, 0) / v.length; within += v.reduce((a, b) => a + (b - m) ** 2, 0); });
    return adj(1 - within / tot, g.size);
  };
  const ex = ROWS.map((r) => r.exp), mx = ex.reduce((a, b) => a + b, 0) / n;
  const cov = ex.reduce((a, e, i) => a + (e - mx) * (y[i] - my), 0), vx = ex.reduce((a, e) => a + (e - mx) ** 2, 0);
  const rows = [
    { group: "experience", r2: adj(cov * cov / (vx * tot), 2) },
    { group: "role", r2: oneWay((r) => r.role) }, { group: "industry", r2: oneWay((r) => r.industry) },
    { group: "work mode", r2: oneWay((r) => r.work_mode) }, { group: "seniority", r2: oneWay((r) => r.seniority) }, { group: "city", r2: oneWay((r) => r.city) },
  ];
  return rows.sort((a, b) => b.r2 - a.r2);
})();
export const AloneChart = () => <PlotFigure label="Share of log salary variance explained by each field on its own" minHeight={300} build={barsH({ data: alone, label: "group", value: "r2", fmt: (v) => v.toFixed(2), color: (d, t) => (d.group === "experience" ? t.cat[0] : t.ink3), domain: [0, 0.6], marginLeft: 110, ticks: [0, 0.2, 0.4, 0.6] })} />;
