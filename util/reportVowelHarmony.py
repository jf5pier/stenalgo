#!/bin/env python
#
# Read-only report: within-lemma vowel-harmony (harmonisation vocalique) candidates in
# LexiqueMixte.tsv. For every lemma, the mid vowel at each (unit index from the word
# start, orthographic unit) position is compared across the lemma's rows; where the
# rows split between the lax and the tense member of a pair (E/e, O/o, 9/2) the position
# is reported with the vowel of the FOLLOWING syllable of each variant.
#
# Classes (heuristic, for human validation -- nothing is written to the lexicon):
#   harmony    every tense row is followed by a high/tense nucleus (i y u j w e o 2 8) and no
#              lax row is: the classic assimilation (essayais /esEjE/ vs essaie /EsE/ is NOT
#              this: see below), lax = the lemma's own vowel to protect
#   reverse    the lax rows are the ones followed by a high/tense nucleus (odd, review)
#   mixed      the following-syllable evidence overlaps or is absent: lexicon noise, or a
#              real alternation (accéder/accède)
#   position   lax rows all in closed syllables, tense rows all in open ones (loi de position,
#              abonne/abonner): regular, reported only with --all
#   ortho-alt  the spelling itself carries the alternation (é vs è, ai/ei...): reported
#              only with --all, these belong to the generator, not to a fix
# The class is only a hint: the columns list the minority forms so a human decides.
#
# Usage: python -m util.reportVowelHarmony [--out scratch/vowel-harmony-report.tsv]
import argparse
import collections
import csv
from dataclasses import dataclass, field

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
PAIRS = {"E": "e", "e": "E", "O": "o", "o": "O", "9": "2", "2": "9"}
LAX = frozenset("EO9")
HIGH_OR_TENSE = frozenset("iyujw8eo2")
NUCLEI = frozenset("aeiouyEO29568@§1°")
ACCENTED_ORTHO = frozenset({"é", "è", "ê", "ë", "ai", "ei", "aî", "eî", "œu", "eu", "oe"})


@dataclass
class Variant:
    forms: list[str] = field(default_factory=list)
    following: collections.Counter = field(default_factory=collections.Counter)
    closed: collections.Counter = field(default_factory=collections.Counter)


def alignedUnits(row: dict[str, str]) -> list[tuple[int, int, str, str]] | None:
    """(unit index, syllable index, phoneme unit, ortho unit) for every unit, or None."""
    phon = [s.split("_") for s in row["syll_cv"].split("|")]
    ortho = [s.split("_") for s in row["orthosyll_cv"].split("|")]
    if [len(s) for s in phon] != [len(s) for s in ortho]:
        return None
    flat = []
    for si, (ps, os_) in enumerate(zip(phon, ortho)):
        for p, o in zip(ps, os_):
            flat.append((len(flat), si, p, o.lower()))
    return flat


def followingNucleus(units: list[tuple[int, int, str, str]], at: int) -> str:
    syllable = units[at][1]
    for _, si, p, _ in units[at + 1:]:
        if si > syllable and p[:1] in NUCLEI:
            return p[:1]
    return "-"


def classify(tense: Variant, lax: Variant) -> str:
    tenseHigh = [n in HIGH_OR_TENSE for n in tense.following.elements()]
    laxHigh = [n in HIGH_OR_TENSE for n in lax.following.elements()]
    if all(tenseHigh) and not any(laxHigh):
        return "harmony"
    if all(laxHigh) and not any(tenseHigh):
        return "reverse"
    return "mixed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only report of within-lemma vowel-harmony candidates in LexiqueMixte.tsv.")
    parser.add_argument("--out", default="scratch/vowel-harmony-report.tsv")
    parser.add_argument("--all", action="store_true", help="Also report spelling-carried alternations.")
    args = parser.parse_args()

    with open(LEXIQUE_MIXTE_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    byLemma: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in rows:
        byLemma[row["lemme"]].append(row)

    report = []
    for lemme, lemmaRows in byLemma.items():
        positions: dict[tuple[int, str], dict[str, Variant]] = collections.defaultdict(
            lambda: collections.defaultdict(Variant))
        for row in lemmaRows:
            if row["infover"].startswith("par") and row["cgram"] != "VER":
                pass
            units = alignedUnits(row)
            if units is None:
                continue
            for i, (idx, si, p, o) in enumerate(units):
                if p in PAIRS and o not in ("",):
                    v = positions[(idx, o)][p]
                    v.forms.append(row["ortho"])
                    v.following[followingNucleus(units, i)] += 1
                    nxt = units[i + 1][3] if i + 1 < len(units) else ""
                    geminate = len(nxt) == 2 and nxt[0] == nxt[1] or nxt == "sc" or nxt == "x"
                    v.closed[(i + 1 < len(units) and units[i + 1][1] == si) or geminate] += 1
        for (idx, o), variants in positions.items():
            laxVowels = [p for p in variants if p in LAX]
            for lax in laxVowels:
                tense = PAIRS[lax]
                if tense not in variants:
                    continue
                cls = classify(variants[tense], variants[lax])
                if variants[lax].closed[False] == 0 and variants[tense].closed[True] == 0:
                    cls = "position"  # lax closed, tense open: the regular loi de position
                if o in ACCENTED_ORTHO:
                    cls = "ortho-alt"
                if cls in ("ortho-alt", "position") and not args.all:
                    continue
                v1, v2 = variants[lax], variants[tense]
                minority = v1 if len(v1.forms) < len(v2.forms) else v2
                report.append({
                    "lemme": lemme, "position": idx, "ortho_unit": o, "pair": f"{lax}/{tense}",
                    "lax_rows": len(v1.forms), "tense_rows": len(v2.forms), "class": cls,
                    "lax_next": ",".join(f"{k}{v}" for k, v in sorted(v1.following.items())),
                    "tense_next": ",".join(f"{k}{v}" for k, v in sorted(v2.following.items())),
                    "minority": ("lax" if minority is v1 else "tense") + ": " +
                                " ".join(sorted(set(minority.forms))[:6]),
                    "majority": " ".join(sorted(set((v2 if minority is v1 else v1).forms))[:4]),
                })

    order = {"harmony": 0, "reverse": 1, "mixed": 2, "position": 3, "ortho-alt": 4}
    report.sort(key=lambda r: (order[r["class"]], r["pair"], r["lemme"]))
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(report[0]) if report else ["lemme"], delimiter="\t")
        writer.writeheader()
        writer.writerows(report)
    counts = collections.Counter((r["class"], r["pair"]) for r in report)
    print(f"{len(report)} (lemma, position) disagreements in {len({r['lemme'] for r in report})} lemmas -> {args.out}")
    for (cls, pair), n in sorted(counts.items(), key=lambda kv: (order[kv[0][0]], kv[0][1])):
        print(f"  {cls:10} {pair}: {n}")


if __name__ == "__main__":
    main()
