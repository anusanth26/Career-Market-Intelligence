"use client";
import PageNav from "@/components/PageNav";
import * as Plot from "@observablehq/plot";
import { useState } from "react";
import Block, { Fig } from "@/components/Block";
import DataDetails from "@/components/DataDetails";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { Tokens } from "@/lib/tokens";
import { barsH, dumbbell, heat } from "@/lib/charts";
import { f3, inr, pct0 } from "@/lib/format";
import R from "@/data/roles.json";

export default function RolesPage() {
  const [cm, setCm] = useState<"full" | "masked">("full");
  const [words, setWords] = useState<"full" | "masked">("full");
  const classes = R.classes as string[];
  const models = (R.models as any[]).map((m) => ({ ...m, base: m.model === "Majority class" }));
  const grid = R.grid as any[];
  const g = (l: string, m: string) => grid.find((d) => d.length === l && d.masking === m).macro_f1;
  const feat = (R.features as any[]).flatMap((f) => [{ input: f.input, kind: "as is", v: f.macro_F1 }, ...(f["macro_F1 (title words removed)"] != null ? [{ input: f.input, kind: "title words removed", v: f["macro_F1 (title words removed)"] }] : [])]);
  const featOrder = (R.features as any[]).map((f) => f.input);
  const per = [...(R.per_role as any[])].sort((a, b) => a["F1 full text"] - b["F1 full text"]);
  const final = R.final as any[];
  const full = final.find((f) => f.model === "full text"), masked = final.find((f) => f.model === "title words removed"), maj = final.find((f) => f.model === "majority class");
  const confLong = (m: number[][]) => m.flatMap((row, i) => row.map((v, j) => ({ true: classes[i], pred: classes[j], v })));
  const cmData = confLong(cm === "full" ? (R.confusion_full as number[][]) : (R.confusion_masked as number[][]));
  const ratio = R.ratio as any[];
  const inputs = [...new Set(ratio.map((r) => r.input))];

  const buildRatio = (t: Tokens): Plot.PlotOptions => ({
    height: 300, marginLeft: 56, marginBottom: 46,
    x: { domain: ["80/20", "70/30", "60/40"], label: "training share / test share of companies", labelAnchor: "left" }, y: { domain: [0.75, 0.92], grid: true, label: "macro-F1 on the held-out part" },
    color: { domain: inputs, range: [t.cat[0], t.cat[1], t.cat[2], t.cat[4]] },
    marks: [Plot.line(ratio, { x: "split", y: "mean", z: "input", stroke: "input", strokeWidth: 2.2 }), Plot.dot(ratio, { x: "split", y: "mean", fill: "input", r: 5.5, stroke: t.bg, strokeWidth: 1.5 }),
      Plot.ruleX(ratio, { x: "split", y1: (d: any) => d.mean - d.sd, y2: (d: any) => d.mean + d.sd, stroke: "input", strokeOpacity: 0.55 }),
      Plot.text(ratio.filter((r) => r.split === "60/40"), { x: "split", y: "mean", text: "input", dx: 10, textAnchor: "start", fill: "input", fontSize: 11.5, fontWeight: 600 })],
    marginRight: 190,
  });
  const buildFeat = (t: Tokens): Plot.PlotOptions => ({
    height: 70 + featOrder.length * 74, marginLeft: 270, marginRight: 60, marginBottom: 40,
    x: { domain: [0.7, 0.95], grid: true, label: "macro-F1, five-fold cross-validation", labelAnchor: "left" }, fy: { domain: featOrder, label: null, tickSize: 0 }, y: { domain: ["as is", "title words removed"], axis: null },
    color: { domain: ["as is", "title words removed"], range: [t.cat[0], t.cat[1]] },
    marks: [Plot.barX(feat, { fy: "input", y: "kind", x1: 0.7, x2: "v", fill: "kind", insetTop: 2, insetBottom: 2 }),
      Plot.text(feat, { fy: "input", y: "kind", x: "v", text: (d: any) => f3(d.v), dx: 6, textAnchor: "start", fill: t.ink, fontSize: 11 })],
  });

  return (
    <>
      <h1>A description names its role about nine times in ten, even with the role's own words removed</h1>
      <p className="lede">Each posting's role comes from its title. The question is whether the description alone can recover it, tested on {inr(R.n_test)} postings from companies that were not in the training data.</p>
      <PageNav />
      <div className="statrow">
        <div><b>{pct0(full.accuracy)}</b><span>of test postings classified correctly (guessing the biggest role: {pct0(maj.accuracy)})</span></div>
        <div><b>{(full["macro-F1"]).toFixed(2)}</b><span>macro-F1, the average over the ten roles</span></div>
        <div><b>{(masked["macro-F1"]).toFixed(2)}</b><span>macro-F1 with the posting's own title words removed from its text</span></div>
        <div><b>{pct0(R.own_title_share)}</b><span>of descriptions contain at least one word of their own title</span></div>
      </div>


      <Block title="Which model reads a description best?"
        note={<><p>Six linear and Bayesian models on the word weights of the text, and four models on 70 compact text-mining features (SVD, topics, clusters). Whiskers show the spread across folds.</p><p><strong>Plain linear models lead</strong> and are tied: logistic regression {f3(models.find((m) => m.model === "Logistic regression").macro_F1)}, linear SVM {f3(models.find((m) => m.model === "Linear SVM").macro_F1)}. The compact features reach {f3(models.find((m) => m.model.startsWith("XGBoost")).macro_F1)}, so most of what identifies a role survives compression into topics and clusters.</p><p>Adding word pairs lifts the linear SVM to 0.909 (phrases like "project management" matter). Class weights, vocabulary size and stop words change nothing.</p></>}>
        <Legend items={[{ color: "var(--ink3)", label: "majority-class guess", shape: "bar" }, { color: "var(--c1)", label: "learned model", shape: "bar" }]} />
        <Fig title="Macro-F1 by model" sub="Five-fold cross-validation, grouped by company."><PlotFigure label="Macro-F1 for ten role-fit models" minHeight={380} build={barsH({ data: models, label: "model", value: "macro_F1", sd: "F1_sd", fmt: f3, domain: [0, 1], color: (d, t) => (d.base ? t.ink3 : t.cat[0]), marginLeft: 260 })} /></Fig>
        <DataDetails summary="Table: how the text is represented" rows={R.repr as any[]} cols={[{ key: "variant", label: "Variant" }, { key: "macro_F1", label: "Macro-F1", right: true, fmt: f3 }, { key: "accuracy", label: "Accuracy", right: true, fmt: f3 }]} />
      </Block>

      <Block title="Is the model just reading the role's name?"
        note={<><p>Almost every description repeats a word from its title, so a high score could be name-reading. Two tests: remove every word that names a role (analyst, engineer, manager, designer, data, software, marketing and so on), or remove each posting's own title words.</p>
          <p><strong>The score barely moves:</strong> {f3(g("full", "none"))} to {f3(g("full", "role words removed"))} without role words and {f3(g("full", "title words removed"))} without the title words. The signal is in the tools, duties and skills.</p>
          <p><strong>Length matters much more.</strong> The first 500 characters give {f3(g("first 500", "none"))}, and {f3(g("first 500", "role words removed"))} once role words are removed too. A short snippet would clearly hurt this task.</p></>}>
        <Fig title="Macro-F1 by text length and by what was removed" sub="Linear SVM, five-fold cross-validation grouped by company."><PlotFigure label="Heat map of macro-F1 by text length and masking" minHeight={260} build={heat({ data: grid, x: "masking", y: "length", v: "macro_f1", fmt: f3, xDomain: ["none", "role words removed", "title words removed"], yDomain: ["first 200", "first 500", "first 1000", "full"], domain: [0.6, 0.9], marginLeft: 100, marginBottom: 50, cellH: 46, xLabelRotate: 0 })} /></Fig>
      </Block>

      <Block title="What kind of evidence identifies the role?"
        note={<><p>The employer's skill tags alone give {f3((R.features as any[])[1].macro_F1)}; the text-mining features {f3((R.features as any[])[2].macro_F1)}; the full text {f3((R.features as any[])[0].macro_F1)}.</p><p><strong>Text and tags together do best, {f3((R.features as any[])[3].macro_F1)}</strong>, and keep {f3((R.features as any[])[3]["macro_F1 (title words removed)"])} when title words are removed. The tags carry information the wording does not.</p></>}>
        <Legend items={[{ color: "var(--c1)", label: "text as is", shape: "bar" }, { color: "var(--c2)", label: "title words removed", shape: "bar" }]} />
        <Fig title="Macro-F1 by kind of evidence"><PlotFigure label="Macro-F1 by kind of evidence" build={buildFeat} minHeight={300} /></Fig>
        <Fig title="Does the split ratio matter?" sub="80/20, 70/30 and 60/40 splits of the companies, five repeats each. Whiskers: one standard deviation."><PlotFigure label="Macro-F1 at three train and test splits" build={buildRatio} minHeight={300} /></Fig>
      </Block>

      <Block title="Which roles are easy, and which are mixed up?"
        note={<><p>Digital Marketing ({f3(per.find((p) => p.role === "Digital Marketing")["F1 full text"])}) and Graphic Designer ({f3(per.find((p) => p.role === "Graphic Designer")["F1 full text"])}) are almost always right: their tools and wording are distinct.</p><p><strong>Business Analyst and Data Analyst are the hardest</strong> ({f3(per.find((p) => p.role === "Business Analyst")["F1 full text"])} and {f3(per.find((p) => p.role === "Data Analyst")["F1 full text"])}). Most mistakes are between neighbours with overlapping duties: business analyst for data analyst or project manager, software engineer for DevOps or data engineer, product manager for business analyst.</p><p>Some mistakes are label noise: the role comes from the title, and a posting titled "Immediate Opening For Data Engineer" can describe work that reads like data science.</p></>}>
        <Legend items={[{ color: "var(--c2)", label: "full text", shape: "dot" }, { color: "var(--c1)", label: "title words removed", shape: "dot" }]} />
        <Fig title="F1 for each role on the test postings" sub="Joined dots show what removing the title words does."><PlotFigure label="F1 by role, full text against title words removed" minHeight={360} build={dumbbell({ data: per, label: "role", a: "F1 full text", b: "F1 title words removed", aName: "full text", bName: "title words removed", fmt: f3, domain: [0.7, 1] })} /></Fig>
        <div className="controls"><span>Confusion matrix for the model trained on</span><div className="segmented" role="group" aria-label="Which model">
          <button aria-pressed={cm === "full"} onClick={() => setCm("full")}>full text</button><button aria-pressed={cm === "masked"} onClick={() => setCm("masked")}>title words removed</button></div></div>
        <Fig title="Where each role's postings were sent" sub="Each row sums to 100% of the role's test postings. The diagonal is correct."><PlotFigure label="Confusion matrix of role fit" minHeight={470} build={heat({ data: cmData, x: "pred", y: "true", v: "v", fmt: (v) => `${Math.round(v * 100)}`, xDomain: classes, yDomain: classes, domain: [0, 1], marginLeft: 170, marginBottom: 130, textMin: 0.03 })} /></Fig>
        <DataDetails summary="The most frequent mistakes" rows={R.confusions as any[]} cols={[{ key: "count", label: "Postings", right: true }, { key: "true", label: "True role" }, { key: "pred", label: "Predicted as" }]} />
      </Block>

      <Block title="What words give each role away?"
        note={<><p>The words with the largest weight for each role in the linear SVM. With the title words removed, the list moves from the name of the role to its tools: Kubernetes and Terraform for DevOps, PySpark and pipelines for data engineers, Photoshop and Illustrator for designers.</p></>}>
        <div className="controls"><span>Show words from the model trained on</span><div className="segmented" role="group" aria-label="Which model">
          <button aria-pressed={words === "full"} onClick={() => setWords("full")}>full text</button><button aria-pressed={words === "masked"} onClick={() => setWords("masked")}>title words removed</button></div></div>
        <div className="tablewrap"><table><thead><tr><th>Role</th><th>Words that point to it</th></tr></thead>
          <tbody>{classes.map((c) => <tr key={c}><td>{c}</td><td>{(R.words as any)[c][words]}</td></tr>)}</tbody></table></div>
      </Block>
    </>
  );
}
