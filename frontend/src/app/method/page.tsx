import S from "@/data/salary.json";
import PageNav from "@/components/PageNav";
import { inr } from "@/lib/format";

export const metadata = { title: "Data and method" };

export default function MethodPage() {
  const f = S.funnel as { label: string; n: number }[];
  return (
    <>
      <h1>Where the numbers come from, and what they cannot tell you</h1>
      <p className="lede">Every figure in this dashboard is read from a file that a notebook in this project wrote. Nothing is typed in by hand.</p>
      <PageNav />

      <section className="section">
        <h2>The postings</h2>
        <p>{inr(f[0].n)} job postings were collected from Naukri with an Apify scraper (thirdwatch/naukri-jobs-scraper), across ten roles and many Indian cities. Each posting has the full description, not a short snippet, the employer's skill tags, the experience asked for, the city and, for some, a salary range.</p>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Step</th><th className="r">Postings</th></tr></thead>
            <tbody>{f.map((r) => <tr key={r.label}><td>{r.label}</td><td className="r">{inr(r.n)}</td></tr>)}</tbody>
          </table>
        </div>
        <p className="small" style={{ marginTop: 12 }}>The role comes from the posting title only, using the rules in <span className="ui">config/roles.json</span>. A title that matches two roles, an exclusion rule or no role is dropped. A salary is used only if it is stated as a yearly range in rupees, does not start at 0, has a midpoint of at least ₹100,000, and is not a repeat of the same title, company and range.</p>
      </section>

      <section className="section">
        <h2>The three kinds of analytics here</h2>
        <p>Descriptive: what postings ask for and pay (Skills, Roles, Trends, Explorer, The dataset). Predictive: what a profile should earn, with an honest 80% range (Estimate, Pay, Scenarios). Prescriptive: what to do about it, for a job seeker, a recruiter or a student (Scenarios, Recommendations). The profile calculator behind Scenarios uses only role, seniority, city, work mode and years, so it is weaker than the main model.</p>
        <h2>The four notebooks</h2>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Notebook</th><th>What it does</th><th>Feeds</th></tr></thead>
            <tbody>
              <tr><td>career_market_intelligence</td><td>Salary model: twelve models compared, ablations, a range with guaranteed coverage, errors by role</td><td>Pay, Estimate a posting</td></tr>
              <tr><td>text_mining</td><td>Skills, topics, clusters, skill bundles, pay associations of skills, classifying a role from its description</td><td>Skills, Roles</td></tr>
              <tr><td>method2_time_series</td><td>Google Trends for 20 skills: trend labels, forecasts, intervals, a test of the AI-assistant explanation</td><td>Trends</td></tr>
              <tr><td>combined_insight</td><td>Joins demand, search interest and pay for each skill</td><td>Trends, Recommendations</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>How to read the measures</h2>
        <div className="tablewrap">
          <table>
            <thead><tr><th>Term</th><th>Meaning here</th></tr></thead>
            <tbody>
              <tr><td>Lakh</td><td>100,000 rupees. Salaries are per year.</td></tr>
              <tr><td>Estimate and range</td><td>The estimate is the median of a quantile model. The 80% range is that model's 10th to 90th percentile band, widened by a conformal correction so that it holds the stated salary about 80% of the time on postings it has not seen.</td></tr>
              <tr><td>R²</td><td>Share of the variation in log salary the model explains. 0 is no better than guessing the median, 1 is perfect.</td></tr>
              <tr><td>Mean error</td><td>Average absolute difference in rupees between the estimate and the stated midpoint.</td></tr>
              <tr><td>Within 30%</td><td>Share of postings whose estimate is within 30% of the stated salary.</td></tr>
              <tr><td>Grouped by employer</td><td>No company appears in both the training and the test part, so the model cannot learn an employer's habits and look better than it is.</td></tr>
              <tr><td>Macro-F1</td><td>Average of the per-role F1 scores, so small roles count as much as large ones. Used for role classification.</td></tr>
              <tr><td>Pay association</td><td>The pay difference, in percent, between postings that ask for a skill and comparable postings that do not, at the same experience, role, seniority, city, work mode and industry. Not a cause.</td></tr>
              <tr><td>False-discovery control</td><td>A correction for testing many skills at once, so that a few lucky results are not reported as findings.</td></tr>
              <tr><td>Conformal coverage</td><td>The share of true outcomes that fall inside an interval built from past errors. The target is the stated level, here 80%.</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>What these results cannot tell you</h2>
        <ul style={{ maxWidth: "66ch", paddingLeft: 20 }}>
          <li>Only about 12% of postings state a salary. The pay results describe postings that disclose pay.</li>
          <li>All postings are one snapshot from one job board. Nothing here shows how pay or demand changes over time.</li>
          <li>Roles come from titles, so some postings are mislabelled and some classification errors are label noise.</li>
          <li>Search interest from Google Trends measures attention, not hiring. The two are shown side by side, with no claim that one leads the other.</li>
          <li>Pay associations of skills are not causes. A skill can stand in for a better employer or a harder job.</li>
          <li>Several groups are small (11 to 64 test postings per role). The notebooks flag where a result is within noise.</li>
          <li>The postings were scraped. Naukri's terms may restrict that, so the postings themselves are not redistributed and the raw files are excluded from version control.</li>
        </ul>
      </section>

      <section className="section">
        <h2>Rebuild it</h2>
        <p className="small" style={{ maxWidth: "70ch" }}>Run the four notebooks in <span className="ui">notebooks/</span>. Each ends with a cell that writes JSON into <span className="ui">frontend/src/data/</span>. Then, in <span className="ui">frontend/</span>, run <span className="ui">npm install</span> and <span className="ui">npm run dev</span> and open port 3100.</p>
      </section>
    </>
  );
}
