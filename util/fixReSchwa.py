#!/bin/env python
#
# Corrects a phonology error for words spelled "re"/"re-" + a consonant or vowel other than "u"
# (relation, recontacter, rebec, re-explique, ...): Lexique383.tsv transcribes the vowel of the
# prefix as /ø/ ("2", the vowel of "ceux") instead of the schwa /ə/ ("°") that every other
# "re" word gets (5,931 words start with "R°"). Found by the `re` affix-rule analysis: the
# wrong rows were not carriers of the `re` anchor (relation "R°lasj§" but relations "R2lasj§").
#
# Scope: ortho starts with "re", not "reu" (where /ø/ is expected), not exactly "re" (the
# adverb), and the phonology starts with "R2". Nothing else moves (röntgens stays).
# Fields rewritten, in place, matching rows only:
#   Lexique383.tsv              phon, syll, phonrenv
#   LexiqueInfraCorrespondance  phono, assoc ("r-R.e-2" -> "r-R.e-°")
#   LexiqueMixte.tsv            phon, syll_cv
#   LexiqueSynthetic.tsv        phon, syll_cv
# Dry-run by default; --apply writes all four files. Idempotent (same convention as
# util/fixCeSchwa.py). After applying: rm -f *.pickle, then rebuild per docs/PIPELINE.md.
import argparse
import sys

# (path, ortho column, {column: (old prefix/suffix, new, where)}); "start" replaces a prefix,
# "end" a suffix (phonrenv is the reversed phonology).
FIXES: list[tuple[str, str, dict[str, tuple[str, str, str]]]] = [
    ("resources/Lexique383.tsv", "ortho",
     {"phon": ("R2", "R°", "start"), "syll": ("R2", "R°", "start"),
      "phonrenv": ("2R", "°R", "end")}),
    ("resources/LexiqueInfraCorrespondance.tsv", "item",
     {"phono": ("R2", "R°", "start"), "assoc": ("r-R.e-2", "r-R.e-°", "start")}),
    ("resources/LexiqueMixte.tsv", "ortho",
     {"phon": ("R2", "R°", "start"), "syll_cv": ("R_2", "R_°", "start")}),
    ("resources/LexiqueSynthetic.tsv", "ortho",
     {"phon": ("R2", "R°", "start"), "syll_cv": ("R_2", "R_°", "start")}),
]


def isTarget(ortho: str) -> bool:
    return ortho.startswith("re") and ortho != "re" and not ortho.startswith("reu")


def replaced(value: str, old: str, new: str, where: str) -> str | None:
    if where == "start":
        return new + value[len(old):] if value.startswith(old) else None
    return value[:len(value) - len(old)] + new if value.endswith(old) else None


def fixFile(path: str, orthoColumn: str, changes: dict[str, tuple[str, str, str]],
            apply: bool) -> int:
    with open(path, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index(orthoColumn)
    phonIdx = header.index("phon" if "phon" in header else "phono")
    changeIdx = {header.index(column): spec for column, spec in changes.items()}

    modified = 0
    for i in range(1, len(lines)):
        fields = lines[i].rstrip("\n").split("\t")
        if len(fields) <= phonIdx or not isTarget(fields[orthoIdx]) \
                or not fields[phonIdx].startswith("R2"):
            continue
        new = {idx: replaced(fields[idx], *spec) for idx, spec in changeIdx.items()}
        if any(value is None for value in new.values()):
            print(f"  {path}: {fields[orthoIdx]} not in the expected state, skipped: "
                  f"{[fields[idx] for idx in changeIdx]}")
            continue
        for idx, value in new.items():
            assert value is not None
            fields[idx] = value
        lines[i] = "\t".join(fields) + ("\n" if lines[i].endswith("\n") else "")
        modified += 1

    print(f"  {path}: {modified} rows")
    if apply and modified:
        with open(path, "w", newline="") as f:
            f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(description='Correct "re"+X words from /R2/ to /R°/.')
    parser.add_argument("--apply", action="store_true",
                        help="Write the corrections back to the four source files (default: dry-run).")
    args = parser.parse_args()

    print("=== re schwa corrections" + ("" if args.apply else " (dry-run, no files modified)") + " ===")
    total = sum(fixFile(path, orthoColumn, changes, args.apply)
                for path, orthoColumn, changes in FIXES)
    if not total:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
