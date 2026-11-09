export const inr = (n: number) => n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
/** value in rupees -> "₹9.4 L" */
export const lakh = (rupees: number, d = 1) => `₹${(rupees / 1e5).toFixed(d)} L`;
/** value already in lakh -> "₹9.4 L" */
export const lk = (l: number, d = 1) => `₹${l.toFixed(d)} L`;
export const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
export const pct0 = (v: number) => `${Math.round(v * 100)}%`;
export const f3 = (v: number) => v.toFixed(3);
export const f2 = (v: number) => v.toFixed(2);
export const sgn = (v: number, d = 3) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}`;
export const sgnPct = (v: number, d = 0) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(d)}%`;
export const num = (n: number) => n.toLocaleString("en-IN");
