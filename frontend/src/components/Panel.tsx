"use client";
import { ReactNode, useState } from "react";

export type Tab = { id: string; label: string; node: ReactNode };
type Props = { title: string; sub?: string; tabs?: Tab[]; children?: ReactNode; info?: ReactNode; tag?: string; span?: number; id?: string };

/** One tile of the dashboard grid: a title row, optional tabs that swap the view in place, and an info button for the method note. */
export default function Panel({ title, sub, tabs, children, info, tag, span = 12, id }: Props) {
  const [cur, setCur] = useState(tabs?.[0]?.id);
  const active = tabs?.find((t) => t.id === cur) ?? tabs?.[0];
  return (
    <section className="panel" id={id} style={{ ["--span" as any]: span }}>
      <header className="phead">
        <div className="ptitle"><h2>{title}</h2>{sub ? <p>{sub}</p> : null}</div>
        {tag ? <span className="ptag" title="This panel is computed in the notebooks and does not change with the filters above">{tag}</span> : null}
        {info ? <details className="pinfo"><summary aria-label={`About: ${title}`}>?</summary><div className="pinfo-body">{info}</div></details> : null}
      </header>
      {tabs && tabs.length > 1 ? (
        <div className="ptabs" role="tablist" aria-label={title}>
          {tabs.map((t) => <button key={t.id} role="tab" aria-selected={t.id === active?.id} onClick={() => setCur(t.id)}>{t.label}</button>)}
        </div>
      ) : null}
      <div className="pbody" key={active?.id}>{tabs ? active?.node : children}</div>
    </section>
  );
}
