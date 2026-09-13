#!/bin/env python
#
# Investigates and (with --apply) corrects a grapheme-segmentation inconsistency
# for the infinitive forms of "effrayer", "repayer" and "ressayer":
# resources/LexiqueInfraCorrespondance.tsv encodes their "ay" as a single
# grapheme mapped to the two-phoneme unit "Ej" (grapheme "...ay.er", assoc
# "...ay-Ej.er-e"), while every other "pa:yer"-conjugation-template infinitive
# ("payer", "essayer", "balayer", "frayer", "monnayer", "relayer", "égayer",
# ...) splits the same cluster into two graphemes "a" and "y", each mapped to
# its own phoneme ("...a.y.er", assoc "...a-E.y-j.er-e"). This is scoped to
# infinitive rows only: LexiqueInfraCorrespondance.tsv is internally
# inconsistent about this cluster across *non*-infinitive forms too (e.g.
# "payant"/"essaye" use the combined "ay-Ej" convention, same as "effrayer"'s
# infinitive) -- normalizing that whole family is a separate, much larger,
# out-of-scope cleanup. This script only touches the 3 infinitive rows that
# are outliers *within the pa:yer template's own infinitive donor pool*,
# which is what src/verbparadigm.py's deriveConjugationEndingTables reads
# (see PROGRESS.md).
#
# Verified by actually running lexique.py's Word.breakdownSyllables with the
# corrected assoc string (not just string surgery): "effrayer" moves from
# orthosyll_cv "e|ff_r_ay|er" to "e|ff_r_a|y_er", matching "essayer"'s own
# "e|ss_a|y_er" shape exactly. syll_cv changes correspondingly.
#
# Dry-run by default: only reads and reports. --apply writes the corrected
# grapheme/assoc/regTo_GP fields back into the matching rows of
# LexiqueInfraCorrespondance.tsv, and the corrected syll_cv/orthosyll_cv
# fields back into the matching rows of the pre-built resources/LexiqueMixte.tsv,
# both in place. Idempotent: a no-op (0 rows modified) if run again after a
# successful --apply.
#
# resources/Lexique383.tsv is deliberately NOT touched: unlike the -gniez fix
# (fixGniezPronunciation.py), where Lexique383.tsv itself encoded the wrong
# phonology, here its cv-cv/syll/orthosyll columns are already consistent
# across the whole pa:yer family for these 3 lemmas too (all 26 infinitives
# uniformly encode the final syllable as a Y+V two-slot pattern, e.g.
# effrayer "V-CCV-YV"/"e-fRE-je" has the same shape as essayer
# "V-CV-YV"/"e-sE-je"). The bug is confined to LexiqueInfraCorrespondance.tsv's
# finer-grained grapheme-to-phoneme correspondence, which Lexique383.tsv
# doesn't encode at all.
import argparse
import csv
import sys

LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

TARGET_LEMMAS = ("effrayer", "repayer", "ressayer")


def readTsv(path: str) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def correctGrapheme(grapheme: str) -> str:
    tokens = grapheme.split(".")
    idx = [i for i, t in enumerate(tokens) if t == "ay"]
    if len(idx) != 1:
        raise ValueError(f"expected exactly one 'ay' token in {grapheme!r}, found {len(idx)}")
    i = idx[0]
    return ".".join(tokens[:i] + ["a", "y"] + tokens[i + 1:])


def correctAssoc(assoc: str) -> str:
    tokens = assoc.split(".")
    idx = [i for i, t in enumerate(tokens) if t == "ay-Ej"]
    if len(idx) != 1:
        raise ValueError(f"expected exactly one 'ay-Ej' token in {assoc!r}, found {len(idx)}")
    i = idx[0]
    return ".".join(tokens[:i] + ["a-E", "y-j"] + tokens[i + 1:])


def correctRegToGP(regToGP: str, grapheme: str) -> str:
    # regTo_GP has one value per grapheme token, trailing-dot-terminated
    # (e.g. "1.1.1.1.1." for a 5-grapheme word). The "ay" token's single
    # regularity flag becomes two flags ("0.0"), matching essayer's/payer's
    # own "a"/"y" flags -- both graphemes are irregular grapheme-phoneme
    # correspondences on their own (the "y" carries the yod that isn't
    # written, and the vowel needs the following "y" to get its /E/ value).
    tokens = grapheme.split(".")
    idx = [i for i, t in enumerate(tokens) if t == "ay"]
    if len(idx) != 1:
        raise ValueError(f"expected exactly one 'ay' token in {grapheme!r}, found {len(idx)}")
    i = idx[0]
    values = regToGP.split(".")  # trailing "" from the trailing dot
    return ".".join(values[:i] + ["0", "0"] + values[i + 1:])


MIXTE_CORRECTIONS: dict[str, tuple[str, str]] = {
    # lemme -> (new syll_cv, new orthosyll_cv), verified by actually running
    # lexique.py's Word.breakdownSyllables with the corrected assoc string
    # (see this script's module docstring).
    "effrayer": ("e|f_R_E|j_e", "e|ff_r_a|y_er"),
    "repayer": ("R_°|p_E|j_e", "r_e|p_a|y_er"),
    "ressayer": ("R_E|s_E|j_e", "r_e|ss_a|y_er"),
}


