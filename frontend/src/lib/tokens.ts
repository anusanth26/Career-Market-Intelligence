"use client";
import { useEffect, useState } from "react";

export type Tokens = {
  bg: string; ink: string; ink2: string; ink3: string; rule: string; grid: string;
  cat: string[]; seq: string[]; neg: string; pos: string; mid: string; dark: boolean;
};

function read(): Tokens {
  const cs = getComputedStyle(document.documentElement);
  const g = (n: string) => cs.getPropertyValue(n).trim();
  return {
    bg: g("--bg"), ink: g("--ink"), ink2: g("--ink2"), ink3: g("--ink3"), rule: g("--rule"), grid: g("--grid"),
    cat: [g("--c1"), g("--c2"), g("--c3"), g("--c4"), g("--c5")],
    seq: [g("--seq0"), g("--seq1"), g("--seq2"), g("--seq3"), g("--seq4")],
    neg: g("--neg"), pos: g("--pos"), mid: g("--mid"), dark: cs.colorScheme.includes("dark"),
  };
}

/** Colour tokens read from the CSS variables. */
export function useTokens(): Tokens | null {
  const [t, setT] = useState<Tokens | null>(null);
  useEffect(() => {
    const update = () => setT(read());
    update();
  }, []);
  return t;
}
