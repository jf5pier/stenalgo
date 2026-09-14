#!/bin/env python
#
# Batch 9 (UNDEFINED_SLOT cluster E) of the lexicon-defect triage plan:
# deletes two VER rows for grammatically impossible person/tense
# combinations of impersonal weather verbs.
#
#   - "neiges"/"neiger" (sub:pre:2s): "que tu neiges" isn't a real French
#     construction -- weather verbs categorically can't take 2nd person,
#     even figuratively. "neiges" already has its own correct NOM row
#     (f/p, "les neiges" -- the plural noun "snows"); this VER row is a
#     spurious duplicate, most likely an artifact of Lexique383's own
#     automated part-of-speech tagging matching the noun's spelling against
#     the verb paradigm (its frequency is only in the films column, not
#     books, consistent with a transcription/tagging quirk).
#   - "bruinasse"/"bruiner" (sub:imp:1s): "que je bruinasse" is grammatically
#     well-formed (regular -er subjonctif-imparfait) but semantically
#     impossible for an impersonal weather verb; decided to remove rather
#     than keep as a rare literary personification.
#
# Confirmed present in both resources/Lexique383.tsv and
# resources/LexiqueMixte.tsv, so both are corrected.
#
# Dry-run by default: only reads and reports. --apply deletes the matching
# rows in place. Idempotent: a no-op (0 rows found) if run again after a
# successful --apply.
import argparse

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

# (ortho, lemme, cgram, infoVerb) rows to delete entirely.
ROWS_TO_DELETE: set[tuple[str, str, str, str]] = {
    ("neiges", "neiger", "VER", "sub:pre:2s;"),
    ("bruinasse", "bruiner", "VER", "sub:imp:1s;"),
}


def findAndDelete(path: str, apply: bool) -> tuple[list[str], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    infoverIdx = header.index("infover")

    found: list[str] = []
    outputLines = [lines[0]]
    for i in range(1, len(lines)):
        if not lines[i].strip():
            outputLines.append(lines[i])
            continue
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx], fields[cgramIdx], fields[infoverIdx])
        if key in ROWS_TO_DELETE:
            found.append(f"ortho={key[0]!r} lemme={key[1]!r} infover={key[3]!r}")
            if not apply:
                outputLines.append(lines[i])
            # if apply: row is simply omitted
            continue
        outputLines.append(lines[i])

    if apply and found:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(outputLines)

    return found, len(found)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete the grammatically impossible 'neiges'/sub:pre:2s "
        "and 'bruinasse'/sub:imp:1s VER rows."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the deletions to Lexique383.tsv and LexiqueMixte.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        found, count = findAndDelete(path, args.apply)
        print(f"=== {path} ===")
        for f in found:
            print(f"  DELETE: {f}")
        print(f"Total rows found: {count} (expected {len(ROWS_TO_DELETE)})")
        if args.apply:
            print(f"--apply: updated {path}")
        print()


if __name__ == "__main__":
    main()
