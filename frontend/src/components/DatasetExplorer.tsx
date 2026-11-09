"use client";
import * as Plot from "@observablehq/plot";
import { ColumnDef, flexRender, getCoreRowModel, getPaginationRowModel, getSortedRowModel, SortingState, useReactTable } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import KpiBar from "@/components/KpiBar";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { Fig } from "@/components/Block";
import { Tokens } from "@/lib/tokens";
import { ALL, OPTIONS, ROWS, applyFilters, useFilters } from "@/lib/filters";
import { logBins, mean, median } from "@/lib/stats";
import { inr, pct0 } from "@/lib/format";
import S from "@/data/salary.json";

type Row = any;
const trainMedian: Record<string, number> = {};
for (const role of OPTIONS.role) trainMedian[role] = median(ROWS.filter((r) => r.role === role && r.split === "train").map((r) => r.mid));

const COLS: { name: string; text: string }[] = [
  { name: "title, company", text: "The posting title and employer, as scraped." },
  { name: "role", text: "One of ten roles, assigned from the title only." },
  { name: "city, work mode", text: "First listed city (grouped into hubs) and office, hybrid or remote." },
  { name: "experience", text: "Years asked for: the minimum and maximum of the stated range." },
  { name: "skills", text: "The first skills the employer tagged, and how many there are." },
  { name: "stated salary", text: "The employer's yearly range in lakh. This is the label the model learns." },
  { name: "split", text: "Train or test. No employer appears in both." },
  { name: "estimate and range", text: "For test postings only: the model's estimate and 80% range, made without seeing the stated salary." },
];

