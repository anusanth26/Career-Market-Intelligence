"use client";
import KpiBar from "@/components/KpiBar";
import Panel from "@/components/Panel";
import { SwitchAccuracy, SwitchBridge, SwitchHeat } from "@/components/SwitchEvidence";
import SwitchDemo from "@/components/SwitchDemo";
import { METRICS, OVERALL } from "@/lib/switch";
import { f2, pct0 } from "@/lib/format";

export default function Careers() {
  return (
    <>
      <h1 className="sr-only">Careers: skills that move you toward another role</h1>
      <KpiBar items={[
        { label: "Role read from skills alone", value: pct0(METRICS.accuracy), sub: `macro-F1 ${f2(METRICS.macro_f1)} on ${METRICS.n_test.toLocaleString("en-IN")} unseen postings` },
        { label: "Moves reached in 5 added skills", value: pct0(OVERALL.flip_5), sub: `${pct0(OVERALL.naive_flip_5)} for adding the target's common skills` },
        { label: "Moves reached in 10", value: pct0(OVERALL.flip_10), sub: `${pct0(OVERALL.naive_flip_10)} for the simple baseline` },
        { label: "Typical move", value: `${Math.round(OVERALL.median_added)} skills`, sub: "median added" },
      ]} />
      <div className="grid">
        <Panel span={12} title="Career switch planner" sub="Pick the role you want to move toward and see the fewest skills to add so a role-fit model reads you as that role"
          info={<><p>The classifier reads only which of 200 skills a posting asks for. Starting from a role's typical skills, or ticks of your own, it adds the skill that most raises the target's lead over its closest rival, one at a time, until the target is the top role.</p><p>Only feasible suggestions are made: skills that at least 10% of the target role's postings ask for, and never a role name such as "data engineer". Without that limit the search picks rare skills with large weights that flip the classifier but are not what the role asks for.</p><p>This is actionable recourse for a linear classifier (Ustun, Spangher and Liu 2019). It describes how job-ad wording changes the reading, not whether a person would be hired.</p></>}>
          <SwitchDemo />
        </Panel>
        <Panel span={12} title="The evidence behind it"
          tabs={[
            { id: "heat", label: "How long is each move", node: <SwitchHeat /> },
            { id: "bridge", label: "Bridge skills", node: <SwitchBridge /> },
            { id: "acc", label: "Can the text tell the role?", node: <SwitchAccuracy /> },
          ]} />
      </div>
    </>
  );
}
