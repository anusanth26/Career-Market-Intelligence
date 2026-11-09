"use client";
import Link from "next/link";
import DatasetExplorer from "@/components/DatasetExplorer";
import DisclosureDemo from "@/components/DisclosureDemo";
import DisclosureEvidence from "@/components/DisclosureEvidence";
import KpiBar from "@/components/KpiBar";
import MethodBody from "@/components/MethodBody";
import Panel from "@/components/Panel";
import { inr, pct0 } from "@/lib/format";
import D from "@/data/disclosure.json";
import S from "@/data/salary.json";

const REPORTS = [
  { href: "/reports/pay", t: "Pay in depth", d: "Every ablation, the learning curve, the text treatments and range coverage." },
  { href: "/reports/skills", t: "Skills in depth", d: "Topics, clusters, skill bundles, pay premiums with all three estimators and their checks." },
  { href: "/reports/roles", t: "Role fit in depth", d: "Ten models, text length and masking, class weights, split ratios and the words that give each role away." },
  { href: "/reports/trends", t: "Search interest in depth", d: "Twenty skills over five years, the AI break test and the forecast intervals." },
  { href: "/reports/recommendations", t: "Recommendations", d: "Each recommendation with its evidence, how firm it is and what would change it." },
  { href: "/reports/method", t: "Method on one page", d: "Data, notebooks, definitions and limits as a single page." },
];

export default function DataAndMethod() {
  return (
    <>
      <h1 className="sr-only">Data and method: the evidence</h1>
      <KpiBar items={[
        { label: "Postings scraped", value: inr(S.funnel[0].n) },
        { label: "Matched to one of ten roles", value: inr(10780), sub: "distinct descriptions" },
        { label: "State a salary", value: inr(S.funnel[3].n), sub: "used for the salary model" },
        { label: "Share that state pay", value: pct0(D.base_rate), sub: "in the role-matched postings" },
      ]} />
      <div className="grid">
        <Panel span={12} title="The evidence" sub="The data, who states pay, and what the numbers cannot tell you"
          tabs={[
            { id: "data", label: "The dataset", node: <DatasetExplorer /> },
            { id: "disc", label: "Who states the pay", node: <div className="stack"><DisclosureDemo /><DisclosureEvidence /></div> },
            { id: "method", label: "Method and limits", node: <div className="methodtab"><MethodBody /></div> },
            { id: "reports", label: "Full write-ups", node: <nav className="linkrow" aria-label="Full write-ups">{REPORTS.map((r) => <Link key={r.href} href={r.href}><b>{r.t}</b><span>{r.d}</span><em>Open</em></Link>)}</nav> },
          ]} />
      </div>
    </>
  );
}
