import Link from "next/link";
import Kpis from "@/components/Kpis";
import PageNav from "@/components/PageNav";
import Estimator from "@/components/Estimator";
import demo from "@/data/demo.json";
import gap from "@/data/gap.json";
import S from "@/data/salary.json";
import R from "@/data/roles.json";
import T from "@/data/textmining.json";
import { inr, pct0, sgnPct } from "@/lib/format";

export default function Home() {
  const f = S.funnel as { label: string; n: number }[];
  const cv = (S.tuned as any[]).find((m) => m.model === "XGBoost (tuned)");
  const roleCv = (S.models as any[]).find((m) => m.model === "Role median");
  const cqr = (S.cqr as any[]).find((c) => c.setting === "CQR, 80% target");
  const ml = (gap.skills as any[]).find((s) => s.skill === "Machine Learning");
  const sql = (gap.skills as any[]).find((s) => s.skill === "SQL"), py = (gap.skills as any[]).find((s) => s.skill === "Python");
  const full = (R.final as any[]).find((x) => x.model === "full text");
  const maxN = f[0].n;
  return (
    <>
      <h1>Pick a posting and see what the model thinks it pays</h1>
      <p className="lede">These are real postings from employers the model never saw in training. It returns an estimate and a range. Then you can reveal what the employer actually stated.</p>
      <Kpis items={[
        { value: inr(f[0].n), label: "postings collected from Naukri" },
        { value: inr(f[3].n), label: "with a stated salary, used to train and test" },
        { value: cv.R2_log.toFixed(2), label: `R² in cross-validation, against ${roleCv.R2_log.toFixed(2)} for the role median` },
        { value: pct0(cqr.coverage), label: "of stated salaries inside the 80% range on unseen employers" },
      ]} />
      <PageNav />
      <Estimator demo={demo as any} />

      <section className="section">
        <h2>What the data says</h2>
        <ul className="findings" style={{ marginTop: 18 }}>
          <li><h3>Experience and the wording of a posting decide pay</h3><p>Experience alone explains over half of the variation in pay; the description adds more. In cross-validation the model reaches R² {cv.R2_log.toFixed(2)}, against {roleCv.R2_log.toFixed(2)} for guessing each role's median.</p><Link href="/pay">See the pay analysis</Link></li>
          <li><h3>An honest answer is a range</h3><p>The model's 80% range held the stated salary {pct0(cqr.coverage)} of the time on postings from unseen employers. A typical range is {cqr.median_width_ratio.toFixed(1)} times wider at the top than at the bottom, and it is too narrow for several roles.</p><Link href="/pay">See how good the ranges are</Link></li>
          <li><h3>Only machine learning is hot on every measure</h3><p>It is in {ml.demand_pct.toFixed(1)}% of postings, search interest is up {ml.pct_change.toFixed(0)}% and it goes with {sgnPct(ml.pay_premium_pct)} pay at the same experience and role. SQL and Python are in about a quarter of postings each but searches for them fell by half and a third.</p><Link href="/trends">See demand against search interest</Link></li>
          <li><h3>Skills come in six bundles, and few carry a pay premium</h3><p>Marketing, cloud and DevOps, data, delivery and business analysis, design, software development. Most of a skill's raw pay premium is seniority; a handful survive controls.</p><Link href="/skills">See the skills analysis</Link></li>
          <li><h3>A description gives away its role about nine times in ten</h3><p>On test postings from unseen companies the role is right {pct0(full.accuracy)} of the time, and just as often with the posting's own title words removed. A 500-character snippet would clearly hurt.</p><Link href="/roles">See the role classifier</Link></li>
          <li><h3>Search interest is attention, not demand</h3><p>Code skills lost about 27% more search interest than tools and platforms, but the gap opened around 2025, not at the first ChatGPT release. Falling searches did not mean falling postings.</p><Link href="/trends">See the test</Link></li>
        </ul>
      </section>

      <section className="section">
        <h2>How many postings each result rests on</h2>
        <div style={{ marginTop: 14, maxWidth: 720 }}>
          {f.map((r) => (
            <div key={r.label} style={{ display: "grid", gridTemplateColumns: "240px 1fr 72px", gap: 12, alignItems: "center", margin: "7px 0", fontFamily: "var(--font-ui)", fontSize: "0.92rem" }}>
              <span>{r.label}</span>
              <span style={{ background: "var(--grid)", height: 14, display: "block" }}><span style={{ display: "block", height: 14, width: `${Math.max(0.8, (r.n / maxN) * 100)}%`, background: "var(--c1)" }} /></span>
              <span className="num" style={{ textAlign: "right", fontWeight: 600 }}>{inr(r.n)}</span>
            </div>
          ))}
        </div>
        <p className="small" style={{ marginTop: 10 }}>Only about {pct0(f[2].n / f[1].n)} of role-matched postings state a salary, so the pay results describe postings that disclose pay. {inr(T.funnel[3].n)} distinct descriptions feed the text analysis.</p>
      </section>
    </>
  );
}
