import { ReactNode } from "react";
/** One question: a heading, a chart area and a margin note. */
export default function Block({ id, title, children, note, wide }: { id?: string; title: string; children: ReactNode; note?: ReactNode; wide?: boolean }) {
  return (
    <section className="section" id={id}>
      <h2>{title}</h2>
      <div className={`cols${note && !wide ? "" : " wide"}`}>
        <div className="chart-col">{children}</div>
        {note && !wide ? <aside className="note">{note}</aside> : null}
      </div>
      {note && wide ? <div className="note" style={{ marginTop: 14, maxWidth: 760 }}>{note}</div> : null}
    </section>
  );
}
export function Fig({ title, sub, children }: { title: string; sub?: string; children: ReactNode }) {
  return (
    <figure style={{ margin: "0 0 28px" }}>
      <p className="figtitle">{title}</p>
      {sub ? <p className="figsub">{sub}</p> : null}
      {children}
    </figure>
  );
}
