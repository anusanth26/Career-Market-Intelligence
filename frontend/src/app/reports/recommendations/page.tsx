import Link from "next/link";
import PageNav from "@/components/PageNav";
import gap from "@/data/gap.json";
import S from "@/data/salary.json";
import T from "@/data/textmining.json";
import R from "@/data/roles.json";
import TR from "@/data/trends.json";
import { lakh, pct, pct0, sgnPct } from "@/lib/format";

type Rec = { title: string; badge: "strong" | "moderate" | "tentative"; evidence: React.ReactNode; change: string; where: string; href: string };
const label = { strong: "Strong", moderate: "Moderate", tentative: "Tentative" };

function Group({ title, intro, recs }: { title: string; intro?: string; recs: Rec[] }) {
  return (
    <section className="section">
      <h2>{title}</h2>
      {intro ? <p className="small" style={{ maxWidth: "62ch" }}>{intro}</p> : null}
      <div style={{ marginTop: 14 }}>
        {recs.map((r) => (
          <div className="rec" key={r.title}>
            <div><h3>{r.title}</h3><p style={{ marginTop: 8 }}><span className={`badge ${r.badge}`}>{label[r.badge]}</span><Link href={r.href} className="small">{r.where}</Link></p></div>
            <div className="why">{r.evidence}<p><strong>What would change this:</strong> {r.change}</p></div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function RecommendationsPage() {
  const sk = (n: string) => (gap.skills as any[]).find((s) => s.skill === n);
  const prem = (n: string) => { const d = (T.premiums as any[]).find((p) => p.skill === n); return (Math.exp(d.dml_beta) - 1) * 100; };
  const ml = sk("Machine Learning"), sql = sk("SQL"), py = sk("Python"), seo = sk("SEO"), az = sk("Azure"), aws = sk("AWS");
  const cqr = (S.cqr as any[]).find((c) => c.setting === "CQR, 80% target"), raw = (S.cqr as any[]).find((c) => c.setting.startsWith("Quantile bands without") && c.setting.includes("80%"));
  const cond = (r: string) => (S.cond_role as any[]).find((c) => c.role === r).coverage;
  const tr: any = T.trunc;
  const models = R.models as any[]; const lr = models.find((m) => m.model === "Logistic regression").macro_F1;
  const grid = R.grid as any[]; const g = (l: string, m: string) => grid.find((d) => d.length === l && d.masking === m).macro_f1;
  const ai: any = TR.ai;
  const topics = T.topics as any[]; const boiler = topics.find((t) => String(t["top words"]).includes("disclaimer"));
  const stated = pct0(S.funnel[2].n / S.funnel[1].n);

  const seekers: Rec[] = [
    { title: "Build machine learning depth if you are aiming at data roles", badge: "moderate", href: "/reports/trends", where: "Evidence: Trends",
      evidence: <p>It is the one skill high on all three measures: asked for in {ml.demand_pct.toFixed(1)}% of postings, search interest up {ml.pct_change.toFixed(0)}%, and a pay association of about {sgnPct(ml.pay_premium_pct)} at the same experience and role. That association survives the correction for testing many skills.</p>,
      change: "It rests on about 125 salaried postings, and a skill can stand in for seniority or employer type. More salaried postings, or a within-role comparison, would tighten it." },
    { title: "Treat SQL and Python as the entry ticket, not the edge", badge: "moderate", href: "/reports/trends", where: "Evidence: Trends",
      evidence: <p>Each is asked for by about a quarter of postings ({sql.demand_pct.toFixed(0)}% and {py.demand_pct.toFixed(0)}%), yet search interest fell {Math.abs(sql.pct_change).toFixed(0)}% and {Math.abs(py.pct_change).toFixed(0)}%, and their pay associations are small and not distinguishable from zero ({sgnPct(sql.pay_premium_pct)}, {sgnPct(py.pay_premium_pct)}). They read as baseline expectations.</p>,
      change: "A pay association with wider data could still appear; the intervals here are about ±15 points." },
    { title: "Negotiate from a range, not a number", badge: "strong", href: "/reports/pay", where: "Evidence: Pay",
      evidence: <p>The model's 80% range typically has a top {cqr.median_width_ratio.toFixed(1)} times its bottom, and it held the employer's stated salary for {pct0(cqr.coverage)} of postings from companies it had not seen. Treat an estimate as the centre of a spread, and compare an offer with the whole range.</p>,
      change: "For Software Engineer, Data Scientist and Product Manager the range held the stated salary less often than promised (" + [cond("Software Engineer"), cond("Data Scientist"), cond("Product Manager")].map((v) => pct0(v)).join(", ") + "), so read it as optimistic there." },
    { title: "In marketing, pair SEO with performance and analytics skills", badge: "tentative", href: "/reports/skills", where: "Evidence: Skills",
      evidence: <p>SEO is in {seo.demand_pct.toFixed(0)}% of postings and goes with a pay association of {sgnPct(seo.pay_premium_pct)}. At the same role and experience, postings that list performance marketing go with about {sgnPct(prem("performance marketing"))} and analytical skills with about {sgnPct(prem("analytical skills"))}; off-page optimization with about {sgnPct(prem("off-page optimization"))}.</p>,
      change: "These are associations from a short list that survives the false-discovery control, not a ranking. Estimates from two halves of the companies agree in rank only about 0.3." },
  ];
  const employers: Rec[] = [
    { title: "State a salary range in the posting", badge: "tentative", href: "/reports/method", where: "Evidence: Data and method",
      evidence: <p>Only about {stated} of postings state a salary. Without one, candidates cannot compare, and a model such as this one cannot learn from the rest. The range style matters too: the median stated range already spans 1.7 times from bottom to top.</p>,
      change: "This is reasoned from how scarce the data is. Nothing here tests whether stating a range changes who applies." },
    { title: "Benchmark offers against a range, and add market data for senior technical roles", badge: "strong", href: "/reports/pay", where: "Evidence: Pay",
      evidence: <p>Seven of the eight largest test errors are under-predictions of high pay: senior or lead postings stated at about ₹32 to 58 lakh were estimated at ₹13 to 32 lakh. Coverage was lowest for Software Engineer ({pct0(cond("Software Engineer"))}) and Data Scientist ({pct0(cond("Data Scientist"))}).</p>,
      change: "More senior technical postings with stated salaries would let the model calibrate those roles." },
    { title: "Put what the job involves in the first lines", badge: "tentative", href: "/reports/skills", where: "Evidence: Skills",
      evidence: <p>Only {pct0(tr.in_first500)} of the skills an employer tags appear in the first 500 characters, against {pct0(tr.in_text)} anywhere in the description. About {boiler ? String(boiler["share of postings (dominant)"]) : "9%"} of postings are dominated by application and disclaimer wording that says nothing about the work.</p>,
      change: "We measured what a short snippet keeps, not whether a better-written opening changes hiring outcomes." },
  ];
  const students: Rec[] = [
    { title: "Learn SQL and Python first, then specialise by bundle", badge: "moderate", href: "/reports/skills", where: "Evidence: Skills",
      evidence: <p>Skills form six bundles: marketing, cloud and DevOps, data, delivery and business analysis, design, and software development. Each role leans on one bundle; Data Analyst, Data Scientist and Data Engineer share the data bundle, so the base skills carry across them and the specialism comes after.</p>,
      change: "Bundles come from co-occurrence in postings, which describes what employers ask together, not what is best taught together." },
    { title: "Pair cloud skills (Azure, AWS) with data work", badge: "moderate", href: "/reports/trends", where: "Evidence: Trends",
      evidence: <p>Azure and AWS are each in about {az.demand_pct.toFixed(0)}% of postings, in the cloud and DevOps bundle where DevOps / Cloud scores highest (0.44), and Data Engineers draw on it too. Their pay associations lean positive ({sgnPct(az.pay_premium_pct)}, {sgnPct(aws.pay_premium_pct)}) but are not distinguishable from zero.</p>,
      change: "Demand is solid; the pay evidence is weak." },
    { title: "Do not choose skills by what people search for", badge: "moderate", href: "/reports/trends", where: "Evidence: Trends",
      evidence: <p>Search interest for Python, SQL, Java and JavaScript fell while postings still ask for them. Code skills lost about {Math.abs(ai.did_pct).toFixed(0)}% more search interest than tools and platforms (p = {ai.p_rand.toFixed(3)}), but the divergence appears around 2025, not at the ChatGPT release in 2022. Falling searches here do not mean falling demand.</p>,
      change: "Whether AI tools caused the fall is not established; the test cannot separate them from other changes." },
  ];
  const platforms: Rec[] = [
    { title: "Keep the full description, not a snippet", badge: "strong", href: "/reports/roles", where: "Evidence: Roles",
      evidence: <p>A 500-character snippet keeps about a third of the skill mentions ({tr.mentions_first500.toFixed(1)} against {tr.mentions_full.toFixed(1)} per posting). It also lowers role fit from {g("full", "none").toFixed(3)} to {g("first 500", "none").toFixed(3)} macro-F1, and to {g("first 500", "role words removed").toFixed(3)} once role-naming words are removed. For pay prediction the loss was small (about 0.02 of R²), so the cost falls on skill and role analysis.</p>,
      change: "Pay prediction lost less than role fit; a task that needs the duties and tools needs the whole text." },
    { title: "Show salary ranges with their coverage, by role", badge: "strong", href: "/reports/pay", where: "Evidence: Pay",
      evidence: <p>Quantile bands aimed at 80% held the stated salary only {pct(raw.coverage)} of the time; after the conformal correction they held it {pct(cqr.coverage)}. Coverage by role ran from {pct0(Math.min(...(S.cond_role as any[]).map((c) => c.coverage)))} to {pct0(Math.max(...(S.cond_role as any[]).map((c) => c.coverage)))}, so a single overall figure hides weak spots.</p>,
      change: "Calibrating within role or experience band would help, and needs more postings per group." },
    { title: "Read search interest as attention, never as demand", badge: "strong", href: "/reports/trends", where: "Evidence: Trends",
      evidence: <p>Of the 20 skills, six have a search trend too small to use. For the rest, the trend label and the demand in postings disagree for the most-asked skills (SQL and Python fell by half and a third while a quarter of postings ask for them).</p>,
      change: "Joining weekly job-posting snapshots with the search series would show whether one leads the other." },
    { title: "Collect repeated snapshots", badge: "tentative", href: "/reports/method", where: "Evidence: Data and method",
      evidence: <p>All postings come from one snapshot, so nothing here shows how pay or demand moves over time. A weekly collection over a few months would turn the demand and pay comparisons into trends.</p>,
      change: "It costs scraping budget and depends on the job board's terms." },
  ];

  return (
    <>
      <h1>What to do with these findings</h1>
      <p className="lede">Each recommendation names the evidence behind it and how firm it is. Strong means measured on held-out data and consistent across checks. Moderate means measured, but an association or based on a small group. Tentative means reasoned from the data and not tested for outcomes.</p>
      <PageNav />
      <Group title="If you are choosing skills or negotiating pay" recs={seekers} />
      <Group title="If you hire or write job postings" recs={employers} />
      <Group title="If you teach or study" recs={students} />
      <Group title="If you run a job platform or analyse postings" recs={platforms} />
      <section className="section"><h2>Before acting on any of it</h2><p className="small" style={{ maxWidth: "66ch" }}>These results come from {S.funnel[3].n.toLocaleString("en-IN")} postings that state a salary, out of {S.funnel[0].n.toLocaleString("en-IN")} collected in a single snapshot from one job board. Roles come from titles, salaries are the ranges employers chose to publish, and skill associations are not causes. See <Link href="/method">Data and method</Link>.</p></section>
    </>
  );
}
