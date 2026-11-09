"use client";
import { usePathname } from "next/navigation";
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import D from "@/data/dataset.json";
import { midpoint } from "@/lib/stats";

export type Row = { id: number; title: string; company: string; role: string; city: string; work_mode: string; exp_min: number; exp_max: number; seniority: string; industry: string; skills: string[]; n_skills: number; stated_min: number; stated_max: number; split: string; est?: number; lo80?: number; hi80?: number; mid: number; exp: number };
export const ALL = "All";
export const BANDS = ["0-2 years", "2-5 years", "5-8 years", "8-12 years", "12+ years"] as const;
const edges = [2, 5, 8, 12];
export const bandOf = (exp: number) => BANDS[edges.filter((e) => exp >= e).length];

export const ROWS: Row[] = (D.rows as any[]).map((r) => ({ ...r, mid: midpoint(r), exp: (r.exp_min + r.exp_max) / 2 }));
const uniq = (k: keyof Row) => Array.from(new Set(ROWS.map((r) => r[k] as string))).sort();
export const OPTIONS = { role: uniq("role"), city: uniq("city"), work_mode: uniq("work_mode"), band: [...BANDS] as string[] };

export type Filters = { role: string; city: string; band: string; mode: string };
const EMPTY: Filters = { role: ALL, city: ALL, band: ALL, mode: ALL };
type Skip = keyof Filters | null;

/** Rows that match every active filter, optionally ignoring one so a chart can compare the groups of that field. */
export function applyFilters(f: Filters, skip: Skip = null): Row[] {
  return ROWS.filter((r) =>
    (skip === "role" || f.role === ALL || r.role === f.role) && (skip === "city" || f.city === ALL || r.city === f.city) &&
    (skip === "band" || f.band === ALL || bandOf(r.exp) === f.band) && (skip === "mode" || f.mode === ALL || r.work_mode === f.mode));
}

type Ctx = { f: Filters; set: (k: keyof Filters, v: string) => void; toggle: (k: keyof Filters, v: string) => void; reset: () => void; active: number };
const C = createContext<Ctx | null>(null);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [f, setF] = useState<Filters>(EMPTY);
  const path = usePathname();
  // the selection can be shared: read it from the address once, then keep the address in step
  useEffect(() => {
    const q = new URLSearchParams(window.location.search); const next = { ...EMPTY };
    (["role", "city", "band", "mode"] as const).forEach((k) => { const v = q.get(k); if (v) next[k] = v; });
    setF(next);
  }, []);
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    (["role", "city", "band", "mode"] as const).forEach((k) => (f[k] === ALL ? q.delete(k) : q.set(k, f[k])));
    const s = q.toString(); window.history.replaceState(null, "", window.location.pathname + (s ? `?${s}` : ""));
  }, [f, path]);
  const set = useCallback((k: keyof Filters, v: string) => setF((o) => ({ ...o, [k]: v })), []);
  const toggle = useCallback((k: keyof Filters, v: string) => setF((o) => ({ ...o, [k]: o[k] === v ? ALL : v })), []);
  const reset = useCallback(() => setF(EMPTY), []);
  const value = useMemo(() => ({ f, set, toggle, reset, active: Object.values(f).filter((v) => v !== ALL).length }), [f, set, toggle, reset]);
  return <C.Provider value={value}>{children}</C.Provider>;
}
export function useFilters() { const c = useContext(C); if (!c) throw new Error("FilterProvider missing"); return c; }
