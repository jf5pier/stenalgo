#!/bin/env python
#
# Generates the missing "i"-form/"y"-form counterpart rows for the pa:yer
# conjugation template family (balayer, essayer, payer, ...). Both spellings
# of every stressed slot are phonologically distinct, genuinely attested
# words (confirmed by the user: "balaie" /balE/ has no glide, "balaye"
# /balEj/ does) -- see util/inventoryPayerFormsCoverage.py's read-only
# inventory, which found 77 (lemma, slot) combinations where only one side
# is present in resources/LexiqueMixte.tsv (45 missing the "y"-form, 32
# missing the "i"-form) out of 714 total combinations (76 both present, 561
# legitimately absent from the corpus -- not a defect).
#
# Method: Verbiste's conjugations-fr.xml gives the exact orthographic ending
# for both alternatives directly (no derivation needed for `ortho`). For the
# 3 phonological fields (phon, syll_cv, orthosyll_cv), this empirically
# derives a per-(slot, form-type) ending from every already-attested donor
# lemma that has that slot+form-type in LexiqueMixte.tsv (mirroring
# src/verbparadigm.py's deriveConjugationEndingTables, except split into "i"
# and "y" buckets -- today's parseConjugationTemplates only keeps the first
# XML alternative, so the shared machinery would otherwise blend the two
# spellings' phonology together for pa:yer specifically), then splices that
# ending onto the missing lemma's own radical (recovered from its attested
# infinitive). A candidate is only generated when EVERY donor lemma agreed
# on the ending for that (field, code, personNumber, formType) -- match rate
# 1.0, the same confidence bar util/completeVerbParadigms.py already uses
# for MIN_FINITE_MATCH_RATE, on the reasoning that phonology is exactly
# where a wrong guess is easiest to introduce silently.
#
# Per the user's direction: generated rows are appended to
# resources/LexiqueSynthetic.tsv (source=synthetic), NOT written into
# resources/LexiqueMixte.tsv directly -- consistent with
# util/completeVerbParadigms.py's existing synthetic-row convention. Both
# resources/LexiqueMixte.tsv (attested donor material) and the current
# resources/LexiqueSynthetic.tsv (to avoid re-generating a row a prior run,
# or completeVerbParadigms.py's own undersampling pass, already added) are
# read to determine what's genuinely still missing.
#
# NOTE: resources/LexiqueMixte.tsv is not yet wired to read
# resources/LexiqueSynthetic.tsv (see completeVerbParadigms.py's module
# docstring) -- util/validateLexiconAgainstVerbiste.py's WRONG_ENDING count
# for pa:yer will not drop until that wiring exists; this script only adds
# the rows to the designated synthetic file.
#
# Dry-run by default: only reads, prints a report of what would be
# generated/skipped. --apply appends the generated rows to
# resources/LexiqueSynthetic.tsv. Idempotent: a lemma/slot/form already
# present in either lexicon file is treated as satisfied, not regenerated.
import argparse
import csv
import os
from collections import Counter, defaultdict

from src.verbparadigm import (
    getTrustedTemplate,
    infinitiveRadical,
    loadVerbModelExceptions,
    loadVerbisteTemplates,
    parseConjugationTemplates,
)
from util.inventoryPayerFormsCoverage import TEMPLATE_NAME, dualSlots, rawDualEndingsForTemplate

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"

STRING_FIELDS = ("phon", "syll_cv", "orthosyll_cv")
MIN_MATCH_RATE = 1.0

SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)


def readTsvRows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def longestCommonSuffix(strings: list[str]) -> str:
    if not strings:
        return ""
    shortest = min(strings, key=len)
    for length in range(len(shortest), 0, -1):
        suffix = shortest[-length:]
        if all(s.endswith(suffix) for s in strings):
            return suffix
    return ""


