"use client";
import Block, { Fig } from "@/components/Block";
import DataDetails from "@/components/DataDetails";
import Legend from "@/components/Legend";
import PlotFigure from "@/components/PlotFigure";
import { barsH, dumbbell } from "@/lib/charts";
import { f2, f3, inr, pct, pct0 } from "@/lib/format";
import D from "@/data/disclosure.json";

const models = D.models as any[], repr = D.repr as any[], len = D.length as any[], F: any = D.firms, byRole = D.by_role as any[], S: any = D.selection, W: any = D.words, ipw: any = D.ipw;
const best = models.find((m) => m.model === "Logistic regression (words)");
const base = models.find((m) => m.model.startsWith("Say"));
const span = (rows: { z: number }[]): [number, number] => [Math.floor(Math.min(...rows.map((r) => r.z)) - 9), Math.ceil(Math.max(...rows.map((r) => r.z)) + 6)];
const wordsRows = (yes: any[], no: any[], n = 9) => [...yes.slice(0, n), ...no.slice(0, n).reverse()].map((d) => ({ term: d.term, z: d.z }));
const metricCols = [
  { key: "ROC-AUC", label: "ROC-AUC", right: true, fmt: f3 }, { key: "accuracy", label: "Accuracy", right: true, fmt: f3 }, { key: "precision", label: "Precision", right: true, fmt: f3 },
  { key: "recall", label: "Recall", right: true, fmt: f3 }, { key: "F1", label: "F1", right: true, fmt: f3 }, { key: "macro-F1", label: "Macro-F1", right: true, fmt: f3 },
];

