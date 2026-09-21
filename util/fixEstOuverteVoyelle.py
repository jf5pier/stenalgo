#!/bin/env python
#
# Corrects a phonology error for "est" (lemme "être", AUX/VER readings, "il
# est"): Lexique383.tsv/LexiqueInfraCorrespondance.tsv/resources/LexiqueMixte.tsv
# currently encode it with the closed vowel /e/ ("e") instead of the open
# vowel /ɛ/ ("E") in X-SAMPA. Only these two readings are wrong -- the
# unrelated homograph "est" (cardinal direction, lemme "est", ADJ/NOM) already
# correctly uses "E" in all three files and is left untouched.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# phon/syll/phonrenv fields back into the matching rows of Lexique383.tsv, the
# corrected phono/assoc fields back into the matching rows of
# LexiqueInfraCorrespondance.tsv, and the corrected phon/syll_cv fields back
# into the matching rows of resources/LexiqueMixte.tsv, all in place. Only the
# exact fields that changed are touched.
import argparse
import csv
import sys

LEXIQUE383_PATH = "resources/Lexique383.tsv"
LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

TARGET_ORTHO = "est"
TARGET_LEMME = "être"
TARGET_CGRAMS = frozenset({"AUX", "VER"})


def readTsv(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def isTargetLexique383Row(row: dict[str, str]) -> bool:
    return (
        row.get("ortho") == TARGET_ORTHO
        and row.get("lemme") == TARGET_LEMME
        and row.get("cgram") in TARGET_CGRAMS
    )


def isTargetInfraRow(row: dict[str, str]) -> bool:
    # LexiqueInfraCorrespondance has no lemme column; item+cgram narrows to
    # exactly the "être" AUX/VER readings (the "est" cardinal-direction
    # homograph uses cgram ADJ/NOM instead).
    return row.get("item") == TARGET_ORTHO and row.get("cgram") in TARGET_CGRAMS


def isTargetMixteRow(row: dict[str, str]) -> bool:
    return (
        row.get("ortho") == TARGET_ORTHO
        and row.get("lemme") == TARGET_LEMME
        and row.get("cgram") in TARGET_CGRAMS
    )


def correctAssoc(assoc: str) -> str:
    # First "."-separated segment is the "e" grapheme's own "grapheme-phon"
    # pair (e.g. "e-e"); the s/t segments ("s-#", "t-#") are already silent
    # and untouched. Idempotent: a no-op once already "e-E".
    segments = assoc.split(".")
    segments[0] = "e-E"
    return ".".join(segments)


def correctSyllCv(syllCv: str) -> str:
    # "e_#_#" -> "E_#_#" -- the first phoneme slot of the (single-syllable)
    # word. Idempotent: a no-op once already "E_#_#".
    phonemes = syllCv.split("_")
    phonemes[0] = "E"
    return "_".join(phonemes)


class EstCorrection:
    def __init__(
        self, lexique383Row: dict[str, str] | None,
        infraRow: dict[str, str] | None,
        mixteRow: dict[str, str] | None,
    ) -> None:
        self.cgram = (lexique383Row or infraRow or mixteRow)["cgram"]  # type: ignore[index]

        self.lexOldPhon = lexique383Row["phon"] if lexique383Row else None
        self.lexOldSyll = lexique383Row["syll"] if lexique383Row else None
        self.lexOldPhonrenv = lexique383Row["phonrenv"] if lexique383Row else None
        self.lexNewPhon = "E" if self.lexOldPhon is not None else None
        self.lexNewSyll = "E" if self.lexOldSyll is not None else None
        self.lexNewPhonrenv = "E" if self.lexOldPhonrenv is not None else None

        self.infraOldPhono = infraRow["phono"] if infraRow else None
        self.infraOldAssoc = infraRow["assoc"] if infraRow else None
        self.infraNewPhono = "E" if self.infraOldPhono is not None else None
        self.infraNewAssoc = (
            correctAssoc(self.infraOldAssoc) if self.infraOldAssoc is not None else None
        )

        self.mixteOldPhon = mixteRow["phon"] if mixteRow else None
        self.mixteOldSyllCv = mixteRow["syll_cv"] if mixteRow else None
        self.mixteNewPhon = "E" if self.mixteOldPhon is not None else None
        self.mixteNewSyllCv = (
            correctSyllCv(self.mixteOldSyllCv) if self.mixteOldSyllCv is not None else None
        )


def findEstCorrections(
    lexique383Rows: list[dict[str, str]],
    infraRows: list[dict[str, str]],
    mixteRows: list[dict[str, str]],
) -> list[EstCorrection]:
    lexique383ByCgram = {r["cgram"]: r for r in lexique383Rows if isTargetLexique383Row(r)}
    infraByCgram = {r["cgram"]: r for r in infraRows if isTargetInfraRow(r)}
    mixteByCgram = {r["cgram"]: r for r in mixteRows if isTargetMixteRow(r)}

    cgrams = sorted(set(lexique383ByCgram) | set(infraByCgram) | set(mixteByCgram))
    return [
        EstCorrection(
            lexique383ByCgram.get(cgram), infraByCgram.get(cgram), mixteByCgram.get(cgram)
        )
        for cgram in cgrams
    ]


def printCorrections(corrections: list[EstCorrection]) -> None:
    print("=== est/être corrections (dry-run, no files modified) ===\n")
    for c in corrections:
        print(f"cgram: {c.cgram}")
        if c.lexOldPhon is not None:
            print(f"  Lexique383  phon     : {c.lexOldPhon!r} -> {c.lexNewPhon!r}")
            print(f"  Lexique383  syll     : {c.lexOldSyll!r} -> {c.lexNewSyll!r}")
            print(f"  Lexique383  phonrenv : {c.lexOldPhonrenv!r} -> {c.lexNewPhonrenv!r}")
        else:
            print("  Lexique383  : (no matching row found)")
        if c.infraOldPhono is not None:
            print(f"  Infra       phono    : {c.infraOldPhono!r} -> {c.infraNewPhono!r}")
            print(f"  Infra       assoc    : {c.infraOldAssoc!r} -> {c.infraNewAssoc!r}")
        else:
            print("  Infra       : (no matching row found)")
        if c.mixteOldPhon is not None:
            print(f"  Mixte       phon     : {c.mixteOldPhon!r} -> {c.mixteNewPhon!r}")
            print(f"  Mixte       syll_cv  : {c.mixteOldSyllCv!r} -> {c.mixteNewSyllCv!r}")
        else:
            print("  Mixte       : (no matching row found)")
        print()


def applyLexique383Corrections(path: str, corrections: list[EstCorrection]) -> int:
    correctionsByCgram = {c.cgram: c for c in corrections if c.lexOldPhon is not None}
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx, lemmeIdx, cgramIdx = header.index("ortho"), header.index("lemme"), header.index("cgram")
    phonIdx, syllIdx, phonrenvIdx = header.index("phon"), header.index("syll"), header.index("phonrenv")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        if fields[orthoIdx] != TARGET_ORTHO or fields[lemmeIdx] != TARGET_LEMME:
            continue
        c = correctionsByCgram.get(fields[cgramIdx])
        if c is not None and fields[phonIdx] == c.lexOldPhon:
            fields[phonIdx] = c.lexNewPhon
            fields[syllIdx] = c.lexNewSyll
            fields[phonrenvIdx] = c.lexNewPhonrenv
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def applyInfraCorrections(path: str, corrections: list[EstCorrection]) -> int:
    correctionsByCgram = {c.cgram: c for c in corrections if c.infraOldPhono is not None}
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx, cgramIdx = header.index("item"), header.index("cgram")
    phonoIdx, assocIdx = header.index("phono"), header.index("assoc")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        if fields[itemIdx] != TARGET_ORTHO:
            continue
        c = correctionsByCgram.get(fields[cgramIdx])
        if c is not None and fields[phonoIdx] == c.infraOldPhono and fields[assocIdx] == c.infraOldAssoc:
            fields[phonoIdx] = c.infraNewPhono
            fields[assocIdx] = c.infraNewAssoc
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def applyMixteCorrections(path: str, corrections: list[EstCorrection]) -> int:
    correctionsByCgram = {c.cgram: c for c in corrections if c.mixteOldPhon is not None}
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx, lemmeIdx, cgramIdx = header.index("ortho"), header.index("lemme"), header.index("cgram")
    phonIdx, syllCvIdx = header.index("phon"), header.index("syll_cv")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        if fields[orthoIdx] != TARGET_ORTHO or fields[lemmeIdx] != TARGET_LEMME:
            continue
        c = correctionsByCgram.get(fields[cgramIdx])
        if c is not None and fields[phonIdx] == c.mixteOldPhon:
            fields[phonIdx] = c.mixteNewPhon
            fields[syllCvIdx] = c.mixteNewSyllCv
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Correct "est" (lemme "être", AUX/VER) phonology from the '
        'closed "e" to the open "E" in Lexique383.tsv, '
        "LexiqueInfraCorrespondance.tsv and resources/LexiqueMixte.tsv."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to the three source files (default: dry-run).",
    )
    args = parser.parse_args()

    lexique383Rows = readTsv(LEXIQUE383_PATH)
    infraRows = readTsv(LEXIQUE_INFRA_PATH)
    mixteRows = readTsv(LEXIQUE_MIXTE_PATH)

    corrections = findEstCorrections(lexique383Rows, infraRows, mixteRows)
    printCorrections(corrections)

    if not corrections:
        print("Nothing found to correct.", file=sys.stderr)
        sys.exit(1)

    if args.apply:
        nbLexique = applyLexique383Corrections(LEXIQUE383_PATH, corrections)
        nbInfra = applyInfraCorrections(LEXIQUE_INFRA_PATH, corrections)
        nbMixte = applyMixteCorrections(LEXIQUE_MIXTE_PATH, corrections)
        print(f"--apply: wrote {nbLexique} corrected rows to {LEXIQUE383_PATH}")
        print(f"--apply: wrote {nbInfra} corrected rows to {LEXIQUE_INFRA_PATH}")
        print(f"--apply: wrote {nbMixte} corrected rows to {LEXIQUE_MIXTE_PATH}")


if __name__ == "__main__":
    main()
