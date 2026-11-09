import Link from "next/link";

/** The long write-ups keep their article layout, one step behind the dashboard. */
export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="report">
      <Link href="/data" className="reportback">Back to Data and method</Link>
      {children}
    </div>
  );
}
