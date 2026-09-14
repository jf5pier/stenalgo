#!/bin/env python
#
# Batch 1 of the lexicon-defect triage plan (see
# util/validateLexiconAgainstVerbiste.py's DUPLICATE_INF_TAG flag type):
# collapses a VER row's `infover` field when it consists solely of repeated
# "inf" tags (e.g. "inf;;inf;;inf;;", "inf;;inf;;inf;;inf;;") down to the
# single canonical "inf;" every other infinitive row already uses. Purely
# mechanical string dedup -- no linguistic judgment involved.
#
# The duplication traces to resources/Lexique383.tsv itself (confirmed via
# spot-check: "abriter"/"aider" carry the same duplicated infover there as in
# resources/LexiqueMixte.tsv), so both files are corrected, keeping
# lexique.py's regeneration of LexiqueMixte.tsv from Lexique383.tsv clean.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# `infover` field back in place. Idempotent: a no-op (0 rows modified) if run
# again after a successful --apply.
import argparse

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

CANONICAL_INF = "inf;"


def isDuplicateInfOnly(infoVerb: str) -> bool:
    tags = [tag for tag in infoVerb.split(";") if tag]
    return len(tags) > 1 and all(tag == "inf" for tag in tags)


def findAndFix(path: str, apply: bool) -> tuple[list[tuple[str, str, str]], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
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
        oldInfoVerb = fields[infoverIdx]
        if not isDuplicateInfOnly(oldInfoVerb):
            continue
        corrections.append((fields[orthoIdx], oldInfoVerb, CANONICAL_INF))
        if apply:
            fields[infoverIdx] = CANONICAL_INF
            lines[i] = "\t".join(fields) + ending
            modified += 1

    if apply and modified:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return corrections, modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collapse VER rows whose infover is all-duplicated 'inf' "
        "tags (e.g. 'inf;;inf;;inf;;') down to the canonical 'inf;'."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to Lexique383.tsv and LexiqueMixte.tsv "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        corrections, modified = findAndFix(path, args.apply)
        print(f"=== {path} ===")
        for ortho, oldInfoVerb, newInfoVerb in corrections:
            print(f"  ortho={ortho!r}: {oldInfoVerb!r} -> {newInfoVerb!r}")
        print(f"Total rows found: {len(corrections)}")
        if args.apply:
            print(f"--apply: wrote {modified} corrected rows to {path}")
        print()


if __name__ == "__main__":
    main()
