"use client";
import { forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY } from "d3-force";
import { useEffect, useMemo, useRef, useState } from "react";

type Node = { skill: string; bundle: number; demand_pct: number; x: number; y: number };
type Edge = { a: string; b: string; lift: number; together: number };
type Bundle = { id: number; skills: string[]; size: number };

const COL = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)", "var(--ink3)"];
const NAMES = ["Marketing", "Cloud and DevOps", "Data", "Delivery and business analysis", "Design", "Software development"];

function Marker({ k, x, y, r, active }: { k: number; x: number; y: number; r: number; active: boolean }) {
  const common = { fill: COL[k % 6], stroke: "var(--bg)", strokeWidth: 1.5, opacity: active ? 1 : 0.25 };
  switch (k % 6) {
    case 0: return <circle cx={x} cy={y} r={r} {...common} />;
    case 1: return <rect x={x - r} y={y - r} width={2 * r} height={2 * r} {...common} />;
    case 2: return <polygon points={`${x},${y - r * 1.2} ${x + r * 1.2},${y} ${x},${y + r * 1.2} ${x - r * 1.2},${y}`} {...common} />;
    case 3: return <polygon points={`${x},${y - r * 1.25} ${x + r * 1.15},${y + r} ${x - r * 1.15},${y + r}`} {...common} />;
    case 4: return <polygon points={`${x - r},${y - r * 0.4} ${x - r * 0.4},${y - r * 0.4} ${x - r * 0.4},${y - r} ${x + r * 0.4},${y - r} ${x + r * 0.4},${y - r * 0.4} ${x + r},${y - r * 0.4} ${x + r},${y + r * 0.4} ${x + r * 0.4},${y + r * 0.4} ${x + r * 0.4},${y + r} ${x - r * 0.4},${y + r} ${x - r * 0.4},${y + r * 0.4} ${x - r},${y + r * 0.4}`} {...common} />;
    default: return <polygon points={`${x - r},${y} ${x - r * 0.5},${y - r * 0.9} ${x + r * 0.5},${y - r * 0.9} ${x + r},${y} ${x + r * 0.5},${y + r * 0.9} ${x - r * 0.5},${y + r * 0.9}`} {...common} />;
  }
}

const BW = 820, BH = 600;
type VB = [number, number, number, number];
const fitAspect = (x0: number, y0: number, x1: number, y1: number, pad: number, minW = 0): VB => {
  let w = x1 - x0 + 2 * pad, h = y1 - y0 + 2 * pad;
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  w = Math.max(w, minW); if (w / h < BW / BH) w = h * BW / BH; else h = w * BH / BW;
  return [cx - w / 2, cy - h / 2, w, h];
};

