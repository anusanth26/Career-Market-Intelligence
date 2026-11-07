"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const ITEMS = [
  { href: "/", title: "Estimate a posting", q: "What would the model say it pays?" },
  { href: "/pay", title: "Pay", q: "What drives pay, and how sure are we?" },
  { href: "/data", title: "The dataset", q: "Browse every posting and test the model on any slice" },
  { href: "/scenarios", title: "Scenarios", q: "Check an offer, benchmark a role, plan skills" },
  { href: "/recommendations", title: "Recommendations", q: "What to do with this" },
  { href: "/skills", title: "Skills", q: "What do postings ask for? Does it move pay?" },
  { href: "/disclosure", title: "Disclosure", q: "Who states the pay, and what does the wording say?" },
  { href: "/roles", title: "Roles", q: "Can a description tell its role?" },
  { href: "/trends", title: "Trends", q: "What are people searching for?" },
  { href: "/explore", title: "Explorer", q: "Filter the data yourself" },
  { href: "/method", title: "Data and method", q: "Where the numbers come from" },
];

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  const path = usePathname();
  return (
    <nav className="nav" aria-label="Sections">
      {ITEMS.map((i) => (
        <Link key={i.href} href={i.href} aria-current={path === i.href ? "page" : undefined} onClick={onNavigate}>
          <b>{i.title}</b>{i.q}
        </Link>
      ))}
    </nav>
  );
}

export default function Rail() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="topbar">
        <Link href="/" className="brand">Career Market Intelligence</Link>
        <button onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="mobilenav">{open ? "Close" : "Menu"}</button>
      </div>
      {open ? <div className="slide"><div id="mobilenav" className="mobilenav"><Nav onNavigate={() => setOpen(false)} /></div></div> : null}
      <aside className="rail">
        <Link href="/" className="brand">
          Career Market Intelligence
          <small>Pay and skills in Indian job postings, from 14,085 Naukri listings</small>
        </Link>
        <Nav />
        <div className="rail-foot">
          <div>Salaries are per year. 1 lakh = 100,000 rupees.</div>
        </div>
      </aside>
    </>
  );
}
