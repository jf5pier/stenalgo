#!/bin/env python
#
# Investigates and (with --apply) corrects a false-homophone bug for "-gner"
# verbs: Lexique383.tsv/LexiqueInfraCorrespondance.tsv currently encode the
# 2nd person plural imperfect indicative ("-gniez", e.g. "gagniez") with the
# exact same phonology/syllabification as the present ("-gnez", e.g.
# "gagnez"), dropping the yod /j/ that "-iez" carries in real French
# (/gaNe/ for both instead of /gaNe/ vs /gaNje/). This collapses two distinct
# conjugated forms into one homophone stroke-group downstream.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# phon/syll/cv-cv fields back into the matching "-gniez" rows of
# Lexique383.tsv, the corrected assoc field back into the matching rows of
# LexiqueInfraCorrespondance.tsv, and the corrected phon/syll_cv fields back
# into the matching rows of the pre-built resources/LexiqueMixte.tsv, all in
# place. Only the exact fields that changed are touched; every other column,
# row, and the "-gnez" sibling rows are left byte-for-byte untouched.
import argparse
import csv
import sys

LEXIQUE383_PATH = "resources/Lexique383.tsv"
LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def readTsv(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def gnezSiblingOrtho(gniezOrtho: str) -> str:
    # "gagniez" -> "gagnez" ("-iez" suffix becomes "-ez")
    return gniezOrtho[:-3] + "ez"


GNIEZ_LEMME_ENDINGS = ("gner", "dre")


def isGniezVerbForm(row: dict[str, str]) -> bool:
    # Catches both "-gner" verbs (gagner -> gagniez) and "-dre" verbs whose
    # stem ends in "gn" before the infinitive ending (craindre -> craigniez,
    # peindre -> peigniez, joindre -> joigniez, plaindre -> plaigniez, ...)
    return (
        row.get("cgram") == "VER"
        and row.get("lemme", "").endswith(GNIEZ_LEMME_ENDINGS)
        and row.get("ortho", "").endswith("gniez")
    )


def insertYodBeforeFinalVowel(text: str) -> str:
    # Inserts the yod semivowel "j" right before the last character
    # (the final vowel phoneme), e.g. "gaNe" -> "gaNje".
    # Idempotent: a no-op if the yod is already there (safe to re-run on
    # already-corrected data).
    if len(text) >= 2 and text[-2] == "j":
        return text
    return text[:-1] + "j" + text[-1]


def correctSyll(syll: str) -> str:
    parts = syll.split("-")
    parts[-1] = insertYodBeforeFinalVowel(parts[-1])
    return "-".join(parts)


def correctCvCv(cvCv: str) -> str:
    # Idempotent, mirroring insertYodBeforeFinalVowel.
    parts = cvCv.split("-")
    last = parts[-1]
    if len(last) >= 2 and last[-2] == "Y":
        return cvCv
    parts[-1] = last[:-1] + "Y" + last[-1]
    return "-".join(parts)


def correctAssoc(assoc: str) -> str:
    # LexiqueInfraCorrespondance encodes the "i" of "-iez" as silent ("i-#");
    # it should map to the yod semivowel instead ("i-j"). str.replace is
    # already a no-op if "i-#" isn't present (already corrected).
    return assoc.replace("i-#", "i-j", 1)


def correctMixteSyllCv(syllCv: str) -> str:
    # LexiqueMixte's syll_cv already reserves a phoneme slot for the "i" of
    # "-iez" but marks it silent ("N_#_e"); it should hold the yod instead
    # ("N_j_e"). The slot lives in the last syllable. Idempotent: a no-op if
    # already corrected (no "#" left to replace).
    syllables = syllCv.split("|")
    phonemes = syllables[-1].split("_")
    if "#" not in phonemes:
        return syllCv
    if phonemes.count("#") != 1:
        raise ValueError(f"expected exactly one silent phoneme in {syllCv!r}")
    phonemes[phonemes.index("#")] = "j"
    syllables[-1] = "_".join(phonemes)
    return "|".join(syllables)


class GniezCorrection:
    def __init__(self, lexique383Row: dict[str, str],
                 siblingRow: dict[str, str] | None,
                 infraRow: dict[str, str] | None,
                 mixteRow: dict[str, str] | None) -> None:
        self.ortho = lexique383Row["ortho"]
        self.lemme = lexique383Row["lemme"]
        self.siblingOrtho = gnezSiblingOrtho(self.ortho)
        self.oldPhon = lexique383Row["phon"]
        self.newPhon = insertYodBeforeFinalVowel(self.oldPhon)
        self.oldSyll = lexique383Row["syll"]
        self.newSyll = correctSyll(self.oldSyll)
        self.oldCvCv = lexique383Row["cv-cv"]
        self.newCvCv = correctCvCv(self.oldCvCv)
        self.siblingPhon = siblingRow["phon"] if siblingRow else None
        # Confirmed either if the row still collides with its -gnez sibling
        # (not yet fixed) or if it already matches the expected corrected
        # form derived from that same sibling (already fixed) — this makes
        # the script idempotent/safe to re-run after a partial --apply.
        self.collisionConfirmed = self.siblingPhon is not None and (
            self.siblingPhon == self.oldPhon
            or self.oldPhon == insertYodBeforeFinalVowel(self.siblingPhon)
        )
        self.infraOldAssoc = infraRow["assoc"] if infraRow else None
        self.infraNewAssoc = (
            correctAssoc(self.infraOldAssoc)
            if self.infraOldAssoc is not None else None
        )
        self.mixteOldPhon = mixteRow["phon"] if mixteRow else None
        self.mixteOldSyllCv = mixteRow["syll_cv"] if mixteRow else None
        self.mixteNewPhon = (
            insertYodBeforeFinalVowel(self.mixteOldPhon)
            if self.mixteOldPhon is not None else None
        )
        self.mixteNewSyllCv = (
            correctMixteSyllCv(self.mixteOldSyllCv)
            if self.mixteOldSyllCv is not None else None
        )


def findGniezCorrections(
    lexique383Rows: list[dict[str, str]],
    infraRows: list[dict[str, str]],
    mixteRows: list[dict[str, str]],
) -> list[GniezCorrection]:
    rowsByOrtho: dict[str, list[dict[str, str]]] = {}
    for row in lexique383Rows:
        rowsByOrtho.setdefault(row["ortho"], []).append(row)

    # Keyed by (item, cgram) rather than (item, phono): Lexique383.tsv and
    # LexiqueInfraCorrespondance.tsv occasionally disagree on phono for the
    # same word even before any correction (e.g. "enseigniez"), and after a
    # first --apply, Lexique383's phon column reflects the fix while infra's
    # own "phono" column never gets touched — a phono-based join would
    # silently stop matching. Orthograph + grammatical category is a stable,
    # reliable key for this narrow set of verb forms.
    infraByItemCgram: dict[tuple[str, str], dict[str, str]] = {
        (row["item"], row["cgram"]): row for row in infraRows
    }

    mixteByOrthoLemme: dict[tuple[str, str], dict[str, str]] = {
        (row["ortho"], row["lemme"]): row
        for row in mixteRows if row["cgram"] == "VER"
    }

    corrections: list[GniezCorrection] = []
    for row in lexique383Rows:
        if not isGniezVerbForm(row):
            continue
        siblingOrtho = gnezSiblingOrtho(row["ortho"])
        siblingCandidates = [
            r for r in rowsByOrtho.get(siblingOrtho, [])
            if r["lemme"] == row["lemme"] and r["cgram"] == "VER"
        ]
        siblingRow = siblingCandidates[0] if siblingCandidates else None
        infraRow = infraByItemCgram.get((row["ortho"], "VER"))
        mixteRow = mixteByOrthoLemme.get((row["ortho"], row["lemme"]))
        corrections.append(
            GniezCorrection(row, siblingRow, infraRow, mixteRow))
    return corrections


def printSample(corrections: list[GniezCorrection], sampleLemmes: list[str]) -> None:
    sampleSet = set(sampleLemmes)
    shown = [c for c in corrections if c.lemme in sampleSet]
    remaining = [c for c in corrections if c.lemme not in sampleSet]

    print("=== Sample corrections (dry-run, no files modified) ===\n")
    for c in shown + remaining[: max(0, 3 - len(shown))]:
        collision = "CONFIRMED" if c.collisionConfirmed else "NOT CONFIRMED"
        print(f"lemme: {c.lemme}")
        print(f"  orthograph      : {c.ortho}  (collides with: {c.siblingOrtho})")
        print(f"  collision with -gnez phon : {collision} "
              f"(sibling phon={c.siblingPhon!r})")
        print(f"  phon            : {c.oldPhon!r} -> {c.newPhon!r}")
        print(f"  syll            : {c.oldSyll!r} -> {c.newSyll!r}")
        print(f"  cv-cv           : {c.oldCvCv!r} -> {c.newCvCv!r}")
        if c.infraOldAssoc is not None:
            print(f"  infra assoc     : {c.infraOldAssoc!r} -> {c.infraNewAssoc!r}")
        else:
            print("  infra assoc     : (no matching LexiqueInfraCorrespondance row found)")
        if c.mixteOldPhon is not None:
            print(f"  mixte phon      : {c.mixteOldPhon!r} -> {c.mixteNewPhon!r}")
            print(f"  mixte syll_cv   : {c.mixteOldSyllCv!r} -> {c.mixteNewSyllCv!r}")
        else:
            print("  mixte           : (no matching LexiqueMixte.tsv row found)")
        print()


def applyLexique383Corrections(
    path: str, confirmedCorrections: list[GniezCorrection]
) -> int:
    correctionsByKey = {
        (c.ortho, c.lemme): c for c in confirmedCorrections
    }
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    phonIdx = header.index("phon")
    syllIdx = header.index("syll")
    cvCvIdx = header.index("cv-cv")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx])
        c = correctionsByKey.get(key)
        if (c is not None and fields[cgramIdx] == "VER"
                and fields[phonIdx] == c.oldPhon
                and fields[syllIdx] == c.oldSyll
                and fields[cvCvIdx] == c.oldCvCv):
            fields[phonIdx] = c.newPhon
            fields[syllIdx] = c.newSyll
            fields[cvCvIdx] = c.newCvCv
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def applyInfraCorrections(
    path: str, confirmedCorrections: list[GniezCorrection]
) -> int:
    correctionsByItem = {
        c.ortho: c for c in confirmedCorrections if c.infraOldAssoc is not None
    }
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx = header.index("item")
    assocIdx = header.index("assoc")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        c = correctionsByItem.get(fields[itemIdx])
        if c is not None and fields[assocIdx] == c.infraOldAssoc:
            fields[assocIdx] = c.infraNewAssoc
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def applyMixteCorrections(
    path: str, confirmedCorrections: list[GniezCorrection]
) -> int:
    correctionsByKey = {
        (c.ortho, c.lemme): c for c in confirmedCorrections
        if c.mixteOldPhon is not None
    }
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    phonIdx = header.index("phon")
    syllCvIdx = header.index("syll_cv")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx])
        c = correctionsByKey.get(key)
        if (c is not None and fields[cgramIdx] == "VER"
                and fields[phonIdx] == c.mixteOldPhon
                and fields[syllCvIdx] == c.mixteOldSyllCv):
            fields[phonIdx] = c.mixteNewPhon
            fields[syllCvIdx] = c.mixteNewSyllCv
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect/correct the -gnez vs -gniez false homophone bug "
        "for -gner verbs in Lexique383.tsv / LexiqueInfraCorrespondance.tsv"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to resources/Lexique383.tsv, "
        "resources/LexiqueInfraCorrespondance.tsv and "
        "resources/LexiqueMixte.tsv (default: dry-run).",
    )
    args = parser.parse_args()

    lexique383Rows = readTsv(LEXIQUE383_PATH)
    infraRows = readTsv(LEXIQUE_INFRA_PATH)
    mixteRows = readTsv(LEXIQUE_MIXTE_PATH)

    corrections = findGniezCorrections(lexique383Rows, infraRows, mixteRows)
    confirmedCorrections = [c for c in corrections if c.collisionConfirmed]

    printSample(confirmedCorrections,
                ["gagner", "accompagner", "soigner", "craindre"])

    print("=== Summary ===")
    print(f"Total -gner verb lemmas with a -gniez entry found: {len(corrections)}")
    print(f"Total confirmed colliding with their -gnez sibling: "
          f"{len(confirmedCorrections)}")
    if len(corrections) != len(confirmedCorrections):
        unconfirmed = [c.lemme for c in corrections if not c.collisionConfirmed]
        print(f"Entries without a confirmed -gnez collision: {unconfirmed}")

    if args.apply:
        nbLexique = applyLexique383Corrections(
            LEXIQUE383_PATH, confirmedCorrections)
        nbInfra = applyInfraCorrections(
            LEXIQUE_INFRA_PATH, confirmedCorrections)
        nbMixte = applyMixteCorrections(
            LEXIQUE_MIXTE_PATH, confirmedCorrections)
        print(f"\n--apply: wrote {nbLexique} corrected rows to "
              f"{LEXIQUE383_PATH}")
        print(f"--apply: wrote {nbInfra} corrected rows to "
              f"{LEXIQUE_INFRA_PATH}")
        print(f"--apply: wrote {nbMixte} corrected rows to "
              f"{LEXIQUE_MIXTE_PATH}")
        if nbLexique != len(confirmedCorrections):
            print(f"WARNING: expected {len(confirmedCorrections)} "
                  f"Lexique383 rows written, only wrote {nbLexique}",
                  file=sys.stderr)
        if nbInfra != len(confirmedCorrections):
            print(f"WARNING: expected {len(confirmedCorrections)} "
                  f"infra rows written, only wrote {nbInfra}", file=sys.stderr)
        expectedMixte = sum(1 for c in confirmedCorrections
                             if c.mixteOldPhon is not None)
        if nbMixte != expectedMixte:
            print(f"WARNING: expected {expectedMixte} "
                  f"mixte rows written, only wrote {nbMixte}", file=sys.stderr)


if __name__ == "__main__":
    main()
