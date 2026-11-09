"use client";
import Estimator from "@/components/Estimator";
import KpiBar from "@/components/KpiBar";
import Panel from "@/components/Panel";
import { AloneChart, CovExp, CovRole, DropChart, ErrChart, ImpChart, ModelErr, ModelR2 } from "@/components/PayCharts";
import { Benchmark, CheckOffer } from "@/components/Scenarios";
import { lk, f3, pct0 } from "@/lib/format";
import demo from "@/data/demo.json";
import S from "@/data/salary.json";

export default function Pay() {
  const test = (S.test as any[]).find((t) => t.model.startsWith("XGBoost")), roleTest = (S.test as any[]).find((t) => t.model === "Role median");
  const c80 = (S.cqr as any[]).find((c) => c.setting === "CQR, 80% target");
  return (
    <>
      <h1 className="sr-only">Pay: estimate a salary and see how far to trust it</h1>
      <KpiBar items={[
        { label: "R² on unseen employers", value: f3(test.R2_log), sub: `${f3(roleTest.R2_log)} for guessing the role's median` },
        { label: "Typical error", value: lk(test.MAE_INR / 1e5), sub: `${lk(roleTest.MAE_INR / 1e5)} for the role median` },
        { label: "Estimate within 30% of stated", value: pct0(test.Within30), sub: `${pct0(roleTest.Within30)} for the role median` },
        { label: "80% range held the stated pay", value: pct0(c80.coverage), sub: `target 80%, ${S.n_test} test postings` },
      ]} />
      <div className="grid">
        <Panel span={12} title="Try the model"
          info={<><p>The estimate comes from a tuned XGBoost model on role, experience, seniority, city, work mode, industry, skills and a compressed summary of the description. The range is conformal: calibrated on separate postings so it holds about 80% of the time.</p><p>Ten held-out postings are shown, one per role. The profile calculator uses only role, seniority, city, work mode and years, so it is weaker than the main model.</p></>}
          tabs={[
            { id: "est", label: "Estimate a posting", node: <Estimator demo={demo as any} /> },
            { id: "offer", label: "Check an offer", node: <CheckOffer /> },
            { id: "bench", label: "Benchmark a role", node: <Benchmark /> },
          ]} />
        <Panel span={6} title="Which model predicts best" sub="Five-fold cross-validation, grouped by employer"
          info={<><p>Four models and two baselines that learn nothing, on identical features and folds. Stacking and XGBoost are tied within the fold-to-fold spread, and Ridge is only about 0.03 behind, so most of the signal is additive.</p><p>Tuning XGBoost changed R² from 0.695 to 0.696, so the limit is the information in the postings.</p></>}
          tabs={[{ id: "r2", label: "Accuracy (R²)", node: <ModelR2 /> }, { id: "mae", label: "Error in lakh", node: <ModelErr /> }]} />
        <Panel span={6} title="What the model relies on" sub="Experience first. Most other inputs overlap with it and with the description"
          info={<><p><strong>Read the first two tabs with care.</strong> They show what the model loses when one group is taken away. If another input already carries the same information, the loss is small even though the input matters.</p><p>That is the case here: the description names the role with about 90% accuracy, seniority in the title moves with experience, and company, location and work mode overlap with role and industry. So role, seniority and the rest look small when removed.</p><p>The third tab shows each field on its own (adjusted for how many levels it has): role alone explains about 40% of the variation in log salary, experience about 50%. Together with the description they explain about 70%, because they overlap.</p></>}
          tabs={[{ id: "drop", label: "Inputs removed", node: <DropChart /> }, { id: "imp", label: "Inputs shuffled", node: <ImpChart /> }, { id: "alone", label: "Each field alone", node: <AloneChart /> }]} />
        <Panel span={6} title="How far to trust the range" sub="Share of test postings whose stated pay fell inside the 80% range"
          info={<><p>The overall figure is {pct0(c80.coverage)}, but it is not the same for every kind of posting. Orange dots are below the 80% target. Small roles have few test postings, so their dots are noisy.</p></>}
          tabs={[{ id: "role", label: "By role", node: <CovRole /> }, { id: "exp", label: "By experience", node: <CovExp /> }]} />
        <Panel span={6} title="Where the model errs" sub="Average error by role on the test postings"
          info={<><p>Joined dots show how much the model improves on guessing each role's median. It helps most where pay varies most inside a role.</p></>}>
          <ErrChart />
        </Panel>
      </div>
    </>
  );
}
