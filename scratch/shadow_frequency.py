"""Shadow-frequency check (user request 2026-10-04): each single-rule shadow (attach rule + host word whose merged
outline equals a live word or brief) weighted by the Google Books bigram count of the phrase it would write
("est pas", "ce est"...; scratch/top_ngrams/orgtre/2grams_french.csv, top 5000 bigrams only).
Usage: PYTHONPATH=. env/bin/python scratch/shadow_frequency.py"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.decode_roundtrip import loadAll  # noqa: E402
from scratch.theory_injectivity import MARKS, mask  # noqa: E402
from src.affixes import PREFIX  # noqa: E402
from src.keyboard import canonicalizeStrokes  # noqa: E402


def main() -> None:
    ctx, rules, pool, words, unitStrokes = loadAll()
    bigram: dict[str, float] = {}
    with open(REPO / "scratch/top_ngrams/orgtre/2grams_french.csv", encoding="utf-8") as fh:
        next(fh)
        for row in csv.reader(fh):
            bigram[row[0].lower()] = float(row[1])
    orthos: dict = defaultdict(set)
    for o, ws in words.items():
        orthos[tuple(mask(s) for s in canonicalizeStrokes(o))] |= set(ws)
    live = set(orthos)
    for b in rules.briefs:
        o = tuple(mask(s) for s in canonicalizeStrokes(b.strokes))
        orthos[o].add("BRIEF:" + " ".join(b.expression))
        live.add(o)
    legal: dict = {}

    def isLegal(m: int) -> bool:
        if m not in legal:
            legal[m] = ctx.isLegal(tuple(k for k in range(64) if (m >> k) & 1 and (1 << k) & MARKS == 0))
        return legal[m]

    events = []        # (bigram count, rule, host, shadowed)
    for r in rules.attaches:
        km = mask(r.keypress)
        sm = km & ~MARKS
        for o in list(orthos):
            if any(x.startswith("BRIEF:") for x in orthos[o]) and not any(
                    not x.startswith("BRIEF:") for x in orthos[o]):
                pass
            idx = 0 if r.position == PREFIX else len(o) - 1
            h = o[idx]
            if h & sm or not isLegal(h | km):
                continue
            composed = o[:idx] + (h | km,) + o[idx + 1:]
            if composed not in live:
                continue
            rule = " ".join(r.expression)
            for host in orthos[o]:
                if host.startswith("BRIEF:"):
                    continue
                forms = [f"{rule} {host}", f"{rule}{host}"] if r.position == PREFIX else [f"{host} {rule}"]
                if rule.endswith("'"):
                    forms = [f"{rule}{host}", f"{rule} {host}"]
                count = max((bigram.get(f, 0.0) for f in forms), default=0.0)
                events.append((count, rule, host, "/".join(sorted(orthos[composed]))))
    n = len(events)
    seen = [e for e in events if e[0] > 0]
    print(f"single-rule shadow events (rule, host word): {n}; with a phrase in the top-5000 bigrams: {len(seen)}")
    total = sum(e[0] for e in seen)
    print(f"bigram mass of those phrases: {total:.3e}")
    byRule: dict = defaultdict(float)
    for e in seen:
        byRule[e[1]] += e[0]
    print("by rule:", {k: f"{v:.2e}" for k, v in sorted(byRule.items(), key=lambda kv: -kv[1])})
    print("\ntop phrases the decoder would misread (phrase count, rule + host -> the word that wins):")
    for e in sorted(seen, reverse=True)[:30]:
        print(f"  {e[0]:.2e}  {e[1]} + {e[2]} -> {e[3]}")
    pooled = {" ".join(e.units) for e in pool}
    print("\nof these, phrases that are themselves pool expressions:",
          [f"{e[1]} {e[2]}" for e in seen if f"{e[1]} {e[2]}" in pooled or f"{e[1]}{e[2]}" in pooled or f"{e[2]} {e[1]}" in pooled][:20])
    ref = sum(float(v) for v in bigram.values())
    print(f"\nreference: top-5000 bigram total {ref:.3e}; the layer's composed pool saving is 4.3e9 strokes")


if __name__ == "__main__":
    main()