/** Skill network: nodes sit where a force layout put them; shape and colour show the bundle. Pick a bundle to zoom in and label every skill in it. */
export default function Network({ nodes, edges, bundles }: { nodes: Node[]; edges: Edge[]; bundles: Bundle[] }) {
  const [sel, setSel] = useState<number | null>(null);
  useEffect(() => { const b = new URLSearchParams(location.search).get("bundle"); if (b !== null && +b >= 0 && +b < bundles.length) setSel(+b); }, [bundles.length]);
  const radius = (n: Node) => 3.5 + Math.sqrt(n.demand_pct) * 1.15;
  const compute = () => {
    let s = 12345; const rng = () => { s = (s + 0x6d2b79f5) | 0; let x = Math.imul(s ^ (s >>> 15), 1 | s); x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x; return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
    // one anchor per bundle on a ring, so the bundles separate; skills settle around their anchor
    const anchors = bundles.map((b, i) => { const a = (i / bundles.length) * 2 * Math.PI - Math.PI / 2; return { x: BW / 2 + 270 * Math.cos(a), y: BH / 2 + 200 * Math.sin(a) }; });
    const A = (b: number) => anchors[b >= 0 && b < anchors.length ? b : 0];
    const ns: any[] = nodes.map((n) => ({ id: n.skill, b: n.bundle, r: radius(n), x: A(n.bundle).x + (rng() - 0.5) * 60, y: A(n.bundle).y + (rng() - 0.5) * 60 }));
    const idx = new Set(ns.map((n) => n.id));
    const ls = edges.filter((e) => idx.has(e.a) && idx.has(e.b)).map((e) => ({ source: e.a, target: e.b, w: e.lift }));
    const sim = forceSimulation(ns).randomSource(rng)
      .force("link", forceLink(ls).id((d: any) => d.id).strength(0.04).distance(46))
      .force("charge", forceManyBody().strength(-34))
      // a stronger pull to the bundle anchor keeps skills with no strong links (design, management) inside their bundle
      .force("x", forceX((d: any) => A(d.b).x).strength(0.22))
      .force("y", forceY((d: any) => A(d.b).y).strength(0.22))
      .force("collide", forceCollide((d: any) => d.r + 5).iterations(2)).stop();
    for (let i = 0; i < 500; i++) sim.tick();
    const P: Record<string, { x: number; y: number; r: number; b: number }> = Object.fromEntries(ns.map((n) => [n.id, { x: n.x, y: n.y, r: n.r, b: n.b }]));
    const box = (list: any[]) => ({ x0: Math.min(...list.map((n) => n.x - n.r)), x1: Math.max(...list.map((n) => n.x + n.r)), y0: Math.min(...list.map((n) => n.y - n.r)), y1: Math.max(...list.map((n) => n.y + n.r)) });
    const full = box(ns); const vbAll = fitAspect(full.x0, full.y0, full.x1, full.y1, 46);
    const vbB = bundles.map((b) => { const m = ns.filter((n) => n.b === b.id); const q = box(m); return fitAspect(q.x0, q.y0, q.x1, q.y1, 46, 230); });
    return { P, vbAll, vbB };
  };
  const [layout, setLayout] = useState<ReturnType<typeof compute> | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { try { setLayout(compute()); } catch { setFailed(true); } /* eslint-disable-next-line */ }, [nodes, edges, bundles]);

  const target: VB | null = layout ? (sel === null ? layout.vbAll : layout.vbB[sel] ?? layout.vbAll) : null;
  const [vb, setVb] = useState<VB | null>(null);
  const cur = useRef<VB | null>(null);
  useEffect(() => {
    if (!target) return;
    const from = cur.current ?? target;
    const reduce = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce || !cur.current) { cur.current = target; setVb(target); return; }
    let raf = 0; const t0 = performance.now(), D = 480;
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / D), e = 1 - Math.pow(1 - k, 3);
      const v = from.map((f, i) => f + (target[i] - f) * e) as VB; cur.current = v; setVb(v);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target]);

  const byName = useMemo(() => Object.fromEntries(nodes.map((n) => [n.skill, n])), [nodes]);
  // labels: biggest skills first, each placed above, below, right or left, only where it overlaps nothing already placed
  const labels = useMemo(() => {
    if (!layout || !target) return [] as { skill: string; x: number; y: number; anchor: "middle" | "start" | "end" }[];
    const k = target[2] / BW, fs = 11 * k, cw = 5.7 * k;
    const placed: [number, number, number, number][] = [];
    const out: { skill: string; x: number; y: number; anchor: "middle" | "start" | "end" }[] = [];
    const inView = (p: { x: number; y: number }) => p.x > target[0] && p.x < target[0] + target[2] && p.y > target[1] && p.y < target[1] + target[3];
    const list = [...nodes].filter((n) => (sel === null ? true : n.bundle === sel) && inView(layout.P[n.skill])).sort((a, b) => b.demand_pct - a.demand_pct).slice(0, sel === null ? 30 : 60);
    Object.values(layout.P).forEach((p) => placed.push([p.x - p.r, p.y - p.r, p.x + p.r, p.y + p.r]));
    for (const n of list) {
      const p = layout.P[n.skill], w = n.skill.length * cw, h = fs;
      const opts: ["middle" | "start" | "end", number, number, [number, number, number, number]][] = [
        ["middle", p.x, p.y - p.r - 3 * k, [p.x - w / 2, p.y - p.r - 3 * k - h, p.x + w / 2, p.y - p.r - 3 * k]],
        ["middle", p.x, p.y + p.r + 3 * k + h, [p.x - w / 2, p.y + p.r + 3 * k, p.x + w / 2, p.y + p.r + 3 * k + h]],
        ["start", p.x + p.r + 4 * k, p.y + h / 3, [p.x + p.r + 4 * k, p.y - h / 2, p.x + p.r + 4 * k + w, p.y + h / 2]],
        ["end", p.x - p.r - 4 * k, p.y + h / 3, [p.x - p.r - 4 * k - w, p.y - h / 2, p.x - p.r - 4 * k, p.y + h / 2]],
      ];
      // a node's own marker is already in `placed`; ignore it when testing its own label
      const own = [p.x - p.r, p.y - p.r, p.x + p.r, p.y + p.r];
      const free = (r: [number, number, number, number]) => !placed.some((q) => !(q[0] === own[0] && q[1] === own[1]) && r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1]);
      const o = opts.find((c) => free(c[3]));
      if (o) { placed.push(o[3]); out.push({ skill: n.skill, x: o[1], y: o[2], anchor: o[0] }); }
    }
    return out;
  }, [layout, target, nodes, sel]);

  if (failed) return <p className="small">The network could not be drawn in this browser. The skills in each bundle are listed under the heatmap below.</p>;
  if (!layout || !vb || !target) return <div style={{ minHeight: 420 }} className="small" aria-busy="true">Drawing the network…</div>;
  const pos = layout.P, k = target[2] / BW;
  // the bundle name sits above its cluster, on whichever side of the cluster has room
  const nameAt = bundles.map((b) => { const m = nodes.filter((n) => n.bundle === b.id).map((n) => pos[n.skill]); return { x: m.reduce((a, p) => a + p.x, 0) / m.length, y: Math.min(...m.map((p) => p.y - p.r)) - 14 * k }; });
  return (
    <div>
      <div className="segmented" role="group" aria-label="Zoom to a bundle" style={{ marginBottom: 10, flexWrap: "wrap" }}>
        <button aria-pressed={sel === null} onClick={() => setSel(null)}>All bundles</button>
        {bundles.map((b) => <button key={b.id} aria-pressed={sel === b.id} onClick={() => setSel(b.id)}>{NAMES[b.id]}</button>)}
      </div>
      <svg viewBox={vb.map((v) => v.toFixed(1)).join(" ")} width="100%" style={{ width: "100%", height: "auto", aspectRatio: `${BW} / ${BH}`, overflow: "hidden" }} role="img" aria-label="Network of the 90 most requested skills, grouped into six bundles">
        {edges.map((e, i) => {
          const a = pos[e.a], b = pos[e.b]; if (!a || !b) return null;
          const on = sel === null || (a.b === sel && b.b === sel);
          return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="var(--ink3)" strokeWidth={Math.min(2.2, 0.5 + e.lift * 0.18) * k} opacity={on ? 0.28 : 0.04} style={{ transition: "opacity .3s ease" }} />;
        })}
        {nodes.map((n) => {
          const p = pos[n.skill]; const active = sel === null || n.bundle === sel;
          return (
            <g key={n.skill} style={{ transition: "opacity .3s ease" }}>
              <Marker k={n.bundle} x={p.x} y={p.y} r={p.r} active={active} />
              <title>{`${n.skill}: asked in ${n.demand_pct.toFixed(1)}% of postings, ${NAMES[n.bundle] ?? "no bundle"}`}</title>
            </g>
          );
        })}
        {labels.map((l) => <text key={l.skill} x={l.x} y={l.y} textAnchor={l.anchor} style={{ fontFamily: "var(--font-ui)", fontSize: 11 * k, fill: "var(--ink)", paintOrder: "stroke", stroke: "var(--bg)", strokeWidth: 3 * k, pointerEvents: "none" }}>{l.skill}</text>)}
        {nameAt.map((c, i) => (sel === null || sel === i) ? <text key={i} x={c.x} y={c.y} textAnchor="middle" style={{ fontFamily: "var(--font-ui)", fontSize: 13.5 * k, fontWeight: 650, fill: COL[i % 6], paintOrder: "stroke", stroke: "var(--bg)", strokeWidth: 4 * k, pointerEvents: "none" }}>{NAMES[i]}</text> : null)}
      </svg>
      <p className="small" style={{ marginTop: 6 }}>Marker size follows how many postings ask for the skill. Lines join skills that appear together at least 2.5 times more often than chance. Four broad skills (management, communication skills, compliance, design) have no such link to another skill, so they sit in their bundle without lines. Pick a bundle to zoom in.</p>
    </div>
  );
}
