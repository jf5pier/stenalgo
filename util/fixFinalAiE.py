#!/bin/env python
#
# Sets the close /e/ for the words that end in "-ai" and are transcribed with the open
# /E/ ("mai", "balai", "quai", "vrai", "j'ai" the auxiliary, ...). The 2292 verb forms
# ending in "-ai" ("chantai", "ai" the verb) already end in /e/, and so does the
# standard final open syllable "-ai" in Quebec speech; the 23 noun/adjective/auxiliary
# rows were the lone /E/. Words ending in "-ais"/"-ait"/"-aid" are not touched.
# "samurai" (/aj/) is not an /E/ row, so it is left out by construction.
#
# Dry-run by default: only reads and reports. --apply rewrites the exact fields below
# in place, in the matching rows only (same convention as util/fixCeSchwa.py).
import argparse
import sys

# The words whose "-ai" is the open /E/ in the author's speech, left untouched
# (minerai only as a noun: the verb form "minerai" ends in /e/ in the source).
KEEP_OPEN = frozenset({
    ("balai", ""), ("brai", ""), ("chai", ""), ("déblai", ""), ("délai", ""), ("essai", ""),
    ("frai", ""), ("minerai", "NOM"), ("rai", ""), ("remblai", ""), ("vrai", ""), ("hai", ""),
})

# (path, ortho column, columns to fix); each column's value must end like the
# per-column rule below says, and the last "E" of that ending becomes "e".
FIXES: list[tuple[str, str, dict[str, str]]] = [
    # phon "ba-lE" -> syll "ba-lE"; phonrenv is the reversed phon ("Elab")
    ("resources/Lexique383.tsv", "ortho", {"phon": "end", "syll": "end", "phonrenv": "start"}),
    ("resources/LexiqueInfraCorrespondance.tsv", "item", {"phono": "end", "assoc": "ai-E"}),
    ("resources/LexiqueMixte.tsv", "ortho", {"phon": "end", "syll_cv": "end"}),
    ("resources/LexiqueSynthetic.tsv", "ortho", {"phon": "end", "syll_cv": "end"}),
]


def fixedValue(value: str, rule: str) -> str | None:
    if rule == "end" and value.endswith("E"):
        return value[:-1] + "e"
    if rule == "start" and value.startswith("E"):
        return "e" + value[1:]
    if rule == "ai-E" and value.endswith("ai-E"):
        return value[:-1] + "e"
    return None


def fixFile(path: str, orthoColumn: str, columns: dict[str, str], apply: bool) -> int:
    with open(path, newline="") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\n").split("\t")
    cgramIdx = header.index("cgram")
    orthoIdx = header.index(orthoColumn)
    phonColumn = "phono" if "phono" in columns else "phon"
    phonIdx = header.index(phonColumn)
    columnIdx = {column: header.index(column) for column in columns}

    modified = 0
    for i in range(1, len(lines)):
        fields = lines[i].rstrip("\n").split("\t")
        if len(fields) <= max(orthoIdx, phonIdx) or not fields[orthoIdx].endswith("ai") \
                or not fields[phonIdx].endswith("E"):
            continue
        ortho, cgram = fields[orthoIdx], fields[cgramIdx]
        if (ortho, "") in KEEP_OPEN or (ortho, cgram) in KEEP_OPEN:
            continue
        edits = {column: fixedValue(fields[columnIdx[column]], rule) for column, rule in columns.items()}
        if any(new is None for new in edits.values()):
            print(f"  {path}: {fields[orthoIdx]} row not in the expected state, skipped: "
                  f"{[fields[columnIdx[column]] for column in columns]}")
            continue
        changes = []
        for column, new in edits.items():
            assert new is not None
            changes.append(f"{column} {fields[columnIdx[column]]!r} -> {new!r}")
            fields[columnIdx[column]] = new
        print(f"  {path}: {fields[orthoIdx]} " + ", ".join(changes))
        lines[i] = "\t".join(fields) + ("\n" if lines[i].endswith("\n") else "")
        modified += 1

    if apply and modified:
        with open(path, "w", newline="") as f:
            f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(description='Correct final "-ai" from /E/ to /e/.')
    parser.add_argument("--apply", action="store_true",
                        help="Write the corrections back to the four source files (default: dry-run).")
    args = parser.parse_args()

    print('=== final "-ai" corrections' + ("" if args.apply else " (dry-run, no files modified)") + " ===")
    total = sum(fixFile(path, orthoColumn, columns, args.apply) for path, orthoColumn, columns in FIXES)
    if not total:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
