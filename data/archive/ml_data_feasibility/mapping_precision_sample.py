"""
Gate 4 sampling. Reproducible (seed 20260930). Samples 50 CLEAN titles per core role (precision) and
unmatched titles retrieved by the role's own queries (recall probe). Writes JSON samples only; labels are added
by a human/reviewer step (mapping_precision_labels.py) and never by the mapping code itself.
"""
import json, os, random, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, HERE)
import adzuna_label_audit as ala
from analyze_coverage import read_jsonl, norm_text
from role_mapping import compile_rules, map_title
SEED = 20260930
cfg = json.load(open(os.path.join(ROOT, "config", "roles.json"))); rules = compile_rules(cfg["roles"])
rcfg = {r["role"]: r for r in rules}
clean, _ = ala.build_clean()
out = {"seed": SEED, "precision": {}, "unmatched": {}}
for role in ala.CORE:
    rows = sorted(clean[role], key=lambda r: r["id"])
    rnd = random.Random(f"{SEED}-{role}")
    pick = sorted(rnd.sample(rows, 50), key=lambda r: r["id"])
    canon = rcfg[role]["_match"][0]
    out["precision"][role] = [{"i": i + 1, "id": r["id"], "title": r["title"], "tier": "C" if canon.search(norm_text(r["title"])) else "S",
                               "retrieved_by": r["variant"]} for i, r in enumerate(pick)]
# unmatched titles retrieved by each role's OWN queries in the feasibility (or deepen) run
UNM = {"Business Analyst": 30, "Project Manager": 30, "Data Analyst": 30, "Graphic Designer": 30}
for role in ala.CORE:
    n = UNM.get(role, 15)
    run = ala.SOURCE_RUN[role]; d = os.path.join(ala.RUNS, run); seen = {}
    for q in read_jsonl(os.path.join(d, "queries.jsonl")):
        if q["query_role"] != role: continue
        for rec in read_jsonl(os.path.join(d, q["records_file"])):
            t = rec["raw"].get("title", "")
            if map_title(t, rules)["status"] == "unmatched":
                seen.setdefault(norm_text(t), (str(rec["raw"]["id"]), t, q["query"]))
    pool = sorted(seen.values())
    rnd = random.Random(f"{SEED}-unm-{role}")
    pick = sorted(rnd.sample(pool, min(n, len(pool))))
    out["unmatched"][role] = {"pool_distinct_unmatched_titles": len(pool),
                              "sample": [{"i": i + 1, "id": p[0], "title": p[1], "query": p[2]} for i, p in enumerate(pick)]}
json.dump(out, open(os.path.join(HERE, "mapping_precision", "samples.json"), "w"), indent=1, ensure_ascii=False)
for role, items in out["precision"].items():
    print(f"\n##P {role}")
    for it in items: print(f"{it['i']:>2} {it['tier']} | {it['title']}")
