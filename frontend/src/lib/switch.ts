import D from "@/data/switch.json";

/** The skills-to-role-fit model exported by the text-mining notebook, with the same greedy recourse search. */
export const CLASSES: string[] = D.classes;
export const SKILLS: string[] = D.skills;
const W = D.coef as number[][], B = D.intercept as number[], SHARE = D.share as number[][];
export const PREM = D.premium as Record<string, { pct: number; clear: boolean; n: number }>;
/** A suggestion must be something the target role really asks for: at least min_share of its postings, and not a role name. */
const ROLE_NAME = ((D as any).role_name ?? []) as boolean[];
export const MIN_SHARE = ((D as any).min_share ?? 0.1) as number;
const feasible = (target: number, i: number) => SHARE[target][i] >= MIN_SHARE && !ROLE_NAME[i];
const IDX = new Map<string, number>(SKILLS.map((s, i) => [s, i]));

const vec = (have: Set<string>) => SKILLS.map((s) => (have.has(s) ? 1 : 0));
const scoresOf = (x: number[]) => W.map((w, k) => B[k] + w.reduce((a, c, i) => a + c * x[i], 0));
export function probsOf(have: Set<string>): number[] {
  const z = scoresOf(vec(have)), m = Math.max(...z), e = z.map((q) => Math.exp(q - m)), s = e.reduce((a, b) => a + b, 0);
  return e.map((q) => q / s);
}
const argmax = (a: number[]) => a.reduce((b, v, i) => (v > a[b] ? i : b), 0);

export type Step = { skill: string; pTarget: number };
/** Add, one at a time, the skill that most raises the target's lead over its closest rival; stop when the target is the top role. */
export function recourse(have: Set<string>, target: number, maxAdd = 10): { steps: Step[]; flipped: boolean } {
  const x = vec(have), steps: Step[] = [];
  for (let n = 0; n < maxAdd; n++) {
    const z = scoresOf(x);
    if (argmax(z) === target) return { steps, flipped: true };
    const z2 = z.slice(); z2[target] = -Infinity; const rival = argmax(z2);
    let bi = -1, bg = 0;
    for (let i = 0; i < x.length; i++) { if (x[i] || !feasible(target, i)) continue; const g = W[target][i] - W[rival][i]; if (g > bg) { bg = g; bi = i; } }
    if (bi < 0) break;
    x[bi] = 1;
    const zz = scoresOf(x), m = Math.max(...zz), e = zz.map((q) => Math.exp(q - m)), s = e.reduce((a, b) => a + b, 0);
    steps.push({ skill: SKILLS[bi], pTarget: e[target] / s });
  }
  return { steps, flipped: argmax(scoresOf(x)) === target };
}
export const shareOf = (role: number, skill: string) => SHARE[role][IDX.get(skill)!];
/** The skills a role's postings ask for most often. */
export const typical = (role: number, n = 8) => SHARE[role].map((v, i) => ({ v, i })).sort((a, b) => b.v - a.v).slice(0, n).map((d) => SKILLS[d.i]);
/** Skills ordered by how many postings ask for them overall. */
export const POPULAR = SKILLS.map((s, i) => ({ s, w: SHARE.reduce((a, r, k) => a + r[i] * (D.n_role as Record<string, number>)[CLASSES[k]], 0) })).sort((a, b) => b.w - a.w).map((d) => d.s);
export const METRICS = D.metrics as { accuracy: number; macro_f1: number; tags_only_accuracy: number; n_skills: number; n_train: number; n_test: number };
export const OVERALL = D.overall as { flip_5: number; flip_10: number; naive_flip_5: number; naive_flip_10: number; median_added: number; naive_median_added: number };
export const PAIRS = D.pairs as { from: string; to: string; postings: number; flip_5: number; flip_10: number; median_added: number | null }[];
export const TOP = D.top as Record<string, { skill: string; pick: number; share_to: number; share_from: number }[]>;
