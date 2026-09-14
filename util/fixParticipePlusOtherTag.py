#!/bin/env python
#
# Batch 3 of the lexicon-defect triage plan (see
# util/validateLexiconAgainstVerbiste.py's PARTICIPE_PLUS_OTHER_TAG flag
# type): a VER row is a genuine participle (its "par:pas" tag's
# gender/number-driven expected orthography matches `ortho`) but also
# carries one or more spurious other tags that DON'T match `ortho` (e.g.
# "adapter"/"adapté" tagged "imp:pre:2s;par:pas;" -- "adapté" is the
# masculine-singular past participle, not the imperative "adapte"). Same
# root cause/fix shape as INF_PLUS_OTHER_TAG (batch 2), just anchored on a
# matching "par:pas" tag instead of "inf".
#
# Reuses util.validateLexiconAgainstVerbiste's own validateRow/loading logic
# directly (rather than re-deriving the classification) so the fix can never
# drift out of sync with what the validator flags: for each row, only the
# *specific* tag(s) validateRow flags as PARTICIPE_PLUS_OTHER_TAG are removed
# (see e.g. "dire"/"dit", tagged "ind:fut:3p;ind:pre:3s;ind:pas:3s;par:pas;"
# -- only "ind:fut:3p" is wrong; "ind:pre:3s"/"ind:pas:3s" are independently
# correct homographs of "dit" and must survive). Duplicate tags (e.g.
# "par:pas;par:pas;") are also collapsed to one occurrence as a side effect.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# `infover` field back to both resources/Lexique383.tsv and
# resources/LexiqueMixte.tsv in place (confirmed present in both -- see the
# provenance check in this script's main()). Idempotent: a no-op (0 rows
# modified) if run again after a successful --apply.
import argparse
import csv

from util.validateLexiconAgainstVerbiste import (
    EXCEPTIONS_PATH,
    PARTICIPE_PLUS_OTHER_TAG,
    VERBISTE_CONJUGATIONS_PATH,
    VERBISTE_VERBS_PATH,
    validateRow,
)
from src.verbparadigm import loadVerbModelExceptions, loadVerbisteTemplates, parseConjugationTemplates

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def findFlaggedTagsByRow(path: str) -> dict[tuple[str, str, str], set[str]]:
    """Maps (ortho, lemme, infover) -> set of tags flagged PARTICIPE_PLUS_OTHER_TAG."""
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)

    flaggedByRow: dict[tuple[str, str, str], set[str]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            for flag in validateRow(row, verbisteTemplates, exceptions, conjugationTemplates):
                if flag.flagType != PARTICIPE_PLUS_OTHER_TAG:
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
        description="Strip spurious non-'par:pas' tag(s) from VER rows that "
        "are genuine participles also carrying an unrelated wrong tag (e.g. "
        "'imp:pre:2s;par:pas;' -> 'par:pas;')."
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
