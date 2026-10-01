"""Rebuild scratch/top_ngrams/*.tsv from the orgtre *_1a_no_pos.csv intermediates
plus direct Ngram Viewer queries for the gaps.

Why not the published final lists: orgtre's final cleaning step silently drops
every fused apostrophe word (c'est, qu'il, n'est...), so their lists miss all
contexts of the most frequent French words. The no_pos intermediates still
have them, but split-elision (`d' un`, `d ' un`) and split-hyphen
(`peut - être`) artifacts that this script normalizes away.

Word units: an elision particle (l', c', d', n', s', j', qu', jusqu'...) glued
to its host counts as TWO words — the steno-theory unit count — so `c'est`
lands in the 2-gram file and `de l'homme` in the 3-gram file. Words whose
apostrophe is not an elision (aujourd'hui) stay one word.

Normalization:
- lowercase (merges case variants);
- collapse spaces around apostrophes and hyphens: `d ' un`/`d' un` -> `d'un`,
  `peut - être` -> `peut-être`;
- re-bin every entry by its word-unit count, summing counts across files.

Blind-spot fill: fragment_completions.py queried the viewer (`fragment *`,
numeric French corpus 30) for the top fragments; completions missing from the
orgtre data (top-N truncation) are merged in here with counts estimated as
viewer_share x scale[bin], where scale is the median count/share of the
entries known both ways. Estimated rows carry an `est` flag column.

Dropped (with counts in the report):
- entries with a token that has no letter, or digits/punctuation beyond
  apostrophe/hyphen;
- euphonic-`t` fragments (`t - il` -> `t-il`).
Trailing fragments (`de l'`) are kept: their counts are the prefix's true
total.

Usage: env/bin/python scratch/rebuild_ngrams.py
Outputs: scratch/top_ngrams/{1..5}gram_topN.tsv + apostrophe_words.tsv
"""

from __future__ import annotations

import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "scratch" / "top_ngrams" / "orgtre"
OUT = REPO / "scratch" / "top_ngrams"
ORDERS = (1, 2, 3, 4, 5)
# Per order, the top-N slices to write (the 2/3-gram top-100s replace the
# old viewer-wildcard files that used a different tokenization).
SLICES = {1: (300,), 2: (300, 100), 3: (200, 100), 4: (100,), 5: (50,)}

ALLOWED = re.compile(r"^[a-zàâäéèêëîïôöùûüçñœæ'-]+$")
HAS_LETTER = re.compile(r"[a-zàâäéèêëîïôöùûüçñœæ]")
# Left parts of elision particles: `X'` gluing onto a host word.
PARTICLES = {"l", "c", "d", "n", "s", "j", "m", "t", "qu", "jusqu", "lorsqu",
             "quelqu", "puisqu", "quoiqu", "presqu", "entr"}


def normalize(ngram: str) -> str:
    s = ngram.lower()
    s = re.sub(r" *' *", "'", s)   # d ' un / d' un -> d'un
    s = re.sub(r" *- *", "-", s)   # peut - être -> peut-être
    return s


def wordUnits(ngram: str) -> int:
    """Steno-theory word count: every elision particle is its own unit."""
    units = 0
    for token in ngram.split():
        if "'" in token:
            left, _, host = token.partition("'")
            # A glued particle + host (`c'est`) is two units; a bare
            # fragment (`l'`, `de l'`'s last token) is one.
            units += 2 if host and left in PARTICLES else 1
        else:
            units += 1
    return units


def keep(tokens: list[str]) -> str | None:
    """Return a rejection reason, or None if the entry is usable."""
    for tok in tokens:
        if not ALLOWED.match(tok) or not HAS_LETTER.search(tok):
            return f"non-word token {tok!r}"
    if tokens[0].startswith("t-"):
        return "euphonic-t fragment"
    return None


def main() -> None:
    counts: dict[int, Counter] = defaultdict(Counter)
    reasons: Counter = Counter()
    for order in ORDERS:
        path = SRC / f"{order}grams_french_1a_no_pos.csv"
        with open(path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                normalized = normalize(row["ngram"])
                tokens = normalized.split()
                reason = keep(tokens)
                if reason:
                    reasons[reason] += 1
                    continue
                counts[wordUnits(normalized)][normalized] += int(row["freq"])

    for reason, n in reasons.most_common(10):
        print(f"dropped {n:5d} entries: {reason}", file=sys.stderr)

    # Blind-spot fill from the viewer queries (fragment_completions.tsv).
    ratios: dict[int, list[float]] = defaultdict(list)
    missing: dict[int, dict[str, float]] = defaultdict(dict)
    with open(OUT / "fragment_completions.tsv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            completion = normalize(row["completion"])
            if keep(completion.split()) is not None:
                continue
            share = float(row["viewer_share"])
            bin_ = wordUnits(completion)
            if row["in_our_bins"] == "yes" and row["our_count"]:
                ratios[bin_].append(int(row["our_count"]) / share)
            elif row["in_our_bins"] == "NO" and completion not in counts[bin_]:
                missing[bin_][completion] = share

    estimated: dict[int, dict[str, int]] = {}
    for bin_, shares in sorted(missing.items()):
        scale = statistics.median(ratios[bin_]) if ratios[bin_] else 0
        estimated[bin_] = {ng: round(share * scale)
                           for ng, share in shares.items()}
        print(f"bin {bin_}: {len(estimated[bin_])} estimated entries "
              f"(scale {scale:.3e} from {len(ratios[bin_])} anchors)")

    for order in ORDERS:
        merged = Counter(counts[order])
        merged.update(estimated.get(order, {}))
        ranking = merged.most_common(max(SLICES[order]))
        for size in SLICES[order]:
            out = OUT / f"{order}gram_top{size}.tsv"
            with open(out, "w", encoding="utf-8") as fh:
                for ngram, freq in ranking[:size]:
                    flag = "\test" if ngram in estimated.get(order, {}) else ""
                    fh.write(f"{ngram}\t{freq}{flag}\n")
            print(f"wrote {out} ({min(size, len(ranking))} rows)")

    # Inventory of apostrophe-bearing entries, across all bins.
    with open(OUT / "apostrophe_words.tsv", "w", encoding="utf-8") as fh:
        fh.write("entry\tword_units\tfreq\n")
        for order in ORDERS:
            for ngram, freq in counts[order].most_common():
                if "'" in ngram:
                    fh.write(f"{ngram}\t{order}\t{freq}\n")


if __name__ == "__main__":
    main()