/** Every salaried posting, filtered by the strip at the top plus a few local controls, with the model's results on exactly that slice. */
export default function DatasetExplorer() {
  const { f } = useFilters();
  const [q, setQ] = useState(""), [split, setSplit] = useState(ALL);
  const [salMin, setSalMin] = useState(0), [salMax, setSalMax] = useState(80);
  const [sorting, setSorting] = useState<SortingState>([{ id: "mid", desc: true }]);
  const base = useMemo(() => applyFilters(f), [f]);
  const sel = useMemo(() => base.filter((r) => (split === ALL || r.split === split) && r.mid >= salMin && r.mid <= salMax && (!q.trim() || `${r.title} ${r.company}`.toLowerCase().includes(q.trim().toLowerCase()))), [base, q, split, salMin, salMax]);
  const tests = useMemo(() => sel.filter((r) => r.split === "test"), [sel]);
  const res = useMemo(() => {
    const err = tests.map((r) => Math.abs(r.est! - r.mid)), baseErr = tests.map((r) => Math.abs(trainMedian[r.role] - r.mid));
    return { n: sel.length, median: median(sel.map((r) => r.mid)), tests: tests.length, mae: mean(err), baseMae: mean(baseErr),
      within30: tests.length ? tests.filter((r) => Math.abs(r.est! / r.mid - 1) <= 0.3).length / tests.length : NaN,
      cover: tests.length ? tests.filter((r) => r.lo80! <= r.mid && r.mid <= r.hi80!).length / tests.length : NaN };
  }, [sel, tests]);
  const fmtL = (v: number) => (Number.isFinite(v) ? `₹${v.toFixed(1)} L` : "n/a");

  const cols = useMemo<ColumnDef<Row>[]>(() => [
    { id: "title", header: "Posting", accessorFn: (r) => `${r.title}`, cell: (c) => <><b style={{ fontWeight: 600 }}>{c.row.original.title}</b><br /><span className="small">{c.row.original.company}</span></> },
    { accessorKey: "role", header: "Role" },
    { id: "where", header: "City, mode", accessorFn: (r) => `${r.city}`, cell: (c) => <>{c.row.original.city}<br /><span className="small">{c.row.original.work_mode}</span></> },
    { accessorKey: "exp", header: "Years asked", cell: (c) => `${c.row.original.exp_min}–${c.row.original.exp_max}`, meta: { right: true } },
    { id: "skills", header: "Skills tagged", enableSorting: false, accessorFn: (r) => r.skills.join(", "), cell: (c) => <span className="small">{c.row.original.skills.slice(0, 4).join(", ")}{c.row.original.n_skills > 4 ? ` (+${c.row.original.n_skills - 4})` : ""}</span> },
    { accessorKey: "mid", header: "Stated salary", cell: (c) => `₹${c.row.original.stated_min}–${c.row.original.stated_max} L`, meta: { right: true } },
    { accessorKey: "split", header: "Split" },
    { id: "est", header: "Model estimate", accessorFn: (r) => r.est ?? -1, cell: (c) => (c.row.original.est == null ? <span className="small">training row</span> : <>₹{c.row.original.est} L<br /><span className="small">{c.row.original.lo80} to {c.row.original.hi80}</span></>), meta: { right: true } },
    { id: "ok", header: "Stated inside range?", accessorFn: (r) => (r.est == null ? "" : r.lo80 <= r.mid && r.mid <= r.hi80 ? "yes" : "no"), cell: (c) => { const r = c.row.original; return r.est == null ? "" : r.lo80 <= r.mid && r.mid <= r.hi80 ? "yes" : "no"; } },
  ], []);
  const table = useReactTable({ data: sel, columns: cols, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(), getPaginationRowModel: getPaginationRowModel(), initialState: { pagination: { pageSize: 12 } } });

  const buildScatter = (t: Tokens): Plot.PlotOptions => ({
    height: 360, marginLeft: 50, marginBottom: 44,
    x: { type: "log", domain: [1.5, 70], label: "stated salary midpoint, lakh (log scale)", labelAnchor: "left", ticks: [2, 5, 10, 20, 40], tickFormat: (d: number) => String(d), grid: true },
    y: { type: "log", domain: [1.5, 70], label: "model estimate, lakh", ticks: [2, 5, 10, 20, 40], tickFormat: (d: number) => String(d), grid: true },
    marks: [
      Plot.line([{ x: 1.5, y: 1.5 }, { x: 70, y: 70 }], { x: "x", y: "y", stroke: t.ink3, strokeDasharray: "4 3" }),
      Plot.ruleX(tests, { x: "mid", y1: "lo80", y2: "hi80", stroke: t.ink3, strokeOpacity: 0.35 }),
      Plot.dot(tests, { x: "mid", y: "est", r: 3.6, fill: (r: any) => (r.lo80 <= r.mid && r.mid <= r.hi80 ? t.cat[0] : t.cat[1]), stroke: t.bg, strokeWidth: 0.8 }),
      Plot.tip(tests, Plot.pointer({ x: "mid", y: "est", title: (r: any) => `${r.title}\n${r.company}\nstated ₹${r.stated_min}–${r.stated_max} L\nestimate ₹${r.est} L, range ${r.lo80} to ${r.hi80}` })),
    ],
  });
  const bins = useMemo(() => logBins(sel.map((r) => r.mid)), [sel]);
  const buildHist = (t: Tokens): Plot.PlotOptions => ({
    height: 220, marginLeft: 46, marginBottom: 40,
    x: { type: "log", domain: [1, 70], label: "stated salary midpoint, lakh (log scale)", labelAnchor: "left", ticks: [1, 2, 5, 10, 20, 40, 70], tickFormat: (d: number) => String(d) }, y: { label: "postings", grid: true },
    marks: [Plot.rectY(bins, { x1: "lo", x2: "hi", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }), Plot.tip(bins, Plot.pointerX({ x: (d: any) => Math.sqrt(d.lo * d.hi), y: "n", title: (d: any) => `₹${d.lo.toFixed(1)} to ${d.hi.toFixed(1)} L\n${d.n} postings` }))],
  });

  return (
    <div className="stack">
      <div className="controls" style={{ margin: 0, alignItems: "flex-end" }}>
        <label className="field">Search title or company<input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="for example “data engineer”" /></label>
        <label className="field">Split<select value={split} onChange={(e) => setSplit(e.target.value)}>{[ALL, "train", "test"].map((r) => <option key={r}>{r}</option>)}</select></label>
        <label className="field">Stated salary from (₹ L)<input type="number" min={0} max={80} value={salMin} onChange={(e) => setSalMin(+e.target.value || 0)} style={{ width: 100 }} /></label>
        <label className="field">to (₹ L)<input type="number" min={0} max={80} value={salMax} onChange={(e) => setSalMax(+e.target.value || 0)} style={{ width: 100 }} /></label>
      </div>
      <KpiBar items={[
        { label: "Postings in this view", value: inr(res.n), sub: `of ${inr(ROWS.length)}` },
        { label: "Median stated salary", value: fmtL(res.median) },
        { label: "Model's typical error", value: res.tests ? fmtL(res.mae) : "n/a", sub: res.tests ? `${fmtL(res.baseMae)} for the role median, on ${res.tests} test postings` : "no test postings here" },
        { label: "Estimated within 30%", value: res.tests ? pct0(res.within30) : "n/a", sub: "of test postings" },
        { label: "Stated salary inside 80% range", value: res.tests ? pct0(res.cover) : "n/a", sub: "target 80%" },
      ]} />
      {res.tests > 0 && res.tests < 20 ? <p className="small" style={{ margin: 0 }}>Fewer than 20 test postings here, so the three model results are noisy.</p> : null}
      <div className="duo">
        <div>
          <Legend items={[{ color: "var(--c1)", label: "stated salary inside the 80% range", shape: "dot" }, { color: "var(--c2)", label: "outside the range", shape: "dot" }]} />
          <Fig title="Model estimate against stated salary" sub="Test postings in this view. Dots on the dashed diagonal are exact; vertical lines are the 80% ranges."><PlotFigure label="Model estimate against stated salary for the selected test postings" build={buildScatter} minHeight={360} /></Fig>
        </div>
        <Fig title="How the salaries in this view are spread"><PlotFigure label="Histogram of stated salaries in the view" build={buildHist} minHeight={220} /></Fig>
      </div>
      <div className="tablewrap">
        <table>
          <thead>{table.getHeaderGroups().map((hg) => <tr key={hg.id}>{hg.headers.map((h) => (
            <th key={h.id} className={(h.column.columnDef.meta as any)?.right ? "r" : ""} style={{ cursor: h.column.getCanSort() ? "pointer" : "default" }} onClick={h.column.getToggleSortingHandler()} aria-sort={h.column.getIsSorted() === "asc" ? "ascending" : h.column.getIsSorted() === "desc" ? "descending" : "none"}>
              {flexRender(h.column.columnDef.header, h.getContext())}{h.column.getIsSorted() === "asc" ? " ↑" : h.column.getIsSorted() === "desc" ? " ↓" : ""}
            </th>))}</tr>)}</thead>
          <tbody>{table.getRowModel().rows.map((r) => <tr key={r.id} className={r.original.split === "test" && !(r.original.lo80 <= r.original.mid && r.original.mid <= r.original.hi80) ? "hl" : ""}>{r.getVisibleCells().map((c) => <td key={c.id} className={(c.column.columnDef.meta as any)?.right ? "r" : ""}>{flexRender(c.column.columnDef.cell, c.getContext())}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <div className="pager">
        <button className="btn ghost" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Previous</button>
        <span>Page {table.getState().pagination.pageIndex + 1} of {Math.max(1, table.getPageCount())}, {inr(sel.length)} postings</span>
        <button className="btn ghost" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Next</button>
        <span style={{ marginLeft: "auto" }}>Shaded rows: test postings whose stated salary fell outside the range</span>
      </div>
      <details className="data"><summary>What is in each row</summary>
        <div className="tablewrap"><table><thead><tr><th>Column</th><th>Meaning</th></tr></thead><tbody>{COLS.map((c) => <tr key={c.name}><td>{c.name}</td><td>{c.text}</td></tr>)}</tbody></table></div>
        <p className="small" style={{ marginTop: 10, maxWidth: "70ch" }}>Job descriptions are not shown here. They are what the model reads, and they are scraped text, so they stay in the notebooks.</p>
      </details>
    </div>
  );
}
