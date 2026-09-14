#!/bin/env python
#
# Plan Category A, step 3 (see the session plan / PAYER_SYLLCV_AUDIT.md): the
# "ay" grapheme is never pronounced closed /e/ ("ej" in this lexicon's
# alphabet) -- always open /E/ ("Ej"). util/fixPayerNonfuturVowelQuality.py and
# util/fixAyGraphemeEjQuality.py already brought resources/Lexique383.tsv and
# resources/LexiqueMixte.tsv into conformance with this rule. Neither touches
# resources/LexiqueInfraCorrespondance.tsv, which encodes the same "ay"
# grapheme's vowel phoneme independently in TWO places for each row: the
# "phono" summary column (what Lexique.breakdownSyllables() first compares
# against Lexique383.tsv's "phon" to decide whether to attach a breakdown at
# all) and the "assoc" grapheme->phoneme mapping column (what the breakdown
# actually walks letter-by-letter to build syll_cv/orthosyll_cv). Fixing only
# "phono" (an earlier pass of this script did exactly that) is not enough:
# it makes the match succeed, but the breakdown then runs on "assoc"'s own
# stale lowercase "e", so the *content* it produces (syll_cv) still carries
# the wrong vowel quality -- caught by diffing a real `lexique.py`
# `outputMixedLexique()` regeneration against the existing LexiqueMixte.tsv.
#
# Scope: every "assoc" occurrence of the exact substring "<grapheme>-e.y-j"
# (confirmed, exhaustively, to be the only shape this defect takes across all
# 186 affected rows -- no merged "-ej" or other variant needs handling) is
# corrected to "<grapheme>-E.y-j". "phono" is then re-derived directly from
# the corrected "assoc" (via the same associationToPhonology logic
# lexique.py's own fallback path uses), so the two columns are guaranteed
# consistent by construction rather than independently patched.
#
# Dry-run by default: only reads and reports. --apply corrects both fields in
# place. Idempotent: a no-op if run again after a successful --apply.
import argparse
import csv
import re

LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"

ASSOC_PATTERN = re.compile(r'([^.]+)-e\.y-j')


def correctAssoc(assoc: str) -> str | None:
    corrected, count = ASSOC_PATTERN.subn(r'\1-E.y-j', assoc)
    if count == 0:
        return None
    return corrected


def associationToPhonology(asso: str) -> str:
    parts = asso.split(".")
    phono = "".join(p.split("-")[1] for p in parts)
    return phono.replace("#", "")


def findAndFix(apply: bool) -> list[str]:
    with open(LEXIQUE_INFRA_PATH, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx = header.index("item")
    phonoIdx = header.index("phono")
    assocIdx = header.index("assoc")

    fixed: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        item = fields[itemIdx]
        if "ay" not in item:
            continue
        oldAssoc = fields[assocIdx]
        newAssoc = correctAssoc(oldAssoc)
        if newAssoc is None:
            continue
        newPhono = associationToPhonology(newAssoc)
        oldPhono = fields[phonoIdx]
        fixed.append(
            f"item={item!r} assoc {oldAssoc!r} -> {newAssoc!r}; "
            f"phono {oldPhono!r} -> {newPhono!r}"
        )
        if apply:
            fields[assocIdx] = newAssoc
            fields[phonoIdx] = newPhono
            lines[i] = "\t".join(fields) + "\n"

    if apply and fixed:
        with open(LEXIQUE_INFRA_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return fixed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix LexiqueInfraCorrespondance.tsv's 'ay'-grapheme "
        "assoc mapping (and re-derive phono from it) to match the now-"
        "corrected Lexique383.tsv/LexiqueMixte.tsv 'E' vowel quality."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to LexiqueInfraCorrespondance.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    fixed = findAndFix(args.apply)
    print(f"=== {LEXIQUE_INFRA_PATH} ===")
    for f in fixed:
        print(f"  FIX: {f}")
    print(f"Total rows fixed: {len(fixed)}")
    if args.apply:
        print(f"--apply: updated {LEXIQUE_INFRA_PATH}")


if __name__ == "__main__":
    main()
