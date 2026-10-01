"""
Deterministic title -> role mapping.

A search query is NOT a role label. Role membership is decided only from the posting's own title,
using the explicit regex rules in config/roles.json. The original title is never modified.

Statuses returned by map_title():
    matched          exactly one role's `match` rule fired and none of its `exclude` rules fired
    excluded_by_rule a role's `match` fired but one of its `exclude` rules also fired (never assigned)
    ambiguous_multi  more than one role matched and they are not resolvable by overlap_group/priority
    unmatched        no role matched
"""

import re
import unicodedata


def normalize_title(title: str) -> str:
    """Lowercase, strip accents, turn every run of non-alphanumerics into one space."""
    t = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def compile_rules(roles: list) -> list:
    """Attach compiled regexes to each role config (returns new dicts; input untouched)."""
    compiled = []
    for r in roles:
        compiled.append({
            **r,
            "_match": [re.compile(p) for p in r.get("match", [])],
            "_exclude": [re.compile(p) for p in r.get("exclude", [])],
        })
    return compiled


def map_title(title: str, rules: list) -> dict:
    """Returns {"status", "role", "candidates", "normalized_title", "reason"}."""
    norm = normalize_title(title)
    fired, excluded = [], []
    for r in rules:
        if any(p.search(norm) for p in r["_match"]):
            hit = next((p.pattern for p in r["_exclude"] if p.search(norm)), None)
            (excluded if hit else fired).append((r, hit))

    out = {"normalized_title": norm, "candidates": [r["role"] for r, _ in fired], "role": None, "reason": ""}

    if len(fired) == 1:
        out.update(status="matched", role=fired[0][0]["role"])
    elif len(fired) > 1:
        groups = {r.get("overlap_group") for r, _ in fired}
        if len(groups) == 1 and None not in groups:
            best = max(fired, key=lambda x: x[0].get("priority", 0))
            ties = [r for r, _ in fired if r.get("priority", 0) == best[0].get("priority", 0)]
            if len(ties) == 1:
                out.update(status="matched", role=best[0]["role"], reason="overlap_group priority")
                return out
        out.update(status="ambiguous_multi", reason="matched: " + ", ".join(out["candidates"]))
    elif excluded:
        out.update(status="excluded_by_rule", candidates=[r["role"] for r, _ in excluded],
                   reason="exclude rule: " + excluded[0][1])
    else:
        out.update(status="unmatched")
    return out
