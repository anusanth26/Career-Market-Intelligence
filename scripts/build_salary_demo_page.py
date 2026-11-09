"""Build ui/salary_demo.html: a self-contained page that shows a job posting and the model's salary estimate.

Input : ui/salary_demo_data.json (written by section 9 of notebooks/career_market_intelligence.ipynb)
Output: ui/salary_demo.html (data embedded, no server and no network needed)
Usage : python scripts/build_salary_demo_page.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.load(open(ROOT / "ui/salary_demo_data.json"))
assert data["postings"] and all(len(p["whatif"]) == len(data["grid"]) for p in data["postings"])

TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Salary Estimator Demo</title>
<style>
:root{--bg:#eef1f4;--card:#fff;--ink:#1b2a3a;--muted:#5b6b7b;--line:#d5dbe2;--accent:#1f5fbf;--accent-soft:#dbe7f8;--band90:#c9d9f1;--band80:#7fa6dd;--good:#1f8a70;--warn:#c4631a;--chip:#eef1f4}
@media (prefers-color-scheme:dark){:root{--bg:#10171f;--card:#18222d;--ink:#e6ecf2;--muted:#9aa9b8;--line:#2b3947;--accent:#6ea2ee;--accent-soft:#1f3552;--band90:#26405f;--band80:#3f6fb0;--good:#4fc4a3;--warn:#f0a063;--chip:#223140}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{padding:18px 16px 6px;max-width:1400px;margin:0 auto}
h1{font-size:1.4rem;margin:0}
.sub{color:var(--muted);margin:2px 0 0}
main{display:grid;grid-template-columns:280px minmax(0,1fr) 380px;gap:14px;max-width:1400px;margin:0 auto;padding:12px 16px 24px}
@media (max-width:1100px){main{grid-template-columns:minmax(0,1fr)}}
.card{min-width:0;overflow-wrap:anywhere}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.card h2{font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 10px;font-weight:600}
#list{display:flex;flex-direction:column;gap:6px;padding:0;margin:0;list-style:none}
#list button{width:100%;text-align:left;background:transparent;border:1px solid transparent;border-radius:8px;padding:9px 10px;cursor:pointer;color:inherit;font:inherit}
#list button:hover{background:var(--chip)}
#list button[aria-current=true]{background:var(--accent-soft);border-color:var(--accent)}
#list b{display:block;font-weight:600}
#list small{color:var(--muted)}
.post h3{font-size:1.25rem;margin:0}
.meta{color:var(--muted);margin:2px 0 10px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 12px}
.chip{background:var(--chip);border-radius:999px;padding:2px 10px;font-size:.82rem}
.desc{white-space:pre-line;color:var(--ink);border-top:1px solid var(--line);padding-top:12px;margin:0;max-height:420px;overflow:auto}
.note{color:var(--muted);font-size:.85rem}
.big{font-size:2.5rem;font-weight:700;line-height:1.1;font-variant-numeric:tabular-nums}
.big small{font-size:1rem;font-weight:500;color:var(--muted)}
.range{margin:2px 0 12px;color:var(--muted)}
.range b{color:var(--ink)}
svg{width:100%;height:auto;display:block}
.axis{fill:var(--muted);font-size:10px}
button.primary{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:9px 14px;font:inherit;cursor:pointer}
button.primary:focus-visible,#list button:focus-visible,input[type=range]:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
#verdict{margin-top:10px;padding:10px 12px;border-radius:8px;background:var(--chip)}
.ok{color:var(--good);font-weight:600}.no{color:var(--warn);font-weight:600}
label{display:block;font-weight:600;margin:14px 0 4px}
input[type=range]{width:100%;accent-color:var(--accent)}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}
.stat{background:var(--chip);border-radius:8px;padding:8px 10px}.stat b{display:block;font-size:1.15rem}.stat span{color:var(--muted);font-size:.8rem}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:.8rem;color:var(--muted);margin-top:4px}
.dot{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}
footer{max-width:1400px;margin:0 auto;padding:0 16px 28px;color:var(--muted);font-size:.85rem}
</style>
</head>
<body>
<header>
  <h1>Salary Estimator</h1>
  <p class="sub">A job posting goes in. The trained model returns a salary estimate and a range. These ten postings come from employers the model never saw in training.</p>
</header>
<main>
  <section class="card" aria-label="Job postings"><h2>Job postings</h2><ul id="list"></ul></section>
  <section class="card post" aria-label="Job posting" id="post"></section>
  <section class="card" aria-label="Model estimate" id="est"></section>
</main>
<footer id="foot"></footer>
<script>
const DATA = __DATA__;
const P = DATA.postings, S = DATA.summary, GRID = DATA.grid;
const L = v => v >= 1e7 ? (v/1e7).toFixed(2) + " Cr" : (v/1e5).toFixed(v < 1e6 ? 1 : 1) + " L";
const rs = v => "₹" + L(v);
const X0 = Math.log(2e5), X1 = Math.log(8e6);
const px = (v, w) => 12 + (w - 24) * (Math.log(Math.min(Math.max(v, 2e5), 8e6)) - X0) / (X1 - X0);
let cur = 0, revealed = false, exp = 0;

function bar(lo90, lo, est, hi, hi90, stated) {
  const W = 340, H = 100, y = 34;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Estimate ${rs(est)}, 80 percent range ${rs(lo)} to ${rs(hi)}">`;
  for (const [v, t] of [[2e5, "2L"], [5e5, "5L"], [1e6, "10L"], [2.5e6, "25L"], [5e6, "50L"]]) s += `<line x1="${px(v, W)}" x2="${px(v, W)}" y1="${y - 8}" y2="${y + 26}" stroke="var(--line)"/><text class="axis" x="${px(v, W)}" y="${y + 40}" text-anchor="middle">${t}</text>`;
  if (lo90) s += `<rect x="${px(lo90, W)}" y="${y}" width="${px(hi90, W) - px(lo90, W)}" height="18" rx="4" fill="var(--band90)"/>`;
  s += `<rect x="${px(lo, W)}" y="${y}" width="${px(hi, W) - px(lo, W)}" height="18" rx="4" fill="var(--band80)"/>`;
  s += `<line x1="${px(est, W)}" x2="${px(est, W)}" y1="${y - 6}" y2="${y + 24}" stroke="var(--ink)" stroke-width="3"/>`;
  s += `<text class="axis" x="${px(est, W)}" y="${y - 10}" text-anchor="middle" style="fill:var(--ink);font-weight:700">estimate</text>`;
  if (stated) {
    s += `<rect x="${px(stated[0], W)}" y="${y + 21}" width="${Math.max(2, px(stated[1], W) - px(stated[0], W))}" height="5" rx="2" fill="var(--warn)"/>`;
    s += `<text class="axis" x="${(px(stated[0], W) + px(stated[1], W)) / 2}" y="${y + 56}" text-anchor="middle" style="fill:var(--warn);font-weight:700">stated by employer</text>`;
  }
  return s + "</svg>";
}

function curve(p) {
  const W = 340, H = 120, pad = 26, n = GRID.length;
  const xs = i => pad + (W - pad - 8) * i / (n - 1);
  const vals = p.whatif.flat(), mn = Math.min(...vals), mx = Math.max(...vals);
  const ys = v => H - 20 - (H - 34) * (Math.log(v) - Math.log(mn)) / (Math.log(mx) - Math.log(mn));
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Estimate against years of experience">`;
  const band = p.whatif.map((w, i) => `${xs(i)},${ys(w[2])}`).join(" ") + " " + p.whatif.map((w, i) => `${xs(n - 1 - i)},${ys(p.whatif[n - 1 - i][0])}`).join(" ");
  s += `<polygon points="${band}" fill="var(--band90)" opacity=".7"/>`;
  s += `<polyline points="${p.whatif.map((w, i) => `${xs(i)},${ys(w[1])}`).join(" ")}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>`;
  s += `<line x1="${xs(exp)}" x2="${xs(exp)}" y1="8" y2="${H - 20}" stroke="var(--ink)" stroke-dasharray="3 3"/>`;
  s += `<circle cx="${xs(exp)}" cy="${ys(p.whatif[exp][1])}" r="4.5" fill="var(--ink)"/>`;
  for (const t of [0, 5, 10, 15, 20]) s += `<text class="axis" x="${xs(t)}" y="${H - 6}" text-anchor="middle">${t}</text>`;
  s += `<text class="axis" x="${pad}" y="10">${rs(mx)}</text><text class="axis" x="${pad}" y="${H - 22}">${rs(mn)}</text>`;
  return s + "</svg>";
}

function renderList() {
  document.getElementById("list").innerHTML = P.map((p, i) => `<li><button data-i="${i}" ${i === cur ? 'aria-current="true"' : ""}><b>${p.title}</b><small>${p.company} · ${p.role}</small></button></li>`).join("");
  document.querySelectorAll("#list button").forEach(b => b.onclick = () => { cur = +b.dataset.i; revealed = false; exp = Math.min(20, Math.round(P[cur].exp_min)); render(); });
}

function render() {
  const p = P[cur];
  renderList();
  document.getElementById("post").innerHTML = `<h2>Job posting</h2><h3>${p.title}</h3>
    <p class="meta">${p.company} · ${p.location} · ${p.work_mode} · ${p.experience}</p>
    <div class="chips">${p.skills.map(s => `<span class="chip">${s}</span>`).join("")}</div>
    <p class="desc">${p.description.replace(/</g, "&lt;")}${p.description.length >= 899 ? "…" : ""}</p>
    <p class="note">Industry: ${p.industry}. Role used by the model (from the title): ${p.role}.</p>`;
  const w = p.whatif[exp], atStart = exp === Math.min(20, Math.round(p.exp_min));
  const [lo, est, hi] = atStart ? [p.low80, p.est, p.high80] : w;
  const mid = (p.stated_min + p.stated_max) / 2, inside = mid >= lo && mid <= hi;
  document.getElementById("est").innerHTML = `<h2>Model estimate</h2>
    <div class="big">${rs(est)} <small>a year</small></div>
    <p class="range">80% range <b>${rs(lo)} – ${rs(hi)}</b></p>
    ${bar(atStart ? p.low90 : null, lo, est, hi, atStart ? p.high90 : null, revealed ? [p.stated_min, p.stated_max] : null)}
    <div class="legend"><span><i class="dot" style="background:var(--band80)"></i>80% range</span>${atStart ? '<span><i class="dot" style="background:var(--band90)"></i>90% range</span>' : ""}</div>
    ${revealed ? `<div id="verdict">Employer states <b>${rs(p.stated_min)} – ${rs(p.stated_max)}</b>. The midpoint is <span class="${inside ? "ok" : "no"}">${inside ? "inside" : "outside"}</span> our 80% range; the estimate is ${Math.round(Math.abs(est / mid - 1) * 100)}% ${est >= mid ? "above" : "below"} it.</div>`
      : `<p style="margin-top:12px"><button class="primary" id="rev">Compare with the stated salary</button></p>`}
    <label for="exp">What if the experience asked for changes? <b id="expv">${exp} years</b></label>
    <input id="exp" type="range" min="0" max="20" step="1" value="${exp}">
    ${curve(p)}
    <p class="note">Only the experience requirement changes; the text and all other fields stay fixed. This shows how the model reads the posting, not what an employer would pay.</p>`;
  const r = document.getElementById("rev"); if (r) r.onclick = () => { revealed = true; render(); };
  const sl = document.getElementById("exp"); sl.oninput = () => { exp = +sl.value; render(); document.getElementById("exp").focus(); };
}
const h = location.hash.replace('#', '').split(',');
if (h[0] !== '' && !isNaN(+h[0]) && P[+h[0]]) cur = +h[0];
revealed = h.includes('reveal');
exp = Math.min(20, Math.round(P[cur].exp_min));
document.getElementById("foot").innerHTML = `<b>How the estimate is made.</b> A gradient-boosted quantile model reads the posting (experience, role from the title, seniority, city, work mode, industry, skills and the description text) and predicts the median salary. A conformal correction (Romano, Patterson and Candès, 2019) turns its quantile bands into a range meant to hold the true salary 80% of the time. Trained on ${S.n_train.toLocaleString()} Naukri postings that state pay, tested on ${S.n_test} postings from unseen employers: R² ${S.test_r2.toFixed(2)} on that test set (${S.cv_r2.toFixed(2)} in cross-validation), average error ₹${(S.test_mae/1e5).toFixed(1)} lakh against ₹${(S.role_median_mae/1e5).toFixed(1)} lakh for a role-median guess, ${(S.coverage80*100).toFixed(0)}% of true salaries inside the 80% range. Coverage is lower for Software Engineer, Data Scientist and Product Manager. Salaries are the ranges employers publish; only about 12% of postings state one. This page shows precomputed model output; it does not call a live model.`;
render();
</script>
</body>
</html>
'''
out = ROOT / "ui/salary_demo.html"
out.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), encoding="utf-8")
print("Wrote", out, f"({out.stat().st_size/1024:.0f} KB)")
