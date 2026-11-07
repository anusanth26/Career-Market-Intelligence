export default function Kpis({ items }: { items: { value: string; label: string }[] }) {
  return (
    <div className="statrow" role="list">
      {items.map((k, i) => <div key={k.label} role="listitem" style={{ ["--i" as any]: i }}><b key={k.value}>{k.value}</b><span>{k.label}</span></div>)}
    </div>
  );
}
