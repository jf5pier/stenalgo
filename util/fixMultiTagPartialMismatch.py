#!/bin/env python
#
# Batch 4 of the lexicon-defect triage plan (see
# util/validateLexiconAgainstVerbiste.py's MULTI_TAG_PARTIAL_MISMATCH flag
# type): a VER row carries multiple tags where at least one agrees with
# `ortho` and at least one doesn't (and the agreeing one isn't "par:pas" --
# that anchor case is PARTICIPE_PLUS_OTHER_TAG, batch 3). E.g.
# "donner"/"donnes" tagged "ind:pre:1p;ind:pre:2s;sub:pre:2s;" -- "donnes" is
# genuinely "tu donnes" (ind:pre:2s/sub:pre:2s), but "ind:pre:1p" is simply
# wrong (that would be "donnons", a different word). Also covers a tag whose
# slot doesn't exist in the template at all (e.g. impersonal/defective verbs
# like "neiger" tagged with a person that doesn't exist, or a mood with no
# 3rd-person imperative) when the row has another, genuinely matching tag to
# anchor on.
#
# Same technique as batch 3 (fixParticipePlusOtherTag.py): reuses
# util.validateLexiconAgainstVerbiste's own validateRow directly so only the
# *specific* tag(s) it flags are removed, never a blanket "keep just one
# tag" -- e.g. "être"/"sommes" tagged "imp:pre:1p;ind:pre:1p;sub:pre:2s;" has
# TWO wrong tags (imp:pre:1p, sub:pre:2s) and one correct one (ind:pre:1p);
# both wrong tags are stripped, leaving "ind:pre:1p;". Duplicate tags (e.g.
# "plaire"/"plut" tagged "...ind:pas:3s;ind:pas:3s;") are also collapsed to
# one occurrence as a side effect.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# `infover` field back to both resources/Lexique383.tsv and
# resources/LexiqueMixte.tsv in place where the defect is confirmed present
# in each (see the provenance check in this script's main()). Idempotent: a
# no-op (0 rows modified) if run again after a successful --apply.
import argparse
import csv

from util.validateLexiconAgainstVerbiste import (
    EXCEPTIONS_PATH,
    MULTI_TAG_PARTIAL_MISMATCH,
    VERBISTE_CONJUGATIONS_PATH,
    VERBISTE_VERBS_PATH,
    validateRow,
)
from src.verbparadigm import loadVerbModelExceptions, loadVerbisteTemplates, parseConjugationTemplates

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def findFlaggedTagsByRow(path: str) -> dict[tuple[str, str, str], set[str]]:
    """Maps (ortho, lemme, infover) -> set of tags flagged MULTI_TAG_PARTIAL_MISMATCH."""
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)

    flaggedByRow: dict[tuple[str, str, str], set[str]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            for flag in validateRow(row, verbisteTemplates, exceptions, conjugationTemplates):
                if flag.flagType != MULTI_TAG_PARTIAL_MISMATCH:
                    continue
                key = (row["ortho"], row["lemme"], row["infover"])
                flaggedByRow.setdefault(key, set()).add(flag.tag)
    return flaggedByRow


def correctedInfoVerb(infoVerb: str, tagsToRemove: set[str]) -> str:
    keptTags: list[str] = []
    for tag in infoVerb.split(";"):
        if not tag or tag in tagsToRemove or tag in keptTags:
            continue
        keptTags.append(tag)
    return ";".join(keptTags) + ";"


def findAndFix(path: str, flaggedByRow: dict[tuple[str, str, str], set[str]], apply: bool
               ) -> tuple[list[tuple[str, str, str]], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    infoverIdx = header.index("infover")

    corrections: list[tuple[str, str, str]] = []  # (ortho, oldInfoVerb, newInfoVerb)
    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        if fields[cgramIdx] != "VER":
            continue
        key = (fields[orthoIdx], fields[lemmeIdx], fields[infoverIdx])
        tagsToRemove = flaggedByRow.get(key)
        if not tagsToRemove:
            continue
        oldInfoVerb = fields[infoverIdx]
        newInfoVerb = correctedInfoVerb(oldInfoVerb, tagsToRemove)
        corrections.append((fields[orthoIdx], oldInfoVerb, newInfoVerb))
        if apply:
            fields[infoverIdx] = newInfoVerb
            lines[i] = "\t".join(fields) + ending
            modified += 1

    if apply and modified:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return corrections, modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strip the specific tag(s) that disagree with `ortho` "
        "from a multi-tag VER row that also has at least one agreeing tag "
        "(e.g. 'ind:pre:1p;ind:pre:2s;sub:pre:2s;' -> 'ind:pre:2s;sub:pre:2s;')."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to Lexique383.tsv and LexiqueMixte.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        flaggedByRow = findFlaggedTagsByRow(path)
        corrections, modified = findAndFix(path, flaggedByRow, args.apply)
        print(f"=== {path} ===")
        for ortho, oldInfoVerb, newInfoVerb in corrections:
            print(f"  ortho={ortho!r}: {oldInfoVerb!r} -> {newInfoVerb!r}")
        print(f"Total rows found: {len(corrections)}")
        if args.apply:
            print(f"--apply: wrote {modified} corrected rows to {path}")
        print()


if __name__ == "__main__":
    main()
