"""Run SEVEN's pre-routing classifier over every prompt in Dolly-15k.

    python evidence/route_audit.py <SEVEN checkout> <databricks-dolly-15k.jsonl>

The classifier is imported from the SEVEN checkout unchanged. For every
API_CHECK decision the script also records which real-time keywords matched
and whether any of them matched as a whole word. A keyword that only occurs
inside a longer word ("eth" in "something") cannot be a request for live data.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"


def load_heuristics(seven: Path):
    sys.path.insert(0, str(seven / "SEVEN"))
    import heuristics  # noqa: E402
    return heuristics


def prompt_text(row: dict) -> str:
    # What a user would paste: the instruction, then any reference text.
    ctx = row.get("context", "").strip()
    return row["instruction"].strip() + ("\n\n" + ctx if ctx else "")


def realtime_hits(h, text: str):
    low = text.lower()
    hits = [k for k in h.REALTIME_KEYWORDS if k in low]
    whole = [k for k in hits if re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", low)]
    return hits, whole


def has_word(low: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", low) is not None


def classify_whole_word(h, text: str) -> str:
    """SEVEN's ordered checks with one change: phrases must match as whole words."""
    low = text.lower()
    if any(has_word(low, k) for k in h.REALTIME_KEYWORDS):
        return "API_CHECK"
    if any(has_word(low, k) for k in h.SPECIALIZED_DOMAINS):
        return "CLOUD"
    if any(has_word(low, k) for k in h.COMPLEX_MARKERS):
        return "CLOUD"
    if len(text.split()) > h.MAX_LOCAL_WORD_COUNT:
        return "CLOUD"
    return "LOCAL"


def first_in_word_example(text: str, keyword: str) -> str:
    low = text.lower()
    for m in re.finditer(re.escape(keyword), low):
        a, b = m.start(), m.end()
        if (a > 0 and low[a - 1].isalnum()) or (b < len(low) and low[b].isalnum()):
            s = a
            while s > 0 and low[s - 1].isalnum():
                s -= 1
            e = b
            while e < len(low) and low[e].isalnum():
                e += 1
            return low[s:e]
    return ""


def main(seven: Path, dolly: Path) -> None:
    h = load_heuristics(seven)
    commit = subprocess.run(["git", "-C", str(seven), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    rows = [json.loads(line) for line in dolly.read_text(encoding="utf-8").splitlines() if line.strip()]

    OUT.mkdir(exist_ok=True)
    by_cat = defaultdict(Counter)
    reasons = Counter()
    kw_any = Counter()
    kw_in_word_only = Counter()
    in_word_examples = defaultdict(Counter)
    api_total = api_in_word_only = 0
    per_prompt = []

    for i, row in enumerate(rows):
        text = prompt_text(row)
        decision = h.classify_query_type(text)
        route, reason = decision["route"], decision["reason"]
        by_cat[row["category"]][route] += 1
        reasons[reason] += 1
        hits, whole = realtime_hits(h, text)
        in_word_only = route == "API_CHECK" and not whole
        if route == "API_CHECK":
            api_total += 1
            api_in_word_only += in_word_only
            for k in hits:
                kw_any[k] += 1
                if k not in whole:
                    kw_in_word_only[k] += 1
                    ex = first_in_word_example(text, k)
                    if ex:
                        in_word_examples[k][ex] += 1
        per_prompt.append({
            "index": i,
            "category": row["category"],
            "words": len(text.split()),
            "route": route,
            "reason": reason,
            "realtime_keywords": " ".join(hits),
            "whole_word_keywords": " ".join(whole),
            "api_check_from_in_word_match_only": int(in_word_only),
            "api_intent": (h.detect_api_intent(text) or "") if route == "API_CHECK" else "",
            "route_if_whole_words": classify_whole_word(h, text),
        })

    with (OUT / "route_audit_prompts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(per_prompt[0]))
        w.writeheader()
        w.writerows(per_prompt)

    keywords = []
    for k, n in kw_any.most_common():
        keywords.append({
            "keyword": k,
            "api_check_prompts_containing": n,
            "of_which_only_inside_other_words": kw_in_word_only[k],
            "most_common_host_words": ", ".join(w for w, _ in in_word_examples[k].most_common(4)),
        })
    with (OUT / "route_audit_keywords.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(keywords[0]))
        w.writeheader()
        w.writerows(keywords)

    summary = {
        "dataset": "databricks/databricks-dolly-15k (CC BY-SA 3.0)",
        "dataset_sha256": hashlib.sha256(dolly.read_bytes()).hexdigest(),
        "seven_commit": commit,
        "heuristics_sha256": hashlib.sha256((seven / "SEVEN/heuristics.py").read_bytes()).hexdigest(),
        "prompts": len(rows),
        "routes": dict(Counter(p["route"] for p in per_prompt)),
        "reasons": dict(reasons),
        "api_check_total": api_total,
        "api_check_from_in_word_match_only": api_in_word_only,
        "routes_if_whole_words": dict(Counter(p["route_if_whole_words"] for p in per_prompt)),
        "by_category": {c: dict(v) for c, v in sorted(by_cat.items())},
        "api_intent": dict(Counter(p["api_intent"] or "none" for p in per_prompt if p["route"] == "API_CHECK")),
        "api_intent_in_word_only": dict(Counter(p["api_intent"] or "none" for p in per_prompt if p["api_check_from_in_word_match_only"])),
    }
    (OUT / "route_audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    for k in keywords[:15]:
        print(k)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
