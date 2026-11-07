import D from "@/data/disclosure.json";

/** The disclosure classifier exported by the text-mining notebook, applied in the browser with the same arithmetic. */
const M = D.model;
const IDX = new Map<string, number>(M.vocab.map((w: string, i: number) => [w, i]));
const STOP = new Set<string>(M.stop);
export type Bag = Record<string, number>;
export type Result = { p: number; up: { w: string; c: number }[]; down: { w: string; c: number }[]; used: number };

export function bagOf(raw: string): Bag {
  const t = raw.replace(new RegExp(M.sal_pattern, "gi"), " ").toLowerCase();
  const bag: Bag = {};
  for (const w of t.match(new RegExp(M.token.replace("(?u)", ""), "g")) ?? []) {
    if (STOP.has(w) || !IDX.has(w)) continue;
    bag[w] = (bag[w] ?? 0) + 1;
  }
  return bag;
}
export function score(bag: Bag): Result {
  const v: [string, number][] = Object.entries(bag).map(([w, c]) => [w, (1 + Math.log(c)) * (M.idf as number[])[IDX.get(w)!]]);
  const norm = Math.sqrt(v.reduce((a, [, x]) => a + x * x, 0)) || 1;
  const parts = v.map(([w, x]) => ({ w, c: (M.coef as number[])[IDX.get(w)!] * x / norm }));
  const z = (M.intercept as number) + parts.reduce((a, d) => a + d.c, 0);
  const sorted = [...parts].sort((a, b) => b.c - a.c);
  return { p: 1 / (1 + Math.exp(-z)), up: sorted.filter((d) => d.c > 0).slice(0, 6), down: sorted.filter((d) => d.c < 0).reverse().slice(0, 6), used: v.length };
}
export const EXAMPLES = D.examples as { states_salary: boolean; role: string; company: string; tags: string[]; exp: string; description: string; bag: Bag }[];
export const TEST = D.test as { auc: number; ap: number; base_rate: number; threshold: number; accuracy: number; precision: number; recall: number; f1: number; n_test: number };
