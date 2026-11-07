"use client";
import DisclosureDemo from "@/components/DisclosureDemo";
import DisclosureEvidence from "@/components/DisclosureEvidence";
import Kpis from "@/components/Kpis";
import PageNav from "@/components/PageNav";
import { f2, inr, pct0 } from "@/lib/format";
import D from "@/data/disclosure.json";

export default function DisclosurePage() {
  const L: any = (D as any).label_counts;
  const best = (D.models as any[]).find((m) => m.model === "Logistic regression (words)");
  return (
    <>
      <h1>Only one posting in eight states its pay, and the wording tells you which</h1>
      <p className="lede">Every salary result in this dashboard rests on the postings that state a salary. Whether an employer states it is a classification problem of its own: from the description alone, trained on all {inr(D.n)} role-matched postings.</p>
      <Kpis items={[
        { value: pct0(D.base_rate), label: `of postings state a salary (${inr(D.n_disclosing)} of ${inr(D.n)})` },
        { value: pct0((D.firms as any).never_share_of_postings), label: "of postings come from companies that never state one" },
        { value: f2(best.F1), label: `F1 for the description words, against 0.00 for always saying "no" (which is ${pct0((D.models as any[]).find((m) => m.model.startsWith("Say")).accuracy)} accurate)` },
        { value: pct0(best["ROC-AUC"]), label: "ROC-AUC across companies it never saw (50% is guessing)" },
      ]} />
      <PageNav />
      <DisclosureDemo />
      <DisclosureEvidence />
      <section className="section" id="label">
        <h2>What counts as stating the pay</h2>
        <p className="small" style={{ maxWidth: "68ch" }}>The label comes from the salary field of each scraped posting, not from words in the description. A posting states its pay when that field holds a yearly range. Across all {inr(L.scraped)} scraped postings:</p>
        <Kpis items={[
          { value: inr(L.states_yearly), label: "show a yearly salary range, which counts as stating pay" },
          { value: inr(L.not_disclosed), label: 'are marked "Not disclosed" by the job board' },
          { value: inr(L.unpaid), label: 'are marked "Unpaid", mostly internships, and count as not stating a salary' },
          { value: inr(L.monthly_amount), label: "show a monthly amount that is not treated as a yearly range, so they count as not stating (a small label error)" },
        ]} />
        <p className="small" style={{ maxWidth: "68ch" }}>Descriptions can still mention pay without the field being filled in: {pct0(D.mention.others)} of the postings that do not state pay name a salary, CTC or an amount in the text, against {pct0(D.mention.disclosers)} of those that do. Those words are removed before the model reads the text. Vague phrases such as "competitive salary" do not count as stating pay.</p>
      </section>
      <section className="section" id="meaning">
        <h2>What to do with this</h2>
        <ul className="findings">
          <li><h3 className="est-title" style={{ fontSize: "1.05rem" }}>If you are looking for a job</h3><p>A posting that omits pay is the norm, not a warning sign: nearly nine in ten omit it. Boilerplate-heavy postings from agencies are the quietest, so ask for the range early.</p></li>
          <li><h3 className="est-title" style={{ fontSize: "1.05rem" }}>If you hire or benchmark</h3><p>Stated salaries come mostly from a minority of employers. Inside a role they do not look different from the silent ones on the pay the text points to, but treat a benchmark from stated pay as a sample, and say how many postings it rests on.</p></li>
          <li><h3 className="est-title" style={{ fontSize: "1.05rem" }}>If you analyse postings</h3><p>Scrape counts of salaried postings overstate how open a market is: disclosure is a habit of the employer. Report the disclosure rate beside any posted-wage figure.</p></li>
        </ul>
      </section>
    </>
  );
}
