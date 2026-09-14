#!/bin/env python
#
# Cross-validates every VER row of a lexicon TSV (resources/LexiqueMixte.tsv by
# default) against Verbiste's own conjugation data (verbs-fr.xml +
# conjugations-fr.xml) and this project's own orthographic-generation code
# (infinitiveRadical / generateOrthoForm), to systematically find the class of
# lexicon-data defects this session kept discovering one at a time (a
# co-tagged infinitive corrupting deriveConjugationEndingTables, a wrong
# ending propagating into a generated form, ...).
#
# For every VER row whose lemma resolves to a trusted template
# (getTrustedTemplate), and for every tag in its infoVerb, this recomputes
# the orthographic form Verbiste's own template says that tag should produce
# (generateOrthoForm(infinitiveRadical(lemme, template), template, ...)) and
# compares it to the row's actual `ortho`. A mismatch means one of: a
# genuinely irregular verb misclassified under a regular template, a data
# error in the lexicon row itself (wrong tag, wrong spelling), or a
# structural gap (the tag doesn't exist in the assigned template at all).
#
# Flags fall into three types, aggregated separately:
#   CO_TAGGED_INFINITIVE  -- row carries "inf" plus >=1 other tag (the class
#                            of bug already found and fixed twice this
#                            session: attestedInfinitiveWordByLemme's
#                            ortho==lemme guard, and
#                            deriveConjugationEndingTables's "inf" skip).
#   UNDEFINED_SLOT         -- a tag whose (code, personNumber) or
#                            (gender, number) doesn't exist in the assigned
#                            template's endings at all (generateOrthoForm
#                            returns None).
#   WRONG_ENDING            -- generateOrthoForm produces a different
#                            orthography than the row's own `ortho` for a
#                            tag that DOES exist in the template.
#
# Report-only: never modifies any file. Prints per-type counts, a per-type
# breakdown by (template, code, personNumber) to separate systematic issues
# (many lemmas, same slot -- likely a template bug, like this session's
# abr:éger/étudi:er fixes) from isolated ones (likely a single bad lexicon
# row), and a sample of concrete rows for each. Use --dump-csv to write every
# flagged row (with its type and expected-vs-actual) to a CSV for full review
# before any correction is made.
import argparse
import csv
from collections import Counter, defaultdict

from src.verbparadigm import (
    ConjugationTemplate,
    VerbModelException,
    Lemme,
    PARTICIPE_PASSE_INDEX,
    generateOrthoForm,
    getTrustedTemplate,
    infinitiveRadical,
    loadVerbModelExceptions,
    loadVerbisteTemplates,
    parseConjugationTemplates,
)

LEXICON_PATH_DEFAULT = "resources/LexiqueMixte.tsv"
VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"

DUPLICATE_INF_TAG = "DUPLICATE_INF_TAG"
INF_PLUS_OTHER_TAG = "INF_PLUS_OTHER_TAG"
PARTICIPE_MISSING_GENDER_NUMBER = "PARTICIPE_MISSING_GENDER_NUMBER"
UNDEFINED_SLOT = "UNDEFINED_SLOT"
WRONG_ENDING = "WRONG_ENDING"
# Step-0 sub-types of what used to all be lumped into WRONG_ENDING (see
# module docstring's batching plan): a row whose infoVerb carries >=2 tags
# where at least one tag's expected orthography agrees with `ortho` and at
# least one disagrees is a tag-noise problem, not a template/spelling
# problem -- the disagreeing tag(s) are simply wrong data on an otherwise
# correct row, and (unlike single-tag WRONG_ENDING) we know that concretely
# because the row's *other* tag proves what the correct form actually is.
PARTICIPE_PLUS_OTHER_TAG = "PARTICIPE_PLUS_OTHER_TAG"
MULTI_TAG_PARTIAL_MISMATCH = "MULTI_TAG_PARTIAL_MISMATCH"
# Residual single-tag WRONG_ENDING flags where `ortho` doesn't even share a
# prefix with `lemme` -- a strong signal the row's `lemme`/`tag` (not the
# template) is simply wrong data (e.g. ortho="contrôler" lemme="chuter").
SUSPECTED_WRONG_LEMME = "SUSPECTED_WRONG_LEMME"
ALL_FLAG_TYPES = (
    DUPLICATE_INF_TAG, INF_PLUS_OTHER_TAG, PARTICIPE_MISSING_GENDER_NUMBER,
    UNDEFINED_SLOT, PARTICIPE_PLUS_OTHER_TAG, MULTI_TAG_PARTIAL_MISMATCH,
    SUSPECTED_WRONG_LEMME, WRONG_ENDING,
)

LEMME_PREFIX_LEN = 3


