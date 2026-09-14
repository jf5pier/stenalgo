#!/bin/env python
#
# Generates the missing alternative-form rows for the ass:eoir conjugation
# template family (asseoir, rasseoir -- surseoir uses its own separate
# surs:eoir template and isn't flagged, out of scope). Every alternative at
# a given slot (2-way for présent/imparfait/imperatif-présent/subjonctif-
# présent, 3-way "ié"/"eye"/"oi" for futur-simple/conditionnel-présent) is a
# phonologically genuine, independently attested French conjugation, not a
# "pick one" situation -- see util/inventoryAsseoirFormsCoverage.py's
# read-only inventory: 23 of 70 (lemma, slot) combinations are PARTIAL (some
# but not all alternatives present), 31 NONE_PRESENT (legitimately absent
# from the corpus, not a defect), 16 ALL_PRESENT already.
#
# Method: same as util/fixPayerDualFormGaps.py, generalized to a variable
# number of alternatives per slot instead of a fixed "i"/"y" pair. Verbiste's
# conjugations-fr.xml gives the exact orthographic ending for every
# alternative directly. For phon/syll_cv/orthosyll_cv, this empirically
# derives a per-(slot, altIndex) ending from whichever of the family's 2
# lemmas already has that (slot, altIndex) attested in
# resources/LexiqueMixte.tsv, splices it onto the missing lemma's own
# radical (recovered from its attested infinitive), and only generates when
# every donor that HAS this (slot, altIndex) attested agrees on the ending
# (match rate 1.0) -- with only 2 possible donor lemmas here, this in
# practice means "generate from the one sibling that has it, when there's
# only one, or require both to agree when both do."
#
# Per established project convention (see util/fixPayerDualFormGaps.py):
# generated rows are appended to resources/LexiqueSynthetic.tsv
# (source=synthetic), NOT written into resources/LexiqueMixte.tsv directly.
# Both resources/LexiqueMixte.tsv (attested donor material) and the current
# resources/LexiqueSynthetic.tsv are read to determine what's genuinely
# still missing, so this is idempotent and safe to re-run.
#
# NOTE: resources/LexiqueSynthetic.tsv is not yet wired into
# resources/LexiqueMixte.tsv/lexique.py's merge step (deliberately deferred
# elsewhere) -- util/validateLexiconAgainstVerbiste.py's WRONG_ENDING count
# for ass:eoir will not drop until that separate wiring decision is made;
# this script only adds the rows to the designated synthetic file.
#
# Dry-run by default: only reads, prints a report of what would be
# generated/skipped. --apply appends the generated rows to
# resources/LexiqueSynthetic.tsv. Idempotent: a lemma/slot/alternative
# already present in either lexicon file is treated as satisfied, not
# regenerated.
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
from util.inventoryAsseoirFormsCoverage import (
    TEMPLATE_NAME,
    multiSlots,
    rawAlternativesForTemplate,
)

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


