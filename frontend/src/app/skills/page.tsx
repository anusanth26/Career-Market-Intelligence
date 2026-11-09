"use client";
import * as Plot from "@observablehq/plot";
import { useState } from "react";
import KpiBar from "@/components/KpiBar";
import Network from "@/components/Network";
import Panel from "@/components/Panel";
import PlotFigure from "@/components/PlotFigure";
import { PlanSkills } from "@/components/Scenarios";
import SkillDetail from "@/components/SkillDetail";
import Sparks from "@/components/Sparks";
import { barsH, heat } from "@/lib/charts";
import { pct0, sgnPct } from "@/lib/format";
import { Tokens } from "@/lib/tokens";
import gap from "@/data/gap.json";
import N from "@/data/network.json";
import T from "@/data/textmining.json";
import trends from "@/data/trends.json";

const ROLES = ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer", "Business Analyst", "Product Manager", "Project Manager", "Digital Marketing", "Graphic Designer"];
const gs = (gap as any).skills as any[];
const prem = (T.premiums as any[]).map((d) => ({ ...d, pct: (Math.exp(d.dml_beta) - 1) * 100, clear: !!(d.dml_fdr_sig || d.ols_fdr_sig) }));
const clear = prem.filter((d) => d.clear).sort((a, b) => b.pct - a.pct);
const sorted = [...(trends.classes as any[])].sort((a, b) => b.pct_change - a.pct_change);
// labels that would sit on top of a neighbour go to the side
const RIGHT = ["Linux", "Java", "Azure"], LEFT = ["Tableau", "JavaScript"];
const lab = (d: any) => d.skill + (d.low_volume ? "*" : "");
const tagOrder = (T.tags_top as any[]).map((d) => d.tag).slice(0, 20);

