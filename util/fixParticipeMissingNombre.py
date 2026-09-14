#!/bin/env python
#
# Batch 6 of the lexicon-defect triage plan (see
# util/validateLexiconAgainstVerbiste.py's PARTICIPE_MISSING_GENDER_NUMBER
# flag type): fills in the missing `nombre` field ("s") for a VER row that's
# a genuine masculine past participle (`genre` already == "m") but has a
# blank `nombre`, e.g. "prendre"/"pris" (genre="m", nombre="").
#
# Verified before batch-fixing (per the triage plan's caveat about not
# blindly assuming m/s): for every one of the 37 affected lemmas
# (absoudre/acquérir/admettre/... -- irregular participle families sharing
# the m:ettre/pr:endre/acqu:érir/ass:eoir/abso:udre/cl:ore/circonc:ire/
# disso:udre/incl:ure/surs:eoir templates), `genre` is ALREADY "m" on the
# bare row (only `nombre` is missing), and the feminine forms (f/s, f/p) --
# where attested in the lexicon at all -- exist as separate, independently
# correctly-tagged rows (e.g. "absoute"/f/s, "absoutes"/f/p alongside the
# bare "absous"/m/""), confirming the bare row really is just missing its
# own `nombre="s"` rather than needing a closer individual look. (Masculine
# singular and masculine plural are orthographic homographs for all of these
# -- "pris" serves both -- so a single row tagged m/s is sufficient; no
# separate m/p row is needed or created.)
#
# Confirmed to also exist in resources/Lexique383.tsv (spot-checked "pris"),
# so both files are corrected.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# `nombre` field back in place. Idempotent: a no-op (0 rows modified) if run
# again after a successful --apply.
import argparse

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def needsNombreFill(cgram: str, infoVerb: str, genre: str, nombre: str) -> bool:
    tags = [tag for tag in infoVerb.split(";") if tag]
    return cgram == "VER" and "par:pas" in tags and genre == "m" and not nombre


def findAndFix(path: str, apply: bool) -> tuple[list[str], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    cgramIdx = header.index("cgram")
    genreIdx = header.index("genre")
    nombreIdx = header.index("nombre")
    infoverIdx = header.index("infover")

    corrections: list[str] = []
    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        if not needsNombreFill(fields[cgramIdx], fields[infoverIdx], fields[genreIdx], fields[nombreIdx]):
            continue
        corrections.append(fields[orthoIdx])
        if apply:
            fields[nombreIdx] = "s"
            lines[i] = "\t".join(fields) + ending
            modified += 1

    if apply and modified:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return corrections, modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill nombre='s' for VER rows that are genuine "
        "masculine (genre='m') past participles with a blank nombre."
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
        for ortho in corrections:
            print(f"  ortho={ortho!r}: nombre='' -> nombre='s'")
        print(f"Total rows found: {len(corrections)}")
        if args.apply:
            print(f"--apply: wrote {modified} corrected rows to {path}")
        print()


if __name__ == "__main__":
    main()
