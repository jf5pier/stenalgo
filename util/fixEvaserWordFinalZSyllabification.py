#!/bin/env python
#
# Corrects a syllabification bug in resources/LexiqueSynthetic.tsv (the
# paradigm-completion file, see src/verbparadigm.py) for "évaser": its
# generator always splits the stem-final consonant onto its own trailing
# onset-only syllable, even for word-final forms with nothing after it (e.g.
# "évase"/"évases", phon "evaz" -- the "z" gets "|z_#" instead of packing it
# as the coda of the preceding syllable, "_z_#"). Real corpus-sourced sibling
# forms of the same lemma ("évase" ind:pre:3s, "évasent" ind:pre:3p, both in
# resources/Lexique383.tsv) correctly keep a word-final consonant as a coda
# ("e|v_a_z_#") -- they only split a consonant onto its own syllable when a
# vowel actually follows it (e.g. "évasait" evazE -> "e|v_a|z_E", "évaser"
# evaze -> "e|v_a|z_e", both correct). This script corrects exactly the
# word-final-z rows (phon == "evaz", nothing after the z) to match that
# established pattern; rows where z is genuinely followed by a vowel
# ("évasâtes", "évasasse", ...) are untouched.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# syll_cv/orthosyll_cv fields back into the matching rows of
# resources/LexiqueSynthetic.tsv in place.
import argparse
import csv
import sys

LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"

TARGET_LEMME = "évaser"
TARGET_PHON = "evaz"  # word-final z, nothing follows -- the buggy case


def readTsv(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def isTargetRow(row: dict[str, str]) -> bool:
    return row.get("lemme") == TARGET_LEMME and row.get("phon") == TARGET_PHON


def correctSyllCv(syllCv: str) -> str:
    # "e|v_a|z_#" -> "e|v_a_z_#": merges the erroneous syllable break right
    # before the word-final z. Idempotent: a no-op once already merged.
    return syllCv.replace("a|z_#", "a_z_#")


def correctOrthosyllCv(orthosyllCv: str) -> str:
    # "é|v_a|s_e" -> "é|v_a_s_e" (mirrors correctSyllCv on the orthographic
    # side: the written "s" carries the same z sound). Idempotent.
    return orthosyllCv.replace("a|s_", "a_s_")


class EvaserCorrection:
    def __init__(self, row: dict[str, str]) -> None:
        self.ortho = row["ortho"]
        self.infover = row["infover"]
        self.oldSyllCv = row["syll_cv"]
        self.oldOrthosyllCv = row["orthosyll_cv"]
        self.newSyllCv = correctSyllCv(self.oldSyllCv)
        self.newOrthosyllCv = correctOrthosyllCv(self.oldOrthosyllCv)
        self.changed = (
            self.newSyllCv != self.oldSyllCv or self.newOrthosyllCv != self.oldOrthosyllCv
        )


def findCorrections(rows: list[dict[str, str]]) -> list[EvaserCorrection]:
    return [EvaserCorrection(row) for row in rows if isTargetRow(row)]


def printCorrections(corrections: list[EvaserCorrection]) -> None:
    print("=== évaser word-final-z corrections (dry-run, no files modified) ===\n")
    for c in corrections:
        status = "CHANGED" if c.changed else "already correct"
        print(f"{c.ortho}  ({c.infover})  [{status}]")
        print(f"  syll_cv       : {c.oldSyllCv!r} -> {c.newSyllCv!r}")
        print(f"  orthosyll_cv  : {c.oldOrthosyllCv!r} -> {c.newOrthosyllCv!r}")
        print()


def applyCorrections(path: str, corrections: list[EvaserCorrection]) -> int:
    correctionsByOrthoInfover = {(c.ortho, c.infover): c for c in corrections}
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx, lemmeIdx, phonIdx = header.index("ortho"), header.index("lemme"), header.index("phon")
    infoverIdx = header.index("infover")
    syllCvIdx, orthosyllCvIdx = header.index("syll_cv"), header.index("orthosyll_cv")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        if fields[lemmeIdx] != TARGET_LEMME or fields[phonIdx] != TARGET_PHON:
            continue
        c = correctionsByOrthoInfover.get((fields[orthoIdx], fields[infoverIdx]))
        if c is not None and fields[syllCvIdx] == c.oldSyllCv and fields[orthosyllCvIdx] == c.oldOrthosyllCv:
            fields[syllCvIdx] = c.newSyllCv
            fields[orthosyllCvIdx] = c.newOrthosyllCv
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Correct the "évaser" word-final-z syllabification bug in '
        "resources/LexiqueSynthetic.tsv."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to resources/LexiqueSynthetic.tsv (default: dry-run).",
    )
    args = parser.parse_args()

    rows = readTsv(LEXIQUE_SYNTHETIC_PATH)
    corrections = findCorrections(rows)
    printCorrections(corrections)

    if not corrections:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)

    if args.apply:
        nbModified = applyCorrections(LEXIQUE_SYNTHETIC_PATH, corrections)
        print(f"--apply: wrote {nbModified} corrected rows to {LEXIQUE_SYNTHETIC_PATH}")


if __name__ == "__main__":
    main()
