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
| `textmining.json`, `roles.json`, `disclosure.json`, `network.json` | `notebooks/text_mining.ipynb` |
| `trends.json` | `notebooks/method2_time_series.ipynb` |
| `gap.json` | `notebooks/combined_insight.ipynb` |

Re-run a notebook and reload the page to refresh its numbers. The JSON files hold aggregates, ten example postings and, in `dataset.json`, the 1,358 modelling rows (title, company, role, city, first skills, stated salary, the model's range for test rows). They do not hold job descriptions. `disclosure.json` also holds the first 1,800 characters of the description of ten postings, shown on `/disclosure`. Because titles, companies and description excerpts are scraped, do not deploy this frontend publicly. The raw scraped postings stay in `data/raw/naukri_apify/`, which is excluded from version control.

## Pages

In the order of the sidebar: the answer, the evidence behind it, the data, how to use it, then the text-mining analyses and supporting tools.

- `/` estimate a posting: ten held-out postings, the model's estimate and range, and the stated salary on request
- `/pay` salary model, ablations, range coverage, errors by role
- `/data` the final dataset with filters, a sortable table and the model's results on any selection
- `/scenarios` three live situations (job seeker checks an offer, recruiter benchmarks a role, student plans skills) driven by a profile calculator
- `/recommendations` what to do with the findings, with the evidence and how firm each one is
- `/skills` skills by role, tags against text, topics, skill bundles, pay associations
- `/disclosure` a classifier for whether a posting states its salary (trained on all role-matched postings): pick or paste a posting, models and ablations, the words that separate disclosing from silent postings, firm concentration, and a selection check on the salary results
- `/roles` role classification and its stress tests
- `/trends` a skill comparison picker, Google Trends for 20 skills, the AI-assistant test, forecast intervals, demand against interest
- `/explore` one-role filter and a sortable skill table
- `/method` data, notebooks, definitions and limits

## Notes

- Charts use Observable Plot, the network layout uses d3-force, the skill table uses TanStack Table.
- Colours are flat. The categorical palette (five hues) and the blue sequential ramp were checked for colour-blind separation and contrast.
- The profile calculator (`src/lib/calc.ts`) is a ridge model on role, seniority, city, work mode and years, so it is weaker than the main model. Its cross-validated error and range coverage are shown beside every result.
- Motion is short and answers an action (page change, a value that updates, a chart redraw). It is switched off for viewers who prefer reduced motion.
