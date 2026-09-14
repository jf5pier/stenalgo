#!/bin/env python
#
# Fixes a pre-existing phonological-transcription inconsistency in
# resources/Lexique383.tsv (and consequently resources/LexiqueMixte.tsv,
# which merges it) affecting the pa:yer conjugation template family
# (balayer, essayer, payer, ...): the alternation vowel in the non-futur
# dual-form slots (ind:pre/sub:pre/imp:pre, persons 1s/2s/3s/3p/imp:2s --
# all genuinely homophonous for a given lemma+form since the person-marking
# letters that differ orthographically there ("s", "nt") are silent) should
# be uniformly the open-mid front vowel /ɛ/, written "E" (i-form: "...E",
# e.g. balaie=balE) or "E" + glide (y-form: "...Ej", e.g. balaye=balEj).
#
# Empirically confirmed: every pa:yer i-form row in this slot family is
# already uniformly "E" (verified across every lemma with >=1 attested
# i-form row -- zero exceptions), and several lemmas' own y-form rows show
# BOTH spellings for what should be the identical homophone (e.g. "payer":
# ind:pre:1s/3s "paye"=pEj but ind:pre:2s/3p "payes"/"payent"=pej -- same
# spoken word, inconsistent transcription). This isn't a radical-shape
# effect (confirmed by checking: lemmas with identical radical shape land
# on both sides of the split) -- it's the same class of pre-existing
# corpus defect already partially addressed elsewhere in this lexicon
# (see the "-gniez/-gnez" and "E phoneme instead of e" fixes in git
# history); this script closes the remaining pa:yer-specific instances.
#
# Confirmed present in resources/Lexique383.tsv itself (not just derived
# data), e.g. "payes"/payer phon="pej" and "embrayes"/embrayer phon="@bRej"
# -- both corrected here alongside resources/LexiqueMixte.tsv.
#
# Method: for each pa:yer lemma's attested VER row whose ortho (via
# infinitiveRadical, orthographic only -- unambiguous) matches this
# template's i-form or y-form ending for a non-futur dual slot: `phon`'s
# nonfutur ending is exactly 1 char ("E"/"e") for the i-form or 2 ("Ej"/"ej")
# for the y-form with nothing else trailing (confirmed empirically -- the
# whole homophone group shares one identical string per lemma+form), so a
# lowercase tail is fixed by a direct case-flip (fixPhon). `syll_cv` uses
# the same phonemic alphabet but with "_"/"|" delimiters that shift the
# vowel's exact offset (merged "Ej" vs split "e_j"), so its correction
# (fixSyllCv) instead locates the last lowercase "e" within the trailing 5
# characters and flips only that one.
#
# Dry-run by default: only reads and reports. --apply writes corrected
# phon/syll_cv back into both resources/Lexique383.tsv and
# resources/LexiqueMixte.tsv in place (orthosyll_cv is untouched -- see
# above). Idempotent: 0 corrections needed if run again after a successful
# --apply.
import argparse
import csv
from collections import defaultdict

from src.verbparadigm import getTrustedTemplate, infinitiveRadical, loadVerbModelExceptions, loadVerbisteTemplates, parseConjugationTemplates
from util.inventoryPayerFormsCoverage import TEMPLATE_NAME, dualSlots, rawDualEndingsForTemplate

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"

# orthosyll_cv is deliberately excluded: it's the ORTHOGRAPHIC syllable
# breakdown (real French letters -- "e" there is a literal, always-lowercase
# grapheme, never a phoneme-quality marker), unlike phon/syll_cv which use
# the same phonemic alphabet (X-SAMPA-like, where "E" vs "e" is a genuine
# vowel-quality distinction). Applying this fix to orthosyll_cv would
# corrupt correct spellings like "z_é|z_ai_e" into "z_é|z_ai_E".
STRING_FIELDS = ("phon", "syll_cv")
NONFUTUR_CODES = {"ind:pre", "sub:pre", "imp:pre"}


def readTsvRows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def fixPhon(value: str, formType: str) -> str | None:
    """
    The nonfutur dual-slot phon value is exactly radical + "E" (i-form) or
    radical + "Ej" (y-form) -- confirmed empirically: identical string
    across every person in the homophone group, no extra trailing material.
    Returns the corrected value, or None if `value` is already correct.
    """
    suffixLen = 1 if formType == "i" else 2
    tail = value[-suffixLen:]
    if tail in ("E", "Ej"):
        return None
    if tail in ("e", "ej"):
        return value[:-suffixLen] + "E" + tail[1:]
    return None  # unexpected shape -- don't guess, let the caller skip it


