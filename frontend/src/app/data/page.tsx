"use client";
import * as Plot from "@observablehq/plot";
import { ColumnDef, flexRender, getCoreRowModel, getPaginationRowModel, getSortedRowModel, SortingState, useReactTable } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import Kpis from "@/components/Kpis";
import Legend from "@/components/Legend";
import PageNav from "@/components/PageNav";
import PlotFigure from "@/components/PlotFigure";
import { Fig } from "@/components/Block";
import { Tokens } from "@/lib/tokens";
import { logBins, mean, median, midpoint } from "@/lib/stats";
import { inr, pct0 } from "@/lib/format";
import D from "@/data/dataset.json";
import S from "@/data/salary.json";

type Row = any;
const ALL = "All";
const ROWS = (D.rows as Row[]).map((r) => ({ ...r, mid: midpoint(r), exp: (r.exp_min + r.exp_max) / 2 }));
const uniq = (k: string) => [ALL, ...Array.from(new Set(ROWS.map((r) => r[k]))).sort()];
const ROLES = uniq("role"), CITIES = uniq("city"), MODES = uniq("work_mode");
const trainMedian: Record<string, number> = {};
for (const role of ROLES.slice(1)) trainMedian[role] = median(ROWS.filter((r) => r.role === role && r.split === "train").map((r) => r.mid));

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

