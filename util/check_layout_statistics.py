"""Hand-run proof that the layout statistics (src/layoutstatistics.py) are rebuilt right from a phonetic theory.

Run: python -m util.check_layout_statistics [--skip-rewrite]   (from the repo root; ~6 min: three statistics builds and their ambiguity tables)

1. refactor: a fresh Dictionary() built from the lexicons (Dictionary.analyseSyllabification, now a caller of buildSyllableStatistics) must give
   the statistics of the committed Dictionary.pickle EXACTLY (same words, same order: floats equal). Two outputs of the biphoneme order
   optimizer are not deterministic across processes and are compared loosely: the best permutation STRING (it starts from a set, so it follows
   Python's hash seed; its scores are compared) and the pairwise order scores (relative 1e-9).
2. theory: buildSyllableStatistics on the words of the original PhoneticTheory.pickle with the plain top-200 exclusion must give the same
   statistics. The order of the words differs from the lexicon's, so floats are compared to a relative 1e-9, and the order lists are reported
   separately (a tie in frequency can be sorted either way). Any difference of CONTENT (a missing syllable, a different weight) is listed.
3. rewrite (informational, skipped by --skip-rewrite): the same on the rewritten theory (resources/phonologyOverrides.tsv) with the exclusion
   minus the overridden spellings; prints the phoneme weights that moved.

Exit 1 when check 1 or 2 finds a difference of content. Needs Dictionary.pickle, PhoneticTheory.pickle, starboard3h.json and the lexicons.
"""
import argparse
import math
import pickle
import sys
from typing import Any

from dictionary import Dictionary
from src.grammar import Syllable
from src.keyboard import Starboard
from src.strokes import Strokes
from src.layoutstatistics import (
    ambiguityTables, buildSyllableStatistics, canonicalStatistics, layoutInput, loadFrequentWords,
)
from src.phonologyrewrite import loadPhonologyRules
from src.word import Word
from util._theoryio import loadDictionary

RELATIVE_TOLERANCE = 1e-9
SHOWN = 15


def diff(expected: Any, actual: Any, path: str, exact: bool, out: list[str]) -> None:
    """Appends to `out` each place where the two canonical forms differ in content (lists under an `*Order` key are skipped: see orderDiff)."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected.keys() | actual.keys():
            if key not in actual:
                out.append(f"{path}/{key}: only in the baseline ({expected[key]!r:.60})")
            elif key not in expected:
                out.append(f"{path}/{key}: only in the new build ({actual[key]!r:.60})")
            elif key == "bestPermutation":
                # the permutation string starts from a set (Python's hash seed picks it); its scores are what must agree
                diff(expected[key][1:], actual[key][1:], f"{path}/{key}[1:]", exact, out)
            elif key == "pairwiseScore":
                # float sums over a set: equal to ~1e-13 only
                diff(expected[key], actual[key], f"{path}/{key}", False, out)
            elif not key.endswith("Order"):
                diff(expected[key], actual[key], f"{path}/{key}", exact, out)
    elif isinstance(expected, list) and isinstance(actual, list) and len(expected) == len(actual):
        for position, (e, a) in enumerate(zip(expected, actual)):
            diff(e, a, f"{path}[{position}]", exact, out)
    elif isinstance(expected, float) and isinstance(actual, (int, float)):
        same = expected == actual if exact else math.isclose(expected, actual, rel_tol=RELATIVE_TOLERANCE, abs_tol=1e-12)
        if not same:
            out.append(f"{path}: {expected!r} -> {actual!r}")
    elif expected != actual:
        out.append(f"{path}: {expected!r:.60} -> {actual!r:.60}")


def orderDiff(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key, value in expected.items():
        if key.endswith("Order") and value != actual.get(key):
            out.append(key)
        elif isinstance(value, dict) and isinstance(actual.get(key), dict):
            out.extend(f"{key}/{sub}" for sub in orderDiff(value, actual[key]))
    return out


def statisticsOf(words: list[Word], excluded: set[str]) -> dict[str, Any]:
    from src.grammar import SyllableCollection
    collection = buildSyllableStatistics(words, excluded, SyllableCollection())
    Syllable.optimizeBiphonemeOrder()
    return canonicalStatistics(collection, ambiguityTables(collection))


def report(title: str, expected: dict[str, Any], actual: dict[str, Any], exact: bool) -> bool:
    differences: list[str] = []
    diff(expected, actual, "", exact, differences)
    orders = orderDiff(expected, actual)
    print(f"\n== {title}: {len(differences)} difference(s) of content" + ("" if not orders else f", order lists differing: {orders}"))
    for line in sorted(differences)[:SHOWN]:
        print("  ", line)
    if len(differences) > SHOWN:
        print(f"   ... and {len(differences) - SHOWN} more")
    return not differences


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skip-rewrite", action="store_true", help="skip check 3 (the rewritten theory)")
    args = parser.parse_args()

    pickled = loadDictionary()
    pickled.ensureAmbiguityStats()
    baseline = canonicalStatistics(pickled.syllableCollection, {
        "syllabicAmbiguity": pickled.syllabicAmbiguity, "lexicalAmbiguity": pickled.lexicalAmbiguity,
        "syllabicPartAmbiguity": pickled.syllabicPartAmbiguity})
    assert loadFrequentWords() == pickled.frequentWords, "loadFrequentWords differs from Dictionary.frequentWords"
    frequentWords = pickled.frequentWords
    del pickled

    fresh = Dictionary()
    fresh.analyseSyllabification()
    Syllable.optimizeBiphonemeOrder()
    fresh.analyseAmbiguities()
    freshStatistics = canonicalStatistics(fresh.syllableCollection, {
        "syllabicAmbiguity": fresh.syllabicAmbiguity, "lexicalAmbiguity": fresh.lexicalAmbiguity,
        "syllabicPartAmbiguity": fresh.syllabicPartAmbiguity})
    ok = report("1. refactor: fresh lexicon build vs Dictionary.pickle (exact)", baseline, freshStatistics, exact=True)
    print("   order lists identical" if not orderDiff(baseline, freshStatistics) else "   ORDER LISTS DIFFER")
    del fresh

    with open("PhoneticTheory.pickle", "rb") as pfile:
        theory: dict[Strokes, list[Word]] = pickle.load(pfile)
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    assert keyboard is not None
    theoryWords, excluded = layoutInput(theory, frequentWords, keyboard, rewrite=False)
    print(f"\nthe original theory holds {len(theoryWords)} distinct words")
    ok = report("2. theory: original theory words vs Dictionary.pickle (relative 1e-9)", baseline,
                statisticsOf(theoryWords, excluded), exact=False) and ok

    if not args.skip_rewrite:
        rewrittenWords, rewrittenExcluded = layoutInput(theory, frequentWords, keyboard, rewrite=True)
        rewritten = statisticsOf(rewrittenWords, rewrittenExcluded)
        print(f"\nthe rewritten theory holds {len(rewrittenWords)} distinct words; exclusion minus {sorted(loadPhonologyRules().phonology)}")
        for part in ("onset", "nucleus", "coda"):
            before, after = baseline[part]["phonemes"], rewritten[part]["phonemes"]
            moved = sorted(((after.get(p, [0.0])[0] - before.get(p, [0.0])[0], p) for p in before.keys() | after.keys()), reverse=True)
            print(f"   {part}: " + ", ".join(f"{p} {delta:+,.0f}" for delta, p in moved if abs(delta) > 1e-9))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
