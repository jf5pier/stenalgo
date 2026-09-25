#!/bin/env python
#
# Corrects item B45 in resources/LexiqueSynthetic.tsv: the past participles that
# src/verbparadigm.py's generateMissingParticiple synthesized while
# spliceParticiplePhon still copied its donor's phonology across genders. A masculine
# spliced from a consonant-final feminine kept the feminine's consonant ("promis"
# /pRomiz/, "enclos" /@kloz/), and a feminine spliced from the masculine lacked it
# ("découverte" /dekuvER/, "éconduites" /ek§d8i/).
#
# The fix is row-local: each synthetic participle row keeps its own phonology and
# only gains or loses the gender consonant of its lemma's feminine stem, via the same
# spliceParticiplePhon the generator now uses (the row stands as a donor of the other
# gender). The feminine spelling comes from the row itself or, for a masculine row,
# from any feminine participle row of the same lemma in either lexicon. Rows that
# duplicate an attested LexiqueMixte participle (same ortho, lemma, gender, number)
# are deleted: they were generated before a lexicon fix filled the attested row's
# gender/number (e3b0358), and the attested row supersedes them.
#
# Dry-run by default: only reads and reports. --apply rewrites the phon and syll_cv
# fields in place (keeping every row's own line ending) and drops the duplicates.
# Rerun Synthetic Lexicon Building (S2) afterwards, with the pickles deleted.
import argparse
import collections
import csv
import sys

from src.verbparadigm import spliceParticiplePhon
from src.word import GramCat, Word

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"


def isParticipleRow(row: dict[str, str]) -> bool:
    return (
        row["cgram"] == "VER" and "par:pas" in row["infover"]
        and row["genre"] in ("m", "f") and row["nombre"] in ("s", "p")
    )


def participleWord(row: dict[str, str], gender: str, ortho: str) -> Word:
    return Word(
        ortho=ortho, phonology=row["phon"], lemme=row["lemme"],
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=gender, number=row["nombre"], infoVerb="par:pas;",
        rawSyllCV=row["syll_cv"], rawOrthosyllCV=row["orthosyll_cv"],
        frequencyBook=0.0, frequencyFilm=0.0,
    )


def readRows(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add or drop the feminine-stem consonant in the synthetic past-participle "
        "rows of resources/LexiqueSynthetic.tsv, and drop the ones an attested row supersedes (item B45)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to resources/LexiqueSynthetic.tsv (default: dry-run).",
    )
    args = parser.parse_args()

    attestedSlots: set[tuple[str, str, str, str]] = set()
    feminineOrthoByLemme: dict[str, str] = {}
    for path in (LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH):
        for row in readRows(path):
            if not isParticipleRow(row):
                continue
            if path == LEXIQUE_MIXTE_PATH:
                attestedSlots.add((row["ortho"], row["lemme"], row["genre"], row["nombre"]))
            if row["genre"] == "f":
                feminineOrthoByLemme.setdefault(row["lemme"], row["ortho"])

    with open(LEXIQUE_SYNTHETIC_PATH, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\r\n").split("\t")
    phonIdx, syllIdx = header.index("phon"), header.index("syll_cv")

    kept = [lines[0]]
    counts: collections.Counter[str] = collections.Counter()
    examples: dict[str, list[str]] = collections.defaultdict(list)
    for line in lines[1:]:
        body = line.rstrip("\r\n")
        fields = body.split("\t")
        row = dict(zip(header, fields))
        if not body.strip() or not isParticipleRow(row):
            kept.append(line)
            continue
        counts["selected"] += 1
        label = f"  {row['ortho']:<16} {row['lemme']:<16} {row['genre']}_{row['nombre']}"
        if (row["ortho"], row["lemme"], row["genre"], row["nombre"]) in attestedSlots:
            counts["deleted"] += 1
            examples["deleted"].append(f"{label} {row['phon']}")
            continue
        if row["genre"] == "f":
            donor = participleWord(row, "m", row["ortho"])
        elif row["lemme"] in feminineOrthoByLemme:
            donor = participleWord(row, "f", feminineOrthoByLemme[row["lemme"]])
        else:
            counts["no feminine spelling"] += 1
            kept.append(line)
            continue
        try:
            new = spliceParticiplePhon(donor, row["genre"], row["ortho"])
        except ValueError as error:
            counts["error"] += 1
            examples["error"].append(f"{label} {error}")
            kept.append(line)
            continue
        old = (fields[phonIdx], fields[syllIdx].replace("_#", "").replace("#", ""))
        if new == old:
            kept.append(line)
            continue
        kind = "masculine consonant dropped" if row["genre"] == "m" else "feminine consonant added"
        counts[kind] += 1
        examples[kind].append(f"{label} {fields[phonIdx]} {fields[syllIdx]} -> {new[0]} {new[1]}")
        fields[phonIdx], fields[syllIdx] = new
        kept.append("\t".join(fields) + line[len(body):])

    print(", ".join(f"{name}: {count}" for name, count in counts.items()))
    for kind, lines_ in examples.items():
        print(f"{kind}:")
        print("\n".join(lines_))

    if len(kept) == len(lines) and not any(k.endswith(("dropped", "added")) for k in counts):
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)
    if args.apply:
        with open(LEXIQUE_SYNTHETIC_PATH, "w", newline="") as f:
            f.writelines(kept)
        print(f"--apply: wrote {LEXIQUE_SYNTHETIC_PATH}")


if __name__ == "__main__":
    main()
