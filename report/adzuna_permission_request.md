# DRAFT: Request for Written Academic Permission (Adzuna API)

**Not sent. Permission has NOT been obtained.** Fill the bracketed fields, review, and send from a team member's own email. The only address I found on the official terms page is info@adzuna.com (it is listed for termination notices); the developer portal may have a better channel.

---

**To:** info@adzuna.com
**Subject:** Written permission request: college capstone (India job-market analysis), Adzuna API app id [APP ID]

Hello,

We are students at [COLLEGE NAME], working on a college capstone project (course: [COURSE / PROGRAMME], supervised by [INSTRUCTOR NAME AND EMAIL]). It is an academic, non-commercial project. We are using the Adzuna API (India, `in`) and would like your written permission to continue and to publish aggregated results, because your terms describe a 14-day trial and say further use needs written consent.

**What we are doing.** We analyse India job-posting demand for ten roles in technology and data, business, and design, to show job seekers which skills employers ask for. We use the Adzuna search endpoint (postings from the last 90 days) and combine it with Google Trends search-interest data. We do not build a job-search site and we do not display individual job listings.

**Expected usage.**
- One validation snapshot has already been collected (about [640] calls during initial testing).
- Planned: three weekly refreshes of postings created in the last 7 days (about 60–75 calls each) and up to two skill-count snapshots (about 300 calls each, spread over two days).
- Total under 1,000 calls in the month, paced below 25 per minute, and inside your published limits of 250 per day, 1,000 per week and 2,500 per month.
- Duration: about [ONE MONTH, from [START DATE] to [END DATE]].

**Data handling.**
- Raw API responses will **not** be publicly redistributed. They are kept locally and in a private, access-controlled repository, and shared only with our team and course instructors for reproducibility and grading.
- Dashboard and report outputs will be **aggregated** (counts, shares, medians per role and skill), not individual postings.
- All published results will acknowledge Adzuna as the source ("The Adzuna API", linking to adzuna.co.uk), or the wording you prefer.
- We need to retain the collected data until the project is graded ([DATE]) for reproducibility and evaluation, and will delete it afterwards if you ask.

**What we are asking.**
1. Is our project treated as "personal research" or as academic-organisation use under the trial?
2. May we continue the collection described above beyond the 14-day trial?
3. May we use the data in aggregate form for our analysis, report and course dashboard?
4. May we store raw responses locally and in a private repository, and share them privately with instructors?
5. Please confirm the rate limits and whether the week and month are rolling or calendar periods.
6. Could you point us to the reference for the parameters `title_only`, `what_phrase`, `max_days_old` and `sort_by`, and tell us whether `what` searches the full description?

[OPTIONAL, recommended for transparency: During initial validation on [DATE] we made about [640] calls in one day, above the 250 per day limit. No rate-limit errors were returned, but we have since added pacing and a daily call budget, and we will stay inside your limits in future.]

Thank you for your time. We would be grateful for a reply in writing.

Kind regards,
[NAME], [ROLE / ROLL NUMBER]
[TEAM MEMBERS]
[COLLEGE, EMAIL, PHONE]

---

**Checklist before sending:** confirm the instructor agrees; remove or keep the optional disclosure paragraph (the team's decision); do not include the API key; keep a copy of the sent message and the reply.
