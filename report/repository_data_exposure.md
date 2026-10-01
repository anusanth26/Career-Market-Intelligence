# Repository Data-Exposure Audit

**Date:** 2026-09-30. Read-only audit; **nothing was deleted, rewritten or pushed.** Script and raw result: `data/raw/ml_data_feasibility/compliance_audit.py` / `compliance_audit.json`. Credential values were never printed or stored; results are booleans and counts only.

## 1. Credentials

| Check | Result |
|---|---|
| `.env` exists | Yes (holds the current API key and app id) |
| `.env` git-ignored | **Yes** (`.gitignore` line 1) |
| `.env` currently tracked | No |
| `.env` ever committed (any branch) | **No** |
| Current API key found in any working-tree file (excluding `.env`) | **No** |
| Current API key found in any tracked file at HEAD | **No** |
| Current API key in any blob reachable from `origin/main` or `origin/cleaning-preprocessing-eda` | **No** (0 files each) |
| Commits on any branch that ever add or remove the key text | **0** |
| Hard-coded key-like assignments in tracked code | **0** |
| Current **app id** in the working tree | Yes, in 87 **untracked** run files, as the `utm_source` value inside Adzuna's `redirect_url` (an identifier Adzuna embeds, not a secret key) |
| Current app id in tracked files or history | No |
| A **different** app id in committed data | Yes: 1 id, in the redirect URLs of the committed raw files (the teammate's original account) |

**Remediation for credentials:** none required for the repository. **Rotate the API key anyway**, because it was pasted into this conversation (which is a copy outside your control): create a new key in the Adzuna developer dashboard, delete the old one, and update `.env`. Nothing suggests the key was used by anyone else; this is precautionary.

## 2. Raw and derived Adzuna data in Git

| Location | Files | Size | Status |
|---|---|---:|---|
| **Tracked at HEAD and on `origin/main`** | `data/raw/adzuna/adzuna_business_analyst_2026-09-29.json`, `…_data_analyst_…`, `…_digital_marketing_…`, `…_software_engineer_…`, `pull_log_2026-09-29.json` | about 3.7 MB (926,396 / 911,807 / 960,742 / 935,021 / 186 bytes) | Raw API records (2,500 postings, including descriptions and redirect URLs) |
| **On `origin/main` and `origin/cleaning-preprocessing-eda` only (not in my local checkout, which is 14 commits behind)** | `data/cleaned/postings_text.csv` | 4.9 MB, 2,500 rows | Teammate's derived file: `description_original`, cleaned and lemmatised description text for the same 2,500 postings |
| **History** | 5 commits (2026-09-29, author anusanth26) added the raw files and pull log; the cleaned file came in the teammate's commits | – | Present in history on both remote-tracking branches |
| **Untracked, not ignored** (local only so far) | `data/raw/adzuna/runs/` (about 41 MB), `data/raw/adzuna/coverage_2026-09-29.json`, `data/raw/trends/` | 41.2 MB in `runs/` | At risk of an accidental `git add .`; `.gitignore` currently un-ignores `data/raw/adzuna/` |

The committed raw files came from the team's original relevance-sorted collection, which predates the audited collector: they include postings back to 2019 and near-duplicates. The teammate's cleaned dataset is derived from them (2,500 rows), not from the audited runs.

## 3. Repository visibility

| Check | Result |
|---|---|
| Remote | `origin` = `https://github.com/anusanth26/Career-Market-Intelligence` (owner is a teammate, not the local git user) |
| GitHub REST API without credentials | HTTP 404 |
| Repository HTML page without credentials | HTTP 404 |
| Conclusion | The repository is **not publicly visible to anonymous users**, or it does not exist under that name. GitHub returns 404 for private repositories, so this is consistent with **private**, but it does not prove it. **Not established.** The team should confirm in GitHub → Settings → General (Danger Zone shows the visibility) and check the collaborator list |

If it is private, the data is shared with collaborators only. The terms of service do not address this case (`report/adzuna_compliance.md`, question 12).

## 4. Assessment

| Issue | Severity | Remediation needed? |
|---|---|---|
| API key in repository | none found | No (rotate precautionarily) |
| Raw Adzuna records on the remote | **Depends on visibility and on Adzuna's answer.** If the repo is public, this is redistribution of job postings that the terms do not clearly allow; if private with limited collaborators, lower risk | Yes, conditionally (below) |
| Derived cleaned text on the remote | Same as raw: it contains the original snippets | Same |
| Untracked 41 MB of new raw runs | Not yet exposed | Add ignore rules before anyone runs `git add .` |
| Local branch is 14 commits behind `origin/main` | Coordination risk: my local edits to `.gitignore` and `scripts/collect_adzuna.py` will conflict with or overwrite teammates' work when merged | Pull and reconcile before committing anything |

## 5. Recommended procedure (not executed)

Do these in order and only with the team's agreement:

1. **Establish visibility** and the collaborator list in GitHub settings. If the repository is public, **make it private immediately**; this is reversible and destroys nothing.
2. **Rotate the API key** (section 1).
3. **Stop adding Adzuna data** to the repository. Add these lines to `.gitignore` (not applied yet):
   ```
   data/raw/adzuna/runs/
   data/raw/adzuna/coverage_*.json
   data/raw/ml_data_feasibility/
   data/cleaned/
   ```
   Note that ignoring only affects **future** commits; already-tracked files stay tracked.
4. **Decide about the existing committed data** once Adzuna answers:
   - **If Adzuna permits private storage:** leave the committed files in a private repository and restrict collaborators to the team and instructors. No history change is needed.
   - **If not permitted, or the repository was ever public:** the files must be removed from **history**, not only from the working tree. `git rm` removes a file from the next commit only; the data stays in every earlier commit, in every clone and fork, and in GitHub's cached views and pull-request refs. The safe procedure is:
     1. Agree a date with all collaborators; have everyone push and stop working.
     2. Make a full backup clone (`git clone --mirror`).
     3. Run `git filter-repo --path data/raw/adzuna --path data/cleaned --invert-paths` on a fresh clone (the tool is the one Git recommends instead of the older `filter-branch`).
     4. Force-push all branches **only after** the team agrees, then ask every collaborator to re-clone (their old clones still contain the data).
     5. Contact GitHub Support to remove cached views and pull-request references, and check for forks.
     6. Do not treat any of this as complete: copies already downloaded cannot be recalled.
5. **Do not re-add** raw data to the repository. Share it privately (course drive, with access restricted) if consent allows.
6. **Reconcile the 14 teammate commits** before any of this: `git fetch`, review, merge.

I did not run any of steps 1, 3–5. In particular I did not rewrite history and did not force-push.
