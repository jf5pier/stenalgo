#!/bin/env python
#
# Batch 2 of the lexicon-defect triage plan (see
# util/validateLexiconAgainstVerbiste.py's INF_PLUS_OTHER_TAG flag type):
# strips whichever side of an "inf" + other-tag(s) combination is spurious
# from a VER row's infover. Which side is spurious is decided per row by
# `ortho == lemme`:
#   - ortho == lemme (e.g. "acheter"/"ind:pre:2p;inf;"): this row genuinely
#     IS the infinitive, so the *other* tag(s) are the spurious ones ->
#     "inf;". This is the common case (this class of bug is already guarded
#     against at the code level in src/verbparadigm.py's
#     deriveConjugationEndingTables and util/completeVerbParadigms.py's
#     attestedFiniteFormsByLemme -- see PROGRESS.md fixes 7/8 -- this batch
#     cleans up the underlying lexicon data those guards route around).
#   - ortho != lemme (e.g. "dois"/"devoir"/"imp:pre:2s;ind:pre:1s;ind:pre:2s;
#     inf;"): this row is NOT the infinitive (confirmed: "devoir" already has
#     its own separate "devoir"/"inf;" row elsewhere), so here it's "inf"
#     itself that's spurious -> drop just that tag, keep the rest. Found for
#     5 rows: dois/devoir, reprenons/reprendre, reviendra/revenir,
#     réprimés/réprimer, viens/venir -- each lemma's own genuine infinitive
#     row was verified present separately before treating "inf" as safe to
#     drop here.
#
# Confirmed to originate in resources/Lexique383.tsv itself (spot-checked:
# "acheter" carries "ind:pre:2p;inf;" there too), so both files are
# corrected.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# `infover` field back in place. Idempotent: a no-op (0 rows modified) if run
# again after a successful --apply.
import argparse

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

CANONICAL_INF = "inf;"


def isInfPlusOtherTag(infoVerb: str) -> bool:
    tags = [tag for tag in infoVerb.split(";") if tag]
    return "inf" in tags and any(tag != "inf" for tag in tags)


def correctedInfoVerb(infoVerb: str, isGenuineInfinitive: bool) -> str:
    if isGenuineInfinitive:
        return CANONICAL_INF
    tags = [tag for tag in infoVerb.split(";") if tag and tag != "inf"]
    return ";".join(tags) + ";"


def findAndFix(path: str, apply: bool) -> tuple[list[tuple[str, str, str]], int]:
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
        oldInfoVerb = fields[infoverIdx]
        if not isInfPlusOtherTag(oldInfoVerb):
            continue
        isGenuineInfinitive = fields[orthoIdx] == fields[lemmeIdx]
        newInfoVerb = correctedInfoVerb(oldInfoVerb, isGenuineInfinitive)
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
        description="Strip spurious non-'inf' tags from VER rows whose "
        "infover carries 'inf' plus other tags (e.g. 'ind:pre:2p;inf;' -> "
        "'inf;')."
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