class Flag:
    def __init__(self, flagType: str, row: dict[str, str], template: str,
                 tag: str, expected: str | None) -> None:
        self.flagType = flagType
        self.ortho = row["ortho"]
        self.lemme = row["lemme"]
        self.infoVerb = row["infover"]
        self.template = template
        self.tag = tag
        self.expected = expected


def rawInfoVerbTags(infoVerb: str) -> list[str]:
    return [tag for tag in infoVerb.split(";") if tag]


class UndefinedSlot(Exception):
    """Raised when a tag's slot doesn't exist in the assigned template at all
    (a structural gap: either the template is incomplete, or the tag is a
    lexicon error), as opposed to existing but disagreeing with `ortho`."""


class MissingParticipeGenderNumber(Exception):
    """Raised for a "par:pas" tag whose row has no (or an unrecognized)
    gender/number -- a lexicon data-completeness gap, not an ending error."""


def expectedOrthoForTag(
    row: dict[str, str], template: ConjugationTemplate, radical: str, tag: str,
) -> str:
    """Returns the orthography `tag` implies under `template`. Raises
    UndefinedSlot if the tag's slot doesn't exist in the template, or
    MissingParticipeGenderNumber for an unresolvable "par:pas" tag."""
    if tag == "inf":
        return row["lemme"]
    parts = tag.split(":")
    if len(parts) == 2:
        moodCode, tenseCode = parts
        code = f"{moodCode}:{tenseCode}"
        if code == "par:pas":
            gender, number = row["genre"] or None, row["nombre"] or None
            if gender is None or number is None or (gender, number) not in PARTICIPE_PASSE_INDEX:
                raise MissingParticipeGenderNumber()
            expected = generateOrthoForm(radical, template, code, gender=gender, number=number)
        else:
            expected = generateOrthoForm(radical, template, code)
    elif len(parts) == 3:
        code = f"{parts[0]}:{parts[1]}"
        personNumber = parts[2]
        expected = generateOrthoForm(radical, template, code, personNumber=personNumber)
    else:
        expected = None
    if expected is None:
        raise UndefinedSlot()
    return expected


def sharesLemmePrefix(ortho: str, lemme: str, prefixLen: int = LEMME_PREFIX_LEN) -> bool:
    """Cheap signal that `ortho` plausibly belongs to `lemme` at all (as
    opposed to a row-level data-corruption case like ortho="contrôler"
    lemme="chuter", where they share nothing)."""
    n = min(prefixLen, len(ortho), len(lemme))
    if n == 0:
        return True
    return ortho[:n] == lemme[:n]


def evaluateTag(
    row: dict[str, str], template: ConjugationTemplate, radical: str, tag: str,
) -> tuple[str, str | None]:
    """Returns (status, expected) for a single tag, where status is one of
    "match", "mismatch", "undefined", "missing_participe". Never raises."""
    try:
        expected = expectedOrthoForTag(row, template, radical, tag)
    except MissingParticipeGenderNumber:
        return ("missing_participe", None)
    except UndefinedSlot:
        return ("undefined", None)
    return ("match" if expected == row["ortho"] else "mismatch", expected)


def validateRow(
    row: dict[str, str],
    verbisteTemplates: dict[Lemme, str],
    exceptions: dict[Lemme, VerbModelException],
    conjugationTemplates: dict[str, ConjugationTemplate],
) -> list[Flag]:
    if row["cgram"] != "VER" or not row["infover"]:
        return []
    lemme = row["lemme"]
    templateName = getTrustedTemplate(lemme, verbisteTemplates, exceptions)
    if templateName is None:
        return []
    template = conjugationTemplates.get(templateName)
    if template is None:
        return []
    try:
        radical = infinitiveRadical(lemme, template)
    except ValueError:
        return []

    tags = rawInfoVerbTags(row["infover"])
    flags: list[Flag] = []

    if "inf" in tags and len(tags) > 1:
        if all(tag == "inf" for tag in tags):
            flags.append(Flag(DUPLICATE_INF_TAG, row, templateName,
                               ";".join(tags), row["lemme"]))
        else:
            flags.append(Flag(INF_PLUS_OTHER_TAG, row, templateName,
                               ";".join(tags), row["lemme"]))
        # A row whose infoVerb also carries "inf" is untrustworthy for its
        # other tags too (see attestedInfinitiveWordByLemme's docstring) --
        # checking them here would just re-report the same root cause as
        # spurious WRONG_ENDING/UNDEFINED_SLOT noise on every non-inf tag.
        return flags

    # A list (not a dict) so that a row with a literal duplicate tag (e.g.
    # "par:pas;par:pas;") still yields one evaluation -- and, downstream, one
    # flag -- per occurrence rather than silently collapsing duplicates.
    evaluations = [(tag, *evaluateTag(row, template, radical, tag)) for tag in tags]

    # "par:pas" resolves via its own gender/number-driven check unconditionally
    # -- a genuinely missing gender/number is a data-completeness gap
    # regardless of what the row's other tags say.
    for tag, status, _ in evaluations:
        if status == "missing_participe":
            flags.append(Flag(PARTICIPE_MISSING_GENDER_NUMBER, row, templateName, tag, None))

    remaining = [(tag, status, expected) for tag, status, expected in evaluations
                 if status != "missing_participe"]
    matchingTags = [tag for tag, status, _ in remaining if status == "match"]
    problemEntries = [(tag, status, expected) for tag, status, expected in remaining
                       if status != "match"]

    if matchingTags and problemEntries:
        # At least one tag on this row agrees with `ortho` and at least one
        # doesn't -- the agreeing tag(s) prove the row's true form, so the
        # disagreeing tag(s) are simply wrong/spurious data, not a
        # template/spelling problem (see PARTICIPE_PLUS_OTHER_TAG /
        # MULTI_TAG_PARTIAL_MISMATCH docs above).
        flagType = PARTICIPE_PLUS_OTHER_TAG if "par:pas" in matchingTags else MULTI_TAG_PARTIAL_MISMATCH
        for tag, _, expected in problemEntries:
            flags.append(Flag(flagType, row, templateName, tag, expected))
        return flags

    for tag, status, expected in problemEntries:
        if status == "undefined":
            flags.append(Flag(UNDEFINED_SLOT, row, templateName, tag, None))
        else:
            flagType = WRONG_ENDING
            if not sharesLemmePrefix(row["ortho"], row["lemme"]):
                flagType = SUSPECTED_WRONG_LEMME
            flags.append(Flag(flagType, row, templateName, tag, expected))

    return flags


