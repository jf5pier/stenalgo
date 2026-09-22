#!/bin/env python
#
# Corrects a phonology error for "ce" (lemme "ce", ADJ:dem/PRO:dem, "ce livre",
# "c'est ce que"): Lexique383.tsv/LexiqueInfraCorrespondance.tsv/
# resources/LexiqueMixte.tsv transcribe its vowel as /ø/ ("2", the vowel of
# "ceux") instead of the schwa /ə/ ("°") every other monosyllabic clitic gets
# ("le", "de", "que", "je", "me", "te", "se", "ne" are all "C°"). Besides being
# wrong, it made "ce" a homophone of "ceux" (so "ceux" carried a */# mark) rather
# than of "se" (s°), which it actually sounds like.
#
# Dry-run by default: only reads and reports. --apply rewrites the exact fields
# below in place, in the matching rows only (same convention as
# util/fixEstOuverteVoyelle.py).
import argparse
import sys

TARGET_ORTHO = "ce"
TARGET_CGRAMS = frozenset({"ADJ:dem", "PRO:dem"})

# (path, ortho column, {column: (old, new)}), mirroring how "le" (l°) is encoded
# in each file.
FIXES: list[tuple[str, str, dict[str, tuple[str, str]]]] = [
    ("resources/Lexique383.tsv", "ortho",
     {"phon": ("s2", "s°"), "syll": ("s2", "s°"), "phonrenv": ("2s", "°s")}),
    ("resources/LexiqueInfraCorrespondance.tsv", "item",
     {"phono": ("s2", "s°"), "assoc": ("c-s.e-2", "c-s.e-°")}),
    ("resources/LexiqueMixte.tsv", "ortho",
     {"phon": ("s2", "s°"), "syll_cv": ("s_2", "s_°")}),
]


def fixFile(path: str, orthoColumn: str, changes: dict[str, tuple[str, str]], apply: bool) -> int:
    with open(path, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\n").split("\t")
    orthoIdx, cgramIdx = header.index(orthoColumn), header.index("cgram")
    changeIdx = {header.index(column): oldNew for column, oldNew in changes.items()}

    modified = 0
    for i in range(1, len(lines)):
        fields = lines[i].rstrip("\n").split("\t")
        if len(fields) <= cgramIdx or fields[orthoIdx] != TARGET_ORTHO or fields[cgramIdx] not in TARGET_CGRAMS:
            continue
        if not all(fields[idx] == old for idx, (old, _new) in changeIdx.items()):
            print(f"  {path}: {fields[cgramIdx]} row not in the expected state, skipped: "
                  f"{[fields[idx] for idx in changeIdx]}")
            continue
        for idx, (_old, new) in changeIdx.items():
            fields[idx] = new
        print(f"  {path}: {fields[cgramIdx]} " + ", ".join(
            f"{header[idx]} {old!r} -> {new!r}" for idx, (old, new) in changeIdx.items()))
        lines[i] = "\t".join(fields) + ("\n" if lines[i].endswith("\n") else "")
        modified += 1

    if apply and modified:
        with open(path, "w", newline="") as f:
            f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(description='Correct "ce" (ADJ:dem/PRO:dem) from /s2/ to /s°/.')
    parser.add_argument("--apply", action="store_true",
                        help="Write the corrections back to the three source files (default: dry-run).")
    args = parser.parse_args()

    print("=== ce corrections" + ("" if args.apply else " (dry-run, no files modified)") + " ===")
    total = sum(fixFile(path, orthoColumn, changes, args.apply) for path, orthoColumn, changes in FIXES)
    if not total:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
