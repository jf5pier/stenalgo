#!/bin/env python
#
# Investigates and (with --apply) fixes a missing orthographic alternative in
# Verbiste's "abr:éger" conjugation template: its futur-simple and
# conditionnel:présent endings only offer the "è" spelling (e.g.
# "<p><i>ègerai</i></p>"), while every attested corpus form for this
# template's own donor lemmas uses "é" instead (abrégerai, allégera,
# protégerai, protégera, siégerai, siégera, piégerai -- confirmed against
# PhoneticTheory.pickle this session, zero "è" spellings attested in the
# future/conditional for any abr:éger lemma).
#
# This matches standard French orthography: "é_consonant+er" verbs (céder,
# protéger, ...) take the e/è alternation in the present tense but keep é in
# the future and conditional. Verbiste's own sibling templates for the same
# linguistic pattern (c:éder, réf:érer, ali:éner, cél:ébrer, décr:éter,
# imp:étrer, int:égrer, l:éser, rév:éler) already encode this correctly by
# listing BOTH spellings per slot, e.g. "<p><i>éderai</i><i>èderai</i></p>"
# -- src/verbparadigm.py's parseConjugationTemplates only reads the first
# <i> child of each <p> (ElementTree's .find() semantics), so listing é
# first is what makes those templates pick é. abr:éger's futur-simple/
# conditionnel:présent entries only ever had the "è" <i>, with no é
# alternative to fall back to.
#
# Root cause of a real bug: src/verbparadigm.py's generateOrthoForm reads
# this ending literally, so any undersampled abr:éger-template lemma (e.g.
# "alléger", "agréger", "assiéger") that needed a missing future/conditional
# form generated got "allègerai" instead of "allégerai" -- confirmed via a
# real `util/completeVerbParadigms.py` dry run's mismatch-counting check.
#
# NOTE: "l:éguer" and "diss:équer" have the same missing-é-alternative shape
# in their own futur-simple entries and are plausibly the same underlying
# issue (not confirmed against a linguist or a broader corpus check), but
# fixing them made no difference to this session's measured mismatch count
# (no lemma using either template currently needs a generated future/
# conditional form) -- left untouched, deliberately out of scope. See
# PROGRESS.md.
#
# Dry-run by default: only reads and reports. --apply rewrites the 12
# affected <p> elements (6 futur-simple + 6 conditionnel:présent) in
# resources/verbiste/conjugations-fr.xml's "abr:éger" template, in place.
# Idempotent: a no-op (0 rows modified) if run again after a successful
# --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
TEMPLATE_NAME = "abr:éger"

# (old <p> element, new <p> element) pairs, futur-simple then
# conditionnel:présent, in template order.
CORRECTIONS = [
    ("<p><i>ègerai</i></p>", "<p><i>égerai</i><i>ègerai</i></p>"),
    ("<p><i>ègeras</i></p>", "<p><i>égeras</i><i>ègeras</i></p>"),
    ("<p><i>ègera</i></p>", "<p><i>égera</i><i>ègera</i></p>"),
    ("<p><i>ègerons</i></p>", "<p><i>égerons</i><i>ègerons</i></p>"),
    ("<p><i>ègerez</i></p>", "<p><i>égerez</i><i>ègerez</i></p>"),
    ("<p><i>ègeront</i></p>", "<p><i>égeront</i><i>ègeront</i></p>"),
    ("<p><i>ègerais</i></p>", "<p><i>égerais</i><i>ègerais</i></p>"),
    ("<p><i>ègerais</i></p>", "<p><i>égerais</i><i>ègerais</i></p>"),
    ("<p><i>ègerait</i></p>", "<p><i>égerait</i><i>ègerait</i></p>"),
    ("<p><i>ègerions</i></p>", "<p><i>égerions</i><i>ègerions</i></p>"),
    ("<p><i>ègeriez</i></p>", "<p><i>égeriez</i><i>ègeriez</i></p>"),
    ("<p><i>ègeraient</i></p>", "<p><i>égeraient</i><i>ègeraient</i></p>"),
]


def extractTemplateBlock(content: str) -> tuple[str, int, int]:
    pattern = re.compile(
        r'<template name="' + re.escape(TEMPLATE_NAME) + r'">.*?</template>',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one <template name={TEMPLATE_NAME!r}> "
                          f"block, found {len(matches)}")
    m = matches[0]
    return m.group(0), m.start(), m.end()


def buildCorrectedBlock(block: str) -> tuple[str, int]:
    corrected = block
    applied = 0
    for old, new in CORRECTIONS:
        if old not in corrected:
            continue
        corrected = corrected.replace(old, new, 1)
        applied += 1
    return corrected, applied


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add the missing 'é' orthographic alternative to "
        "'abr:éger's futur-simple/conditionnel:présent endings in "
        "resources/verbiste/conjugations-fr.xml, matching its own donor "
        "lemmas' attested corpus spelling (see module docstring)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the correction to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    block, start, end = extractTemplateBlock(content)
    correctedBlock, applied = buildCorrectedBlock(block)

    if applied == 0 and correctedBlock == block:
        print("Already applied (or nothing to correct): 0 endings needed a fix.")
        return

    print("=== Corrections (dry-run, no files modified) ===\n")
    for old, new in CORRECTIONS:
        if old in block:
            print(f"  {old} -> {new}")

    print(f"\n=== Summary ===")
    print(f"Endings to correct: {applied} (expected {len(CORRECTIONS)})")

    if args.apply:
        newContent = content[:start] + correctedBlock + content[end:]
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(newContent)
        print(f"\n--apply: corrected {applied} endings in {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
