#!/bin/env python
#
# Batch 9 (UNDEFINED_SLOT cluster D) of the lexicon-defect triage plan: adds
# the missing 3rd-person-plural slots (ind:pre, ind:imp, cnd:pre) to the
# "grêl:er" template (shared by grêler/bruiner).
#
# Unlike the neiger/bruiner 1st/2nd-person rows deleted earlier this batch
# (grammatically impossible for a weather verb), all 3 flagged grêler rows
# here are 3rd-person PLURAL: "grêlaient" (ind:imp:3p), "grêlent"
# (ind:pre:3p), "grêleraient" (cnd:pre:3p) -- a real, idiomatically
# well-established figurative extension of weather verbs to plural subjects
# ("les obus grêlaient" = "shells rained down"), preserving the
# impersonal-verb restriction to 3rd person while extending it to plural.
# All 3 have nonzero book-frequency (0.07-0.2), and the template's
# participe-passé is already fully inflected across all 4 gender/number
# forms (grêlé/grêlée/grêlés/grêlées), showing grêl:er was never meant to be
# AS restrictively impersonal as the template's finite-tense slots (which
# only ever defined 3s) suggest -- those 3p slots were simply never filled
# in, not deliberately omitted.
#
# The endings added ("ent"/"aient"/"eraient") are the completely regular
# plain -er verb 3p endings (matching aim:er's own 3p endings exactly), so
# this is a mechanical completion, not an invented pattern -- and each
# matches its attested lexicon row exactly (grêl + ent = grêlent, etc.).
# Conservative scope, matching this session's adv:enir fix: only the 3
# slots with an attested lexicon row are added (not e.g. ind:fut:3p or
# sub:pre:3p, which aren't currently attested for grêler or bruiner).
#
# The Indicatif's <présent> and the Subjonctif's <présent> are byte-identical
# text in this template (both "<p></p><p></p><p><i>e</i></p><p></p><p></p>
# <p></p>"), so this script replaces only the FIRST occurrence (count=1),
# which is the Indicatif's présent -- it appears first in document order --
# leaving the Subjonctif's présent (not being extended here) untouched.
#
# Dry-run by default: only reads and reports. --apply rewrites the affected
# <p> elements in resources/verbiste/conjugations-fr.xml, in place.
# Idempotent: a no-op (0 corrections needed) if run again after a
# successful --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
TEMPLATE_NAME = "grêl:er"

INDICATIF_PRESENT_OLD = (
    "<présent>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>e</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</présent>"
)
INDICATIF_PRESENT_NEW = (
    "<présent>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>e</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>ent</i></p>\n"
    "\t\t</présent>"
)

IMPARFAIT_OLD = (
    "<imparfait>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>ait</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</imparfait>"
)
IMPARFAIT_NEW = (
    "<imparfait>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>ait</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>aient</i></p>\n"
    "\t\t</imparfait>"
)

CONDITIONNEL_PRESENT_OLD = (
    "<présent>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>erait</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t</présent>"
)
CONDITIONNEL_PRESENT_NEW = (
    "<présent>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>erait</i></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p></p>\n"
    "\t\t\t<p><i>eraient</i></p>\n"
    "\t\t</présent>"
)

# (old, new) applied with count=1 each, in this order.
CORRECTIONS = [
    (INDICATIF_PRESENT_OLD, INDICATIF_PRESENT_NEW),
    (IMPARFAIT_OLD, IMPARFAIT_NEW),
    (CONDITIONNEL_PRESENT_OLD, CONDITIONNEL_PRESENT_NEW),
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add grêl:er's missing 3rd-person-plural slots "
        "(ind:pre, ind:imp, cnd:pre), matching attested 'grêler' rows."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to resources/verbiste/conjugations-fr.xml "
        "(default: dry-run).",
    )
    args = parser.parse_args()

    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    block, start, end = extractTemplateBlock(content)
    corrected = block
    applied = 0
    warnings: list[str] = []
    for old, new in CORRECTIONS:
        count = corrected.count(old)
        if count == 0:
            warnings.append(f"not found: {old!r}")
            continue
        print(f"  {old!r} ->\n  {new!r}\n")
        corrected = corrected.replace(old, new, 1)
        applied += 1

    print(f"Sections corrected: {applied} (expected {len(CORRECTIONS)})")
    for w in warnings:
        print(f"  WARNING: {w}")

    if args.apply and applied:
        newContent = content[:start] + corrected + content[end:]
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(newContent)
        print(f"\n--apply: wrote {applied} correction(s) to {CONJUGATIONS_PATH}")


if __name__ == "__main__":
    main()
