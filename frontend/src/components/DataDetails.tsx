type Col = { key: string; label: string; fmt?: (v: any, row: any) => string; right?: boolean };
export default function DataDetails({ rows, cols, summary = "Show the numbers" }: { rows: any[]; cols: Col[]; summary?: string }) {
  return (
    <details className="data">
      <summary>{summary}</summary>
      <div className="tablewrap">
        <table>
          <thead><tr>{cols.map((c) => <th key={c.key} className={c.right ? "r" : ""}>{c.label}</th>)}</tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>{cols.map((c) => <td key={c.key} className={c.right ? "r" : ""}>{c.fmt ? c.fmt(r[c.key], r) : String(r[c.key] ?? "")}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
