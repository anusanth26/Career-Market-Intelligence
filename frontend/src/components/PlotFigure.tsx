"use client";
import * as Plot from "@observablehq/plot";
import { useEffect, useRef, useState } from "react";
import { Tokens, useTokens } from "@/lib/tokens";

type Props = {
  build: (t: Tokens, width: number) => Plot.PlotOptions;
  label: string;
  minHeight?: number;
};

/** Renders an Observable Plot chart at the width of its container, restyled from the theme tokens. */
export default function PlotFigure({ build, label, minHeight = 120 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const t = useTokens();
  const [w, setW] = useState(0);
  const drawn = useRef(false);
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setW(Math.floor(e.contentRect.width)));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  useEffect(() => {
    if (!ref.current || !t || w < 120) return;
    const opts = build(t, w);
    const el = Plot.plot({
      ...opts,
      width: w,
      style: `background:transparent;color:${t.ink2};font-family:var(--font-ui),system-ui,sans-serif;font-size:12.5px;overflow:visible;--plot-background:${t.bg};`,
    });
    el.setAttribute("role", "img");
    el.setAttribute("aria-label", label);
    // first draw wipes in from the left; later redraws (filters, resize) only fade, so typing stays calm
    el.classList.add(drawn.current ? "redraw" : "firstdraw");
    drawn.current = true;
    ref.current.replaceChildren(el);
    return () => { el.remove(); };
  }, [t, w, build, label]);
  return <div ref={ref} className="chart" style={{ minHeight }} />;
}