export default function DisclosureEvidence() {
  const selRows = (S.by_role as any[]).map((r) => ({ role: r.role, silent: r["does not"], states: r["states a salary"] })).sort((a, b) => a.states - b.states);
  return (
    <>
      <Block title="Which model reads disclosure best?"
        note={<><p><strong>The words carry most of the signal.</strong> The role alone gets F1 {f2(models.find((m) => m.model.includes("role only")).F1)}, posting attributes {f2(models.find((m) => m.model.startsWith("XGBoost")).F1)}, the description words {f2(best.F1)}.</p>
          <p><strong>Accuracy flatters.</strong> Saying "does not state" every time is right {pct0(base.accuracy)} of the time and finds nothing. F1 and recall for the postings that do state pay are the honest scores.</p>
          <p>Adding attributes to the words gains almost nothing, and a linear SVM is about as good as logistic regression. Naive Bayes and the neural network trail.</p></>}>
        <Fig title="F1 for postings that state a salary" sub="Five-fold cross-validation, grouped by company, on all role-matched postings. Cut-off taken from the scores of the other folds.">
          <PlotFigure label="F1 of seven disclosure models and a do-nothing baseline" minHeight={380} build={barsH({ data: models, label: "model", value: "F1", fmt: f2, domain: [0, 0.6], xLabel: "F1", marginLeft: 270, ticks: [0, 0.2, 0.4, 0.6], color: (d, t) => (d.model.startsWith("Say") ? t.ink3 : t.cat[0]) })} />
        </Fig>
        <DataDetails summary="Table: every metric for every model" rows={models} cols={[{ key: "model", label: "Model" }, ...metricCols]} />
      </Block>

      <Block title="Does the way the text is represented matter?"
        note={<><p>Not much. Every variant sits between F1 {f2(Math.min(...repr.map((r) => r.F1)))} and {f2(Math.max(...repr.map((r) => r.F1)))}, with two-word phrases the best (ROC-AUC {f3(repr.find((r) => r.variant.includes("bigrams"))["ROC-AUC"])}).</p>
          <p><strong>Leaving the salary figures in changes little</strong> (F1 {f2(repr.find((r) => r.variant.includes("left in"))!.F1)}), so the model is reading wording, not a number.</p>
          <p><strong>Length matters a lot.</strong> The first 500 characters give F1 {f2(len.find((r) => r.length.includes("500")).F1)} against {f2(len.find((r) => r.length === "full").F1)} for the whole description. The cues sit late in the text, in the boilerplate.</p></>}>
        <Fig title="Changing one thing at a time" sub="Logistic regression on the description words, F1 for postings that state a salary."><PlotFigure label="F1 for nine text representations" minHeight={400} build={barsH({ data: repr, label: "variant", value: "F1", fmt: f2, domain: [0, 0.6], marginLeft: 270, ticks: [0, 0.2, 0.4, 0.6] })} /></Fig>
        <Fig title="How much of the description the model reads" sub="The same model on the first 200, 500 or 1,000 characters, or all of it."><PlotFigure label="F1 by length of text read" minHeight={240} build={barsH({ data: len, label: "length", value: "F1", fmt: f2, domain: [0, 0.6], marginLeft: 200, ticks: [0, 0.2, 0.4, 0.6] })} /></Fig>
        <DataDetails summary="Table: the 80/20, 70/30, 60/40 and 50/50 splits" rows={D.split as any[]} cols={[{ key: "split", label: "Train/test" }, { key: "ROC-AUC", label: "ROC-AUC", right: true, fmt: f3 }, { key: "AUC sd", label: "sd", right: true, fmt: f3 }, { key: "average precision", label: "Average precision", right: true, fmt: f3 }, { key: "AP sd", label: "sd", right: true, fmt: f3 }]} />
      </Block>

      <Block title="Which words separate the two groups?"
        note={<><p>Scores are weighted log-odds with a prior (Monroe, Colaresi and Quinn 2008): the further from zero, the more a word or phrase belongs to one group.</p>
          <p><strong>Two kinds of signal.</strong> Marketing and advertising vocabulary leans toward stating pay. That is the role effect: Digital Marketing postings state pay most often. Boilerplate leans toward silence: "company website", "job posting", "disclaimer", "role details".</p>
          <p>Boilerplate points to agencies and large templated postings, which is consistent with disclosure being a habit of the employer more than a feature of the job.</p></>}>
        <Legend items={[{ color: "var(--c1)", label: "leans toward stating pay", shape: "bar" }, { color: "var(--c2)", label: "leans toward silence", shape: "bar" }]} />
        <Fig title="Words" sub="Nine on each side."><PlotFigure label="Words that lean toward stating pay or toward silence" minHeight={560} build={barsH({ data: wordsRows(W.uni_yes, W.uni_no), label: "term", value: "z", fmt: (v) => v.toFixed(0), domain: span(wordsRows(W.uni_yes, W.uni_no)), marginLeft: 120, color: (d, t) => (d.z >= 0 ? t.cat[0] : t.cat[1]), xLabel: "weighted log-odds score" })} /></Fig>
        <Fig title="Two-word phrases" sub="Nine on each side."><PlotFigure label="Phrases that lean toward stating pay or toward silence" minHeight={560} build={barsH({ data: wordsRows(W.bi_yes, W.bi_no), label: "term", value: "z", fmt: (v) => v.toFixed(0), domain: span(wordsRows(W.bi_yes, W.bi_no)), marginLeft: 170, color: (d, t) => (d.z >= 0 ? t.cat[0] : t.cat[1]), xLabel: "weighted log-odds score" })} /></Fig>
      </Block>

      <Block title="Is it the job, or the employer?"
        note={<><p><strong>It is largely the employer.</strong> {pct0(F.never_share_of_postings)} of postings come from companies that never state a salary in this data, and {pct0(F.disclosers_from_heavy_firms)} of the postings that do state one come from companies that do so in at least half of their postings.</p>
          <p>Among the {F.multi_n} companies with at least five postings, {pct0(F.multi_never)} never state pay and {pct0(F.multi_heavy)} state it most of the time. This matches Batra, Michaud and Mongey for the US: disclosure is concentrated in few firms.</p>
          <p>Roles differ too: Software Engineer postings state pay least, Digital Marketing most.</p></>}>
        <Fig title="Share of postings that state a salary, by role" sub={`${inr(D.n)} role-matched postings.`}><PlotFigure label="Share of postings stating a salary by role" minHeight={380} build={barsH({ data: byRole, label: "role", value: "share", fmt: (v) => pct(v, 1), domain: [0, 0.25], ref: D.base_rate, marginLeft: 190, ticks: [0, 0.05, 0.1, 0.15, 0.2, 0.25], tickFmt: (v) => `${Math.round(v * 100)}%`, xLabel: "dashed line: all postings" })} /></Fig>
      </Block>

      <Block title="What does silence do to the salary results?"
        note={<><p><strong>No clear difference inside a role.</strong> For every posting, a ridge model fitted on the postings that state pay estimates what the text points to. Weighted by role, employers that stay silent point to {Math.abs(S.adj_gap_pct).toFixed(1)}% {S.adj_gap_pct < 0 ? "lower" : "higher"} pay, with an interval from {S.ci[0].toFixed(1)}% to {S.ci[1] >= 0 ? "+" : ""}{S.ci[1].toFixed(1)}%, which includes zero.</p>
          <p>The overall median does differ (₹{S.overall["does not"].toFixed(1)} L silent, ₹{S.overall["states a salary"].toFixed(1)} L stating), but that comes from the role mix, not from the same job paying differently.</p>
          <p><strong>Limits.</strong> The pay estimate for silent postings is extrapolated from those that state pay. Weighting each stated salary by how unlikely it was to be stated moves role medians by a few percent up to about {Math.max(...(ipw.table as any[]).map((r) => r["shift %"])).toFixed(0)}%, but the effective sample falls to {Math.round(ipw.ess)} of {inr(ipw.n)} and it only corrects for what the text shows. Treat it as a bound on the size of the problem, not a correction.</p></>}>
        <Legend items={[{ color: "var(--c1)", label: "states a salary", shape: "dot" }, { color: "var(--c2)", label: "does not", shape: "dot" }]} />
        <Fig title="Pay the description points to, median by role" sub="In lakh per year. Joined dots show how far apart the two groups are inside each role."><PlotFigure label="Median pay the text points to for postings that state pay and those that do not" minHeight={380} build={dumbbell({ data: selRows, label: "role", a: "silent", b: "states", aName: "does not state pay", bName: "states pay", fmt: (v) => `₹${v.toFixed(1)} L`, xLabel: "lakh per year", marginLeft: 190 })} /></Fig>
        <DataDetails summary="Table: role medians before and after weighting" rows={ipw.table} cols={[{ key: "role", label: "Role" }, { key: "n", label: "Salaried postings", right: true }, { key: "raw median", label: "Raw median, L", right: true, fmt: f2 }, { key: "weighted median", label: "Weighted median, L", right: true, fmt: f2 }, { key: "shift %", label: "Shift, %", right: true, fmt: (v) => v.toFixed(1) }]} />
      </Block>
    </>
  );
}
