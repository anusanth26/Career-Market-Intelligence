# Career Market Intelligence dashboard

A Next.js (App Router, TypeScript) front end for the project. It shows what the notebooks found: the salary model and its ranges, skills and topics from the postings, role classification, search-interest trends, and recommendations.

## Run it

```bash
cd frontend
npm install
npm run dev      # http://localhost:3100
# or: npm run build && npm start
```

## Where the numbers come from

Every figure is read from a JSON file in `src/data/`. Each file is written by the last cell of a notebook, so the dashboard and the notebooks cannot disagree.

| File | Written by |
|---|---|
| `salary.json`, `demo.json`, `dataset.json`, `calculator.json` | `notebooks/career_market_intelligence.ipynb` |
| `textmining.json`, `roles.json`, `disclosure.json`, `switch.json`, `network.json` | `notebooks/text_mining.ipynb` |
| `trends.json` | `notebooks/method2_time_series.ipynb` |
| `gap.json` | `notebooks/combined_insight.ipynb` |

Re-run a notebook and reload the page to refresh its numbers. The JSON files hold aggregates, ten example postings and, in `dataset.json`, the 1,358 modelling rows (title, company, role, city, first skills, stated salary, the model's range for test rows). They do not hold job descriptions. `disclosure.json` also holds the first 1,800 characters of the description of ten postings, shown on `/disclosure`. Because titles, companies and description excerpts are scraped, do not deploy this frontend publicly. The raw scraped postings stay in `data/raw/naukri_apify/`, which is excluded from version control.

## Layout

A top bar with five sections, a filter strip (role, city, experience asked, work mode) that carries across them, and a grid of linked panels on each page. Tabs inside a panel swap the view without scrolling; the "?" button on a panel holds the method note. Clicking a row in "Who is paid what" sets that filter. The filter is also kept in the address, so a view can be shared.

- `/` **Overview**: KPIs for the selection, pay by role, experience and city, the distribution, the skills employers tag, and where to go next
- `/pay` **Pay**: estimate a posting, check an offer, benchmark a role; which model is best, what it relies on, how far to trust the range, where it errs
- `/skills` **Skills**: demand, search interest and pay in one map, pay associations, the skill network, role by skill, a one-skill detail panel, and a skill planner
- `/careers` **Careers**: which skills move you toward another role (a role classifier run backwards, limited to skills the target role really asks for), how long each move is, bridge skills, and how well text identifies a role
- `/data` **Data and method**: the dataset with the model's results on any slice, who states the pay, method and limits, and links to the full write-ups
- `/reports/...` the long write-ups (pay, skills, roles, trends, recommendations, method), kept as articles for depth

Filters apply to the 1,358 salaried postings (pay charts, KPIs, the dataset). Panels computed in the notebooks, such as skill premiums, topics and trends, cannot be re-cut by city or experience and carry a "not filtered" tag.

## Notes

- Charts use Observable Plot, the network layout uses d3-force, the skill table uses TanStack Table.
- Colours are flat. The categorical palette (five hues) and the blue sequential ramp were checked for colour-blind separation and contrast.
- The profile calculator (`src/lib/calc.ts`) is a ridge model on role, seniority, city, work mode and years, so it is weaker than the main model. Its cross-validated error and range coverage are shown beside every result.
- Motion is short and answers an action (page change, a value that updates, a chart redraw). It is switched off for viewers who prefer reduced motion.
- Shared state lives in `src/lib/filters.tsx`; the panel, KPI bar and ranked-list pieces are in `src/components/` (`Panel`, `KpiBar`, `RankList`).
