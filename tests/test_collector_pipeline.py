"""
Offline tests for the Adzuna collector and coverage pipeline (no network, no credentials needed).

    python -m unittest discover -s tests -v
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from unittest import mock

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import analyze_coverage as ac  # noqa: E402
import collect_adzuna as ca  # noqa: E402
from role_mapping import compile_rules, map_title  # noqa: E402

CFG = json.load(open(os.path.join(ROOT, "config", "roles.json")))
SETTINGS = {**CFG["settings"], "min_interval_seconds": 0, "backoff_base_seconds": 1, "max_retries": 3}
RULES = compile_rules(CFG["roles"])


class Resp:
    def __init__(self, status=200, payload=None, headers=None, text=""):
        self.status_code, self._p, self.headers, self.text = status, payload, headers or {}, text

    def json(self):
        if self._p is None:
            raise ValueError("no json")
        return self._p


def job(i, title="Data Analyst", company="Acme", created="2026-09-20T00:00:00Z", desc=None, **kw):
    return {"id": str(i), "title": title, "company": {"display_name": company}, "created": created,
            "description": desc or f"unique description {i}", **kw}


class RoleMapping(unittest.TestCase):
    def m(self, t):
        return map_title(t, RULES)

    def test_query_is_not_role(self):
        # a Graphic Designer / WordPress dev returned by a 'digital marketing' query must not become Digital Marketing
        self.assertNotEqual(self.m("Graphic Designer - Real Estate")["role"], "Digital Marketing")
        self.assertEqual(self.m("WordPress Developer")["status"], "unmatched")
        self.assertEqual(self.m("Senior Data Engineer (immediate joiner)")["role"], "Data Engineer")

    def test_generic_reporting_analyst_not_forced_into_data_analyst(self):
        # found by manual title inspection: title_only='reporting analyst' returns finance/compliance roles
        for t in ("Regulatory Reporting Analyst", "Record to Report Ops Analyst", "Financial Reporting Analyst"):
            self.assertNotEqual(self.m(t)["role"], "Data Analyst")
        self.assertEqual(self.m("Senior Data Analyst - SQL, BI Reporting")["role"], "Data Analyst")

    def test_original_title_untouched_and_normalised(self):
        r = self.m("Senior Data Engineer [T500-29640]")
        self.assertEqual(r["role"], "Data Engineer")
        self.assertEqual(r["normalized_title"], "senior data engineer t500 29640")

    def test_ambiguous_and_excluded_never_forced(self):
        self.assertEqual(self.m("Data Analyst / Business Analyst")["status"], "ambiguous_multi")
        self.assertEqual(self.m("Software Engineer in Test")["status"], "excluded_by_rule")
        self.assertEqual(self.m("Quality Engineer - Software Automation")["status"], "excluded_by_rule")
        self.assertEqual(self.m("Quality Assurance Engineer")["status"], "unmatched")  # never forced

    def test_overlap_group_priority(self):
        self.assertEqual(self.m("Information Security Analyst")["role"], "Information Security Analyst")
        self.assertEqual(self.m("Information Security Engineer")["role"], "Information Security Engineer")
        self.assertEqual(self.m("Security Engineer II")["role"], "Security Engineer")
        self.assertEqual(self.m("Cyber Security Engineer")["role"], "Cybersecurity Engineer")

    def test_fpa_and_uiux(self):
        self.assertEqual(self.m("FP&A Analyst")["role"], "Financial Analyst")
        self.assertEqual(self.m("UI/UX Designer")["role"], "UX Designer")


class Retry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log = os.path.join(self.tmp, "attempts.jsonl")
        self.stats = {"http_failures": 0, "retries": 0, "stop_reason": None}
        self.limiter = ca.RateLimiter(0)

    def call(self, responses):
        session = mock.Mock()
        session.get.side_effect = responses
        with mock.patch.object(ca.time, "sleep") as sleep:
            out = ca.request_with_retry(session, "u", {}, {"q": 1}, SETTINGS, self.limiter, self.log, self.stats)
        return out, session, sleep

    def test_recovers_after_429_and_500(self):
        out, session, sleep = self.call([Resp(429, headers={"Retry-After": "5"}), Resp(500), Resp(200, {"ok": 1})])
        self.assertEqual(out, {"ok": 1})
        self.assertEqual((self.stats["http_failures"], self.stats["retries"]), (2, 2))
        delays = [c.args[0] for c in sleep.call_args_list]
        self.assertGreaterEqual(delays[0], 5)          # honours Retry-After
        self.assertGreaterEqual(delays[1], 2)          # attempt 1 -> base(1) * 2**1
        with open(self.log) as fh:
            lines = [json.loads(l) for l in fh]
        self.assertEqual([l.get("status") for l in lines if "status" in l], [429, 500])
        self.assertTrue(any(l.get("outcome") == "recovered" for l in lines))

    def test_backoff_is_exponential(self):
        _, _, sleep = self.call([Resp(500), Resp(500), Resp(500), Resp(200, {"ok": 1})])
        d = [c.args[0] for c in sleep.call_args_list]
        self.assertEqual([int(x) for x in d], [1, 2, 4])   # base 1s doubling; jitter < 1s

    def test_no_infinite_loop(self):
        out, session, _ = self.call([Resp(503)] * 10)
        self.assertIsNone(out)
        self.assertEqual(session.get.call_count, SETTINGS["max_retries"] + 1)
        self.assertEqual(self.stats["stop_reason"], "retries_exhausted")

    def test_non_retryable_is_not_retried(self):
        out, session, _ = self.call([Resp(401, text="bad key")] * 3)
        self.assertIsNone(out)
        self.assertEqual(session.get.call_count, 1)
        self.assertEqual(self.stats["stop_reason"], "non_retryable_http_401")

    def test_timeout_retried_and_credentials_redacted(self):
        with mock.patch.object(ca, "APP_KEY", "SECRETKEY123"), mock.patch.object(ca, "APP_ID", "ID999"):
            err = requests.ConnectionError("HTTPSConnectionPool ... url: /x?app_id=ID999&app_key=SECRETKEY123&a=1")
            out, _, _ = self.call([err, Resp(200, {"ok": 1})])
        self.assertEqual(out, {"ok": 1})
        with open(self.log) as fh:
            text = fh.read()
        self.assertNotIn("SECRETKEY123", text)
        self.assertNotIn("ID999", text)

    def test_bad_json_200_is_retried(self):
        out, _, _ = self.call([Resp(200, None), Resp(200, {"ok": 1})])
        self.assertEqual(out, {"ok": 1})


class FetchQuery(unittest.TestCase):
    def run_query(self, pages, max_records=100, window_start="2026-06-30T00:00:00Z"):
        tmp = tempfile.mkdtemp()
        session = mock.Mock()
        session.get.side_effect = pages
        q = {"domain": "D", "role": "Data Analyst", "country": "in", "query": "data analyst", "max_records": max_records}
        s = {**SETTINGS, "page_size": 2}
        from datetime import datetime, timezone
        with mock.patch.object(ca.time, "sleep"), mock.patch.object(ca, "APP_ID", "id"), mock.patch.object(ca, "APP_KEY", "key"):
            meta = ca.fetch_query(session, q, s, "RUN", tmp, ca.RateLimiter(0),
                                  datetime.strptime(window_start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))
        recs = [json.loads(l) for l in open(os.path.join(tmp, meta["records_file"]))] \
            if os.path.exists(os.path.join(tmp, meta["records_file"])) else []
        return meta, recs, session

    def page(self, ids, count=99):
        return Resp(200, {"count": count, "results": [job(i, created=f"2026-09-{30 - i:02d}T00:00:00Z") for i in ids]})

    def test_params_sent_count_logged_pagination_and_cap(self):
        meta, recs, session = self.run_query([self.page([1, 2]), self.page([3, 4]), self.page([5, 6])], max_records=4)
        params = session.get.call_args_list[0].kwargs["params"]
        self.assertEqual(params["title_only"], "data analyst")
        self.assertEqual(params["max_days_old"], 90)
        self.assertEqual(params["sort_by"], "date")
        self.assertEqual(session.get.call_args_list[1].args[0].split("/")[-1], "2")  # page 2 requested
        self.assertEqual(meta["api_count"], 99)
        self.assertEqual((meta["pages_ok"], meta["raw_records"]), (2, 4))
        self.assertEqual(meta["stop_reason"], "max_records_reached")
        self.assertTrue(meta["capped_by_max_records"])
        self.assertTrue(meta["created_sorted_desc"])
        self.assertNotIn("app_key", json.dumps(meta))         # credentials never recorded in metadata
        self.assertEqual(recs[0]["raw"]["id"], "1")            # raw record untouched
        self.assertEqual(recs[0]["collection"]["query_variant"], "data analyst")
        self.assertEqual(recs[0]["collection"]["adzuna_id"], "1")

    def test_partial_progress_preserved_on_failure(self):
        meta, recs, _ = self.run_query([self.page([1, 2]), Resp(500), Resp(500), Resp(500), Resp(500)])
        self.assertEqual(meta["status"], "partial")
        self.assertEqual(meta["raw_records"], 2)
        self.assertEqual(len(recs), 2)
        self.assertEqual(meta["http_failures"], 4)
        self.assertEqual(meta["retries"], 3)

    def test_out_of_window_detected(self):
        p = Resp(200, {"count": 1, "results": [job(1, created="2019-05-17T00:00:00Z")]})
        meta, _, _ = self.run_query([p])
        self.assertEqual(meta["records_older_than_window"], 1)


class Dedup(unittest.TestCase):
    def rows(self, specs):
        out = []
        for n, (i, title, comp, created, desc, variant) in enumerate(specs):
            out.append({"order": n, "id": i, "title": title, "employer": comp, "employer_norm": ac.norm_text(comp),
                        "description": desc, "created": created, "variant": variant, "vkey": variant,
                        "salary_min": None, "salary_max": None, "salary_pred": "0"})
        return out

    def test_exact_near_cap_and_synonym_dedup(self):
        s = {**SETTINGS, "employer_cap_fraction": 0.25, "dedup_description_chars": 20}
        specs = [
            ("1", "Data Analyst", "A", "2026-09-01", "aaaa", "data analyst"),
            ("1", "Data Analyst", "A", "2026-09-01", "aaaa", "bi analyst"),          # same id via another synonym
            ("2", "Data  Analyst!", "A ", "2026-09-02", "AAAA", "data analyst"),      # near-dup of 1 (normalised)
            ("3", "Data Analyst", "B", "2026-09-03", "bbbb", "data analyst"),
            ("4", "Data Analyst", "C", "2026-09-04", "cccc", "bi analyst"),
            ("5", "Data Analyst", "D", "2026-09-05", "dddd", "bi analyst"),
            ("6", "Data Analyst II", "X", "2026-09-06", "e1", "data analyst"),
            ("7", "Data Analyst III", "X", "2026-09-07", "e2", "data analyst"),
            ("8", "Data Analyst IV", "", "2026-09-08", "f1", "data analyst"),         # no employer: never capped
        ]
        rem, attrib = [], defaultdict(Counter)
        clean, cap_n = ac.dedupe_and_cap(self.rows(specs), s, "Data Analyst", rem, attrib)
        reasons = Counter(r["reason"].split("(")[0] for r in rem)
        self.assertEqual(reasons["exact_id_duplicate"], 1)   # counted once, not twice
        self.assertEqual(reasons["near_duplicate"], 1)
        self.assertEqual(attrib["bi analyst"]["exact_dup"], 1)  # attributed to the synonym that re-retrieved it
        self.assertEqual(cap_n, 1)                              # floor(0.25 * 7)
        ids = {r["id"] for r in clean}
        self.assertEqual(len(clean), len(ids))                  # no double counting
        self.assertIn("7", ids)                                 # cap keeps the most recent per employer
        self.assertNotIn("6", ids)
        self.assertIn("8", ids)
        self.assertTrue(all(r["employer"] == "X" for r in rem if r["reason"].startswith("employer_cap")))
        self.assertEqual(len(rem), 1 + 1 + 1)                   # nothing removed silently


class Salary(unittest.TestCase):
    def test_counts(self):
        mk = lambda a, b, p="0": {"salary_min": a, "salary_max": b, "salary_pred": p}
        rows = [mk(None, None), mk(500000, 900000), mk(800000, 800000), mk(12, 400000),
                mk(600000, None), mk(900000, 100000), mk(200000, 99000000, "1")]
        s = ac.salary_stats(rows, CFG["settings"])
        self.assertEqual(s["clean_postings"], 7)
        self.assertEqual(s["salary_min_count"], 6)
        self.assertEqual(s["salary_max_count"], 5)
        self.assertEqual(s["salary_both_count"], 5)
        self.assertEqual(s["salary_percentage"], round(100 * 6 / 7, 1))
        self.assertEqual(s["predicted_count"], 1)
        self.assertEqual(s["suspicious_below_floor"], 1)     # only the "12" value is below the 100,000 floor
        self.assertEqual(s["suspicious_above_ceiling"], 1)
        self.assertEqual(s["suspicious_min_gt_max"], 1)
        self.assertEqual(s["point_salary_min_eq_max"], 1)


class RerunSafety(unittest.TestCase):
    def test_second_run_never_overwrites_first(self):
        tmp = tempfile.mkdtemp()
        cfg = {"settings": {**SETTINGS, "page_size": 2, "default_max_records": 2},
               "roles": [{"domain": "D", "role": "Data Analyst", "enabled": True, "countries": ["in"],
                          "variants": ["data analyst"], "match": [], "exclude": []}]}
        cfgp = os.path.join(tmp, "c.json")
        json.dump(cfg, open(cfgp, "w"))
        digests = []
        for n in range(2):
            session = mock.Mock()
            session.get.return_value = Resp(200, {"count": 5, "results": [job(1), job(2)]})
            with mock.patch.object(ca.requests, "Session", return_value=session), \
                 mock.patch.object(ca.time, "sleep"), mock.patch.object(ca, "APP_ID", "i"), mock.patch.object(ca, "APP_KEY", "k"), \
                 mock.patch.object(ca, "utcnow", side_effect=lambda n=n: __import__("datetime").datetime(2026, 9, 29, 10, 0, n, tzinfo=__import__("datetime").timezone.utc)), \
                 mock.patch.object(sys, "argv", ["x", "--config", cfgp, "--output-root", os.path.join(tmp, "runs")]):
                ca.main()
            dirs = sorted(os.listdir(os.path.join(tmp, "runs")))
            digests.append({d: hashlib.md5(open(os.path.join(tmp, "runs", d, "queries.jsonl"), "rb").read()).hexdigest()
                            for d in dirs})
        self.assertEqual(len(digests[1]), 2)                                    # a NEW directory was created
        first = next(iter(digests[0]))
        self.assertEqual(digests[0][first], digests[1][first])                  # first run byte-identical afterwards


if __name__ == "__main__":
    unittest.main()
