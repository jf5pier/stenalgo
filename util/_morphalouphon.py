"""
Morphalou 3.1 pronunciations as a reference for NOM/ADJ rows: conversion of Morphalou's `PHONETIQUE` notation into the lexicon
alphabet of util/_pronunciation.py, the index (lemme, ortho, cgram, genre, nombre) -> pronunciations, and a calibration against
LexiqueMixte.tsv.

Notation (LISEZ-MOI.html only names the column; the rest is inferred from the data, see MORPHALOU_TO_LEXICON): phonemes separated by
spaces, `OU` between alternative transcriptions, `/` a marker glued to a mid vowel (`E/`, `O/`: the open/close alternation of a
non-final syllable) that carries no phoneme of its own. Nasals are `a~ e~ o~ 9~`.

The CSV is external and gitignored (README, Morphalou paragraph); the index is optional.

Run: python -m util._morphalouphon --stats   (calibration against resources/LexiqueMixte.tsv)
"""
import argparse
import csv
import os
import sys
import time
import warnings
from collections import Counter, defaultdict
from pathlib import Path

from util._pronunciation import compare

MORPHALOU_PATH_DEFAULT = "morphalou/Morphalou3.1_CSV.csv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
README_HINT = "see the Morphalou paragraph of README.md (extract Morphalou 3.1 under morphalou/, gitignored)"

# Morphalou symbol -> lexicon symbol; the symbols not listed are identical (a b d e f g i j k l m n p s t u v w y z, and the
# vowels E O o a which share the SAMPA meaning). The mapping of the non-obvious ones was calibrated on the data.
MORPHALOU_TO_LEXICON = {
    "a~": "@", "e~": "5", "o~": "§", "9~": "1",
    "J": "N",   # palatal nasal (`a k a J a R d e`, acagnarder)
    "N": "G",   # velar nasal (`b a s t i N`, bastringue... -ing)
    "H": "8",   # labio-palatal glide (`a k H i t e`)
    "@": "°",   # Morphalou writes the schwa @ (`p O l i s @`) and the nasal a~ where the lexicon has @
    "6": "9",   # open-mid front rounded variant (`a b R 6 v a Z @`, alternative to 2)
}
LEXICON_SYMBOLS = set("RaeiEtslkp@dmnjOybfzvugZ5SwO928NG1°o§") | set("abdefgijklmnoprstuvwyz")
ALTERNATIVE_SEPARATOR = "OU"
MARKER = "/"

Key = tuple[str, str, str, str, str]  # (lemme, ortho, cgram, genre, nombre)
CATEGORIES = {"Nom commun": "NOM", "Adjectif qualificatif": "ADJ"}
GENDERS = {"masculine": ("m",), "feminine": ("f",), "invariable": ("m", "f")}
NUMBERS = {"singular": ("s",), "plural": ("p",), "invariable": ("s", "p")}


def morphalouToLexicon(phon: str, unknown: Counter[str] | None = None) -> set[str]:
    """The lexicon spellings of a Morphalou transcription, one per `OU` alternative. A transcription holding a symbol outside
    the known alphabet gives no variant for that alternative; the offending tokens are counted in `unknown` when given."""
    result: set[str] = set()
    for alternative in phon.split(ALTERNATIVE_SEPARATOR):
        out: list[str] = []
        valid = True
        for token in alternative.replace(MARKER, " ").split():
            symbol = MORPHALOU_TO_LEXICON.get(token, token)
            if len(symbol) == 1 and symbol in LEXICON_SYMBOLS:
                out.append(symbol)
            else:
                valid = False
                if unknown is not None:
                    unknown[token] += 1
        if valid and out:
            result.add("".join(out))
    return result


def loadMorphalouPronunciations(path: str | Path = MORPHALOU_PATH_DEFAULT, required: bool = True,
                                unknown: Counter[str] | None = None) -> dict[Key, set[str]]:
    """The NOM/ADJ index (lemme, ortho, cgram, genre, nombre) -> lexicon pronunciations of the inflected forms. A missing CSV
    raises FileNotFoundError when `required`, else warns and returns an empty index. An `invariable` genre or number is
    stored under both of its values; a `-` genre falls back on the lemma's."""
    if not os.path.exists(path):
        message = f"Morphalou CSV not found at {path}: {README_HINT}"
        if required:
            raise FileNotFoundError(message)
        warnings.warn(message)
        return {}
    index: dict[Key, set[str]] = defaultdict(set)
    lemme = category = lemmeGenre = ""
    with open(path, encoding="utf-8", errors="replace", newline="") as csvFile:
        for row in csv.reader(csvFile, delimiter=";"):
            if len(row) < 18 or (row[0] == "GRAPHIE" and row[9] == "GRAPHIE"):
                continue
            if row[0]:
                lemme, category, lemmeGenre = row[0], row[2], row[5]
            cgram = CATEGORIES.get(category)
            if cgram is None or not row[9] or not row[16].strip():
                continue
            genres = GENDERS.get(row[13]) or GENDERS.get(lemmeGenre) or ("",)
            numbers = NUMBERS.get(row[11], ("",))
            phons = morphalouToLexicon(row[16], unknown)
            if not phons:
                continue
            for genre in genres:
                for number in numbers:
                    index[(lemme, row[9], cgram, genre, number)] |= phons
    return dict(index)


