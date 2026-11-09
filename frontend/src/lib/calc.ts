import calc from "@/data/calculator.json";

export type Profile = { role: string; seniority: string; city: string; work_mode: string; years: number };
export const CALC = calc as {
  features: string[]; coef: number[]; intercept: number; q80: number; cv_r2: number; cv_mae_inr: number; cv_coverage80: number; n: number;
  options: { role: string[]; seniority: string[]; city: string[]; work_mode: string[] };
};

/** Estimate and 80% range in lakh per year for a profile, from the ridge calculator model. */
export function predict(p: Profile) {
  let z = CALC.intercept;
  CALC.features.forEach((f, i) => {
    let x = 0;
    if (f === "exp") x = p.years; else if (f === "exp2") x = (p.years * p.years) / 10;
    else if (f === `role_${p.role}` || f === `seniority_${p.seniority}` || f === `city_${p.city}` || f === `work_mode_${p.work_mode}`) x = 1;
    z += CALC.coef[i] * x;
  });
  return { est: Math.exp(z) / 1e5, lo: Math.exp(z - CALC.q80) / 1e5, hi: Math.exp(z + CALC.q80) / 1e5 };
}
