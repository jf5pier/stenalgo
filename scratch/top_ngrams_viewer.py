"""Collect top French 2/3/4-grams from the unofficial Google Ngram Viewer
JSON endpoint via wildcard expansions, without downloading the n-gram database.

Heuristic: every n-gram's frequency is at most its (n-1)-gram prefix's, so
anchoring wildcards on the deepest available shorter n-grams covers the head
of the distribution. Each wildcard returns at most 10 expansions, so the
anchor lists go deeper than the requested 100.

Usage: env/bin/python scratch/top_ngrams_viewer.py
Writes scratch/top_ngrams/{2,3,4}gram_top100.tsv
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

VIEWER_JSON_URL = "https://books.google.com/ngrams/json"
# The JSON endpoint silently ignores string corpus names ("fre", "fre_2019"
# fall back to English); 30 is the numeric id of the French corpus.
CORPUS = "30"
YEAR_START = 2015
YEAR_END = 2019
BATCH_TERMS = 8
THROTTLE_SECONDS = 1.0
TOP_KEEP = 100          # size of each output list
ANCHOR_DEPTH = {2: 200, 3: 300, 4: 300}  # anchors per n-gram order

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "scratch" / "top_ngrams"


def viewerExpansions(terms: list[str]) -> dict[str, float]:
    """One batched request; returns n-gram -> mean relative frequency for
    every EXPANSION row (the wildcard fills) across all terms."""
    content = ",".join(terms)
    url = (f"{VIEWER_JSON_URL}?content={urllib.parse.quote(content)}"
           f"&corpus={CORPUS}&year_start={YEAR_START}"
           f"&year_end={YEAR_END}&smoothing=0")
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                rows = json.loads(response.read().decode("utf-8"))
            break
        except Exception as exc:  # noqa: BLE001 - retry then give up loudly
            if attempt == 2:
                raise
            print(f"  retry after {exc!r}")
            time.sleep(5.0)
    out: dict[str, float] = {}
    for row in rows:
        if row.get("type") != "EXPANSION":
            continue
        out[row["ngram"]] = sum(row["timeseries"]) / len(row["timeseries"])
    return out


def collectRanking(anchors: list[str], order: int) -> list[tuple[str, float]]:
    """Query 'anchor *' for every anchor; rank expansions by frequency."""
    results: dict[str, float] = {}
    for start in range(0, len(anchors), BATCH_TERMS):
        batch = [f"{anchor} *" for anchor in anchors[start:start + BATCH_TERMS]]
        results.update(viewerExpansions(batch))
        done = min(start + BATCH_TERMS, len(anchors))
        print(f"  order {order}: {done}/{len(anchors)} anchors", flush=True)
        if done < len(anchors):
            time.sleep(THROTTLE_SECONDS)
    return sorted(results.items(), key=lambda kv: kv[1], reverse=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Order-1 anchors: top words from the committed books frequency list
    # (first line is the "Somme" total, skipped).
    anchors1: list[str] = []
    with open(REPO / "resources" / "top500_books.txt", encoding="utf-8") as fh:
        for line in fh:
            word = line.split("\t")[0]
            if word and word != "Somme":
                anchors1.append(word)
    anchors1 = anchors1[:ANCHOR_DEPTH[2]]

    previous = anchors1
    for order in (2, 3, 4):
        ranking = collectRanking(previous, order)
        ranking = [(ng, f) for ng, f in ranking if len(ng.split()) == order]
        top = ranking[:TOP_KEEP]
        outPath = OUT_DIR / f"{order}gram_top100.tsv"
        with open(outPath, "w", encoding="utf-8") as fh:
            for ngram, freq in top:
                fh.write(f"{ngram}\t{freq:.10f}\n")
        print(f"wrote {outPath} ({len(top)} rows)", flush=True)
        previous = [ngram for ngram, _ in ranking[:ANCHOR_DEPTH[order]]]


if __name__ == "__main__":
    main()
