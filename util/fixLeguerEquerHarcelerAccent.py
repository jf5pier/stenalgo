#!/bin/env python
#
# Batch 7 (partial) of the lexicon-defect triage plan: fixes the futur-
# simple/conditionnel:présent WRONG_ENDING flags for "l:éguer", "diss:équer"
# and "harc:eler" in resources/verbiste/conjugations-fr.xml. Same technique
# as the already-applied "abr:éger" fix (util/fixAbregerFutureAccent.py) --
# NOT the same situation as the pa:yer "-ayer" family (see todo.md): the "i"
# vs "y" spellings there are phonologically distinct and both genuinely
# attested, so both need their own lexicon rows. Here, by contrast, only ONE
# spelling is ever attested in the lexicon for the affected slots (confirmed
# by checking every "déléguer"/"léguer"/"alléguer"/"harceler" row: e.g.
# "harceler" has ONLY "harcèle"/"harcèlera"/... rows -- no "harcelle"/
# "harcellera" counterpart exists anywhere), so this is a genuine template
# defect/misconfiguration, not a case needing new rows generated for a
# second valid spelling:
#   - l:éguer / diss:équer: futur-simple and conditionnel:présent currently
#     only encode the "è" spelling, but every attested lemma (déléguer,
#     léguer, alléguer, disséquer) uses "é" (déléguerai, léguera, ...) --
#     add "é" as the first (primary) <i> alternative, keeping "è" as a
#     second, currently-inert alternative for consistency with sibling
#     templates (c:éder, réf:érer, ...; note src/verbparadigm.py's
#     parseConjugationTemplates only ever reads the FIRST <i> child, so this
#     second alternative doesn't affect generation either way).
#   - harc:eler: already has both alternatives in its présent/futur-simple/
#     conditionnel:présent/subjonctif-présent slots, but in the wrong order
#     ("elle"/"èle" -- doubled-consonant form listed first) -- every attested
#     "harceler" row uses the "è" spelling ("harcèle", not "harcelle"), so
#     swap the two so "è" is primary.
#
# Dry-run by default: only reads and reports. --apply rewrites the affected
# <p> elements in resources/verbiste/conjugations-fr.xml, in place.
# Idempotent: a no-op (0 corrections needed) if run again after a successful
# --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"

LEGUER_CORRECTIONS = [
    ("<p><i>èguerai</i></p>", "<p><i>éguerai</i><i>èguerai</i></p>", 1),
    ("<p><i>ègueras</i></p>", "<p><i>égueras</i><i>ègueras</i></p>", 1),
    ("<p><i>èguera</i></p>", "<p><i>éguera</i><i>èguera</i></p>", 1),
    ("<p><i>èguerons</i></p>", "<p><i>éguerons</i><i>èguerons</i></p>", 1),
    ("<p><i>èguerez</i></p>", "<p><i>éguerez</i><i>èguerez</i></p>", 1),
    ("<p><i>ègueront</i></p>", "<p><i>égueront</i><i>ègueront</i></p>", 1),
    # 1s and 2s conditionnel share this identical text; both get corrected.
    ("<p><i>èguerais</i></p>", "<p><i>éguerais</i><i>èguerais</i></p>", 2),
    ("<p><i>èguerait</i></p>", "<p><i>éguerait</i><i>èguerait</i></p>", 1),
    ("<p><i>èguerions</i></p>", "<p><i>éguerions</i><i>èguerions</i></p>", 1),
    ("<p><i>ègueriez</i></p>", "<p><i>égueriez</i><i>ègueriez</i></p>", 1),
    ("<p><i>ègueraient</i></p>", "<p><i>égueraient</i><i>ègueraient</i></p>", 1),
]

EQUER_CORRECTIONS = [
    ("<p><i>èquerai</i></p>", "<p><i>équerai</i><i>èquerai</i></p>", 1),
    ("<p><i>èqueras</i></p>", "<p><i>équeras</i><i>èqueras</i></p>", 1),
    ("<p><i>èquera</i></p>", "<p><i>équera</i><i>èquera</i></p>", 1),
    ("<p><i>èquerons</i></p>", "<p><i>équerons</i><i>èquerons</i></p>", 1),
    ("<p><i>èquerez</i></p>", "<p><i>équerez</i><i>èquerez</i></p>", 1),
    ("<p><i>èqueront</i></p>", "<p><i>équeront</i><i>èqueront</i></p>", 1),
    # 1s and 2s conditionnel share this identical text; both get corrected.
    ("<p><i>èquerais</i></p>", "<p><i>équerais</i><i>èquerais</i></p>", 2),
    ("<p><i>èquerait</i></p>", "<p><i>équerait</i><i>èquerait</i></p>", 1),
    ("<p><i>èquerions</i></p>", "<p><i>équerions</i><i>èquerions</i></p>", 1),
    ("<p><i>èqueriez</i></p>", "<p><i>équeriez</i><i>èqueriez</i></p>", 1),
    ("<p><i>èqueraient</i></p>", "<p><i>équeraient</i><i>èqueraient</i></p>", 1),
]