def indexByLemmeOrtho(rows: list[dict[str, str]], lemmas: set[str]) -> dict[tuple[str, str], list[dict[str, str]]]:
    index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("cgram") != "VER" or row.get("lemme") not in lemmas:
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
        description="Generate the missing ass:eoir alternative-form rows "
        "(ortho + phon + syllable breakdown) into resources/LexiqueSynthetic.tsv."
    )
    parser.add_argument("--apply", action="store_true",
                         help="Append generated rows to resources/LexiqueSynthetic.tsv "
                         "(default: dry-run report only).")
    args = parser.parse_args()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    template = conjugationTemplates[TEMPLATE_NAME]

    lemmas = {
        lemme for lemme, _name in verbisteTemplates.items()
        if getTrustedTemplate(lemme, verbisteTemplates, exceptions) == TEMPLATE_NAME
    }

    rawForms = rawAlternativesForTemplate(VERBISTE_CONJUGATIONS_PATH, TEMPLATE_NAME)
    slots = multiSlots(rawForms)  # (code, personNumber, alternatives)

    mixteRows = readTsvRows(LEXIQUE_MIXTE_PATH)
    syntheticRows = readTsvRows(SYNTHETIC_PATH) if os.path.exists(SYNTHETIC_PATH) else []

    attestedByLemmeOrtho = indexByLemmeOrtho(mixteRows, lemmas)
    syntheticByLemmeOrtho = indexByLemmeOrtho(syntheticRows, lemmas)

    infinitiveByLemme: dict[str, dict[str, str]] = {}
    for (lemme, ortho), rows in attestedByLemmeOrtho.items():
        if ortho != lemme:
            continue
        for row in rows:
            if "inf" in {t for t in row["infover"].split(";") if t}:
                infinitiveByLemme[lemme] = row
                break

    # Unlike pa:yer (whose infinitive suffix is derived by longest-common-
    # suffix across 26 donor lemmas), ass:eoir's infinitiveSuffix comes
    # straight from the template (only 2 lemmas share it).
    infSuffix = template.infinitiveSuffix

    # candidatesByKey[(field, code, personNumber, altIndex)] -> list of endings
    candidatesByKey: dict[tuple[str, str, str, int], list[str]] = defaultdict(list)
    for lemme, infinitiveWord in infinitiveByLemme.items():
        try:
            radical = infinitiveRadical(lemme, template)
        except ValueError:
            continue
        for code, personNumber, alternatives in slots:
            tag = f"{code}:{personNumber}"
            for altIndex, ending in enumerate(alternatives):
                ortho = radical + ending
                for row in attestedByLemmeOrtho.get((lemme, ortho), []):
                    if tag not in {t for t in row["infover"].split(";") if t}:
                        continue
                    for field in STRING_FIELDS:
                        infVal = infinitiveWord[field]
                        radicalLen = len(infVal) - len(infSuffix) if infSuffix else len(infVal)
                        if radicalLen < 0 or not row[field].startswith(infVal[:radicalLen]):
                            continue
                        candidatesByKey[(field, code, personNumber, altIndex)].append(
                            row[field][radicalLen:])

    slotEnding: dict[tuple[str, str, str, int], str] = {}
    slotMatchRate: dict[tuple[str, str, str, int], float] = {}
    slotDonorCount: dict[tuple[str, str, str, int], int] = {}
    for key, candidates in candidatesByKey.items():
        mode, count = Counter(candidates).most_common(1)[0]
        slotEnding[key] = mode
        slotMatchRate[key] = count / len(candidates)
        slotDonorCount[key] = len(candidates)

    generated: list[dict[str, str]] = []
    skipped: list[tuple[str, str, str, str]] = []  # lemme, tag, ortho, reason

    for lemme in sorted(lemmas):
        infinitiveWord = infinitiveByLemme.get(lemme)
        if infinitiveWord is None:
            continue
        try:
            radical = infinitiveRadical(lemme, template)
        except ValueError as error:
            skipped.append((lemme, "", "", str(error)))
            continue
        for code, personNumber, alternatives in slots:
            tag = f"{code}:{personNumber}"
            orthos = [radical + ending for ending in alternatives]
            present = [
                tagPresent(attestedByLemmeOrtho, syntheticByLemmeOrtho, lemme, o, tag)
                for o in orthos
            ]
            if all(present) or not any(present):
                continue  # ALL_PRESENT or NONE_PRESENT -- nothing to generate

            for altIndex, (ending, ortho, isPresent) in enumerate(zip(alternatives, orthos, present)):
                if isPresent:
                    continue
                fieldValues: dict[str, str] = {}
                reasons: list[str] = []
                for field in STRING_FIELDS:
                    infVal = infinitiveWord[field]
                    radicalLen = len(infVal) - len(infSuffix) if infSuffix else len(infVal)
                    key = (field, code, personNumber, altIndex)
                    fieldEnding = slotEnding.get(key)
                    matchRate = slotMatchRate.get(key, 0.0)
                    donorCount = slotDonorCount.get(key, 0)
                    if radicalLen < 0 or fieldEnding is None or matchRate < MIN_MATCH_RATE:
                        reasons.append(f"{field}: no confident donor ending "
                                        f"(matchRate={matchRate:.2f}, donors={donorCount})")
                        continue
                    fieldValues[field] = infVal[:radicalLen] + fieldEnding

                if reasons:
                    skipped.append((lemme, tag, ortho, "; ".join(reasons)))
                    continue

                generated.append({
                    "ortho": ortho, "phon": fieldValues["phon"], "lemme": lemme,
                    "cgram": "VER", "cgramortho": "VER", "genre": "", "nombre": "",
                    "infover": f"{tag};", "syll_cv": fieldValues["syll_cv"],
                    "orthosyll_cv": fieldValues["orthosyll_cv"],
                    "freqlivres": "0.0", "freqfilms2": "0.0", "source": "synthetic",
                })

    print(f"ass:eoir-family lemmas: {len(lemmas)}  (with attested infinitive: {len(infinitiveByLemme)})")
    print(f"Multi-alternative slots per lemma: {len(slots)}\n")
    print(f"=== Generated candidates ({len(generated)}) ===")
    for row in generated:
        print(f"  {row['lemme']}: {row['ortho']!r}  phon={row['phon']!r}  "
              f"infover={row['infover']!r}  syll_cv={row['syll_cv']!r}  orthosyll_cv={row['orthosyll_cv']!r}")

    print(f"\n=== Skipped ({len(skipped)}) ===")
    for lemme, tag, ortho, reason in skipped:
        print(f"  {lemme} {tag} ({ortho!r}): {reason}")

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
