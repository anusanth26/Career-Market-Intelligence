"use client";
import * as Plot from "@observablehq/plot";
import Link from "next/link";
import { useMemo } from "react";
import KpiBar from "@/components/KpiBar";
import Legend from "@/components/Legend";
import Panel from "@/components/Panel";
import PlotFigure from "@/components/PlotFigure";
import RankList from "@/components/RankList";
import { barsH } from "@/lib/charts";
import { ALL, BANDS, applyFilters, bandOf, useFilters } from "@/lib/filters";
import { inr, lk, pct0 } from "@/lib/format";
import { logBins, mean, median, quantile } from "@/lib/stats";
import { Tokens } from "@/lib/tokens";
import T from "@/data/textmining.json";

const TOTAL_TAGGED = 10780;
const group = (rows: ReturnType<typeof applyFilters>, key: (r: any) => string) => {
  const m = new Map<string, number[]>(); rows.forEach((r) => { const k = key(r); m.set(k, [...(m.get(k) ?? []), r.mid]); });
  return m;
};

export default function Overview() {
  const { f, toggle } = useFilters();
  const sel = useMemo(() => applyFilters(f), [f]);
  const tests = sel.filter((r) => r.split === "test");
  const mids = sel.map((r) => r.mid);
  const cover = tests.length ? tests.filter((r) => r.lo80! <= r.mid && r.mid <= r.hi80!).length / tests.length : NaN;
  const mae = tests.length ? mean(tests.map((r) => Math.abs(r.est! - r.mid))) : NaN;
  const what = [f.role, f.city, f.band, f.mode].filter((v) => v !== ALL).join(", ") || "all postings";

  const byRole = useMemo(() => [...group(applyFilters(f, "role"), (r) => r.role)].map(([key, vals]) => ({ key, label: key, vals })), [f]);
  const byBand = useMemo(() => { const g = group(applyFilters(f, "band"), (r) => bandOf(r.exp)); return BANDS.map((b) => ({ key: b, label: b, vals: g.get(b) ?? [] })); }, [f]);
  const byCity = useMemo(() => [...group(applyFilters(f, "city"), (r) => r.city)].map(([key, vals]) => ({ key, label: key, vals })).filter((g) => g.vals.length >= 8), [f]);

  const bins = useMemo(() => logBins(mids), [mids]);
  const med = median(mids);
  const hist = (t: Tokens): Plot.PlotOptions => ({
    height: 240, marginLeft: 44, marginBottom: 38, marginTop: 26,
    x: { type: "log", domain: [1, 70], label: "stated salary midpoint, lakh (log scale)", labelAnchor: "left", ticks: [1, 2, 5, 10, 20, 40, 70], tickFormat: (d: number) => String(d) }, y: { label: "postings", grid: true },
    marks: [Plot.rectY(bins, { x1: "lo", x2: "hi", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }),
      Number.isFinite(med) ? Plot.ruleX([med], { stroke: t.ink, strokeDasharray: "4 3" }) : null,
      Number.isFinite(med) ? Plot.text([{ x: med, y: Math.max(1, ...bins.map((b) => b.n)) }], { x: "x", y: "y", text: () => `median ₹${med.toFixed(1)} L`, dx: 6, textAnchor: "start", fill: t.ink, fontWeight: 650, stroke: t.bg, strokeWidth: 4 }) : null,
      Plot.tip(bins, Plot.pointerX({ x: (d: any) => Math.sqrt(d.lo * d.hi), y: "n", title: (d: any) => `₹${d.lo.toFixed(1)} to ${d.hi.toFixed(1)} L\n${d.n} postings` }))].filter(Boolean) as Plot.Markish[],
  });
  const scatter = (t: Tokens): Plot.PlotOptions => ({
    height: 260, marginLeft: 46, marginBottom: 40, marginTop: 10,
    x: { type: "log", domain: [1.5, 70], label: "stated salary, lakh", labelAnchor: "left", ticks: [2, 5, 10, 20, 40], tickFormat: (d: number) => String(d), grid: true },
    y: { type: "log", domain: [1.5, 70], label: "model estimate, lakh", ticks: [2, 5, 10, 20, 40], tickFormat: (d: number) => String(d), grid: true },
    marks: [Plot.line([{ x: 1.5, y: 1.5 }, { x: 70, y: 70 }], { x: "x", y: "y", stroke: t.ink3, strokeDasharray: "4 3" }),
      Plot.dot(tests, { x: "mid", y: "est", r: 3.4, fill: (r: any) => (r.lo80 <= r.mid && r.mid <= r.hi80 ? t.cat[0] : t.cat[1]), stroke: t.bg, strokeWidth: 0.8 }),
      Plot.tip(tests, Plot.pointer({ x: "mid", y: "est", title: (r: any) => `${r.title}\n${r.company}\nstated ₹${r.stated_min}–${r.stated_max} L\nestimate ₹${r.est} L` }))],
  });

  const skills = useMemo(() => {
    const rs = (T as any).role_skills?.[f.role] as { skill: string; tag_pct: number }[] | undefined;
    return rs ? rs.slice(0, 12).map((d) => ({ skill: d.skill, pct: d.tag_pct })) : (T.tags_top as any[]).slice(0, 12).map((d) => ({ skill: d.tag, pct: (d.n / TOTAL_TAGGED) * 100 }));
  }, [f.role]);

  const skillMax = Math.max(40, ...skills.map((s) => s.pct + 8));
  return (
    <>
      <h1 className="sr-only">Overview: pay and skills for the postings you select</h1>
      <KpiBar items={[
        { label: "Postings in view", value: inr(sel.length), sub: `${what}` },
        { label: "Median stated pay", value: sel.length ? lk(med) : "n/a", sub: "per year" },
        { label: "Middle 80% of postings", value: sel.length >= 5 ? `${lk(quantile(mids, 0.1), 0)} to ${lk(quantile(mids, 0.9), 0)}` : "n/a" },
        { label: "Model's typical error", value: tests.length ? lk(mae) : "n/a", sub: tests.length ? `on ${tests.length} postings from unseen employers` : "no test postings in this view" },
        { label: "Range held the stated pay", value: tests.length ? pct0(cover) : "n/a", sub: "target 80%" },
      ]} />
      <div className="grid">
        <Panel span={7} title="Who is paid what" sub="Click a row to filter everything to it. Bar: middle half. Line: 10th to 90th percentile. Tick: median."
          info={<><p>Each tab groups the salaried postings by one field and ignores that field's own filter, so you can compare the groups; every other filter still applies.</p><p>Pay is the midpoint of the range the employer states, per year, in lakh (1 lakh = ₹100,000).</p></>}
          tabs={[
            { id: "role", label: "By role", node: <RankList groups={byRole} selected={f.role} onPick={(k) => toggle("role", k)} /> },
            { id: "band", label: "By experience", node: <RankList groups={byBand} keepOrder selected={f.band} onPick={(k) => toggle("band", k)} /> },
            { id: "city", label: "By city", node: <RankList groups={byCity} selected={f.city} onPick={(k) => toggle("city", k)} empty="Fewer than 8 postings per city in this view." /> },
          ]} />
        <Panel span={5} title="How pay is spread" sub={`Postings in view: ${sel.length}`}
          tabs={[
            { id: "hist", label: "Distribution", node: sel.length ? <PlotFigure label="Histogram of stated salaries in the current view" build={hist} minHeight={230} /> : <p className="small">No postings match these filters.</p> },
            { id: "sc", label: "Model against stated", node: tests.length ? <><Legend items={[{ color: "var(--c1)", label: "stated pay inside the model's 80% range", shape: "dot" }, { color: "var(--c2)", label: "outside it", shape: "dot" }]} /><PlotFigure label="Model estimate against stated salary for the test postings in view" build={scatter} minHeight={260} /></> : <p className="small">No test postings in this view. The model's estimate is only shown for postings from employers it did not train on.</p> },
          ]} />
        <Panel span={5} title={f.role === ALL ? "Skills employers tag most" : `Skills ${f.role} postings tag most`} sub="Share of postings that tag the skill" tag="not filtered by city or experience">
          <PlotFigure label="Most tagged skills for the selected role" minHeight={330} build={barsH({ data: skills, label: "skill", value: "pct", fmt: (v) => `${Math.round(v)}%`, domain: [0, skillMax], marginLeft: 150, rowH: 24, ticks: [0, 20, 40, 60].filter((t) => t <= skillMax), tickFmt: (v) => `${v}%` })} />
        </Panel>
        <Panel span={7} title="Where to go next" sub={`With the view set to ${what}`}>
          <nav className="linkrow" aria-label="Next steps">
            <Link href="/pay"><b>Estimate a salary or check an offer</b><span>Pick a posting for an estimate and an 80% range, or enter a profile and an offer. The model's range held the stated pay for {pct0(0.833)} of postings from employers it had not seen.</span><em>Pay</em></Link>
            <Link href="/skills"><b>See which skills pay, and which are rising</b><span>Python and SQL are in about a quarter of postings but carry small pay associations; Machine Learning is the one skill high on demand, interest and pay.</span><em>Skills</em></Link>
            <Link href="/careers"><b>Find the skills that move you to another role</b><span>A handful of added skills separates neighbouring roles; distant moves need a different base.</span><em>Careers</em></Link>
            <Link href="/data"><b>Check the evidence</b><span>Only one posting in eight states its pay, mostly from the same few employers. See the dataset, who discloses and what the numbers cannot tell you.</span><em>Data and method</em></Link>
          </nav>
        </Panel>
      </div>
    </>
  );
}