export default function DataPage() {
  const [q, setQ] = useState("");
  const [role, setRole] = useState(ALL), [city, setCity] = useState(ALL), [mode, setMode] = useState(ALL), [split, setSplit] = useState(ALL);
  const [expMin, setExpMin] = useState(0), [expMax, setExpMax] = useState(30);
  const [salMin, setSalMin] = useState(0), [salMax, setSalMax] = useState(80);
  const [sorting, setSorting] = useState<SortingState>([{ id: "mid", desc: true }]);

  const sel = useMemo(() => ROWS.filter((r) =>
    (role === ALL || r.role === role) && (city === ALL || r.city === city) && (mode === ALL || r.work_mode === mode) && (split === ALL || r.split === split) &&
    r.exp >= expMin && r.exp <= expMax && r.mid >= salMin && r.mid <= salMax &&
    (!q.trim() || `${r.title} ${r.company}`.toLowerCase().includes(q.trim().toLowerCase()))), [q, role, city, mode, split, expMin, expMax, salMin, salMax]);
  const tests = useMemo(() => sel.filter((r) => r.split === "test"), [sel]);
  const res = useMemo(() => {
    const err = tests.map((r) => Math.abs(r.est - r.mid)), base = tests.map((r) => Math.abs(trainMedian[r.role] - r.mid));
    return {
      n: sel.length, median: median(sel.map((r) => r.mid)), tests: tests.length, mae: mean(err), baseMae: mean(base),
      within30: tests.length ? tests.filter((r) => Math.abs(r.est / r.mid - 1) <= 0.3).length / tests.length : NaN,
      cover: tests.length ? tests.filter((r) => r.lo80 <= r.mid && r.mid <= r.hi80).length / tests.length : NaN,
    };
  }, [sel, tests]);
  const reset = () => { setQ(""); setRole(ALL); setCity(ALL); setMode(ALL); setSplit(ALL); setExpMin(0); setExpMax(30); setSalMin(0); setSalMax(80); };
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
    <>
      <h1>The final dataset, and how the model does on any slice of it</h1>
      <p className="lede">Every posting used for the salary model is listed here with its stated salary. The {D.rows.filter((r: any) => r.split === "test").length} test postings also carry the model's estimate and range, made without seeing the salary. Filter the table and the results below it follow your selection.</p>
      <Kpis items={[{ value: inr(D.n), label: "postings in the final dataset, each with a stated yearly range" }, { value: inr(S.companies), label: "different employers" }, { value: "10", label: "roles, from the title" }, { value: `${S.n_train} / ${S.n_test}`, label: "training and test postings, no employer in both" }, { value: inr(S.funnel[0].n), label: "postings scraped before the screens" }]} />
      <PageNav />

      <section className="section">
        <h2>What is in each row</h2>
        <div className="tablewrap"><table><thead><tr><th>Column</th><th>Meaning</th></tr></thead><tbody>{COLS.map((c) => <tr key={c.name}><td>{c.name}</td><td>{c.text}</td></tr>)}</tbody></table></div>
        <p className="small" style={{ marginTop: 10, maxWidth: "70ch" }}>Job descriptions are not shown here. They are what the model reads, and they are scraped text, so they stay in the notebooks. The text-mining analysis uses {inr(10780)} role-matched postings; the {inr(D.n)} listed here are the ones that state a usable salary.</p>
      </section>

      <section className="section">
        <h2>Browse and filter the dataset</h2>
        <div className="controls" style={{ alignItems: "flex-end" }}>
          <label className="field">Search title or company<input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="for example “data engineer”" /></label>
          <label className="field">Role<select value={role} onChange={(e) => setRole(e.target.value)}>{ROLES.map((r) => <option key={r}>{r}</option>)}</select></label>
          <label className="field">City<select value={city} onChange={(e) => setCity(e.target.value)}>{CITIES.map((r) => <option key={r}>{r}</option>)}</select></label>
          <label className="field">Work mode<select value={mode} onChange={(e) => setMode(e.target.value)}>{MODES.map((r) => <option key={r}>{r}</option>)}</select></label>
          <label className="field">Split<select value={split} onChange={(e) => setSplit(e.target.value)}>{[ALL, "train", "test"].map((r) => <option key={r}>{r}</option>)}</select></label>
        </div>
        <div className="controls" style={{ alignItems: "flex-end" }}>
          <label className="field">Years asked, from<input type="number" min={0} max={30} value={expMin} onChange={(e) => setExpMin(+e.target.value || 0)} style={{ width: 90 }} /></label>
          <label className="field">to<input type="number" min={0} max={30} value={expMax} onChange={(e) => setExpMax(+e.target.value || 0)} style={{ width: 90 }} /></label>
          <label className="field">Stated salary, from (₹ L)<input type="number" min={0} max={80} value={salMin} onChange={(e) => setSalMin(+e.target.value || 0)} style={{ width: 110 }} /></label>
          <label className="field">to (₹ L)<input type="number" min={0} max={80} value={salMax} onChange={(e) => setSalMax(+e.target.value || 0)} style={{ width: 110 }} /></label>
          <button className="btn ghost" onClick={reset}>Clear filters</button>
        </div>

        <h3 style={{ marginTop: 22 }}>Results on this selection</h3>
        <Kpis items={[
          { value: inr(res.n), label: `postings selected, of ${inr(D.n)}` },
          { value: fmtL(res.median), label: "median stated salary of the selection" },
          { value: res.tests ? fmtL(res.mae) : "n/a", label: res.tests ? `model's typical error on the ${res.tests} test postings, against ${fmtL(res.baseMae)} for the role median` : "no test postings in this selection" },
          { value: res.tests ? pct0(res.within30) : "n/a", label: "of test postings estimated within 30% of the stated salary" },
          { value: res.tests ? pct0(res.cover) : "n/a", label: "of test postings whose stated salary falls inside the 80% range (target 80%)" },
        ]} />
        {res.tests > 0 && res.tests < 20 ? <p className="small" style={{ marginTop: 6 }}>Fewer than 20 test postings are selected, so these three results are noisy.</p> : null}

        <div className="cols" style={{ marginTop: 24 }}>
          <div className="chart-col">
            <Legend items={[{ color: "var(--c1)", label: "stated salary inside the 80% range", shape: "dot" }, { color: "var(--c2)", label: "outside the range", shape: "dot" }]} />
            <Fig title="Model estimate against stated salary, test postings in the selection" sub="Dots on the dashed diagonal are exact. Vertical lines are the 80% ranges."><PlotFigure label="Model estimate against stated salary for the selected test postings" build={buildScatter} minHeight={360} /></Fig>
            <Fig title="How the selection's salaries are spread"><PlotFigure label="Histogram of stated salaries in the selection" build={buildHist} minHeight={220} /></Fig>
          </div>
          <aside className="note">
            <p><strong>Try this.</strong> Pick Software Engineer: the range holds the stated salary for fewer postings than the 80% target. Pick Graphic Designer: it holds for nearly all.</p>
            <p>Set years asked from 8 to 15 and the typical error grows, because senior pay is the hardest to predict.</p>
            <p>Only test postings carry a model estimate. Training postings were used to fit the model, so scoring on them would flatter it.</p>
          </aside>
        </div>

        <div className="tablewrap" style={{ marginTop: 18 }}>
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
      </section>
    </>
  );
}
