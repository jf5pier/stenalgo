#!/bin/env python
#
# Plan Category C, item 1: resources/LexiqueInfraCorrespondance.tsv has 4 rows
# (marin x2, marins x2) whose phono field reads the literal string "Mar-05"
# instead of "maR5" -- Excel autocorrect reading the phoneme string as a date
# ("5-Mar") when the file was opened/saved in Excel, the same underlying
# failure mode as the _xlfn.SINGLE(...) corruption fixed by
# util/fixXlfnSingleCorruption.py, just a different Excel misinterpretation.
# A lexicon-wide sweep for the same date-like shape (^[A-Za-z]{3}-\d{1,2}$)
# found no other instances -- this script is deliberately scoped to exactly
# these two orthos rather than a general date-corruption fixer.
#
# Dry-run by default: only reads and reports. --apply corrects the phono
# field in place. Idempotent: a no-op if run again after a successful
# --apply.
import argparse

LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"

OLD_TO_NEW: dict[str, str] = {
    "Mar-05": "maR5",
}


def findAndFix(apply: bool) -> list[str]:
    with open(LEXIQUE_INFRA_PATH, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx = header.index("item")
    phonoIdx = header.index("phono")

    fixed: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        oldPhono = fields[phonoIdx]
        if oldPhono not in OLD_TO_NEW:
            continue
        newPhono = OLD_TO_NEW[oldPhono]
        fixed.append(f"item={fields[itemIdx]!r} phono {oldPhono!r} -> {newPhono!r}")
        if apply:
            fields[phonoIdx] = newPhono
            lines[i] = "\t".join(fields) + "\n"

    if apply and fixed:
        with open(LEXIQUE_INFRA_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return fixed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix the 'Mar-05' Excel date-autocorrect corruption of "
        "marin/marins' phono field in LexiqueInfraCorrespondance.tsv."
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
    print(f"Total rows fixed: {len(fixed)} (expected {len(OLD_TO_NEW)} distinct value(s), 4 rows)")
    if args.apply:
        print(f"--apply: updated {LEXIQUE_INFRA_PATH}")


if __name__ == "__main__":
    main()
