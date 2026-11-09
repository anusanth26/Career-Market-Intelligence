export const quantile = (a: number[], p: number) => {
  if (!a.length) return NaN;
  const s = [...a].sort((x, y) => x - y); const i = (s.length - 1) * p; const lo = Math.floor(i);
  return s[lo] + (s[Math.ceil(i)] - s[lo]) * (i - lo);
};
export const median = (a: number[]) => quantile(a, 0.5);
export const mean = (a: number[]) => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : NaN);
/** share of values at or below x, as 0..1 */
export const rankOf = (a: number[], x: number) => (a.length ? a.filter((v) => v <= x).length / a.length : NaN);
export const midpoint = (r: { stated_min: number; stated_max: number }) => (r.stated_min + r.stated_max) / 2;
/** log-spaced histogram bins (values in lakh) */
export function logBins(vals: number[], lo = 1, hi = 70, n = 20) {
  const edges = Array.from({ length: n + 1 }, (_, i) => lo * Math.pow(hi / lo, i / n));
  return edges.slice(0, -1).map((a, i) => ({ lo: a, hi: edges[i + 1], n: vals.filter((v) => v >= a && (v < edges[i + 1] || (i === n - 1 && v <= edges[i + 1]))).length }));
}
