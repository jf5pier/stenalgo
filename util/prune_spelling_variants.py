#!/bin/env python
#
# Physically removes the dropped variant spellings (resources/spellingVariants.tsv,
# status "active" rows; see util/build_spelling_variants.py) from
# resources/LexiqueSynthetic.tsv.
#
# LexiqueMixte.tsv is NOT touched: python lexique.py regenerates it clean
# (src.spellingvariants hooks in Lexique.read_corpus and
# Lexique.outputMixedLexique). The synthetic file is append-only by design, so
# rows written earlier for a now-dropped spelling linger until this prune runs.
# Dictionary.readCorpus also filters at load time, so the pipeline is correct
# even before the prune -- this just keeps the file from carrying dead rows
# (and the S2 convergence md5 from being perturbed by them).
#
# Dry-run by default: reports what would go. --apply rewrites the file in
# place, preserving each row's own line ending.
import argparse
import csv
import sys

from src.spellingvariants import loadSpellingVariantDrops

LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prune dropped variant-spelling rows from "
                    "resources/LexiqueSynthetic.tsv (dry-run by default).")
    parser.add_argument("--apply", action="store_true",
                        help="Rewrite the file in place (default: dry-run).")
    parser.add_argument("--path", default=LEXIQUE_SYNTHETIC_PATH)
    args = parser.parse_args()

    drops = loadSpellingVariantDrops()
    if not drops.dropLemmes and not drops.dropOrthos:
        print("No active variant drops (resources/spellingVariants.tsv) -- "
              "nothing to prune.")
        return

    # Canonical -> lemmes of Mixte rows spelled with it: same-paradigm
    # variant verb rows ("absout" under lemme "absoudre", which carries the
    # canonical "absous") drop, while a kept different verb's form ("boite"
    # of "boiter") stays exempt.
    carriers: dict[str, set[str]] = {}
    try:
        with open(LEXIQUE_MIXTE_PATH, newline="") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                carriers.setdefault(row["ortho"], set()).add(row["lemme"])
    except FileNotFoundError:
        pass
    drops = drops.withCanonicalCarriers(
        {ortho: frozenset(lemmes) for ortho, lemmes in carriers.items()})

    with open(args.path, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\r\n").split("\t")
    lemmeIdx, orthoIdx = header.index("lemme"), header.index("ortho")
    cgramIdx = header.index("cgram")

    kept: list[str] = [lines[0]]
    removedByLemme = removedByOrtho = 0
    for line in lines[1:]:
        columns = line.rstrip("\r\n").split("\t")
        if drops.isDroppedLemme(columns[lemmeIdx]):
            removedByLemme += 1
        elif drops.isDroppedOrthoRow(columns[orthoIdx], columns[lemmeIdx],
                                     columns[cgramIdx]):
            removedByOrtho += 1
        else:
            kept.append(line)

    total = removedByLemme + removedByOrtho
    print(f"{args.path}: {len(lines) - 1} rows -> {len(kept) - 1} rows "
          f"({total} pruned: {removedByLemme} by lemme, "
          f"{removedByOrtho} by ortho).")
    if total == 0:
        return
    if not args.apply:
        print("Dry-run only; rerun with --apply to rewrite the file.")
        return
    with open(args.path, "w", newline="") as f:
        f.writelines(kept)
    print("File rewritten. Delete the pickles and rebuild the pipeline "
          "(python dictionary.py).")


if __name__ == "__main__":
    main()