# (old, new, expectedOccurrences) -- some <p> texts repeat verbatim within
# the template (e.g. 1s/3s présent share "<p><i>elle</i><i>èle</i></p>", and
# the whole présent block is duplicated for subjonctif:présent), so each
# entry is replaced everywhere it occurs (all identical occurrences get the
# same correction) rather than just once.
HARCELER_CORRECTIONS = [
    ("<p><i>elle</i><i>èle</i></p>", "<p><i>èle</i><i>elle</i></p>", 5),
    ("<p><i>elles</i><i>èles</i></p>", "<p><i>èles</i><i>elles</i></p>", 2),
    ("<p><i>ellent</i><i>èlent</i></p>", "<p><i>èlent</i><i>ellent</i></p>", 2),
    ("<p><i>ellerai</i><i>èlerai</i></p>", "<p><i>èlerai</i><i>ellerai</i></p>", 1),
    ("<p><i>elleras</i><i>èleras</i></p>", "<p><i>èleras</i><i>elleras</i></p>", 1),
    ("<p><i>ellera</i><i>èlera</i></p>", "<p><i>èlera</i><i>ellera</i></p>", 1),
    ("<p><i>ellerons</i><i>èlerons</i></p>", "<p><i>èlerons</i><i>ellerons</i></p>", 1),
    ("<p><i>ellerez</i><i>èlerez</i></p>", "<p><i>èlerez</i><i>ellerez</i></p>", 1),
    ("<p><i>elleront</i><i>èleront</i></p>", "<p><i>èleront</i><i>elleront</i></p>", 1),
    ("<p><i>ellerais</i><i>èlerais</i></p>", "<p><i>èlerais</i><i>ellerais</i></p>", 2),
    ("<p><i>ellerait</i><i>èlerait</i></p>", "<p><i>èlerait</i><i>ellerait</i></p>", 1),
    ("<p><i>ellerions</i><i>èlerions</i></p>", "<p><i>èlerions</i><i>ellerions</i></p>", 1),
    ("<p><i>elleriez</i><i>èleriez</i></p>", "<p><i>èleriez</i><i>elleriez</i></p>", 1),
    ("<p><i>elleraient</i><i>èleraient</i></p>", "<p><i>èleraient</i><i>elleraient</i></p>", 1),
]


def extractTemplateBlock(content: str, templateName: str) -> tuple[str, int, int]:
    pattern = re.compile(
        r'<template name="' + re.escape(templateName) + r'">.*?</template>',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one <template name={templateName!r}> "
                          f"block, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def buildCorrectedBlock(block: str, corrections: list[tuple[str, str, int]]
                         ) -> tuple[str, int, list[str]]:
    corrected = block
    applied = 0
    warnings: list[str] = []
    for old, new, expectedCount in corrections:
        count = corrected.count(old)
        if count == 0:
            warnings.append(f"expected {expectedCount} occurrence(s) of {old!r}, found 0")
            continue
        if count != expectedCount:
            warnings.append(f"expected {expectedCount} occurrence(s) of {old!r}, found {count}")
        corrected = corrected.replace(old, new)
        applied += count
    return corrected, applied, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix the futur-simple/conditionnel:présent (and, for "
        "harc:eler, présent/subjonctif) accent/order defects in the "
        "l:éguer, diss:équer and harc:eler conjugation templates."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    totalApplied = 0
    for templateName, corrections in (
        ("l:éguer", LEGUER_CORRECTIONS),
        ("diss:équer", EQUER_CORRECTIONS),
        ("harc:eler", HARCELER_CORRECTIONS),
    ):
        block, start, end = extractTemplateBlock(content, templateName)
        correctedBlock, applied, warnings = buildCorrectedBlock(block, corrections)

        print(f"=== {templateName} ===")
        for old, new, expectedCount in corrections:
            if old in block:
                print(f"  {old} -> {new}  (x{expectedCount})")
        print(f"<p> texts corrected: {applied}")
        for w in warnings:
            print(f"  WARNING: {w}")
        print()

        if args.apply and applied:
            content = content[:start] + correctedBlock + content[end:]
            totalApplied += applied

    if args.apply:
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"--apply: wrote corrections ({totalApplied} <p> texts) to {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