def slotKey(flag: Flag) -> tuple[str, str]:
    parts = flag.tag.split(":")
    if len(parts) >= 2:
        return (flag.template, f"{parts[0]}:{parts[1]}")
    return (flag.template, flag.tag)


def printReport(flags: list[Flag], worstSlots: int, samplesPerType: int) -> None:
    byType: dict[str, list[Flag]] = defaultdict(list)
    for flag in flags:
        byType[flag.flagType].append(flag)

    print("=== Summary ===")
    for flagType in ALL_FLAG_TYPES:
        print(f"  {flagType}: {len(byType[flagType])}")
    print(f"  TOTAL: {len(flags)}")

    for flagType in ALL_FLAG_TYPES:
        typeFlags = byType[flagType]
        if not typeFlags:
            continue
        print(f"\n=== {flagType} ({len(typeFlags)}) ===")
        slotCounts = Counter(slotKey(f) for f in typeFlags)
        print(f"By (template, code) -- top {worstSlots}:")
        for (template, code), count in slotCounts.most_common(worstSlots):
            print(f"  {count:>5}  {template:>12} {code}")
        print(f"Sample rows (up to {samplesPerType}):")
        for flag in typeFlags[:samplesPerType]:
            expectedStr = f" expected={flag.expected!r}" if flag.expected != flag.ortho else ""
            print(f"  lemme={flag.lemme!r} ortho={flag.ortho!r} template={flag.template}"
                  f" tag={flag.tag!r}{expectedStr}")


def writeCsv(path: str, flags: list[Flag]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["flagType", "lemme", "ortho", "template", "tag", "expected", "infoVerb"])
        for flag in flags:
            writer.writerow([flag.flagType, flag.lemme, flag.ortho, flag.template,
                              flag.tag, flag.expected or "", flag.infoVerb])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-validate every VER row in a lexicon TSV against "
        "Verbiste's own templates and this project's orthographic-generation "
        "code. Report-only: never modifies any file."
    )
    parser.add_argument("--lexicon", default=LEXICON_PATH_DEFAULT,
                         help=f"Lexicon TSV to validate (default: {LEXICON_PATH_DEFAULT}).")
    parser.add_argument("--worst-slots", type=int, default=25,
                         help="How many (template, code) slots to show per flag type (default: 25).")
    parser.add_argument("--samples", type=int, default=10,
                         help="How many sample rows to print per flag type (default: 10).")
    parser.add_argument("--dump-csv", default=None,
                         help="Write every flagged row to this CSV path for full review.")
    args = parser.parse_args()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)

    flags: list[Flag] = []
    with open(args.lexicon, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rowCount = 0
        for row in reader:
            rowCount += 1
            flags.extend(validateRow(row, verbisteTemplates, exceptions, conjugationTemplates))

    print(f"Validated {rowCount} rows from {args.lexicon}.\n")
    printReport(flags, args.worst_slots, args.samples)

    if args.dump_csv:
        writeCsv(args.dump_csv, flags)
        print(f"\nWrote {len(flags)} flagged rows to {args.dump_csv}")


if __name__ == "__main__":
    main()
