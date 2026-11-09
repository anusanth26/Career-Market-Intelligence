"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ALL, useFilters } from "@/lib/filters";

const TABS = [
  { href: "/", label: "Overview" },
  { href: "/pay", label: "Pay" },
  { href: "/skills", label: "Skills" },
  { href: "/careers", label: "Careers" },
  { href: "/data", label: "Data and method" },
];

export default function TopBar() {
  const path = usePathname();
  const { f } = useFilters();
  const q = new URLSearchParams();
  (["role", "city", "band", "mode"] as const).forEach((k) => f[k] !== ALL && q.set(k, f[k]));
  const qs = q.toString() ? `?${q.toString()}` : "";
  const here = (h: string) => (h === "/" ? path === "/" : path === h || path.startsWith(h + "/") || (h === "/data" && path.startsWith("/reports")));
  return (
    <header className="topbar2">
      <Link href="/" className="brand2">Career Market Intelligence</Link>
      <nav aria-label="Sections" className="tabs2">
        {TABS.map((t) => <Link key={t.href} href={`${t.href}${qs}`} aria-current={here(t.href) ? "page" : undefined}>{t.label}</Link>)}
      </nav>
      <span className="topnote">14,085 Naukri listings · salaries per year, 1 lakh = ₹100,000</span>
    </header>
  );
}
