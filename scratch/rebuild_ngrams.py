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

Usage:
- env/bin/python scratch/rebuild_ngrams.py
  Outputs: scratch/top_ngrams/{1..5}gram_topN.tsv + apostrophe_words.tsv
- env/bin/python scratch/rebuild_ngrams.py --query TERMS.txt [OUT.tsv] [--fill]
  Point-query mode: look every term of TERMS.txt up in the same merged bins
  (orgtre intermediates + viewer-estimated fill), NOT just the top-N slices,
  and write term/word_units/freq/source rows (source: orgtre | est | MISSING).
  Default OUT: scratch/tao_coverage.tsv. With --fill, additionally query the
  Ngram Viewer for every term: locally-found terms anchor a per-bin
  share->count scale (median), and MISSING terms get estimated counts from it
  (source: fill); still-missing terms stay MISSING (viewer index omits
  below-threshold words).
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
sys.path.insert(0, str(REPO))  # for the --fill viewer import of util/
ORDERS = (1, 2, 3, 4, 5)
# Per order, the top-N slices to write (the 2/3-gram top-100s replace the
# old viewer-wildcard files that used a different tokenization).
SLICES = {1: (300,), 2: (300, 100), 3: (200, 100), 4: (100,), 5: (50,)}

ALLOWED = re.compile(r"^[a-zàâäéèêëîïôöùûüçñœæ'-]+$")
HAS_LETTER = re.compile(r"[a-zàâäéèêëîïôöùûüçñœæ]")
from util._expressioninput import PARTICLES  # noqa: E402,F401  (left parts of elision particles, one source)


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


def loadBins() -> tuple[dict[int, Counter], dict[int, dict[str, int]]]:
    """Read the orgtre intermediates into per-word-unit-bin Counters, plus the
    viewer-estimated blind-spot fill (see module docstring)."""
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
    return counts, estimated


def queryTerms(terms_path: Path, out_path: Path, fill: bool = False) -> None:
    """Point-query every term against the merged bins (orgtre + estimates),
    far beyond the top-N slices; report coverage. With fill=True, top up the
    MISSING rows with viewer-scaled estimates (see module docstring)."""
    counts, estimated = loadBins()
    merged = {bin_: Counter(cnt) for bin_, cnt in counts.items()}
    for bin_, est in estimated.items():
        merged[bin_].update(est)

    terms: list[str] = []
    seen: set[str] = set()
    with open(terms_path, encoding="utf-8") as fh:
        for line in fh:
            term = normalize(line.strip())
            if not term or term in seen or term.startswith("#"):
                continue
            seen.add(term)
            terms.append(term)

    rows: dict[str, tuple[int, int, str]] = {}  # term -> (bin, freq, source)
    for term in terms:
        bin_ = wordUnits(term)
        if term in merged.get(bin_, {}):
            source = "est" if term in estimated.get(bin_, {}) else "orgtre"
            rows[term] = (bin_, merged[bin_][term], source)
        else:
            rows[term] = (bin_, 0, "MISSING")

    if fill:
        from util.ngram_data import viewerShares  # heavy import, query-time only
        shares = {normalize(ng): share
                  for ng, share in viewerShares(terms).items()}
        # Per-bin share->count scale from the terms known both ways.
        ratios: dict[int, list[float]] = defaultdict(list)
        allRatios: list[float] = []
        for term, (bin_, freq, source) in rows.items():
            share = shares.get(term)
            if source != "MISSING" and share:
                ratios[bin_].append(freq / share)
                allRatios.append(freq / share)
        globalScale = statistics.median(allRatios) if allRatios else 0
        for term, (bin_, freq, source) in list(rows.items()):
            if source != "MISSING":
                continue
            share = shares.get(term)
            if not share:
                continue  # below the viewer's threshold too
            anchors = ratios.get(bin_) or allRatios
            scale = statistics.median(anchors) if anchors else 0
            rows[term] = (bin_, round(share * scale), "fill")
            print(f"filled {term!r} (bin {bin_}, "
                  f"{'bin' if ratios.get(bin_) else 'GLOBAL'} scale)", file=sys.stderr)

    found = sum(1 for _, (_, _, source) in rows.items() if source != "MISSING")
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("term\tword_units\tfreq\tsource\n")
        for term in terms:  # input order
            bin_, freq, source = rows[term]
            out.write(f"{term}\t{bin_}\t{freq}\t{source}\n")
    total = len(terms)
    print(f"{found}/{total} terms found "
          f"({total - found} missing beyond orgtre depth) -> {out_path}")


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--fill"]
    fill = len(args) != len(sys.argv[1:])
    if args and args[0] == "--query":
        terms_path = Path(args[1])
        out_path = (Path(args[2]) if len(args) > 2
                    else REPO / "scratch" / "tao_coverage.tsv")
        queryTerms(terms_path, out_path, fill=fill)
        return

    counts, estimated = loadBins()
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