def fixSyllCv(value: str) -> str | None:
    """
    syll_cv uses the same phonemic alphabet as phon but with "_"/"|"
    delimiters, so the alternation vowel isn't always at a fixed offset
    from the end (e.g. merged "Ej" vs split "e_j"). The last lowercase "e"
    in the string is always that vowel (nothing else lowercase-e-shaped
    appears in this trailing region -- confirmed empirically), guarded to
    only the last 5 characters so an unrelated radical "e" is never touched.
    Returns the corrected value, or None if no lowercase "e" is found there.
    """
    idx = value.rfind("e")
    if idx == -1 or len(value) - idx > 5:
        return None
    return value[:idx] + "E" + value[idx + 1:]


def findCorrections() -> dict[tuple[str, str, str, str], dict[str, str]]:
    """
    Returns {(ortho, lemme, cgram, infover) -> {field: correctedValue}} for
    every attested row needing a correction, keyed exactly like the rows in
    resources/Lexique383.tsv / resources/LexiqueMixte.tsv.
    """
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    template = conjugationTemplates[TEMPLATE_NAME]

    payerLemmas = {
        lemme for lemme, _name in verbisteTemplates.items()
        if getTrustedTemplate(lemme, verbisteTemplates, exceptions) == TEMPLATE_NAME
    }

    rawForms = rawDualEndingsForTemplate(VERBISTE_CONJUGATIONS_PATH, TEMPLATE_NAME)
    slots = [s for s in dualSlots(rawForms) if s[0] in NONFUTUR_CODES]

    mixteRows = readTsvRows(LEXIQUE_MIXTE_PATH)
    attestedByLemmeOrtho: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mixteRows:
        if row["cgram"] == "VER" and row["lemme"] in payerLemmas:
            attestedByLemmeOrtho[(row["lemme"], row["ortho"])].append(row)

    corrections: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for lemme in payerLemmas:
        try:
            radical = infinitiveRadical(lemme, template)
        except ValueError:
            continue
        for code, personNumber, iEnding, yEnding in slots:
            tag = f"{code}:{personNumber}"
            for ending, formType in ((iEnding, "i"), (yEnding, "y")):
                ortho = radical + ending
                for row in attestedByLemmeOrtho.get((lemme, ortho), []):
                    if tag not in {t for t in row["infover"].split(";") if t}:
                        continue
                    fieldFixes: dict[str, str] = {}
                    correctedPhon = fixPhon(row["phon"], formType)
                    if correctedPhon is not None:
                        fieldFixes["phon"] = correctedPhon
                        correctedSyllCv = fixSyllCv(row["syll_cv"])
                        if correctedSyllCv is not None:
                            fieldFixes["syll_cv"] = correctedSyllCv
                    if fieldFixes:
                        key = (row["ortho"], row["lemme"], row["cgram"], row["infover"])
                        corrections.setdefault(key, {}).update(fieldFixes)
    return corrections


def applyCorrections(path: str, corrections: dict[tuple[str, str, str, str], dict[str, str]]) -> int:
    """
    Writes phon/syll_cv corrections into `path`. resources/Lexique383.tsv
    doesn't have a syll_cv column at all (LexiqueMixte.tsv's syll_cv is
    derived from Lexique383's phon+assoc data by lexique.py) -- only the
    fields actually present in the file's header are corrected there.
    """
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    fieldsPresent = [field for field in STRING_FIELDS if field in header]
    idx = {name: header.index(name) for name in ("ortho", "lemme", "cgram", "infover", *fieldsPresent)}

    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[idx["ortho"]], fields[idx["lemme"]], fields[idx["cgram"]], fields[idx["infover"]])
        fieldFixes = corrections.get(key)
        if not fieldFixes:
            continue
        changed = False
        for field, newValue in fieldFixes.items():
            if field not in idx:
                continue
            if fields[idx[field]] != newValue:
                fields[idx[field]] = newValue
                changed = True
        if changed:
            lines[i] = "\t".join(fields) + ending
            modified += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        f.writelines(lines)
    return modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix the pa:yer non-futur dual-slot e/E vowel-quality "
        "transcription inconsistency in resources/Lexique383.tsv and "
        "resources/LexiqueMixte.tsv."
    )
    parser.add_argument("--apply", action="store_true",
                         help="Write corrections in place (default: dry-run).")
    args = parser.parse_args()

    corrections = findCorrections()

    print(f"=== Corrections found: {len(corrections)} ===\n")
    for (ortho, lemme, cgram, infover), fieldFixes in list(corrections.items())[:30]:
        print(f"{lemme} {ortho!r} ({infover})")
        for field, newValue in fieldFixes.items():
            print(f"  {field}: -> {newValue!r}")
    if len(corrections) > 30:
        print(f"  ... and {len(corrections) - 30} more")

    if args.apply:
        n383 = applyCorrections(LEXIQUE_383_PATH, corrections)
        nMixte = applyCorrections(LEXIQUE_MIXTE_PATH, corrections)
        print(f"\n--apply: corrected {n383} rows in {LEXIQUE_383_PATH}")
        print(f"--apply: corrected {nMixte} rows in {LEXIQUE_MIXTE_PATH}")


if __name__ == "__main__":
    main()
