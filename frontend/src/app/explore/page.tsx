"use client";
import PageNav from "@/components/PageNav";
import * as Plot from "@observablehq/plot";
import { ColumnDef, flexRender, getCoreRowModel, getSortedRowModel, SortingState, useReactTable } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import Block, { Fig } from "@/components/Block";
import PlotFigure from "@/components/PlotFigure";
import { Tokens } from "@/lib/tokens";
import { barsH, heat } from "@/lib/charts";
import { f3, lakh, pct0, sgnPct } from "@/lib/format";
import S from "@/data/salary.json";
import T from "@/data/textmining.json";
import N from "@/data/network.json";
import R from "@/data/roles.json";

const ROLES = ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer", "Business Analyst", "Product Manager", "Project Manager", "Digital Marketing", "Graphic Designer"];
const BNAME = ["Marketing", "Cloud and DevOps", "Data", "Delivery and business analysis", "Design", "Software development"];
const asPct = (b: number) => (Math.exp(b) - 1) * 100;

function SkillTable() {
  const [q, setQ] = useState("");
  const [minN, setMinN] = useState(25);
  const [onlySig, setOnlySig] = useState(false);
  const [sorting, setSorting] = useState<SortingState>([{ id: "dml_pct", desc: true }]);
  const data = useMemo(() => (T.premiums as any[]).map((d) => ({ ...d, dml_pct: asPct(d.dml_beta), ols_pct: asPct(d.ols_beta), ridge_pct: asPct(d.ridge_beta), lo: asPct(d.dml_beta - 1.96 * d.dml_se), hi: asPct(d.dml_beta + 1.96 * d.dml_se) }))
    .filter((d) => d.n_postings >= minN && d.skill.includes(q.trim().toLowerCase()) && (!onlySig || d.dml_fdr_sig || d.ols_fdr_sig)), [q, minN, onlySig]);
  const cols = useMemo<ColumnDef<any>[]>(() => [
    { accessorKey: "skill", header: "Skill" },
    { accessorKey: "n_postings", header: "Salaried postings", meta: { right: true } },
    { accessorKey: "dml_pct", header: "Pay association", cell: (c) => sgnPct(c.getValue() as number), meta: { right: true } },
    { id: "interval", header: "95% interval", accessorFn: (d) => d.hi - d.lo, cell: (c) => `${sgnPct(c.row.original.lo)} to ${sgnPct(c.row.original.hi)}`, meta: { right: true } },
    { accessorKey: "dml_fdr_sig", header: "Survives the correction", cell: (c) => (c.row.original.dml_fdr_sig ? "yes" : c.row.original.ols_fdr_sig ? "regression only" : "no") },
    { accessorKey: "ols_pct", header: "Simple regression", cell: (c) => sgnPct(c.getValue() as number), meta: { right: true } },
    { accessorKey: "ridge_pct", header: "Ridge", cell: (c) => sgnPct(c.getValue() as number), meta: { right: true } },
  ], []);
  const table = useReactTable({ data, columns: cols, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() });
  return (
    <div>
      <div className="controls">
        <label>Search <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="a skill" aria-label="Search skills" /></label>
        <label>At least <input type="number" min={10} max={300} value={minN} onChange={(e) => setMinN(Math.max(10, +e.target.value || 10))} style={{ width: 72 }} aria-label="Minimum salaried postings" /> salaried postings</label>
        <label><input type="checkbox" checked={onlySig} onChange={(e) => setOnlySig(e.target.checked)} /> only skills that survive the correction</label>
        <span>{data.length} skills</span>
      </div>
      <div className="tablewrap" style={{ maxHeight: 560, overflowY: "auto" }}>
        <table>
          <thead>{table.getHeaderGroups().map((hg) => <tr key={hg.id}>{hg.headers.map((h) => (
            <th key={h.id} className={(h.column.columnDef.meta as any)?.right ? "r" : ""} style={{ position: "sticky", top: 0, background: "var(--bg)", cursor: "pointer" }} onClick={h.column.getToggleSortingHandler()} aria-sort={h.column.getIsSorted() === "asc" ? "ascending" : h.column.getIsSorted() === "desc" ? "descending" : "none"}>
              {flexRender(h.column.columnDef.header, h.getContext())}{h.column.getIsSorted() === "asc" ? " ↑" : h.column.getIsSorted() === "desc" ? " ↓" : ""}
            </th>))}</tr>)}</thead>
          <tbody>{table.getRowModel().rows.map((r) => <tr key={r.id} className={r.original.dml_fdr_sig ? "hl" : ""}>{r.getVisibleCells().map((c) => <td key={c.id} className={(c.column.columnDef.meta as any)?.right ? "r" : ""}>{flexRender(c.column.columnDef.cell ?? ((x) => String(x.getValue())), c.getContext())}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <p className="small" style={{ marginTop: 8 }}>Pay association: percent pay difference between postings that ask for the skill and comparable postings that do not, at the same experience, role, seniority, city, work mode and industry. Shaded rows survive the correction for testing many skills.</p>
    </div>
  );
}

export default function ExplorePage() {
  const [role, setRole] = useState<string>("Data Analyst");
  const pts = useMemo(() => (S.scatter as any[]).filter((d) => d.role === role), [role]);
  const all = S.scatter as any[];
  const b = (S.by_role as any[]).find((r) => r.role === role);
  const e = (S.err_role as any[]).find((r) => r.role === role);
  const c = (S.cond_role as any[]).find((r) => r.role === role);
  const pr = (R.per_role as any[]).find((r) => r.role === role);
  const bins = useMemo(() => {
    const edges = Array.from({ length: 21 }, (_, i) => Math.pow(70, i / 20));
    return edges.slice(0, -1).map((lo, i) => ({ lo, hi: edges[i + 1], n: pts.filter((d) => d.lakh >= lo && (d.lakh < edges[i + 1] || (i === 19 && d.lakh <= edges[i + 1]))).length }));
  }, [pts]);
  const rs: any[] = useMemo(() => ((T as any).role_skills?.[role] ?? []) as any[], [role]);
  const bund = useMemo(() => (N.role_in_bundle as any[]).filter((d) => d.role === role).map((d) => ({ b: BNAME[+d.bundle.replace("bundle ", "") - 1], v: d.score })), [role]);

  const buildHist = (t: Tokens): Plot.PlotOptions => ({
    height: 240, marginLeft: 46, marginBottom: 40,
    x: { type: "log", domain: [1, 70], label: "salary midpoint, lakh per year (log scale)", labelAnchor: "left", ticks: [1, 2, 3, 5, 10, 20, 40, 70], tickFormat: (d: number) => String(d) }, y: { label: "postings in this role", grid: true },
    marks: [Plot.rectY(bins, { x1: "lo", x2: "hi", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }), Plot.ruleX([b.median / 1e5], { stroke: t.ink, strokeDasharray: "4 3" }),
      Plot.tip(bins, Plot.pointerX({ x: (d: any) => Math.sqrt(d.lo * d.hi), y: "n", title: (d: any) => `₹${d.lo.toFixed(1)} to ${d.hi.toFixed(1)} L\n${d.n} postings` }))],
  });
  const buildSkills = (t: Tokens): Plot.PlotOptions => ({
    height: 44 + rs.length * 27, marginLeft: 170, marginRight: 60, marginBottom: 34, marginTop: 6,
    x: { domain: [0, 100], grid: true, label: "share of the role's postings that tag the skill", labelAnchor: "left", tickFormat: (d: number) => `${d}%` }, y: { domain: rs.map((d) => d.skill), label: null, tickSize: 0 },
    marks: [
      Plot.barX(rs, { y: "skill", x1: 0, x2: "tag_pct", fill: t.cat[0], insetTop: 4, insetBottom: 4 }),
      Plot.text(rs, { y: "skill", x: "tag_pct", text: (d: any) => `${Math.round(d.tag_pct)}%`, dx: 7, textAnchor: "start", fill: t.ink }),
      Plot.tip(rs, Plot.pointerY({ y: "skill", x: "tag_pct", title: (d: any) => `${d.skill}\ntagged by the employer in ${d.tag_pct.toFixed(0)}% of postings` })),
    ],
  });
  const buildScatter = (t: Tokens): Plot.PlotOptions => ({
    height: 300, marginLeft: 46, marginBottom: 42,
    x: { label: "experience asked for, years", domain: [0, 30], labelAnchor: "left" }, y: { type: "log", domain: [1.5, 70], label: "salary, lakh", grid: true, ticks: [2, 5, 10, 20, 40], tickFormat: (d: number) => String(d) },
    marks: [Plot.dot(all, { x: "exp", y: "lakh", r: 2, fill: t.ink3, fillOpacity: 0.12 }), Plot.dot(pts, { x: "exp", y: "lakh", r: 3.4, fill: t.cat[1], fillOpacity: 0.7, stroke: t.bg, strokeWidth: 0.6 }),
      Plot.linearRegressionY(pts, { x: "exp", y: "lakh", stroke: t.cat[1], strokeWidth: 2 })],
  });

  return (
    <>
      <h1>Filter the data yourself</h1>
      <p className="lede">Pick a role to see its pay, its skills, how well the model does on it, and how reliably a description identifies it. Then look up any skill's pay association.</p>
      <PageNav />

      <section className="section">
        <h2>One role at a time</h2>
        <div className="controls">
          <label>Role <select value={role} onChange={(ev) => setRole(ev.target.value)} aria-label="Role">{ROLES.map((r) => <option key={r}>{r}</option>)}</select></label>
        </div>
        <div className="statrow">
          <div><b>{lakh(b.median)}</b><span>median salary, {b.n} postings state one</span></div>
          <div><b>{lakh(b.p10, 0)} to {lakh(b.p90, 0)}</b><span>middle 80% of those postings</span></div>
          <div><b>{lakh(e.MAE_INR)}</b><span>model's typical error on test postings, against {lakh(e.role_median_MAE)} for the role median</span></div>
          <div><b>{pct0(c.coverage)}</b><span>of test salaries inside the model's 80% range ({c.n} postings)</span></div>
          <div><b>{f3(pr["F1 full text"])}</b><span>F1 for recognising the role from its description</span></div>
        </div>
        <div className="cols" style={{ marginTop: 26 }}>
          <div className="chart-col">
            <Fig title={`How ${role} salaries are spread`}><PlotFigure label="Histogram of salaries for the chosen role" build={buildHist} minHeight={240} /></Fig>
            <Fig title="Pay against experience" sub="Orange: this role, with its trend line. Grey: all other postings."><PlotFigure label="Salary against experience for the chosen role" build={buildScatter} minHeight={300} /></Fig>
            <Fig title="Skills this role's postings tag most" sub="Share of the role's postings whose employer tagged the skill. The 15 most tagged of 200 skills."><PlotFigure label="Most tagged skills for the chosen role" minHeight={420} build={buildSkills} /></Fig>
          </div>
          <aside className="note">
            <p>Roles differ in how well the model does. Compare the error and the coverage with the role median and the 80% target.</p>
            <p>Small roles (Data Scientist has 11 test postings) give noisy figures: read the direction, not the digits.</p>
            <p><strong>Bundle profile.</strong> {bund.sort((a, z) => z.v - a.v).slice(0, 2).map((x) => `${x.b} ${x.v.toFixed(2)}`).join(", ")}: the two bundles of skills this role's postings ask for most, as a share of each bundle.</p>
          </aside>
        </div>
      </section>

      <section className="section">
        <h2>Look up a skill</h2>
        <SkillTable />
      </section>
    </>
  );
}
