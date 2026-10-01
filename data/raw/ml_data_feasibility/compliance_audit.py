"""
Gate 2 (API usage) and Gate 3 (repository / credential exposure) audit.
Read-only. Makes NO API calls. NEVER prints or stores credential values: secrets are only used as search
needles in memory and results are reported as booleans/counts/locations.

    python data/raw/ml_data_feasibility/compliance_audit.py
Writes data/raw/ml_data_feasibility/compliance_audit.json
"""

import glob
import json
import math
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUNS = os.path.join(ROOT, "data", "raw", "adzuna", "runs")
PAGE = 50


def parse(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def jl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def git(*args):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def main():
    out = {"api_usage": {}, "credentials": {}, "repository": {}}

    # ── Gate 2: API usage from local logs ────────────────────────────
    events = []  # (timestamp, kind, run)
    per_run = {}
    for run in sorted(d for d in os.listdir(RUNS) if os.path.isdir(os.path.join(RUNS, d))):
        d = os.path.join(RUNS, run)
        man = json.load(open(os.path.join(d, "run_manifest.json")))
        queries = jl(os.path.join(d, "queries.jsonl"))
        pages = sum(q["pages_ok"] for q in queries)
        failed = sum(q["http_failures"] for q in queries)
        empty_final = sum(1 for q in queries if q["stop_reason"] == "no_more_results" and q["raw_records"] % PAGE == 0)
        per_run[run] = {"started": man["started"], "finished": man.get("finished"), "queries": len(queries),
                        "successful_pages": pages, "failed_attempts_http": failed,
                        "final_empty_page_calls_estimated": empty_final,
                        "estimated_total_calls": pages + failed + empty_final,
                        "retries": sum(q["retries"] for q in queries), "http_429": 0,
                        "min_gap_setting_seconds": man["config_snapshot"]["settings"]["min_interval_seconds"]}
        # timestamps of successful page fetches (one per page, taken from the first record of that page)
        seen = set()
        for q in queries:
            for rec in jl(os.path.join(d, q["records_file"])):
                c = rec["collection"]
                key = (q["records_file"], c["page"])
                if key not in seen:
                    seen.add(key)
                    events.append((parse(c["collected_at"]), "page", run))
        att = os.path.join(d, "attempts.jsonl")
        status_counts = Counter()
        if os.path.exists(att):
            for a in jl(att):
                if "status" in a:
                    status_counts[str(a["status"])] += 1
                    events.append((parse(a["at"]), "failed_attempt", run))
        per_run[run]["failed_attempt_status_counts"] = dict(status_counts)
        per_run[run]["http_429"] = status_counts.get("429", 0)
    out["api_usage"]["per_run"] = per_run

    # coverage probe (no per-call timestamps): 47 roles x 3 countries, 2.6 s sleep after each call
    cov = json.load(open(os.path.join(ROOT, "data", "raw", "adzuna", "coverage_2026-09-29.json")))
    n_probe = sum(1 for r in cov["results"] for c in ("in", "gb", "us") if c in r)
    errs = sum(1 for r in cov["results"] for c in ("in", "gb", "us") if isinstance(r.get(c), dict) and "error" in r[c])
    pstart = datetime.fromisoformat(cov["pulled"])
    out["api_usage"]["coverage_probe"] = {"calls": n_probe, "started_utc": pstart.isoformat(), "errors": errs,
                                          "assumed_pace_seconds_per_call": 2.6 + 0.4,
                                          "estimated_end_utc": (pstart + timedelta(seconds=n_probe * 3.0)).isoformat()}
    for i in range(n_probe):  # synthetic per-call times at the probe's known sleep pacing (approximation)
        events.append((pstart + timedelta(seconds=i * 3.0), "probe", "coverage_probe"))

    # legacy team pull (old collector): 4 categories x 625 records, 50 per page => 13 calls each (+ maybe 1 empty)
    legacy = json.load(open(os.path.join(ROOT, "data", "raw", "adzuna", "pull_log_2026-09-29.json")))
    legacy_calls = 4 * math.ceil(625 / PAGE)
    out["api_usage"]["legacy_team_pull"] = {"pull_date_in_log": legacy["pull_date"], "categories": len(legacy["categories"]),
                                            "estimated_calls": legacy_calls,
                                            "note": "Made with a DIFFERENT app id (utm_source in its redirect URLs differs from the current key's), so probably a separate quota. Time of day unknown."}

    by_day = defaultdict(lambda: Counter())
    for ts, kind, run in events:
        by_day[ts.strftime("%Y-%m-%d")][kind] += 1
    out["api_usage"]["logged_calls_by_utc_date"] = {d: {**c, "total": sum(c.values())} for d, c in sorted(by_day.items())}
    # per-minute peak using logged timestamps
    minute = Counter(ts.strftime("%Y-%m-%dT%H:%M") for ts, _, _ in events)
    peak_minute, peak = minute.most_common(1)[0]
    out["api_usage"]["peak_calls_in_any_clock_minute"] = {"minute_utc": peak_minute, "calls": peak}
    out["api_usage"]["clock_minutes_over_25"] = sum(1 for v in minute.values() if v > 25)
    # overlap of run windows
    wins = sorted((parse(v["started"]), parse(v["finished"]) if v["finished"] else parse(v["started"]), r) for r, v in per_run.items())
    wins.append((pstart, pstart + timedelta(seconds=n_probe * 3.0), "coverage_probe"))
    wins.sort()
    overlaps = [(a[2], b[2]) for a, b in zip(wins, wins[1:]) if b[0] < a[1]]
    out["api_usage"]["overlapping_run_windows"] = overlaps
    # totals for 2026-09-29 (UTC)
    d29 = {r: v for r, v in per_run.items() if v["started"].startswith("2026-09-29")}
    total_29 = sum(v["estimated_total_calls"] for v in d29.values()) + n_probe
    out["api_usage"]["estimated_project_calls_2026-09-29_utc_from_logs"] = total_29
    out["api_usage"]["estimated_project_calls_2026-09-29_utc_from_logs_note"] = (
        "Runs + coverage probe only. Excludes ~6 hand-made calls in the chat session that day (not logged) and the legacy team pull "
        "(different app id).")
    out["api_usage"]["documented_daily_limit"] = 250

    # ── Gate 3: credentials + raw data exposure ─────────────────────
    env = {}
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v
    key, aid = env.get("ADZUNA_APP_KEY"), env.get("ADZUNA_APP_ID")
    needles = {"current_app_key": key, "current_app_id": aid}
    cred = {"env_file_exists": os.path.exists(p), "env_file_git_ignored": git("check-ignore", ".env")[0] == 0,
            "env_file_tracked_now": bool(git("ls-files", ".env")[1].strip()),
            "env_file_ever_committed": bool(git("log", "--all", "--oneline", "--", ".env")[1].strip())}
    for name, needle in needles.items():
        if not needle:
            cred[name] = "not_present_in_env_file"
            continue
        files = []
        for base, dirs, fs in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            for f in fs:
                fp = os.path.join(base, f)
                if fp == p or os.path.getsize(fp) > 80_000_000:
                    continue
                try:
                    if needle.encode() in open(fp, "rb").read():
                        files.append(os.path.relpath(fp, ROOT))
                except OSError:
                    pass
        rc, so, _ = git("log", "--all", "--oneline", f"-S{needle}")
        commits = [l for l in so.splitlines() if l]
        rc2, so2, _ = git("grep", "-l", "-F", needle, "--", ".")
        cred[name] = {"found_in_working_tree_files": sorted(files)[:20], "working_tree_file_count": len(files),
                      "tracked_files_containing_it_now": [l for l in so2.splitlines()],
                      "commits_in_history_that_add_or_remove_it": len(commits),
                      "kind": "secret" if name.endswith("key") else "identifier (appears in Adzuna redirect URLs as utm_source)"}
    # any other app id seen in committed data (old team pull)
    rc, so, _ = git("show", "HEAD:data/raw/adzuna/adzuna_data_analyst_2026-09-29.json")
    ids = set(re.findall(r"utm_source=([0-9a-f]{8})", so))
    cred["other_app_ids_in_committed_redirect_urls"] = {"count": len(ids), "note": "identifier Adzuna embeds in redirect_url; not a secret key"}
    # generic key-like strings assigned in tracked code
    rc, so, _ = git("grep", "-n", "-I", "-E", "(app_key|APP_KEY|api_key)\\s*[:=]\\s*[\"'][0-9a-fA-F]{16,}[\"']")
    cred["hardcoded_key_like_assignment_in_tracked_files"] = len([l for l in so.splitlines() if l])
    out["credentials"] = cred

    rc, so, _ = git("remote", "-v")
    out["repository"]["remotes_configured"] = [l.split()[0:2] for l in so.splitlines()]
    out["repository"]["branch"] = git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    out["repository"]["commit_count"] = int(git("rev-list", "--all", "--count")[1].strip() or 0)
    rc, so, _ = git("ls-files", "data/raw")
    tracked = [l for l in so.splitlines() if l]
    out["repository"]["tracked_raw_files_now"] = [{"path": f, "bytes": os.path.getsize(os.path.join(ROOT, f))} for f in tracked if os.path.exists(os.path.join(ROOT, f))]
    rc, so, _ = git("log", "--all", "--name-only", "--pretty=format:%h|%ad|%s", "--date=short", "--", "data/raw")
    hist, cur = [], None
    for line in so.splitlines():
        if "|" in line and not line.startswith("data/"):
            cur = line
        elif line.startswith("data/") and cur:
            hist.append({"commit": cur, "file": line})
    out["repository"]["history_commits_touching_data_raw"] = hist
    out["repository"]["untracked_adzuna_data_not_ignored"] = [
        l[3:] for l in git("status", "--short", "--", "data/raw")[1].splitlines() if l.startswith("??")]
    out["repository"]["untracked_runs_dir_bytes"] = sum(os.path.getsize(f) for f in glob.glob(os.path.join(RUNS, "**", "*"), recursive=True) if os.path.isfile(f))
    out["repository"]["gitignore_lines"] = open(os.path.join(ROOT, ".gitignore")).read().splitlines()
    json.dump(out, open(os.path.join(HERE, "compliance_audit.json"), "w"), indent=2)
    print(json.dumps(out, indent=1)[:9000])


if __name__ == "__main__":
    main()
