"""Build scratch/expr_candidates.tsv: the Phase 0 expression candidate pool
(PLAN_2026-10-01-abbreviations-algorithm.md, Phase 0 step 3).

Pool = every row of the widest n-gram slice per order (2gram_top300,
3gram_top300, 4gram_top100, 5gram_top50) UNION every term of
scratch/tao_abbreviations.txt. Frequencies come from the same merged bins
`scratch/rebuild_ngrams.py` builds (orgtre window counts + viewer-estimated
fill); tao-only terms take theirs from scratch/tao_coverage.tsv (written by
`rebuild_ngrams.py --query scratch/tao_abbreviations.txt --fill`), so the
viewer point queries are not repeated here.

Token -> theory resolution (the longform a writer must stroke today):
1. the whole token as a lexicon orthography (aujourd'hui, l', jusqu);
2. hyphen split: peut-être -> peut + être;
3. elision split (rebuild_ngrams.PARTICLES): c'est -> c' fragment, else the
   bare left part, else the full form (ce/je/que...) + the host token.
   A glued particle counts as its own word unit (rebuild_ngrams.wordUnits).

A term is DROPPED (logged to scratch/expr_candidates_drops.txt) when any
unit resolves to no Word: the acceptance is every kept row strokes out.

Columns: expr, freq, freq_source (orgtre|est|fill), word_units (steno-theory
count: glued particles are units), words (resolved theory words), sylls,
strokes, phonologies (unit=phono, comma-joined), longform (RTFCRE,
'/'-joined across words), flags (tao,elision,fragMissing,hyphen).

Usage (from the repo root):
- env/bin/python scratch/build_expr_candidates.py           # build the pool
- env/bin/python scratch/build_expr_candidates.py --spotcheck  # top-20 freqs
  vs the Ngram Viewer (one batched request; shares x median scale should
  track freq within bin noise)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scratch.rebuild_ngrams import loadBins, normalize, wordUnits  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from src.word import Word  # noqa: E402
from util._expressioninput import FULL_FORMS, PARTICLES, pickWord, resolveTerm, resolveToken  # noqa: E402,F401
from util._stenorender import renderFinalStrokesToRTFCRE  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402

TAO_LIST = REPO / "scratch" / "tao_abbreviations.txt"
TAO_COVERAGE = REPO / "scratch" / "tao_coverage.tsv"
OUT_TSV = REPO / "scratch" / "expr_candidates.tsv"
DROPS_TXT = REPO / "scratch" / "expr_candidates_drops.txt"
SLICES = {2: "2gram_top300.tsv", 3: "3gram_top200.tsv",
          4: "4gram_top100.tsv", 5: "5gram_top50.tsv"}
def main() -> None:
    spotcheck = "--spotcheck" in sys.argv

    # Frequency bins + the tao coverage fill.
    counts, estimated = loadBins()
    merged: dict[int, dict[str, int]] = {}
    for bin_, cnt in counts.items():
        merged[bin_] = dict(cnt)
    for bin_, est in estimated.items():
        merged.setdefault(bin_, {}).update(est)
    taoFreq: dict[str, tuple[int, str]] = {}
    with open(TAO_COVERAGE, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            term, _, freq, source = line.rstrip("\n").split("\t")
            taoFreq[term] = (int(freq), source)

    # The pool: slice rows and tao terms, normalized and deduplicated.
    pool: dict[str, set[str]] = {}  # term -> origin flags
    for name in SLICES.values():
        with open(REPO / "scratch" / "top_ngrams" / name, encoding="utf-8") as fh:
            for line in fh:
                term = normalize(line.split("\t")[0])
                pool.setdefault(term, set())
    with open(TAO_LIST, encoding="utf-8") as fh:
        for line in fh:
            term = normalize(line.strip())
            if term and not term.startswith("#"):
                pool.setdefault(term, set()).add("tao")

    # Theory lookup.
    starboard = Starboard.fromJSONFile("starboard3h.json")
    assert starboard is not None
    theory = loadDisambiguatedTheory(starboard)
    byOrtho: dict[str, list[Word]] = {}
    for w in theory:
        byOrtho.setdefault(w.ortho, []).append(w)

    rows: list[str] = []
    drops: list[str] = []
    for term in pool:
        origins = pool[term]
        if "tao" in origins:
            freq, source = taoFreq.get(term, (0, "MISSING"))
        else:
            bin_ = wordUnits(term)
            if term in merged.get(bin_, {}):
                freq = merged[bin_][term]
                source = "est" if term in estimated.get(bin_, {}) else "orgtre"
            else:
                freq, source = 0, "MISSING"

        units = resolveTerm(term, byOrtho)
        missing = [display for display, w in units if w is None]
        if missing:
            drops.append(f"{term}\t{','.join(missing)}\t{source}\t{freq}")
            continue

        flags = set(origins)
        gluedLefts = [tok.partition("'")[0] for tok in term.split()
                      if "'" in tok and tok.partition("'")[0] in PARTICLES
                      and tok.partition("'")[2]]
        if gluedLefts:
            flags.add("elision")
            if any(left + "'" not in byOrtho and left not in byOrtho
                   for left in gluedLefts):
                flags.add("fragMissing")
        if "-" in term:
            flags.add("hyphen")

        pairs = [(display, w) for display, w in units if w is not None]
        phonologies = ",".join(f"{display}={w.phonology}"
                               for display, w in pairs)
        longform = "/".join(renderFinalStrokesToRTFCRE(starboard, theory[w][0])
                            for _, w in pairs)
        sylls = sum(len(w.syllCV) for _, w in pairs)
        strokes = sum(len(theory[w][0]) for _, w in pairs)
        rows.append("\t".join((
            term, str(freq), source, str(wordUnits(term)), str(len(pairs)),
            str(sylls), str(strokes), phonologies, longform,
            ",".join(sorted(flags)))))

    rows.sort(key=lambda r: -int(r.split("\t")[1]))
    with open(OUT_TSV, "w", encoding="utf-8") as out:
        out.write("expr\tfreq\tfreq_source\tword_units\twords\tsylls\tstrokes\t"
                  "phonologies\tlongform\tflags\n")
        out.write("\n".join(rows) + "\n")
    with open(DROPS_TXT, "w", encoding="utf-8") as out:
        out.write("term\tmissing_units\tfreq_source\tfreq\n")
        out.write("\n".join(sorted(drops, key=lambda d: -int(d.rsplit("\t", 1)[1]))
                            ) + ("\n" if drops else ""))
    kept = len(rows)
    print(f"{kept} candidates kept, {len(drops)} dropped -> {OUT_TSV}")

    if spotcheck and rows:
        from util.ngram_data import viewerShares
        top = [r.split("\t") for r in rows[:20]]
        shares = viewerShares([r[0] for r in top])
        ratios = sorted(float(r[1]) / shares[r[0]]
                        for r in top if shares.get(r[0]))
        median = ratios[len(ratios) // 2] if ratios else 0
        print("top-20 spot check (freq vs viewer share x median scale):")
        for r in top:
            share = shares.get(r[0])
            ratio = f"{float(r[1]) / share:.2e}" if share else "-"
            print(f"  {r[0]:30} freq={r[1]:>12} source={r[2]:6} "
                  f"viewer_share={share or 0:.3e} ratio={ratio}")
        print(f"  median ratio {median:.2e} (spread "
              f"{ratios[0]:.2e}..{ratios[-1]:.2e})" if ratios else "  no shares")


if __name__ == "__main__":
    main()
