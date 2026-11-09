"use client";
import PageNav from "@/components/PageNav";
import Kpis from "@/components/Kpis";
import * as Plot from "@observablehq/plot";
import Block, { Fig } from "@/components/Block";
import DataDetails from "@/components/DataDetails";
import Legend from "@/components/Legend";
import Network from "@/components/Network";
import PlotFigure from "@/components/PlotFigure";
import { Tokens } from "@/lib/tokens";
import { barsH, heat } from "@/lib/charts";
import { f2, f3, inr, pct, pct0, sgn, sgnPct } from "@/lib/format";
import T from "@/data/textmining.json";
import N from "@/data/network.json";

const ROLES = ["Software Engineer", "Data Analyst", "Data Scientist", "Data Engineer", "DevOps / Cloud Engineer", "Business Analyst", "Product Manager", "Project Manager", "Digital Marketing", "Graphic Designer"];
const BNAME = ["Marketing", "Cloud and DevOps", "Data", "Delivery and business analysis", "Design", "Software development"];
const asPct = (b: number) => (Math.exp(b) - 1) * 100;

export default function SkillsPage() {
  const tagOrder = (T.tags_top as any[]).map((d) => d.tag);
  const prem = (T.premiums as any[]).map((d) => ({ ...d, dml_lo: d.dml_beta - 1.96 * d.dml_se, dml_hi: d.dml_beta + 1.96 * d.dml_se }));
  const ranked = [...prem].sort((a, b) => b.dml_beta - a.dml_beta);
  const forest = [...ranked.slice(0, 12), ...ranked.slice(-12)].reverse().map((d) => ({ ...d, lbl: `${d.skill} (${d.n_postings})`, pctv: asPct(d.dml_beta) }));
  const topicPrem = [...(T.topic_prem as any[])].sort((a, b) => a.beta_per_SD - b.beta_per_SD).map((d) => ({ ...d, lbl: `${d.topic}: ${String(d["top words"]).split(", ").filter((w) => w.length > 1).slice(0, 3).join(", ")}` }));
  const nSig = { ols: prem.filter((d) => d.ols_fdr_sig).length, dml: prem.filter((d) => d.dml_fdr_sig).length, ridge: prem.filter((d) => d.ridge_ci_excludes_0).length };
  const spear = (T.agree as any).spearman;
  const stab = T.stability as any[];
  const place: any = T.placebo;
  const ctrl: any = T.controls;
  const grid = T.exp_grid as any[];
  const f0 = (l: string) => grid.find((g) => g.set === "F0 controls only" && g.learner === l).r2;
  const gridGain = grid.filter((g) => g.set !== "F0 controls only").map((g) => ({ ...g, gain: g.r2 - f0(g.learner) }));
  const sets = [...new Set(gridGain.map((g) => g.set))];
  const ratioGain = (T.ratio_gain as any[]).filter((g) => g.learner === "XGBoost" || g.learner === "Ridge");
  const textOnly = (N.text_only as any[]).filter((d) => d["text only, Ridge"] != null);
  const toLong = textOnly.flatMap((d) => [{ f: d.features, learner: "Ridge", r2: d["text only, Ridge"] }, { f: d.features, learner: "XGBoost", r2: d["text only, XGBoost"] }]);
  const topics = T.topics as any[];
  const lenH = (T.length_hist as any);
  const lengthBins = lenH.counts.map((c: number, i: number) => ({ x1: lenH.edges[i], x2: lenH.edges[i + 1], n: c }));
  const rec = T.tag_recall as any[];
  const recLong = rec.flatMap((r) => [{ skill: r.skill, kind: "anywhere in the text", v: r.full }, { skill: r.skill, kind: "first 500 characters", v: r.first500 }]);

  const buildLen = (t: Tokens): Plot.PlotOptions => ({
    height: 200, marginLeft: 50, marginBottom: 40,
    x: { label: "description length, characters (longer ones pooled at 6,000)", labelAnchor: "left" }, y: { label: "postings", grid: true },
    marks: [
      Plot.rectY(lengthBins, { x1: "x1", x2: "x2", y: "n", fill: t.cat[0], insetLeft: 0.6, insetRight: 0.6 }),
      Plot.ruleX([500], { stroke: t.cat[1], strokeWidth: 2 }),
      Plot.text([{ x: 500, y: Math.max(...lengthBins.map((b: any) => b.n)) }], { x: "x", y: "y", text: () => "a 500-character limit", dx: 8, dy: -4, textAnchor: "start", fill: t.cat[1], fontWeight: 650, stroke: t.bg, strokeWidth: 4 }),
    ],
  });
  const buildRecall = (t: Tokens): Plot.PlotOptions => ({
    height: 60 + rec.length * 26, marginLeft: 130, marginRight: 50,
    x: { domain: [0, 1], label: "share of tagged postings where the skill is also named in the text", labelAnchor: "left", grid: true, tickFormat: (d: number) => `${Math.round(d * 100)}%` }, y: { label: null, tickSize: 0, domain: rec.map((r) => r.skill) },
    marks: [
      Plot.ruleY(rec, { y: "skill", x1: "first500", x2: "full", stroke: t.ink3, strokeWidth: 2 }),
      Plot.dot(rec, { y: "skill", x: "first500", r: 5.5, fill: t.cat[1], stroke: t.bg, strokeWidth: 1.5 }),
      Plot.dot(rec, { y: "skill", x: "full", r: 5.5, fill: t.cat[0], stroke: t.bg, strokeWidth: 1.5 }),
      Plot.tip(recLong, Plot.pointerY({ y: "skill", x: "v", title: (d: any) => `${d.skill}\n${d.kind}: ${pct0(d.v)}` })),
    ],
  });
  const buildForest = (t: Tokens): Plot.PlotOptions => ({
    height: 60 + forest.length * 24, marginLeft: 190, marginRight: 70, marginBottom: 40,
    x: { label: "pay association at the same experience, role, seniority, city, work mode and industry (log points, about %)", labelAnchor: "left", grid: true, domain: [-0.55, 0.65] },
    y: { label: null, tickSize: 0, domain: forest.map((d) => d.lbl) },
    marks: [
      Plot.ruleX([0], { stroke: t.ink }),
      Plot.ruleY(forest, { y: "lbl", x1: "dml_lo", x2: "dml_hi", stroke: t.ink3, strokeWidth: 1.6 }),
      Plot.dot(forest.filter((d) => d.dml_fdr_sig), { y: "lbl", x: "dml_beta", r: 5, fill: (d: any) => (d.dml_beta > 0 ? t.pos : t.neg), stroke: t.bg, strokeWidth: 1.5 }),
      Plot.dot(forest.filter((d) => !d.dml_fdr_sig), { y: "lbl", x: "dml_beta", r: 5, fill: t.bg, stroke: (d: any) => (d.dml_beta > 0 ? t.pos : t.neg), strokeWidth: 1.8 }),
      Plot.text(forest, { y: "lbl", x: "dml_hi", text: (d: any) => sgnPct(d.pctv), dx: 8, textAnchor: "start", fill: t.ink, fontSize: 11.5 }),
      Plot.tip(forest, Plot.pointerY({ y: "lbl", x: "dml_beta", title: (d: any) => `${d.skill}\n${d.n_postings} salaried postings\n${sgnPct(d.pctv)} pay (95% interval ${sgnPct(asPct(d.dml_lo))} to ${sgnPct(asPct(d.dml_hi))})\n${d.dml_fdr_sig ? "survives the false-discovery control" : "not distinguishable from zero after the control"}` })),
    ],
  });
  const buildTopicPrem = (t: Tokens): Plot.PlotOptions => ({
    height: 60 + topicPrem.length * 30, marginLeft: 270, marginRight: 70, marginBottom: 40,
    x: { label: "pay difference per +1 SD of the topic's share (log points)", labelAnchor: "left", grid: true, domain: [-0.35, 0.2] }, y: { label: null, tickSize: 0, domain: topicPrem.map((d) => d.lbl) },
    marks: [
      Plot.ruleX([0], { stroke: t.ink }), Plot.ruleY(topicPrem, { y: "lbl", x1: "lo", x2: "hi", stroke: t.ink3, strokeWidth: 1.6 }),
      Plot.dot(topicPrem, { y: "lbl", x: "beta_per_SD", r: 5.5, fill: (d: any) => (d.fdr_sig ? (d.beta_per_SD > 0 ? t.pos : t.neg) : t.bg), stroke: (d: any) => (d.beta_per_SD > 0 ? t.pos : t.neg), strokeWidth: 1.8 }),
      Plot.text(topicPrem, { y: "lbl", x: "hi", text: (d: any) => sgnPct(asPct(d.beta_per_SD)), dx: 8, textAnchor: "start", fill: t.ink, fontSize: 11.5 }),
    ],
  });
  const buildGain = (t: Tokens): Plot.PlotOptions => ({
    height: 60 + sets.length * 30, marginLeft: 250, marginRight: 50, marginBottom: 40,
    x: { label: "change in cross-validated R² against experience, role, city, work mode and industry alone", labelAnchor: "left", grid: true, domain: [-0.05, 0.06] }, y: { label: null, tickSize: 0, domain: sets, tickFormat: (d: string) => d.replace(/^F\d /, "") },
    color: { domain: ["Ridge", "Lasso", "Random forest", "XGBoost"], range: [t.cat[0], t.cat[1], t.cat[2], t.cat[4]] },
    marks: [Plot.ruleX([0], { stroke: t.ink }), Plot.dot(gridGain, { y: "set", x: "gain", fill: "learner", r: 5, stroke: t.bg, strokeWidth: 1.4 }),
      Plot.tip(gridGain, Plot.pointer({ y: "set", x: "gain", title: (d: any) => `${d.set}\n${d.learner}: ${sgn(d.gain)}` }))],
  });
  const buildRatio = (t: Tokens): Plot.PlotOptions => ({
    height: 280, marginLeft: 56, marginBottom: 40,
    x: { label: "training share / test share of companies", domain: ["80/20", "70/30", "60/40"], labelAnchor: "left" }, y: { label: "paired gain in held-out R² over controls only", grid: true },
    color: { domain: sets.filter((s) => ratioGain.some((g) => g.set === s)), range: [t.cat[0], t.cat[1], t.cat[2], t.cat[4]] },
    fx: { label: null, domain: ["Ridge", "XGBoost"] },
    marks: [Plot.ruleY([0], { stroke: t.ink }), Plot.dot(ratioGain, { fx: "learner", x: "split", y: "gain", fill: "set", r: 6, stroke: t.bg, strokeWidth: 1.5 }),
      Plot.line(ratioGain, { fx: "learner", x: "split", y: "gain", z: "set", stroke: "set", strokeWidth: 1.5, strokeOpacity: 0.6 })],
  });
  const buildTextOnly = (t: Tokens): Plot.PlotOptions => ({
    height: 70 + textOnly.length * 70, marginLeft: 270, marginRight: 50, marginBottom: 40,
    x: { label: "R², no experience, role or city given", labelAnchor: "left", grid: true, domain: [0, 0.62] }, fy: { label: null, tickSize: 0, domain: textOnly.map((d) => d.features) }, y: { domain: ["Ridge", "XGBoost"], axis: null },
    color: { domain: ["Ridge", "XGBoost"], range: [t.cat[0], t.cat[1]] },
    marks: [Plot.barX(toLong, { fy: "f", y: "learner", x1: 0, x2: "r2", fill: "learner", insetTop: 2, insetBottom: 2 }), Plot.text(toLong, { fy: "f", y: "learner", x: "r2", text: (d: any) => d.r2.toFixed(2), dx: 6, textAnchor: "start", fill: t.ink, fontSize: 11 })],
  });

  return (
    <>
      <h1>Postings ask for skills in six bundles, and only a handful of skills go with higher pay</h1>
      <p className="lede">The text of {inr(T.funnel[3].n)} role-matched postings, each with its full description and the skills the employer tagged. {inr(T.funnel[5].n)} of them also state a salary.</p>
      <Kpis items={[
        { value: inr(T.funnel[3].n), label: "role-matched postings mined for skills" },
        { value: "6", label: "skill bundles found without being told the roles" },
        { value: String((T.premiums as any[]).length), label: "skills tested for a pay association" },
        { value: String((T.premiums as any[]).filter((d) => d.dml_fdr_sig || d.ols_fdr_sig).length), label: "with an association that survives the false-discovery correction" },
      ]} />
      <PageNav />

      <Block title="What do postings ask for, role by role?"
        note={<><p>Each cell is the share of that role's postings whose employer tagged the skill.</p><p><strong>Python and SQL are everywhere in the data roles</strong> (Python in {pct0((T.tag_role_share as any[]).find((d) => d.tag === "python" && d.role === "Data Scientist").pct / 100)} of Data Scientist postings) and still common in software engineering. SEO and Google Analytics belong to Digital Marketing.</p><p>Employer tags are incomplete: only about 6 skills per posting are tagged, while the description names about 12.</p></>}>
        <Fig title="Share of each role's postings that tag the skill" sub="The 20 most common tags."><PlotFigure label="Heat map of skill tags by role" minHeight={640} build={heat({ data: T.tag_role_share as any[], x: "role", y: "tag", v: "pct", fmt: (v) => `${Math.round(v)}`, xDomain: ROLES, yDomain: tagOrder, domain: [0, 90], marginLeft: 150, marginBottom: 130, cellH: 26 })} /></Fig>
      </Block>

      <Block title="Do employers describe the skills they tag, and what would 500 characters keep?"
        note={<><p>Of the skills employers tagged, <strong>{pct0((T.trunc as any).in_text)}</strong> are named somewhere in the description and only <strong>{pct0((T.trunc as any).in_first500)}</strong> within its first 500 characters.</p><p>The description names <strong>{(T.trunc as any).mentions_full.toFixed(1)}</strong> skills per posting; its first 500 characters name {(T.trunc as any).mentions_first500.toFixed(1)}. A short snippet keeps about a third.</p><p>{pct0(lenH.share_over_500)} of descriptions are longer than 500 characters; the median is {inr(lenH.median)}.</p></>}>
        <Fig title="How long descriptions are"><PlotFigure label="Histogram of description length" build={buildLen} minHeight={200} /></Fig>
        <Legend items={[{ color: "var(--c2)", label: "within the first 500 characters", shape: "dot" }, { color: "var(--c1)", label: "anywhere in the description", shape: "dot" }]} />
        <Fig title="Is a tagged skill also named in the text?" sub="The 15 most common skills that can be matched safely in text."><PlotFigure label="Share of tagged skills named in the description, first 500 characters against full text" build={buildRecall} minHeight={440} /></Fig>
      </Block>

      <Block title="What are postings about?"
        note={<><p>Eight topics found by LDA, with no role or skill list given. Most line up with a role.</p><p><strong>Topic 6 is boilerplate</strong> (application steps, disclaimers): about 9% of postings are dominated by it. A topic model gives some of its room to wording that says nothing about the job.</p><p>Twelve clusters of postings recover the role with an agreement of {(T.cluster_nmi as number).toFixed(2)} (1 is perfect); the topics reach {Math.min(...(T.topic_k as any[]).map((k) => k.LDA_NMI_vs_role)).toFixed(2)} to {Math.max(...(T.topic_k as any[]).map((k) => k.LDA_NMI_vs_role)).toFixed(2)}.</p></>}>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Topic</th><th>Most characteristic words</th><th className="r">Postings dominated</th><th>Closest role</th></tr></thead>
            <tbody>{topics.map((t) => <tr key={t.topic}><td>{t.topic}</td><td>{String(t["top words"]).split(", ").filter((w) => w.length > 1).join(", ")}</td><td className="r">{t["share of postings (dominant)"]}</td><td>{t["main role"]}</td></tr>)}</tbody>
          </table>
        </div>
        <Fig title="Average topic share by role"><PlotFigure label="Topic shares by role" minHeight={420} build={heat({ data: T.topic_role as any[], x: "topic", y: "role", v: "share", fmt: (v) => v.toFixed(2), xDomain: topics.map((t) => t.topic), yDomain: ROLES, domain: [0, 0.6], marginLeft: 170, marginBottom: 40, xLabelRotate: 0, textMin: 0.01 })} /></Fig>
      </Block>

      <Block title="Which skills travel together?"
        note={<><p>Skills that appear together far more than chance form a network. Community detection splits it into <strong>six bundles</strong> without being told anything about roles.</p><p>Each role leads on one bundle: DevOps and Cloud on cloud (0.44 of its skills asked on average), Graphic Designer on design (0.35), Digital Marketing on marketing (0.30). <strong>Data Analyst, Data Scientist and Data Engineer share the data bundle</strong>, which is why those three are hard to tell apart.</p></>}>
        <Network nodes={N.nodes as any} edges={N.edges as any} bundles={N.bundles as any} />
        <Fig title="How much of each bundle a role's postings ask for" sub="Average share of the bundle's skills in a posting."><PlotFigure label="Bundle scores by role" minHeight={420} build={heat({ data: (N.role_in_bundle as any[]).map((d) => ({ ...d, b: BNAME[+d.bundle.replace("bundle ", "") - 1] })), x: "b", y: "role", v: "score", fmt: (v) => v.toFixed(2), xDomain: BNAME, yDomain: ROLES, domain: [0, 0.45], marginLeft: 170, marginBottom: 90, textMin: 0.01 })} /></Fig>
        <DataDetails summary="The skills in each bundle" rows={(N.bundles as any[]).map((b) => ({ name: BNAME[b.id], size: b.size, skills: b.skills.slice(0, 14).join(", ") }))} cols={[{ key: "name", label: "Bundle" }, { key: "size", label: "Skills", right: true }, { key: "skills", label: "Most common" }]} />
      </Block>

      <Block title="Does asking for a skill go with higher pay?"
        note={<><p>For two postings with the same experience, role, seniority, city, work mode and industry, how much more does the one asking for the skill pay? Filled dots survive a correction for testing many skills at once; hollow dots do not.</p>
          <p><strong>Strongest higher:</strong> bash, PMP, performance marketing, analytical skills. <strong>Strongest lower:</strong> off-page optimization, graphic designer, corel draw, video editing, mostly comparisons within a role.</p>
          <p><strong>Treat it as a short list, not a ranking.</strong> Intervals are wide, and estimates from two halves of the companies agree in rank only about {stab[0].spearman_mean.toFixed(1)}. Most of a raw skill premium is seniority: after controls the typical skill keeps {pct0(ctrl.median_share_left)} of it.</p></>}>
        <Legend items={[{ color: "var(--pos)", label: "higher pay", shape: "dot" }, { color: "var(--neg)", label: "lower pay", shape: "dot" }]} />
        <Fig title="The 12 largest and 12 smallest pay associations" sub="Number of salaried postings in brackets. Lines are 95% intervals."><PlotFigure label="Pay association of skills with intervals" build={buildForest} minHeight={700} /></Fig>
        <Fig title="How far to trust these numbers" sub="Checks run in the text-mining notebook.">
          <div className="tablewrap"><table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>
            <tr><td>Three different estimators</td><td>Rank agreement {f2(spear.ols_beta.dml_beta)} (regression vs double machine learning), {f2(spear.ols_beta.ridge_beta)} (vs ridge), {f2(spear.ridge_beta.dml_beta)} (ridge vs double machine learning); same sign for {pct0((T.agree as any).same_sign)} of the {prem.length} skills</td></tr>
            <tr><td>Skills that survive the false-discovery control</td><td>{nSig.ols} by regression, {nSig.dml} by double machine learning, {nSig.ridge} intervals excluding zero in the ridge bootstrap, out of {prem.length}</td></tr>
            <tr><td>Placebo: shuffle skills within role and experience</td><td>{pct(place.fp_mean)} of skills flagged at p&lt;0.05 (5% expected), against {pct(place.real_flagged)} on the real data; {place.fdr_mean.toFixed(2)} pass the control on average, {nSig.ols} on the real data</td></tr>
            <tr><td>Stability across company splits</td><td>{stab.map((s) => `${s.split}: rank agreement ${s.spearman_mean.toFixed(2)}, same sign ${pct0(s.sign_agree_mean)}`).join("; ")}</td></tr>
            <tr><td>Held-out companies</td><td>For the {(T.selected as any[]).length} skills picked on the training companies, the sign held on the test companies for 71%, rank agreement 0.23</td></tr>
          </tbody></table></div>
        </Fig>
        <Fig title="Topic wording and pay" sub="Per standard deviation of the topic's share, at the same experience and role."><PlotFigure label="Pay association of topics" build={buildTopicPrem} minHeight={330} /></Fig>
      </Block>

      <Block title="Can the words alone tell the pay?"
        note={<><p>With no experience, role or city given, <strong>about half of the variation in pay is readable from the description</strong>. Four features built from the text only, readable one by one, do as well as 50 opaque SVD dimensions in a linear model (0.54 against 0.52).</p><p>One number does a lot: a seniority index that predicts the years of experience asked for from the words (R² {(N.seniority_r2 as number).toFixed(2)}) reaches 0.39 to 0.41 on its own.</p></>}>
        <Legend items={[{ color: "var(--c1)", label: "Ridge" }, { color: "var(--c2)", label: "XGBoost" }]} />
        <Fig title="Salary variation explained by the text alone" sub="Five-fold cross-validation grouped by company, 1,348 postings."><PlotFigure label="R-squared of text-only features" build={buildTextOnly} minHeight={360} /></Fig>
        <DataDetails summary="Table: with and without experience and role" rows={N.text_only as any[]} cols={[{ key: "features", label: "Features" }, { key: "text only, Ridge", label: "Text only, Ridge", right: true, fmt: (v) => (v == null ? "-" : f3(v)) }, { key: "text only, XGBoost", label: "Text only, XGBoost", right: true, fmt: (v) => (v == null ? "-" : f3(v)) }, { key: "+ experience and role, Ridge", label: "With experience and role, Ridge", right: true, fmt: (v) => f3(v) }, { key: "+ experience and role, XGBoost", label: "With experience and role, XGBoost", right: true, fmt: (v) => f3(v) }]} />
      </Block>

      <Block title="Once experience and role are known, do skills and topics still help predict pay?"
        note={<><p><strong>Hardly.</strong> Adding skills to experience, role, city, work mode and industry changes cross-validated R² by between −0.03 and +0.01. Topics add about 0.01. Only the SVD of the whole text adds clearly (+0.01 to +0.03).</p><p>The same ranking holds at 80/20, 70/30 and 60/40 splits of the companies, with 15 repeats each. What helps is the overall wording of the description, not the skill list.</p></>}>
        <Legend items={[{ color: "var(--c1)", label: "Ridge", shape: "dot" }, { color: "var(--c2)", label: "Lasso", shape: "dot" }, { color: "var(--c3)", label: "Random forest", shape: "dot" }, { color: "var(--c5)", label: "XGBoost", shape: "dot" }]} />
        <Fig title="Gain in R² from each text feature set" sub="Four learners per set. Right of zero is better."><PlotFigure label="Change in R-squared from adding text features" build={buildGain} minHeight={400} /></Fig>
        <Legend items={[{ color: "var(--c1)", label: "skills (tag or text)", shape: "dot" }, { color: "var(--c2)", label: "topics", shape: "dot" }, { color: "var(--c3)", label: "SVD-50", shape: "dot" }, { color: "var(--c5)", label: "skills, topics, SVD and clusters", shape: "dot" }]} />
        <Fig title="The same comparison at three train and test splits" sub="Mean paired gain over 15 random splits grouped by company."><PlotFigure label="Gain by split ratio" build={buildRatio} minHeight={280} /></Fig>
      </Block>
    </>
  );
}