class AyCorrection:
    def __init__(self, infraRow: dict[str, str]) -> None:
        self.item = infraRow["item"]
        self.oldGrapheme = infraRow["grapheme"]
        self.newGrapheme = correctGrapheme(self.oldGrapheme)
        self.oldAssoc = infraRow["assoc"]
        self.newAssoc = correctAssoc(self.oldAssoc)
        self.oldRegToGP = infraRow["regTo_GP"]
        self.newRegToGP = correctRegToGP(self.oldRegToGP, self.oldGrapheme)
        self.newSyllCv, self.newOrthosyllCv = MIXTE_CORRECTIONS[self.item]


def findAyCorrections(infraRows: list[dict[str, str]]) -> list[AyCorrection]:
    corrections = []
    for row in infraRows:
        if row["item"] in TARGET_LEMMAS and row["cgram"] == "VER" \
                and "ay-Ej" in row["assoc"]:
            corrections.append(AyCorrection(row))
    return corrections


def printSample(corrections: list[AyCorrection]) -> None:
    print("=== Corrections (dry-run, no files modified) ===\n")
    for c in corrections:
        print(f"item: {c.item}")
        print(f"  grapheme : {c.oldGrapheme!r} -> {c.newGrapheme!r}")
        print(f"  assoc    : {c.oldAssoc!r} -> {c.newAssoc!r}")
        print(f"  regTo_GP : {c.oldRegToGP!r} -> {c.newRegToGP!r}")
        print(f"  mixte syll_cv     : -> {c.newSyllCv!r}")
        print(f"  mixte orthosyll_cv: -> {c.newOrthosyllCv!r}")
        print()


def applyInfraCorrections(path: str, corrections: list[AyCorrection]) -> int:
    correctionsByItem = {c.item: c for c in corrections}
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    itemIdx = header.index("item")
    cgramIdx = header.index("cgram")
    graphemeIdx = header.index("grapheme")
    assocIdx = header.index("assoc")
    regToGPIdx = header.index("regTo_GP")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        c = correctionsByItem.get(fields[itemIdx])
        if (c is not None and fields[cgramIdx] == "VER"
                and fields[graphemeIdx] == c.oldGrapheme
                and fields[assocIdx] == c.oldAssoc
                and fields[regToGPIdx] == c.oldRegToGP):
            fields[graphemeIdx] = c.newGrapheme
            fields[assocIdx] = c.newAssoc
            fields[regToGPIdx] = c.newRegToGP
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def applyMixteCorrections(path: str, corrections: list[AyCorrection]) -> int:
    correctionsByLemme = {c.item: c for c in corrections}
    with open(path, newline="") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    syllCvIdx = header.index("syll_cv")
    orthosyllCvIdx = header.index("orthosyll_cv")

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        c = correctionsByLemme.get(fields[lemmeIdx])
        # Scoped to the infinitive row: ortho == lemme for an infinitive.
        if (c is not None and fields[cgramIdx] == "VER"
                and fields[orthoIdx] == fields[lemmeIdx]):
            fields[syllCvIdx] = c.newSyllCv
            fields[orthosyllCvIdx] = c.newOrthosyllCv
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="") as f:
        f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect/correct the effrayer/repayer/ressayer infinitive "
        "'ay' grapheme-segmentation outlier in LexiqueInfraCorrespondance.tsv "
        "(and the resulting LexiqueMixte.tsv orthosyll_cv/syll_cv), "
        "bringing them in line with payer/essayer's own infinitive encoding."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections back to resources/LexiqueInfraCorrespondance.tsv "
        "and resources/LexiqueMixte.tsv (default: dry-run).",
    )
    args = parser.parse_args()

    infraRows = readTsv(LEXIQUE_INFRA_PATH)
    corrections = findAyCorrections(infraRows)

    printSample(corrections)

    print("=== Summary ===")
    print(f"Total infinitive rows found needing correction: {len(corrections)}")
    expected = len(TARGET_LEMMAS)
    if len(corrections) != expected:
        print(f"WARNING: expected {expected} corrections ({TARGET_LEMMAS}), "
              f"found {len(corrections)}: {[c.item for c in corrections]}",
              file=sys.stderr)

    if args.apply:
        nbInfra = applyInfraCorrections(LEXIQUE_INFRA_PATH, corrections)
        nbMixte = applyMixteCorrections(LEXIQUE_MIXTE_PATH, corrections)
        print(f"\n--apply: wrote {nbInfra} corrected rows to {LEXIQUE_INFRA_PATH}")
        print(f"--apply: wrote {nbMixte} corrected rows to {LEXIQUE_MIXTE_PATH}")
        if nbInfra != len(corrections):
            print(f"WARNING: expected {len(corrections)} infra rows written, "
                  f"only wrote {nbInfra}", file=sys.stderr)
        if nbMixte != len(corrections):
            print(f"WARNING: expected {len(corrections)} mixte rows written, "
                  f"only wrote {nbMixte}", file=sys.stderr)


if __name__ == "__main__":
    main()
