export default function Legend({ items }: { items: { color: string; label: string; shape?: "dot" | "bar" | "line" }[] }) {
  return (
    <p className="small" style={{ margin: "0 0 6px", fontFamily: "var(--font-ui)" }}>
      {items.map((i, k) => (
        <span key={k} style={{ marginRight: 20, whiteSpace: "nowrap" }}>
          <span style={{ display: "inline-block", background: i.color, marginRight: 6, verticalAlign: "-1px", width: i.shape === "line" ? 3 : 12, height: i.shape === "line" ? 13 : 12, borderRadius: i.shape === "dot" ? 6 : 2 }} />
          {i.label}
        </span>
      ))}
    </p>
  );
}
