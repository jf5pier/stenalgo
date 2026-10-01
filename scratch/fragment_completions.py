"""Blind-spot check for the rebuilt n-gram TSVs.

The orgtre sources are top-N truncated, so the completions of a trailing
fragment (`de l'`) are only partially covered by the next order's file. This
script queries the Ngram Viewer directly (`fragment *`, numeric French corpus
30) for the most frequent fragments and reports, per completion:
- the viewer's relative share (note: the endpoint canonicalizes `l'` to the
  detached `l '` variant, so shares are for that variant; rankings carry over);
- whether the completion is already present in our rebuilt bins, and its
- absolute count there.

Also prints prefix coverage: known-completion mass / fragment mass from the
orgtre absolute counts.

Usage: env/bin/python scratch/fragment_completions.py
Outputs: console report + scratch/top_ngrams/fragment_completions.tsv
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from rebuild_ngrams import ORDERS, SRC, keep, normalize

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "scratch" / "top_ngrams"
VIEWER = "https://books.google.com/ngrams/json"
CORPUS = "30"
TOP_FRAGMENTS_PER_ORDER = 12
THROTTLE = 1.0


def viewerExpansions(prefix: str) -> list[tuple[str, float]]:
    url = (f"{VIEWER}?content={urllib.parse.quote(prefix + ' *')}"
           f"&corpus={CORPUS}&year_start=2015&year_end=2019&smoothing=0")
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        rows = json.loads(response.read().decode("utf-8"))
    return [(r["ngram"], sum(r["timeseries"]) / len(r["timeseries"]))
            for r in rows if r.get("type") == "EXPANSION"]


def main() -> None:
    # Rebuild the in-memory bins exactly like rebuild_ngrams.py (fragments kept).
    counts: dict[int, Counter] = defaultdict(Counter)
    for order in ORDERS:
        with open(SRC / f"{order}grams_french_1a_no_pos.csv", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                normalized = normalize(row["ngram"])
                if keep(normalized.split()) is None:
                    counts[len(normalized.split())][normalized] += int(row["freq"])

    lines = ["prefix\tcompletion\tviewer_share\tin_our_bins\tour_count"]
    for order in (1, 2, 3, 4):
        # Completions glue onto the fragment (`de l'` -> `de l'homme`), so a
        # completion of an n-word fragment is an n-word entry sharing its prefix.
        frags = [(ng, f) for ng, f in counts[order].items()
                 if ng.endswith(("'", "-"))]
        frags.sort(key=lambda x: -x[1])
        for prefix, fragFreq in frags[:TOP_FRAGMENTS_PER_ORDER]:
            known = sum(f for ng, f in counts[order].items()
                        if ng.startswith(prefix) and len(ng) > len(prefix))
            print(f"[{prefix}] {fragFreq/1e6:7.1f}M  known completions cover "
                  f"{100*known/fragFreq:5.1f}%", flush=True)
            try:
                expansions = viewerExpansions(prefix)
            except Exception as exc:  # noqa: BLE001
                print(f"  viewer query failed: {exc!r}", flush=True)
                continue
            for raw, share in expansions:
                completion = normalize(raw)
                ours = counts[len(completion.split())].get(completion)
                lines.append(f"{prefix}\t{completion}\t{share:.10f}\t"
                             f"{'yes' if ours else 'NO'}\t{ours or ''}")
                if not ours:
                    print(f"  MISSING from our bins: {completion}", flush=True)
            time.sleep(THROTTLE)

    with open(OUT / "fragment_completions.tsv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {OUT / 'fragment_completions.tsv'}")


if __name__ == "__main__":
    main()
