export type Kpi = { label: string; value: string; sub?: string };
export default function KpiBar({ items }: { items: Kpi[] }) {
  return (
    <div className="kpibar" role="list">
      {items.map((k) => <div key={k.label} role="listitem"><span className="kl">{k.label}</span><b key={k.value}>{k.value}</b>{k.sub ? <span className="ks">{k.sub}</span> : null}</div>)}
    </div>
  );
}
