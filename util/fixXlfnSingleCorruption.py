#!/bin/env python
#
# resources/LexiqueInfraCorrespondance.tsv has 34 rows (27 distinct orthos)
# whose "phono" field was corrupted into a literal Excel internal formula
# token, e.g. "@_xlfn.SINGLE(SJ5)" instead of "@sj5" (for "ancien") -- an
# artifact of the file having been opened/saved in Excel at some point
# (commit 7da7bf3). Since every affected ortho has exactly one distinct
# phon value in resources/Lexique383.tsv, that value is an unambiguous
# source of truth to restore the correct phono.
#
# Dry-run by default: only reads and reports. --apply corrects the phono
# field in place. Idempotent: a no-op if run again after a successful
# --apply (no "_xlfn.SINGLE" tokens left to match).
import argparse
import csv
import re

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"

CORRUPTION_RE = re.compile(r"_xlfn\.SINGLE\(")


def loadLexique383Phons() -> dict[str, set[str]]:
    phonsByOrtho: dict[str, set[str]] = {}
    with open(LEXIQUE_383_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            phonsByOrtho.setdefault(row["ortho"], set()).add(row["phon"])
    return phonsByOrtho


def findAndFix(apply: bool) -> tuple[list[str], list[str]]:
    phonsByOrtho = loadLexique383Phons()

    with open(LEXIQUE_INFRA_PATH, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx = header.index("item")
    phonoIdx = header.index("phono")

    fixed: list[str] = []
    skipped: list[str] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        fields = lines[i].rstrip("\n").split("\t")
        oldPhono = fields[phonoIdx]
        if not CORRUPTION_RE.search(oldPhono):
            continue
        item = fields[itemIdx]
        candidates = phonsByOrtho.get(item, set())
        if len(candidates) != 1:
            skipped.append(
                f"item={item!r} phono={oldPhono!r}: "
                f"{len(candidates)} candidate phon(s) in Lexique383.tsv "
                f"{sorted(candidates)!r}, need exactly 1"
            )
            continue
        newPhono = next(iter(candidates))
        fixed.append(f"item={item!r} phono {oldPhono!r} -> {newPhono!r}")
        if apply:
            fields[phonoIdx] = newPhono
            lines[i] = "\t".join(fields) + "\n"

    if apply and fixed:
        with open(LEXIQUE_INFRA_PATH, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return fixed, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restore Excel-corrupted '_xlfn.SINGLE(...)' phono "
        "values in LexiqueInfraCorrespondance.tsv from Lexique383.tsv."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to LexiqueInfraCorrespondance.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    fixed, skipped = findAndFix(args.apply)
    print(f"=== {LEXIQUE_INFRA_PATH} ===")
    for f in fixed:
        print(f"  FIX: {f}")
    for s in skipped:
        print(f"  SKIP (ambiguous/no match): {s}")
    print(f"Total rows fixed: {len(fixed)}, skipped: {len(skipped)}")
    if args.apply:
        print(f"--apply: updated {LEXIQUE_INFRA_PATH}")


if __name__ == "__main__":
    main()
