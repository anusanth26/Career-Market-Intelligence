"use client";
import PageNav from "@/components/PageNav";
import Kpis from "@/components/Kpis";
import * as Plot from "@observablehq/plot";
import { useState } from "react";
import Block, { Fig } from "@/components/Block";
import DataDetails from "@/components/DataDetails";
import PlotFigure from "@/components/PlotFigure";
import Sparks from "@/components/Sparks";
import { Tokens } from "@/lib/tokens";
import { f2, f3, pct, sgnPct } from "@/lib/format";
import trends from "@/data/trends.json";
import gap from "@/data/gap.json";

const utc = (m: string) => new Date(m.length === 7 ? `${m}-01T00:00:00Z` : `${m}T00:00:00Z`);
const MON = new Intl.DateTimeFormat("en", { month: "short", year: "numeric", timeZone: "UTC" });

export default function TrendsPage() {
  const [pick, setPick] = useState<string[]>(["Python", "SQL", "AWS"]);
  const ai: any = trends.ai;
  const sorted = [...(trends.classes as any[])].sort((a, b) => b.pct_change - a.pct_change);
  const months = ai.months.map(utc);
  const treated: string[] = ai.treated, control: string[] = ai.control;
  const long: any[] = [];
  for (const s of [...treated, ...control]) ai.index[s].forEach((v: number, i: number) => long.push({ skill: s, group: treated.includes(s) ? "treated" : "control", date: months[i], v }));
  const gmean = (g: string) => months.map((d: Date, i: number) => {
    const names = g === "treated" ? treated : control; const logs = names.map((s) => Math.log(ai.index[s][i]));
    return { group: g, date: d, v: Math.exp(logs.reduce((a, b) => a + b, 0) / logs.length) };
  });
  const groupLines = [...gmean("treated"), ...gmean("control")];
  const event = utc(ai.event);
  const place: any[] = ai.placebo.map((p: any) => ({ date: utc(p.month), did: p.did }));
  const minP = place.reduce((a: any, b: any) => (b.did < a.did ? b : a));
  const hist = ai.perm_hist.counts.map((c: number, i: number) => ({ x1: ai.perm_hist.edges[i], x2: ai.perm_hist.edges[i + 1], n: c }));
  const conf: any[] = (trends.conformal as any).table;
  const ex: any = (trends.conformal as any).example;
  const gs: any[] = (gap as any).skills;

  const names = Object.keys(trends.series as any).sort();
  const cmpData = pick.flatMap((sk, k) => (trends.series as any)[sk].map((v: number, i: number) => ({ skill: sk, k, date: utc(trends.dates[i]), v })));
  const cmpLabel = (() => { // keep end labels apart where lines finish close together
    const rows = pick.map((sk) => { const l = cmpData.filter((d: any) => d.skill === sk).slice(-1)[0]; return { skill: sk, date: l.date, v: l.v, y: l.v }; }).sort((a, b) => b.v - a.v);
    for (let i = 1; i < rows.length; i++) rows[i].y = Math.min(rows[i].v, rows[i - 1].y - 7);
    return rows;
  })();
  const buildCmp = (t: Tokens, w: number): Plot.PlotOptions => ({
    height: 352, marginLeft: 44, marginRight: Math.min(150, w * 0.22), marginTop: 24,
    x: { type: "utc", label: null, tickSize: 0 }, y: { label: "search interest (100 = the skill's own peak)", grid: true, domain: [0, 100] },
    color: { domain: pick, range: pick.map((_, k) => t.cat[k % 5]) },
    marks: [
      Plot.line(cmpData, { x: "date", y: "v", stroke: "skill", strokeWidth: 2 }),
      Plot.text(cmpLabel, { x: "date", y: "y", text: "skill", dx: 8, textAnchor: "start", fill: "skill", fontWeight: 650, stroke: t.bg, strokeWidth: 4 }),
      Plot.tip(cmpData, Plot.pointerX({ x: "date", y: "v", z: "skill", title: (d: any) => `${d.skill}\n${MON.format(d.date)}: ${d.v}` })),
    ],
  });
  const togglePick = (sk: string) => setPick((p) => (p.includes(sk) ? (p.length > 1 ? p.filter((x) => x !== sk) : p) : p.length < 5 ? [...p, sk] : p));
  const buildAI = (t: Tokens, w: number): Plot.PlotOptions => ({
    height: 380, marginLeft: 50, marginRight: Math.min(190, w * 0.28), marginTop: 14,
    x: { type: "utc", label: null, tickSize: 0 },
    y: { type: "log", label: "search interest (each skill's pre-event average = 100)", grid: true, domain: [30, 300], tickFormat: (d: number) => String(d), ticks: [30, 50, 100, 200] },
    color: { domain: ["treated", "control"], range: [t.cat[1], t.cat[0]] },
    marks: [
      Plot.line(long, { x: "date", y: "v", z: "skill", stroke: "group", strokeOpacity: 0.28, strokeWidth: 1.2 }),
      Plot.line(groupLines, { x: "date", y: "v", z: "group", stroke: "group", strokeWidth: 3 }),
      Plot.ruleX([event], { stroke: t.ink, strokeDasharray: "4 3" }),
      Plot.text([{ date: event, v: 290 }], { x: "date", y: "v", text: () => "ChatGPT released", textAnchor: "start", dx: 6, fill: t.ink }),
      Plot.text(groupLines.filter((d: any) => d.date.getTime() === months[months.length - 1].getTime()), { x: "date", y: "v", text: (d: any) => (d.group === "treated" ? "code skills" : "tools and platforms"), textAnchor: "start", dx: 8, fill: (d: any) => (d.group === "treated" ? t.cat[1] : t.cat[0]), fontWeight: 650 }),
    ],
  });
  const buildPlacebo = (t: Tokens, w: number): Plot.PlotOptions => ({
    height: 250, marginLeft: 54, marginTop: 14,
    x: { type: "utc", label: null, tickSize: 0 }, y: { label: "treated minus control, log points", grid: true },
    marks: [
      Plot.ruleY([0], { stroke: t.ink3 }),
      Plot.line(place, { x: "date", y: "did", stroke: t.cat[0], strokeWidth: 2 }),
      Plot.dot(place, { x: "date", y: "did", r: 2.6, fill: t.cat[0] }),
      Plot.ruleX([event], { stroke: t.ink, strokeDasharray: "4 3" }),
      Plot.text([{ date: event, did: 0.27 }], { x: "date", y: "did", text: () => "ChatGPT released", textAnchor: "start", dx: 6, fill: t.ink }),
      Plot.dot([minP], { x: "date", y: "did", r: 6, stroke: t.cat[1], strokeWidth: 2, fill: "none" }),
      Plot.text([minP], { x: "date", y: "did", text: (d: any) => `largest gap: ${MON.format(d.date)}`, dy: -16, fill: t.cat[1], fontWeight: 650, textAnchor: "end", stroke: t.bg, strokeWidth: 4 }),
      Plot.tip(place, Plot.pointerX({ x: "date", y: "did", title: (d: any) => `${MON.format(d.date)}\n${d.did.toFixed(2)} log points` })),
    ],
  });
  const buildPerm = (t: Tokens): Plot.PlotOptions => ({
    height: 230, marginLeft: 48, marginBottom: 40,
    x: { label: "treated minus control, log points, for each way of picking 5 skills out of 12 as “treated”", labelAnchor: "left" }, y: { label: "ways", grid: true },
    marks: [
      Plot.rectY(hist, { x1: "x1", x2: "x2", y: "n", fill: t.ink3, fillOpacity: 0.5, insetLeft: 0.5, insetRight: 0.5 }),
      Plot.ruleX([ai.did], { stroke: t.cat[1], strokeWidth: 3 }),
      Plot.text([{ x: ai.did, y: Math.max(...ai.perm_hist.counts) * 0.9 }], { x: "x", y: "y", text: () => `the real grouping, ${ai.did.toFixed(2)}`, textAnchor: "start", dx: 8, fill: t.cat[1], fontWeight: 650 }),
    ],
  });
  const covData = [
    ...conf.map((c: any) => ({ label: `${c.method}, conformal`, v: c["conformal coverage"], kind: "conformal" })),
    ...conf.filter((c: any) => c["ARIMA's own interval: coverage"] != null).map((c: any) => ({ label: "arima, its own interval", v: c["ARIMA's own interval: coverage"], kind: "own" })),
  ];
  const buildCov = (t: Tokens): Plot.PlotOptions => ({
    height: 40 + covData.length * 30, marginLeft: 140, marginRight: 50,
    x: { domain: [0.5, 1], label: "share of outcomes inside the 80% interval", grid: true, tickFormat: (d: number) => `${Math.round(d * 100)}%` }, y: { label: null, tickSize: 0 },
    marks: [
      Plot.barX(covData, { y: "label", x1: 0.5, x2: "v", fill: (d: any) => (d.kind === "own" ? t.cat[1] : t.cat[0]), insetTop: 3, insetBottom: 3 }),
      Plot.text(covData, { y: "label", x: "v", text: (d: any) => `${(d.v * 100).toFixed(1)}%`, dx: 6, textAnchor: "start", fill: t.ink }),
      Plot.ruleX([0.8], { stroke: t.ink, strokeDasharray: "4 3" }),
    ],
  });
  const exd = ex.dates.map((m: string, i: number) => ({ date: utc(m), actual: ex.actual[i] }));
  const exf = ex.fc_dates.map((m: string, i: number) => ({ date: utc(m), pred: ex.pred[i], lo: ex.lo[i], hi: ex.hi[i] }));
  const buildEx = (t: Tokens): Plot.PlotOptions => ({
    height: 280, marginLeft: 44, x: { type: "utc", label: null, tickSize: 0 }, y: { label: "search interest, monthly mean", grid: true, zero: false },
    marks: [
      Plot.areaY(exf, { x: "date", y1: "lo", y2: "hi", fill: t.cat[0], fillOpacity: 0.22 }),
      Plot.line(exd, { x: "date", y: "actual", stroke: t.ink, strokeWidth: 2 }),
      Plot.line(exf, { x: "date", y: "pred", stroke: t.cat[0], strokeWidth: 2, strokeDasharray: "5 3" }),
      Plot.text([exf[exf.length - 1]], { x: "date", y: "hi", text: () => "80% interval", dy: -8, textAnchor: "end", fill: t.cat[0], fontWeight: 650 }),
    ],
  });
  const buildQuad = (t: Tokens, w: number): Plot.PlotOptions => {
    const pts = gs.map((g: any) => ({ ...g, y: Math.max(-80, Math.min(80, g.pct_change)) }));
    return {
      height: 470, marginLeft: 56, marginBottom: 44, marginRight: 24,
      x: { type: "log", label: "employer demand: % of postings asking for the skill (log scale)", ticks: [2, 3, 5, 10, 20], tickFormat: (d: number) => `${d}%`, grid: true },
      y: { label: "5-year change in search interest, %", grid: true, domain: [-85, 80] },
      color: { type: "linear", domain: [-30, 0, 30], range: [t.neg, t.mid, t.pos], clamp: true, legend: false },
      marks: [
        Plot.ruleX([(gap as any).median_demand], { stroke: t.ink3, strokeDasharray: "4 3" }), Plot.ruleY([10], { stroke: t.ink3, strokeDasharray: "4 3" }),
        Plot.dot(pts.filter((d: any) => !d.low_volume), { x: "demand_pct", y: "y", r: 8, fill: (d: any) => (d.pay_premium_pct == null ? t.bg : d.pay_premium_pct), stroke: t.ink, strokeWidth: 1.6 }),
        Plot.dot(pts.filter((d: any) => d.low_volume), { x: "demand_pct", y: "y", r: 8, fill: (d: any) => (d.pay_premium_pct == null ? t.bg : d.pay_premium_pct), stroke: t.ink3, strokeWidth: 1.6, strokeDasharray: "2 2" }),
        Plot.text(pts, { x: "demand_pct", y: "y", text: (d: any) => d.skill + (d.low_volume ? "*" : ""), dy: -14, fill: t.ink, fontSize: 11.5 }),
        Plot.tip(pts, Plot.pointer({ x: "demand_pct", y: "y", title: (d: any) => `${d.skill}\n${d.demand_pct.toFixed(1)}% of postings\n${sgnPct(d.pct_change)} search interest${d.low_volume ? " (trend too small)" : ""}\npay: ${d.pay_premium_pct == null ? "not estimated" : sgnPct(d.pay_premium_pct)}` })),
        Plot.text([{ x: 2.1, y: 76, t: "emerging" }, { x: 2.1, y: -82, t: "avoid" }], { x: "x", y: "y", text: "t", fill: t.ink3, fontSize: 13, fontWeight: 620, textAnchor: "start" }),
        Plot.text([{ x: 26, y: 76, t: "hot" }, { x: 26, y: -82, t: "opportunity" }], { x: "x", y: "y", text: "t", fill: t.ink3, fontSize: 13, fontWeight: 620, textAnchor: "end", dx: -4 }),
      ],
    };
  };

  return (
    <>
      <h1>People search less for Python and SQL, yet a quarter of postings still ask for them</h1>
      <p className="lede">Search interest comes from Google Trends for India over five years, weekly. It measures attention, not hiring. Set against what postings ask for, it shows which skills have become assumed knowledge.</p>
      <Kpis items={[
        { value: String(trends.classes.length), label: "skills followed in Google Trends for India, weekly for five years" },
        { value: String((trends.classes as any[]).filter((c) => c.class === "rising").length), label: "rising" },
        { value: String((trends.classes as any[]).filter((c) => c.class === "declining").length), label: "declining" },
        { value: `${Math.abs(ai.did_pct).toFixed(0)}%`, label: "further fall for code skills than for tools and platforms since the AI release" },
      ]} />
      <PageNav />

      <section className="section" id="compare">
        <h2>Compare skills</h2>
        <p className="small" style={{ maxWidth: "66ch" }}>Pick up to five skills. Each is scaled to its own peak, so the lines show shape over time, not which skill is searched more.</p>
        <div className="presets"><span>Try:</span>
          <button onClick={() => setPick(["Python", "SQL", "Java", "JavaScript"])}>Code skills</button>
          <button onClick={() => setPick(["AWS", "Azure", "Google Cloud", "Kubernetes", "Docker"])}>Cloud</button>
          <button onClick={() => setPick(["Excel", "Power BI", "Tableau", "SQL"])}>Analytics tools</button>
        </div>
        <div className="skillpick" role="group" aria-label="Skills to compare">
          {names.map((sk) => <button key={sk} className="chip" aria-pressed={pick.includes(sk)} onClick={() => togglePick(sk)}>{sk}</button>)}
        </div>
        <Kpis items={pick.map((sk) => { const c = (trends.classes as any[]).find((x) => x.skill === sk); return { value: sgnPct(c.pct_change), label: `${sk}: change over five years, ${c.class}${c.low_volume ? " (small trend, treat with care)" : ""}` }; })} />
        <PlotFigure label="Search interest over time for the chosen skills" build={buildCmp} minHeight={340} />
      </section>


      <Block title="How has search interest moved for each skill?" wide
        note={<><p>Each panel has its own scale, so compare shapes and the five-year change, not heights. Teal rose, orange fell, grey did not move.</p><p><strong>Six skills are too small to judge</strong> (Google Cloud, Kubernetes, Spark, Tableau, SAP, Deep Learning). Their raw values are single digits, so a change of 50% is one or two points of rounding.</p><p>Of the 14 skills that are large enough, 11 agree with a Mann-Kendall trend test. Machine Learning is the only clear riser.</p></>}>
        <Sparks dates={trends.dates} series={trends.series as any} rows={sorted} />
      </Block>

      <Block title="Did AI coding assistants lower the search interest?"
        note={<><p>Five code skills (Python, SQL, Java, JavaScript, React) are compared with seven tools, platforms and SEO, all measured against their own average before ChatGPT.</p>
          <p><strong>Code skills fell about {Math.abs(ai.did_pct).toFixed(0)}% more than the others.</strong> Only {ai.rank} of {ai.n_assign} ways of picking five skills out of twelve give a gap this large (p = {ai.p_rand.toFixed(3)}).</p>
          <p><strong>The date is wrong for ChatGPT.</strong> Nothing dropped in late 2022. The gap grows late and is largest around March 2025, so a later wave of AI tools or slow adoption fits better. The test cannot prove either, and the pre-event window is only 60 weeks.</p></>}>
        <Fig title="Search interest, indexed to each skill's average before the release" sub="Thin lines are single skills. Thick lines are the geometric mean of each group.">
          <PlotFigure label="Indexed search interest for code skills and control skills around November 2022" build={buildAI} />
        </Fig>
        <Fig title="The same comparison with the event date moved" sub="If ChatGPT were the cause, the gap would open at the dashed line.">
          <PlotFigure label="Treated minus control gap as the assumed event month changes" build={buildPlacebo} />
        </Fig>
        <Fig title="How unusual is the real grouping?" sub="All 792 ways to call five of the twelve skills the treated group.">
          <PlotFigure label="Distribution of differences for all possible groupings" build={buildPerm} />
        </Fig>
        <DataDetails summary="Break test per skill" rows={ai.its} cols={[{ key: "skill", label: "Skill" }, { key: "group", label: "Group" }, { key: "level_change_%", label: "Level change at release, %", right: true, fmt: (v) => sgnPct(v, 1) }, { key: "p_level", label: "p", right: true, fmt: (v) => f3(v) }, { key: "slope_change_%_per_year", label: "Slope change, % a year", right: true, fmt: (v) => sgnPct(v, 0) }, { key: "p_slope", label: "p", right: true, fmt: (v) => f3(v) }]} />
      </Block>

      <Block title="Can search interest be forecast?"
        note={<><p>Three months ahead, no method beats “next value equals the last value”. Exponential smoothing is 3% better by MASE and not significantly so; ARIMA and Holt-Winters are worse.</p>
          <p>An honest range is still useful. ARIMA's own 80% interval covers {pct(conf.find((c: any) => c.method === "arima")["ARIMA's own interval: coverage"], 1)} of outcomes. The conformal intervals, which only reuse past errors, cover more than 80% for three methods (86% to 90%): safe, but wider than needed.</p>
          <p><strong>Either way a three-month forecast is uncertain by about a fifth of its value.</strong></p></>}>
        <Fig title="Forecast error against “next value equals last value”" sub="MASE relative to the naive forecast. Below 1 beats it. 14 skills, 7 forecast origins, 3 months ahead.">
          <PlotFigure label="Forecast error relative to the naive forecast for four methods" minHeight={170} build={(t) => ({
            height: 40 + trends.backtest.length * 34, marginLeft: 110, marginRight: 60,
            x: { domain: [0.8, 1.3], grid: true, label: "mean MASE relative to naive", ticks: [0.8, 0.9, 1, 1.1, 1.2, 1.3] }, y: { label: null, tickSize: 0 },
            marks: [
              Plot.barX(trends.backtest as any[], { y: "model", x1: 1, x2: "mase_vs_naive", fill: (d: any) => (d.mase_vs_naive < 1 ? t.cat[2] : t.cat[1]), insetTop: 4, insetBottom: 4 }),
              Plot.text(trends.backtest as any[], { y: "model", x: "mase_vs_naive", text: (d: any) => f2(d.mase_vs_naive), dx: 6, textAnchor: "start", fill: t.ink }),
              Plot.ruleX([1], { stroke: t.ink }),
            ],
          })} />
        </Fig>
        <Fig title="How often the 80% interval contained the outcome" sub="Dashed line: the 80% target.">
          <PlotFigure label="Coverage of 80 percent intervals by method" build={buildCov} minHeight={200} />
        </Fig>
        <Fig title="An example: Python, three months ahead" sub="Exponential smoothing forecast with the conformal interval, scored on data it had not seen.">
          <PlotFigure label="Python search interest, forecast and conformal interval" build={buildEx} />
        </Fig>
      </Block>

      <Block title="Where do demand and search interest part ways?"
        note={<><p>Demand is the share of postings asking for the skill, within the ten roles in the data. Colour is the pay association at the same experience and role: blue higher, orange lower, empty where it could not be estimated. A star marks skills whose search trend is too small to use.</p>
          <p><strong>Machine Learning is the only skill high on all three:</strong> {gs.find((g: any) => g.skill === "Machine Learning").demand_pct.toFixed(1)}% of postings, search interest up 40%, pay about {sgnPct(gs.find((g: any) => g.skill === "Machine Learning").pay_premium_pct)}.</p>
          <p>SQL and Python are asked for by about a quarter of postings each while searches fell by half and a third. They read as baseline expectations.</p></>}>
        <PlotFigure label="Employer demand against change in search interest for 20 skills, coloured by pay association" build={buildQuad} minHeight={470} />
        <DataDetails summary="Table: all 20 skills" rows={gs} cols={[{ key: "skill", label: "Skill" }, { key: "demand_pct", label: "% of postings", right: true, fmt: (v) => v.toFixed(1) }, { key: "pct_change", label: "Interest, 5 years", right: true, fmt: (v) => sgnPct(v) }, { key: "quadrant", label: "Quadrant" }, { key: "pay_premium_pct", label: "Pay association", right: true, fmt: (v) => (v == null ? "not estimated" : sgnPct(v)) }, { key: "recommendation", label: "Reading" }]} />
      </Block>
    </>
  );
}