export default function Skills() {
  const [skill, setSkill] = useState("machine learning");
  const buildQuad = (t: Tokens): Plot.PlotOptions => {
    const pts = gs.map((g) => ({ ...g, y: Math.max(-80, Math.min(80, g.pct_change)) }));
    const on = pts.filter((d) => d.skill.toLowerCase() === skill.toLowerCase());
    return {
      height: 430, marginLeft: 56, marginBottom: 44, marginRight: 24,
      x: { type: "log", label: "employer demand: % of postings asking for the skill (log scale)", labelAnchor: "left", ticks: [2, 3, 5, 10, 20], tickFormat: (d: number) => `${d}%`, grid: true },
      y: { label: "5-year change in search interest, %", grid: true, domain: [-85, 80] },
      color: { type: "linear", domain: [-30, 0, 30], range: [t.neg, t.mid, t.pos], clamp: true, legend: false },
      marks: [
        Plot.ruleX([(gap as any).median_demand], { stroke: t.ink3, strokeDasharray: "4 3" }), Plot.ruleY([10], { stroke: t.ink3, strokeDasharray: "4 3" }),
        Plot.dot(pts.filter((d) => !d.low_volume), { x: "demand_pct", y: "y", r: 8, fill: (d: any) => (d.pay_premium_pct == null ? t.bg : d.pay_premium_pct), stroke: t.ink, strokeWidth: 1.6 }),
        Plot.dot(pts.filter((d) => d.low_volume), { x: "demand_pct", y: "y", r: 8, fill: (d: any) => (d.pay_premium_pct == null ? t.bg : d.pay_premium_pct), stroke: t.ink3, strokeWidth: 1.6, strokeDasharray: "2 2" }),
        Plot.dot(on, { x: "demand_pct", y: "y", r: 13, stroke: t.cat[1], strokeWidth: 2.5, fill: "none" }),
        Plot.text(pts.filter((d) => !RIGHT.includes(d.skill) && !LEFT.includes(d.skill)), { x: "demand_pct", y: "y", text: lab, dy: -14, fill: t.ink, fontSize: 11.5, stroke: t.bg, strokeWidth: 3 }),
        Plot.text(pts.filter((d) => RIGHT.includes(d.skill)), { x: "demand_pct", y: "y", text: lab, dx: 13, textAnchor: "start", fill: t.ink, fontSize: 11.5, stroke: t.bg, strokeWidth: 3 }),
        Plot.text(pts.filter((d) => LEFT.includes(d.skill)), { x: "demand_pct", y: "y", text: lab, dx: -13, textAnchor: "end", fill: t.ink, fontSize: 11.5, stroke: t.bg, strokeWidth: 3 }),
        Plot.tip(pts, Plot.pointer({ x: "demand_pct", y: "y", title: (d: any) => `${d.skill}\n${d.demand_pct.toFixed(1)}% of postings\n${sgnPct(d.pct_change)} search interest${d.low_volume ? " (trend too small)" : ""}\npay: ${d.pay_premium_pct == null ? "not estimated" : sgnPct(d.pay_premium_pct)}` })),
        Plot.text([{ x: 2.1, y: 76, t: "emerging" }, { x: 2.1, y: -82, t: "avoid" }], { x: "x", y: "y", text: "t", fill: t.ink3, fontSize: 13, fontWeight: 620, textAnchor: "start" }),
        Plot.text([{ x: 26, y: 76, t: "hot" }, { x: 26, y: -82, t: "opportunity" }], { x: "x", y: "y", text: "t", fill: t.ink3, fontSize: 13, fontWeight: 620, textAnchor: "end", dx: -4 }),
      ],
    };
  };
  const prems = [...clear.slice(0, 8), ...clear.slice(-8)].filter((d, i, a) => a.findIndex((e) => e.skill === d.skill) === i);
  return (
    <>
      <h1 className="sr-only">Skills: demand, search interest and pay</h1>
      <KpiBar items={[
        { label: "Skills with a pay estimate", value: String(prem.length), sub: "at least 25 salaried postings each" },
        { label: "Clear pay associations", value: String(clear.length), sub: "survive the false-discovery correction" },
        { label: "Tracked for search interest", value: String(gs.length), sub: `${(trends.classes as any[]).filter((c) => c.class === "rising").length} rising, ${(trends.classes as any[]).filter((c) => c.class === "declining").length} declining` },
        { label: "Only skill high on demand and rising interest", value: "Machine Learning", sub: "pay +21% in one analysis (clear), +14% in the other (not clear)" },
      ]} />
      <div className="grid">
        <Panel span={8} title="Demand, interest and pay" sub="Each skill's place on three measures" tag="not filtered by role, city or experience"
          info={<><p><strong>Quadrant map:</strong> horizontal is how many postings ask for the skill, vertical is the five-year change in Google search interest in India, fill is the pay association. Search interest is attention, not hiring; skills people search less for can still be what most postings ask for.</p><p>Pay associations compare postings at the same role, experience, seniority, city, work mode and industry. They are not causal.</p></>}
          tabs={[
            { id: "quad", label: "Quadrant map", node: <><p className="small" style={{ margin: "0 0 6px" }}>Fill: pay association (blue higher, orange lower, grey near zero, empty not estimated). Dashed outline and *: search trend too small to judge. Ring: the skill picked on the right.</p><PlotFigure label="Employer demand against change in search interest, coloured by pay association" build={buildQuad} minHeight={430} /></> },
            { id: "prem", label: "Pay associations", node: <PlotFigure label="Skills with a pay association that survives the correction" minHeight={460} build={barsH({ data: prems, label: "skill", value: "pct", fmt: (v) => sgnPct(v), color: (d, t) => (d.pct >= 0 ? t.cat[0] : t.cat[1]), domain: [-30, 40], marginLeft: 150, rowH: 24, xLabel: "pay association, % at the same role and experience (double machine learning)" })} /> },
            { id: "trend", label: "Search interest", node: <Sparks dates={trends.dates} series={trends.series as any} rows={sorted} /> },
            { id: "net", label: "Skill network", node: <Network nodes={N.nodes as any} edges={N.edges as any} bundles={N.bundles as any} /> },
            { id: "heat", label: "Role by skill", node: <PlotFigure label="Share of each role's postings that tag each of the 20 most common skills" minHeight={560} build={heat({ data: T.tag_role_share as any[], x: "role", y: "tag", v: "pct", fmt: (v) => `${Math.round(v)}`, xDomain: ROLES, yDomain: tagOrder, domain: [0, 80], marginLeft: 130, marginBottom: 150, cellH: 22, textMin: 0 })} /> },
          ]} />
        <Panel span={4} title="One skill in detail" sub="Type or pick any skill">
          <SkillDetail skill={skill} onPick={setSkill} />
        </Panel>
        <Panel span={12} title="Plan skills for a target role" sub="Tick what you have, see what is missing and what it has gone with in pay"
          info={<><p>The role follows the Role filter above. Skills are the role's most tagged by employers. Pay association is where it could be estimated, marked clear only where it survives the correction.</p></>}>
          <PlanSkills />
        </Panel>
      </div>
    </>
  );
}
