#!/bin/env python
#
# Standalone validation for src/verbparadigm.py's deriveConjugationEndingTables:
# the empirically-derived per-template phonemic/syllable-breakdown endings used
# by generateMissingConjugatedForm to synthesize missing finite conjugation
# forms (indicatif/subjonctif/conditionnel/impératif). Unlike past-participle
# splicing (verbatim reuse, valid because gender/number doesn't change a
# participle's pronunciation), finite forms genuinely change pronunciation, so
# this mechanism is new and needs its own targeted validation before being
# trusted by util/completeVerbParadigms.py -- this script is that validation,
# read-only, no files modified.
#
# Reports, per (field, template, code, personNumber) slot: how many attested
# donor lemmas contributed a candidate ending, and what fraction of them agreed
# with the chosen (mode) ending -- the same match rate
# util/completeVerbParadigms.py gates generation on via MIN_FINITE_MATCH_RATE.
import argparse
from collections import Counter

from src.verbparadigm import (
    deriveConjugationEndingTables,
    loadVerbisteTemplates,
    loadVerbModelExceptions,
)
from util.completeVerbParadigms import (
    EXCEPTIONS_PATH,
    VERBISTE_VERBS_PATH,
    loadTheoryAndKeyboard,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report per-slot match rates for the empirically-derived "
        "finite-conjugation ending tables (read-only, no files modified)."
    )
    parser.add_argument(
        "--min-donors", type=int, default=2,
        help="Only report slots with at least this many attested donor lemmas "
        "(default: 2 -- a single donor gives a trivially 'perfect' 100%% rate).",
    )
    parser.add_argument(
        "--worst", type=int, default=25,
        help="How many of the lowest-match-rate slots to print (default: 25).",
    )
    args = parser.parse_args()

    print("Loading theory (uses PhoneticTheory.pickle if present)...")
    theory, _starboard = loadTheoryAndKeyboard()
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)

    tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)

    entries = [
        (key, rate) for key, rate in tables.slotMatchRateByKey.items()
        if tables.slotDonorCountByKey[key] >= args.min_donors
    ]
    entries.sort(key=lambda kv: kv[1])

    skippedForFewDonors = len(tables.slotMatchRateByKey) - len(entries)
    print(f"\n{len(entries)} (field, template, code, personNumber) slots derived "
          f"with >= {args.min_donors} donor lemmas "
          f"({skippedForFewDonors} skipped below that threshold).")
    fullMatch = sum(1 for _key, rate in entries if rate == 1.0)
    print(f"{fullMatch}/{len(entries)} slots at 100% match rate across attested donor lemmas.")

    print(f"\nWorst {args.worst} by match rate:")
    for (field, template, code, personNumber), rate in entries[: args.worst]:
        ending = tables.slotEndingByKey[(field, template, code, personNumber)]
        donors = tables.slotDonorCountByKey[(field, template, code, personNumber)]
        print(f"  {rate:6.1%} ({donors:>4} donors)  {template:>10} {code:>8}:{personNumber:<3}"
              f" [{field:>14}]  chosen ending: {ending!r}")

    fieldCounts = Counter(field for field, *_rest in tables.slotMatchRateByKey)
    print("\nSlots derived per field:")
    for field, count in fieldCounts.most_common():
        print(f"  {field:>15}: {count}")


if __name__ == "__main__":
    main()
