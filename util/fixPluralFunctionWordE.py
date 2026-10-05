#!/bin/env python
#
# Corrects the vowel of the plural function words "les", "des", "ses", "mes", "tes",
# "ces": Lexique383.tsv/LexiqueInfraCorrespondance.tsv/resources/LexiqueMixte.tsv
# transcribe it as the close /e/ ("le", "de", ...) but it is the open /E/ ("lE", "dE",
# ...) (the usual pronunciation, and the Quebec one). The singular "le", "de", "se",
# "me", "te" keep their schwa; only the "-es" forms change.
#
# Dry-run by default: only reads and reports. --apply rewrites the exact fields
# below in place, in the matching rows only (same convention as util/fixCeSchwa.py).
import argparse
import sys

TARGET_ORTHOS = frozenset({"les", "des", "ses", "mes", "tes", "ces"})
# "ces" is /se/, the others are C + /e/; the consonant is the word's first letter,
# except "ces" whose onset is /s/.
ONSET = {"les": "l", "des": "d", "ses": "s", "mes": "m", "tes": "t", "ces": "s"}

# (path, ortho column, {column: (old, new)}); "{c}" is the onset phoneme, "{g}" its grapheme.
FIXES: list[tuple[str, str, dict[str, tuple[str, str]]]] = [
    ("resources/Lexique383.tsv", "ortho",
     {"phon": ("{c}e", "{c}E"), "syll": ("{c}e", "{c}E"), "phonrenv": ("e{c}", "E{c}")}),
    ("resources/LexiqueInfraCorrespondance.tsv", "item",
     {"phono": ("{c}e", "{c}E"), "assoc": ("{g}-{c}.e-e.s-#", "{g}-{c}.e-E.s-#")}),
    ("resources/LexiqueMixte.tsv", "ortho",
     {"phon": ("{c}e", "{c}E"), "syll_cv": ("{c}_e_#", "{c}_E_#")}),
]


def fixFile(path: str, orthoColumn: str, changes: dict[str, tuple[str, str]], apply: bool) -> int:
    with open(path, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index(orthoColumn)
    columnIdx = {column: header.index(column) for column in changes}

    modified = 0
    for i in range(1, len(lines)):
        fields = lines[i].rstrip("\n").split("\t")
        if len(fields) <= orthoIdx or fields[orthoIdx] not in TARGET_ORTHOS:
            continue
        onset = ONSET[fields[orthoIdx]]
        grapheme = "c" if fields[orthoIdx] == "ces" else onset
        edits: list[tuple[int, str, str]] = []
        for column, (oldT, newT) in changes.items():
            old, new = oldT.format(c=onset, g=grapheme), newT.format(c=onset, g=grapheme)
            value = fields[columnIdx[column]]
            if value != old:
                print(f"  {path}: {fields[orthoIdx]} row not in the expected state, skipped: {column}={value!r}")
                edits = []
                break
            edits.append((columnIdx[column], old, new))
        if len(edits) != len(changes):
            continue
        for idx, _old, new in edits:
            fields[idx] = new
        print(f"  {path}: {fields[orthoIdx]} " + ", ".join(f"{header[idx]} {old!r} -> {new!r}" for idx, old, new in edits))
        lines[i] = "\t".join(fields) + ("\n" if lines[i].endswith("\n") else "")
        modified += 1

    if apply and modified:
        with open(path, "w", newline="") as f:
            f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(description='Correct "les/des/ses/mes/tes/ces" from /Ce/ to /CE/.')
    parser.add_argument("--apply", action="store_true",
                        help="Write the corrections back to the three source files (default: dry-run).")
    args = parser.parse_args()

    print("=== plural function word corrections" + ("" if args.apply else " (dry-run, no files modified)") + " ===")
    total = sum(fixFile(path, orthoColumn, changes, args.apply) for path, orthoColumn, changes in FIXES)
    if not total:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
