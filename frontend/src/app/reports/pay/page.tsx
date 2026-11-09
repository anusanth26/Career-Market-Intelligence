"use client";
import PageNav from "@/components/PageNav";
import * as Plot from "@observablehq/plot";
import Block, { Fig } from "@/components/Block";
import DataDetails from "@/components/DataDetails";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { Tokens } from "@/lib/tokens";
import { barsH, dumbbell, rangeBars } from "@/lib/charts";
import { f3, inr, lakh, pct, pct0, sgn } from "@/lib/format";
import S from "@/data/salary.json";

const q = (arr: number[], p: number) => { const a = [...arr].sort((x, y) => x - y); const i = (a.length - 1) * p; const lo = Math.floor(i); return a[lo] + (a[Math.ceil(i)] - a[lo]) * (i - lo); };
const strip = (s: string) => s.replace(" (tuned, all features)", "");

export default function PayPage() {
  const medians = q((S.scatter as any[]).map((d) => d.lakh), 0.5);
  const models = (S.models as any[]).map((m) => ({ ...m, base: m.model === "Global median" || m.model === "Role median" }));
  const byR2 = [...models].sort((a, b) => b.R2_log - a.R2_log);
  const byMae = [...models].sort((a, b) => a.MAE_INR - b.MAE_INR).map((m) => ({ ...m, mae_l: m.MAE_INR / 1e5 }));
  const ref = (S.drop as any[]).find((d) => d.variant === "all groups (reference)");
  const drop = (S.drop as any[]).filter((d) => d.variant !== "all groups (reference)").map((d) => ({ ...d, group: d.variant.replace("without ", ""), dR2: d.R2_log - ref.R2_log })).sort((a, b) => a.dR2 - b.dR2);
  const add = S.add as any[];
  const imp = [...(S.importance as any[])].sort((a, b) => b.drop_in_R2 - a.drop_in_R2);
  const txt = [...(S.text_ablation as any[])].sort((a, b) => b.R2_log - a.R2_log);
  const curve = (S.curve as any[]).map((c) => ({ ...c, rows: Math.round(S.n_train * 0.8 * (parseFloat(c.share) / 100)) }));
  const cqr = S.cqr as any[];
  const err = [...(S.err_role as any[])].sort((a, b) => b.MAE_INR - a.MAE_INR).map((r) => ({ ...r, model_l: r.MAE_INR / 1e5, base_l: r.role_median_MAE / 1e5 }));
  const condR = [...(S.cond_role as any[])].sort((a, b) => a.coverage - b.coverage);
  const condE = S.cond_exp as any[];
  const test = S.test as any[];
  const modelTest = test.find((t) => t.model.startsWith("XGBoost")), roleTest = test.find((t) => t.model === "Role median");
  const cv = (S.tuned as any[]).find((t) => t.model === "XGBoost (tuned)");
  const roleCv = models.find((m) => m.model === "Role median");
  const c80 = cqr.find((c) => c.setting === "CQR, 80% target"), raw80 = cqr.find((c) => c.setting.startsWith("Quantile bands without") && c.setting.includes("80%")), rm80 = cqr.find((c) => c.setting.startsWith("Role median") && c.setting.includes("80%"));

  const buildHist = (t: Tokens): Plot.PlotOptions => ({
    height: 220, marginLeft: 46, marginBottom: 40,
    x: { type: "log", label: "salary midpoint, lakh per year (log scale)", labelAnchor: "left", ticks: [1, 2, 3, 5, 10, 20, 40, 70], tickFormat: (d: number) => String(d) }, y: { label: "postings", grid: true },
    marks: [
      Plot.rectY(S.hist as any[], { x1: "lo", x2: "hi", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }),
      Plot.ruleX([medians], { stroke: t.ink, strokeDasharray: "4 3" }),
      Plot.text([{ x: medians, y: Math.max(...(S.hist as any[]).map((h) => h.n)) }], { x: "x", y: "y", text: () => `median ₹${medians.toFixed(1)} L`, dx: 6, textAnchor: "start", fill: t.ink, fontWeight: 650 }),
      Plot.tip(S.hist as any[], Plot.pointerX({ x: (d: any) => Math.sqrt(d.lo * d.hi), y: "n", title: (d: any) => `₹${d.lo.toFixed(1)} to ${d.hi.toFixed(1)} L\n${d.n} postings` })),
    ],
  });
  const buildScatter = (t: Tokens): Plot.PlotOptions => ({
    height: 340, marginLeft: 46, marginBottom: 42,
    x: { label: "experience asked for, years (midpoint of the range)", labelAnchor: "left", domain: [0, 30] }, y: { type: "log", label: "salary midpoint, lakh", grid: true, ticks: [2, 5, 10, 20, 40], tickFormat: (d: number) => String(d) },
    marks: [
      Plot.dot(S.scatter as any[], { x: "exp", y: "lakh", r: 2.4, fill: t.cat[0], fillOpacity: 0.25, clip: true }),
      Plot.line((S.by_exp as any[]).map((b, i) => ({ x: [1, 3.5, 6.5, 10, 14][i], y: b.median / 1e5 })), { x: "x", y: "y", stroke: t.cat[1], strokeWidth: 3 }),
      Plot.dot((S.by_exp as any[]).map((b, i) => ({ x: [1, 3.5, 6.5, 10, 14][i], y: b.median / 1e5, band: b.band })), { x: "x", y: "y", r: 5, fill: t.cat[1], stroke: t.bg, strokeWidth: 2 }),
      Plot.text([{ x: 14.5, y: ((S.by_exp as any[])[4].median) / 1e5 }], { x: "x", y: "y", text: () => "median of each band", dx: 10, textAnchor: "start", fill: t.cat[1], fontWeight: 650 }),
    ],
  });
  const buildBuild = (t: Tokens): Plot.PlotOptions => ({
    height: 320, marginLeft: 50, marginBottom: 80,
    x: { type: "point", domain: add.map((a) => a.variant), label: null, tickRotate: -35, tickSize: 0 }, y: { label: "R², cross-validated", grid: true, domain: [0.33, 0.75] },
    marks: [
      Plot.ruleY([roleCv.R2_log], { stroke: t.cat[1], strokeDasharray: "4 3" }),
      Plot.text([{ x: add[add.length - 1].variant, y: roleCv.R2_log }], { x: "x", y: "y", text: () => "role median alone", dy: 10, textAnchor: "end", fill: t.cat[1], fontWeight: 650 }),
      Plot.ruleX(add, { x: "variant", y1: (d: any) => d.R2_log - d.R2_sd, y2: (d: any) => d.R2_log + d.R2_sd, stroke: t.ink3 }),
      Plot.line(add, { x: "variant", y: "R2_log", stroke: t.cat[0], strokeWidth: 2.5 }),
      Plot.dot(add, { x: "variant", y: "R2_log", r: 4.5, fill: t.cat[0], stroke: t.bg, strokeWidth: 2 }),
      Plot.text(add, { x: "variant", y: "R2_log", text: (d: any) => d.R2_log.toFixed(2), dy: -12, fill: t.ink }),
    ],
  });
  const buildCurve = (t: Tokens): Plot.PlotOptions => ({
    height: 260, marginLeft: 50, marginBottom: 42,
    x: { label: "training postings per fold", labelAnchor: "left", domain: [100, 960] }, y: { label: "R², cross-validated", grid: true, domain: [0.55, 0.75] },
    marks: [
      Plot.ruleX(curve, { x: "rows", y1: (d: any) => d.R2_log - d.R2_sd, y2: (d: any) => d.R2_log + d.R2_sd, stroke: t.ink3 }),
      Plot.line(curve, { x: "rows", y: "R2_log", stroke: t.cat[0], strokeWidth: 2.5 }),
      Plot.dot(curve, { x: "rows", y: "R2_log", r: 4.5, fill: t.cat[0], stroke: t.bg, strokeWidth: 2 }),
      Plot.text(curve, { x: "rows", y: "R2_log", text: (d: any) => d.R2_log.toFixed(3), dy: -12, fill: t.ink }),
    ],
  });
  const buildCover = (t: Tokens): Plot.PlotOptions => {
    const d = [
      { k: "Quantile bands as fitted", v: raw80.coverage, w: raw80.median_width_ratio },
      { k: "Conformal bands (the model's range)", v: c80.coverage, w: c80.median_width_ratio },
      { k: "Role median plus conformal band", v: rm80.coverage, w: rm80.median_width_ratio },
    ];
    return {
      height: 150, marginLeft: 230, marginRight: 150, marginBottom: 34,
      x: { domain: [0.6, 0.9], label: "share of test postings whose stated salary fell inside the band", labelAnchor: "left", grid: true, tickFormat: (v: number) => `${Math.round(v * 100)}%` }, y: { label: null, tickSize: 0 },
      marks: [
        Plot.barX(d, { y: "k", x1: 0.6, x2: "v", fill: (r: any) => (r.k.startsWith("Conformal") ? t.cat[0] : t.ink3), insetTop: 6, insetBottom: 6 }),
        Plot.text(d, { y: "k", x: "v", text: (r: any) => `${(r.v * 100).toFixed(1)}%, ${r.w.toFixed(1)}× wide`, dx: 7, textAnchor: "start", fill: t.ink }),
        Plot.ruleX([0.8], { stroke: t.ink, strokeDasharray: "4 3" }),
      ],
    };
  };
  const buildCondRole = (t: Tokens): Plot.PlotOptions => ({
    height: 56 + condR.length * 28, marginLeft: 170, marginRight: 70,
    x: { domain: [0.4, 1], label: "share of the role's test postings inside the 80% range", labelAnchor: "left", grid: true, tickFormat: (v: number) => `${Math.round(v * 100)}%` }, y: { label: null, tickSize: 0, domain: condR.map((r) => r.role) },
    marks: [
      Plot.ruleY(condR, { y: "role", x1: 0.4, x2: "coverage", stroke: t.ink3 }),
      Plot.dot(condR, { y: "role", x: "coverage", r: (d: any) => 3 + Math.sqrt(d.n) * 0.9, fill: (d: any) => (d.coverage < 0.8 ? t.cat[1] : t.cat[0]), stroke: t.bg, strokeWidth: 1.5 }),
      Plot.text(condR, { y: "role", x: "coverage", text: (d: any) => `${pct0(d.coverage)}  (n ${d.n})`, dx: 16, textAnchor: "start", fill: t.ink, fontSize: 11.5 }),
      Plot.ruleX([0.8], { stroke: t.ink, strokeDasharray: "4 3" }),
    ],
  });
  const buildCondExp = (t: Tokens): Plot.PlotOptions => ({
    height: 56 + condE.length * 28, marginLeft: 80, marginRight: 80,
    x: { domain: [0.4, 1], label: "share inside the 80% range", labelAnchor: "left", grid: true, tickFormat: (v: number) => `${Math.round(v * 100)}%` }, y: { label: "years of experience", tickSize: 0, domain: condE.map((r) => r.band) },
    marks: [
      Plot.ruleY(condE, { y: "band", x1: 0.4, x2: "coverage", stroke: t.ink3 }),
      Plot.dot(condE, { y: "band", x: "coverage", r: (d: any) => 3 + Math.sqrt(d.n) * 0.9, fill: (d: any) => (d.coverage < 0.8 ? t.cat[1] : t.cat[0]), stroke: t.bg, strokeWidth: 1.5 }),
      Plot.text(condE, { y: "band", x: "coverage", text: (d: any) => `${pct0(d.coverage)}  (n ${d.n})`, dx: 16, textAnchor: "start", fill: t.ink, fontSize: 11.5 }),
      Plot.ruleX([0.8], { stroke: t.ink, strokeDasharray: "4 3" }),
    ],
  });

  return (
    <>
      <h1>Pay follows experience and the wording of a posting, and the honest answer is a range</h1>
      <p className="lede">{inr(S.funnel[2].n)} postings state a salary; {inr(S.funnel[3].n)} of them, from {inr(S.companies)} companies, are used here. The model is cross-validated on postings grouped by employer and tested once on {S.n_test} postings from employers it never saw.</p>
      <PageNav />
      <div className="statrow">
        <div><b>{(cv.R2_log).toFixed(2)}</b><span>R² in cross-validation, against {roleCv.R2_log.toFixed(2)} for the role median</span></div>
        <div><b>{lakh(cv.MAE_INR)}</b><span>typical error, against {lakh(roleCv.MAE_INR)} for the role median</span></div>
        <div><b>{pct0(c80.coverage)}</b><span>of stated salaries fall inside the 80% range on the test postings</span></div>
        <div><b>{c80.median_width_ratio.toFixed(1)}×</b><span>how much wider the top of a range is than its bottom, typically</span></div>
      </div>

      <Block title="What do these postings pay?"
        note={<><p>The middle of the data is <strong>₹{medians.toFixed(1)} lakh a year</strong>, and the spread is wide: the middle 80% of postings run from about ₹2 to ₹33 lakh.</p>
          <p><strong>Role and experience separate pay clearly.</strong> Data Scientist and Product Manager sit around ₹20 lakh, Graphic Designer around ₹4 lakh. Median pay rises from about ₹3 lakh at 0 to 2 years to ₹16 lakh beyond 12.</p>
          <p>Only about 12% of postings state a salary, so these are postings that disclose pay.</p></>}>
        <Fig title="How salaries are spread" sub={`${inr(S.funnel[3].n)} postings, midpoint of the stated range`}><PlotFigure label="Histogram of salary midpoints on a log scale" build={buildHist} minHeight={220} /></Fig>
        <Fig title="Pay by role" sub="Line: middle 80% of postings. Bar: middle half. White tick: median."><PlotFigure label="Salary range by role" build={rangeBars({ data: S.by_role as any[], label: "role" })} minHeight={360} /></Fig>
        <Fig title="Pay against experience asked for" sub="Each dot is a posting."><PlotFigure label="Salary against years of experience asked for" build={buildScatter} minHeight={340} /></Fig>
        <DataDetails summary="Table: pay by role" rows={[...(S.by_role as any[])].reverse()} cols={[{ key: "role", label: "Role" }, { key: "n", label: "Postings", right: true }, { key: "p10", label: "10%", right: true, fmt: (v) => lakh(v) }, { key: "median", label: "Median", right: true, fmt: (v) => lakh(v) }, { key: "p90", label: "90%", right: true, fmt: (v) => lakh(v) }]} />
      </Block>

      <Block title="Which model predicts best?"
        note={<><p>Four models were compared on identical features and folds, with two baselines that learn nothing. Bars show R² on log salary; the whisker is the spread across folds.</p>
          <p><strong>Stacking and XGBoost are tied</strong> within that spread. Ridge and the random forest are only 0.03 behind, so most of the signal is additive.</p>
          <p>Tuning XGBoost made no difference (R² 0.695 to 0.696). The limit is the information in the postings, not the settings.</p></>}>
        <Legend items={[{ color: "var(--ink3)", label: "baseline that learns nothing" }, { color: "var(--c1)", label: "learned model" }]} />
        <Fig title="R² on unseen employers, five-fold cross-validation" sub="Higher is better. Whisker: standard deviation across folds."><PlotFigure label="R-squared for four models and two baselines" build={barsH({ data: byR2, label: "model", value: "R2_log", sd: "R2_sd", fmt: f3, domain: [-0.2, 0.8], color: (d, t) => (d.base ? t.ink3 : t.cat[0]), marginLeft: 200 })} minHeight={300} /></Fig>
        <Fig title="Average error in lakh" sub="Lower is better."><PlotFigure label="Mean absolute error in lakh for four models and two baselines" build={barsH({ data: byMae, label: "model", value: "mae_l", fmt: (v) => `₹${v.toFixed(1)} L`, color: (d, t) => (d.base ? t.ink3 : t.cat[0]), marginLeft: 200, domain: [0, 9] })} minHeight={300} /></Fig>
        <DataDetails summary="Table: all models" rows={byR2} cols={[{ key: "model", label: "Model" }, { key: "R2_log", label: "R²", right: true, fmt: f3 }, { key: "R2_sd", label: "Fold SD", right: true, fmt: f3 }, { key: "MAE_INR", label: "Mean error", right: true, fmt: (v) => lakh(v) }, { key: "Within30", label: "Within 30%", right: true, fmt: (v) => pct0(v) }]} />
      </Block>

      <Block title="What does the model rely on?"
        note={<><p><strong>Experience is the one input it cannot lose:</strong> without it R² drops by about 0.11. The description text is second (about 0.02).</p>
          <p>Every other group costs almost nothing when removed, because role, seniority and skills overlap with experience and text.</p>
          <p>Shuffling a group on the test postings tells the same story: experience {imp[0].drop_in_R2.toFixed(2)}, text {imp[1].drop_in_R2.toFixed(2)}, everything else under 0.01.</p></>}>
        <Fig title="Accuracy lost when one group of inputs is removed" sub="Change in cross-validated R². Negative means the model got worse."><PlotFigure label="Change in R-squared when each feature group is removed" build={barsH({ data: drop, label: "group", value: "dR2", fmt: (v) => sgn(v), color: (d, t) => (d.dR2 < -0.01 ? t.cat[1] : t.ink3), domain: [-0.13, 0.02], marginLeft: 120, ticks: [-0.12, -0.08, -0.04, 0] })} minHeight={380} /></Fig>
        <Fig title="Accuracy as groups are added one at a time" sub="Whisker: spread across folds."><PlotFigure label="R-squared as feature groups are added" build={buildBuild} minHeight={320} /></Fig>
        <Fig title="How much shuffling a group hurts on the test postings" sub="Drop in test R² when all columns of the group are shuffled together."><PlotFigure label="Group permutation importance" build={barsH({ data: imp, label: "group", value: "drop_in_R2", sd: "sd", fmt: (v) => v.toFixed(3), color: (d, t) => (d.drop_in_R2 > 0.05 ? t.cat[0] : t.ink3), domain: [0, 0.7], marginLeft: 120 })} minHeight={360} /></Fig>
      </Block>

      <Block title="What does the description add, and what did the 500-character limit cost?"
        note={<><p>Fifty SVD dimensions of the description raise R² from {txt.find((d) => d.variant === "no text").R2_log.toFixed(3)} to {txt.find((d) => d.variant === "all + text, SVD 50").R2_log.toFixed(3)}. On its own the text reaches {txt.find((d) => d.variant === "text only (50 dims)").R2_log.toFixed(2)}, well above the role median.</p>
          <p><strong>Cutting the text to its first 500 characters</strong>, the limit of the earlier data, lowers R² to {txt.find((d) => d.variant.startsWith("all + first 500")).R2_log.toFixed(3)}. The gap is smaller than the fold spread, so call it a small loss.</p>
          <p>Removing quoted pay amounts changes nothing, so the model is not reading the answer from the text.</p></>}>
        <Fig title="R² under each way of using the text" sub="Whisker: spread across folds."><PlotFigure label="R-squared under different text treatments" build={barsH({ data: txt, label: "variant", value: "R2_log", sd: "R2_sd", fmt: f3, domain: [0.4, 0.75], base: 0.4, color: (d, t) => (d.variant.includes("500") ? t.cat[1] : d.variant === "no text" ? t.ink3 : t.cat[0]), marginLeft: 300 })} minHeight={360} /></Fig>
        <Fig title="Would more postings help?" sub="Training on a growing share of each training fold."><PlotFigure label="Learning curve" build={buildCurve} minHeight={260} /></Fig>
      </Block>

      <Block title="How good are the ranges?"
        note={<><p>A range is only worth giving if it holds its promise. Aimed at 80%, the raw quantile bands held the stated salary only <strong>{pct(raw80.coverage)}</strong> of the time. After the conformal correction they held it <strong>{pct(c80.coverage)}</strong>.</p>
          <p>A role-median band reaches the same coverage but is <strong>{(rm80.median_width_ratio / c80.median_width_ratio).toFixed(1)} times wider</strong>: that is the gain from using the posting.</p>
          <p><strong>Coverage is uneven.</strong> Software Engineer, Data Scientist, Product Manager and Business Analyst are under 80%, and mid-career postings (5 to 12 years) sit near 77%. Groups are small (11 to 64 test postings), so read the direction, not the digits.</p></>}>
        <Fig title="Did the stated salary fall inside the band?" sub="257 test postings from employers the model had not seen. Dashed line: the 80% target."><PlotFigure label="Coverage of 80 percent bands for three methods" build={buildCover} minHeight={150} /></Fig>
        <Fig title="Coverage by role" sub="Dot size follows the number of test postings. Orange is under target."><PlotFigure label="Coverage of the 80 percent range by role" build={buildCondRole} minHeight={340} /></Fig>
        <Fig title="Coverage by experience band"><PlotFigure label="Coverage of the 80 percent range by experience" build={buildCondExp} minHeight={200} /></Fig>
      </Block>

      <Block title="Where does it go wrong?"
        note={<><p>On the test postings the model beats the role median in <strong>9 of 10 roles</strong>. Data Scientist is the exception, on only 11 postings.</p>
          <p>The big misses are <strong>under-predictions of high pay</strong>: senior or lead postings stated at ₹32 to 58 lakh predicted at ₹13 to 32 lakh, the usual pull of a regression towards the middle. One miss goes the other way, a data engineer stated at ₹5 to 12 lakh and predicted at ₹27 lakh.</p></>}>
        <Legend items={[{ color: "var(--c2)", label: "role median (no posting information)", shape: "dot" }, { color: "var(--c1)", label: "the model", shape: "dot" }]} />
        <Fig title="Average error by role on the test postings, in lakh" sub="Joined dots: how much the model improves on guessing the role's median."><PlotFigure label="Mean error by role, model against role median" build={dumbbell({ data: err, label: "role", a: "base_l", b: "model_l", aName: "role median", bName: "model", fmt: (v) => `₹${v.toFixed(1)} L` })} minHeight={360} /></Fig>
        <DataDetails summary="Table: the data-handling choices tested" rows={S.data_variants as any[]} cols={[{ key: "variant", label: "Variant" }, { key: "R2_log", label: "R²", right: true, fmt: f3 }, { key: "MAE_INR", label: "Mean error", right: true, fmt: (v) => lakh(v) }]} />
      </Block>
    </>
  );
}