def indexByLemmeOrtho(rows: list[dict[str, str]], payerLemmas: set[str]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("cgram") != "VER" or row.get("lemme") not in payerLemmas:
            continue
        index[(row["lemme"], row["ortho"])].append(row)
    return index


def tagPresent(
    attested: dict[tuple[str, str], list[dict[str, str]]],
    synthetic: dict[tuple[str, str], list[dict[str, str]]],
    lemme: str, ortho: str, tag: str,
) -> bool:
    for row in attested.get((lemme, ortho), []) + synthetic.get((lemme, ortho), []):
        if tag in {t for t in row["infover"].split(";") if t}:
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the missing pa:yer 'i'-form/'y'-form counterpart "
        "rows (ortho + phon + syllable breakdown) into resources/LexiqueSynthetic.tsv."
    )
    parser.add_argument("--apply", action="store_true",
                         help="Append generated rows to resources/LexiqueSynthetic.tsv "
                         "(default: dry-run report only).")
    args = parser.parse_args()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    template = conjugationTemplates[TEMPLATE_NAME]

    payerLemmas = {
        lemme for lemme, _name in verbisteTemplates.items()
        if getTrustedTemplate(lemme, verbisteTemplates, exceptions) == TEMPLATE_NAME
    }

    rawForms = rawDualEndingsForTemplate(VERBISTE_CONJUGATIONS_PATH, TEMPLATE_NAME)
    slots = dualSlots(rawForms)  # (code, personNumber, iEnding, yEnding)

    mixteRows = readTsvRows(LEXIQUE_MIXTE_PATH)
    syntheticRows = readTsvRows(SYNTHETIC_PATH) if os.path.exists(SYNTHETIC_PATH) else []

    attestedByLemmeOrtho = indexByLemmeOrtho(mixteRows, payerLemmas)
    syntheticByLemmeOrtho = indexByLemmeOrtho(syntheticRows, payerLemmas)

    infinitiveByLemme: dict[str, dict[str, str]] = {}
    for (lemme, ortho), rows in attestedByLemmeOrtho.items():
        if ortho != lemme:
            continue
        for row in rows:
            if "inf" in {t for t in row["infover"].split(";") if t}:
                infinitiveByLemme[lemme] = row
                break

    fieldSuffix = {
        field: longestCommonSuffix([row[field] for row in infinitiveByLemme.values()])
        for field in STRING_FIELDS
    }

    # candidatesByKey[(field, code, personNumber, formType)] -> list of endings
    candidatesByKey: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for lemme, infinitiveWord in infinitiveByLemme.items():
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
                    for field in STRING_FIELDS:
                        suffix = fieldSuffix[field]
                        infVal = infinitiveWord[field]
                        radicalLen = len(infVal) - len(suffix)
                        if radicalLen < 0 or not row[field].startswith(infVal[:radicalLen]):
                            continue
                        candidatesByKey[(field, code, personNumber, formType)].append(row[field][radicalLen:])

    slotEnding: dict[tuple[str, str, str, str], str] = {}
    slotMatchRate: dict[tuple[str, str, str, str], float] = {}
    slotDonorCount: dict[tuple[str, str, str, str], int] = {}
    for key, candidates in candidatesByKey.items():
        mode, count = Counter(candidates).most_common(1)[0]
        slotEnding[key] = mode
        slotMatchRate[key] = count / len(candidates)
        slotDonorCount[key] = len(candidates)

    generated: list[dict[str, str]] = []
    skipped: list[tuple[str, str, str, str]] = []  # lemme, tag, ortho, reason

    for lemme in sorted(payerLemmas):
        infinitiveWord = infinitiveByLemme.get(lemme)
        if infinitiveWord is None:
            continue
        try:
            radical = infinitiveRadical(lemme, template)
        except ValueError as error:
            skipped.append((lemme, "", "", str(error)))
            continue
        for code, personNumber, iEnding, yEnding in slots:
            tag = f"{code}:{personNumber}"
            iOrtho, yOrtho = radical + iEnding, radical + yEnding
            iPresent = tagPresent(attestedByLemmeOrtho, syntheticByLemmeOrtho, lemme, iOrtho, tag)
            yPresent = tagPresent(attestedByLemmeOrtho, syntheticByLemmeOrtho, lemme, yOrtho, tag)
            if iPresent == yPresent:
                continue  # BOTH_PRESENT or NEITHER_PRESENT -- nothing to generate
            missingSide = "y" if iPresent else "i"
            missingOrtho = yOrtho if iPresent else iOrtho

            fieldValues: dict[str, str] = {}
            reasons: list[str] = []
            for field in STRING_FIELDS:
                suffix = fieldSuffix[field]
                infVal = infinitiveWord[field]
                radicalLen = len(infVal) - len(suffix)
                key = (field, code, personNumber, missingSide)
                ending = slotEnding.get(key)
                matchRate = slotMatchRate.get(key, 0.0)
                donorCount = slotDonorCount.get(key, 0)
                if radicalLen < 0 or ending is None or matchRate < MIN_MATCH_RATE:
                    reasons.append(f"{field}: no confident donor ending "
                                    f"(matchRate={matchRate:.2f}, donors={donorCount})")
                    continue
                fieldValues[field] = infVal[:radicalLen] + ending

            if reasons:
                skipped.append((lemme, tag, missingOrtho, "; ".join(reasons)))
                continue

            generated.append({
                "ortho": missingOrtho, "phon": fieldValues["phon"], "lemme": lemme,
                "cgram": "VER", "cgramortho": "VER", "genre": "", "nombre": "",
                "infover": f"{tag};", "syll_cv": fieldValues["syll_cv"],
                "orthosyll_cv": fieldValues["orthosyll_cv"],
                "freqlivres": "0.0", "freqfilms2": "0.0", "source": "synthetic",
            })

    print(f"pa:yer-family lemmas: {len(payerLemmas)}  (with attested infinitive: {len(infinitiveByLemme)})")
    print(f"Dual-form slots per lemma: {len(slots)}\n")
    print(f"=== Generated candidates ({len(generated)}) ===")
    for row in generated[:20]:
        print(f"  {row['lemme']}: {row['ortho']!r}  phon={row['phon']!r}  "
              f"infover={row['infover']!r}  syll_cv={row['syll_cv']!r}  orthosyll_cv={row['orthosyll_cv']!r}")
    if len(generated) > 20:
        print(f"  ... and {len(generated) - 20} more")

    print(f"\n=== Skipped ({len(skipped)}) ===")
    for lemme, tag, ortho, reason in skipped[:20]:
        print(f"  {lemme} {tag} ({ortho!r}): {reason}")
    if len(skipped) > 20:
        print(f"  ... and {len(skipped) - 20} more")

    if args.apply:
        fileExists = os.path.exists(SYNTHETIC_PATH)
        with open(SYNTHETIC_PATH, "a", newline="", encoding="utf-8") as f:
            if not fileExists:
                f.write(SYNTHETIC_HEADER)
            for row in generated:
                f.write("\t".join(row[col] for col in (
                    "ortho", "phon", "lemme", "cgram", "cgramortho", "genre", "nombre",
                    "infover", "syll_cv", "orthosyll_cv", "freqlivres", "freqfilms2", "source",
                )) + "\n")
        print(f"\n--apply: appended {len(generated)} rows to {SYNTHETIC_PATH}")


if __name__ == "__main__":
    main()