def byOrthoCgram(index: dict[Key, set[str]]) -> dict[tuple[str, str], set[str]]:
    """The coarser view (ortho, cgram) -> every pronunciation, for rows whose lemma or slot is not matched."""
    coarse: dict[tuple[str, str], set[str]] = defaultdict(set)
    for (_, ortho, cgram, _, _), phons in index.items():
        coarse[(ortho, cgram)] |= phons
    return dict(coarse)


def lookup(index: dict[Key, set[str]], coarse: dict[tuple[str, str], set[str]], lemme: str, ortho: str, cgram: str,
           genre: str, nombre: str) -> tuple[set[str], str]:
    """(pronunciations, level): 'slot' when (lemme, ortho, cgram, genre, nombre) matches, else 'ortho' on (ortho, cgram), else ('', 'none')."""
    found = index.get((lemme, ortho, cgram, genre, nombre))
    if found:
        return found, "slot"
    found = coarse.get((ortho, cgram))
    if found:
        return found, "ortho"
    return set(), "none"


def calibrate(index: dict[Key, set[str]], mixtePath: str = LEXIQUE_MIXTE_PATH, topDifferences: int = 30) -> str:
    coarse = byOrthoCgram(index)
    levels: Counter[str] = Counter()
    verdicts: dict[str, Counter[str]] = {"slot": Counter(), "ortho": Counter()}
    equivalent: Counter[str] = Counter()
    patterns: Counter[str] = Counter()
    examples: dict[str, str] = {}
    with open(mixtePath, encoding="utf-8", newline="") as tsv:
        for row in csv.DictReader(tsv, delimiter="\t"):
            if row["cgram"] not in ("NOM", "ADJ"):
                continue
            refs, level = lookup(index, coarse, row["lemme"], row["ortho"], row["cgram"], row["genre"], row["nombre"])
            levels[level] += 1
            if level == "none":
                continue
            verdict, detail = compare(row["phon"], refs)
            verdicts[level][verdict] += 1
            if verdict == "equivalent":
                equivalent[detail] += 1
            elif verdict == "differs":
                patterns[detail] += 1
                examples.setdefault(detail, f"{row['ortho']} {row['phon']} / {sorted(refs)}")
    lines = ["NOM/ADJ rows of LexiqueMixte.tsv: " + ", ".join(f"{k} {v}" for k, v in sorted(levels.items()))]
    for level in ("slot", "ortho"):
        total = sum(verdicts[level].values())
        if total:
            lines.append(f"reference by {level}: {total} rows; " + ", ".join(
                f"{v} {verdicts[level][v]} ({100 * verdicts[level][v] / total:.1f}%)" for v in ("exact", "equivalent", "differs")))
    both = verdicts["slot"] + verdicts["ortho"]
    total = sum(both.values())
    if total:
        lines.append(f"all references: {total} rows; " + ", ".join(
            f"{v} {both[v]} ({100 * both[v] / total:.1f}%)" for v in ("exact", "equivalent", "differs")))
    lines.append("equivalent by relaxation: " + ", ".join(f"{k} {v}" for k, v in equivalent.most_common()))
    lines.append(f"top {topDifferences} first-difference patterns:")
    for pattern, count in patterns.most_common(topDifferences):
        lines.append(f"  {count:6d}  {pattern}   e.g. {examples[pattern]}")
    return "\n".join(lines)


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stats", action="store_true", help="print the calibration against LexiqueMixte.tsv")
    parser.add_argument("--morphalou", default=MORPHALOU_PATH_DEFAULT)
    args = parser.parse_args()
    if not args.stats:
        parser.print_help()
        return
    start = time.time()
    unknown: Counter[str] = Counter()
    try:
        index = loadMorphalouPronunciations(args.morphalou, unknown=unknown)
    except FileNotFoundError as error:
        sys.exit(str(error))
    print(f"{len(index)} (lemme, ortho, cgram, genre, nombre) keys with a pronunciation; unknown symbols: "
          f"{sum(unknown.values())} {dict(unknown.most_common(10))}")
    print(calibrate(index))
    print(f"{time.time() - start:.0f} s")


if __name__ == "__main__":
    main()
