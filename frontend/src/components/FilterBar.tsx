"use client";
import { usePathname } from "next/navigation";
import { ALL, OPTIONS, ROWS, applyFilters, useFilters } from "@/lib/filters";

const SHOW = ["/", "/pay", "/skills", "/data"];

export default function FilterBar() {
  const path = usePathname();
  const { f, set, reset, active } = useFilters();
  if (!SHOW.includes(path)) return null;
  const n = applyFilters(f).length;
  const Sel = ({ k, label, opts }: { k: "role" | "city" | "band" | "mode"; label: string; opts: string[] }) => (
    <label className={f[k] !== ALL ? "on" : ""}>{label}
      <select value={f[k]} onChange={(e) => set(k, e.target.value)}>
        <option value={ALL}>All</option>{opts.map((o) => <option key={o}>{o}</option>)}
      </select>
    </label>
  );
  return (
    <div className="filterbar" role="region" aria-label="Filters">
      <Sel k="role" label="Role" opts={OPTIONS.role} />
      <Sel k="city" label="City" opts={OPTIONS.city} />
      <Sel k="band" label="Experience asked" opts={OPTIONS.band} />
      <Sel k="mode" label="Work mode" opts={OPTIONS.work_mode} />
      <span className="fcount" aria-live="polite"><b>{n.toLocaleString("en-IN")}</b> of {ROWS.length.toLocaleString("en-IN")} salaried postings{n < 15 && n > 0 ? ", too few to trust" : ""}{n === 0 ? ", none match" : ""}</span>
      {active ? <button className="fclear" onClick={reset}>Clear filters</button> : null}
    </div>
  );
}
