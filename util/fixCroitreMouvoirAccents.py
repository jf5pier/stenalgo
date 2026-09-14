#!/bin/env python
#
# Resolves the 4 circumflex-accent WRONG_ENDING/SUSPECTED_WRONG_LEMME flags
# deferred earlier as "needs real linguistic verification" (see todo.md).
# Confirmed against standard French orthography (Bescherelle/Académie):
# "croître" itself needs the circumflex in every form that would otherwise
# collide with "croire" (croîs/croit/crut/cru are croire's own forms), but
# its compounds ("accroître", "décroître", "recroître") do NOT need it in
# those same slots since there's no colliding "accroire"/"décroire"/
# "recroire" present-tense/participle in ordinary use -- the compounds only
# keep the circumflex in forms that derive directly from the infinitive
# spelling itself (3s présent "accroît", futur/conditionnel "accroîtrai" --
# untouched here, already correct).
#
#   - accr:oître (accroître, décroître): présent 1s/2s currently generate
#     "oîs" (circumflex), but every attested row ("accrois") has no
#     circumflex, matching Bescherelle. Fix to "ois". (Its participe-passé
#     is already correctly circumflex-free -- "accru"/"accrue"/etc. --
#     confirmed by checking before editing, so left untouched.)
#   - recr:oître (recroître): same présent 1s/2s "oîs" -> "ois" fix, PLUS
#     its participe-passé currently generates "û"/"ûs"/"ûe"/"ûes"
#     (circumflex), but attested rows ("recru", "recrus") have no
#     circumflex, matching accroître's own already-correct pattern. Fix to
#     "u"/"us"/"ue"/"ues".
#   - m:ouvoir: participe-passé m/s already has BOTH "u" and "û" as
#     alternatives, but lists the unaccented "u" first (primary), so
#     generation currently produces "mu" -- the attested row is "mû" (with
#     circumflex, one of the few circumflexes explicitly retained even
#     under the 1990 spelling reform, to distinguish it from the invariable
#     "mu"). "mus"/"mue"/"mues" (m/p, f/s, f/p) correctly have NO
#     circumflex already (confirmed against the attested "mus" row) and are
#     left untouched. Swap "u"/"û" order so "û" is primary, matching the
#     already-applied l:éguer/harc:eler reordering technique.
#   - cr:oître (croître itself): per Bescherelle, "croître"'s past participle
#     is "crû, crue, crus, crues" -- the circumflex is retained ONLY on the
#     masculine singular (same minimal-disambiguation convention as
#     "mû"/"mus"/"mue"/"mues" above), not across all 4 forms. The template
#     currently over-applies it to all 4 ("û"/"ûs"/"ûe"/"ûes"). Confirmed
#     against the lexicon's own attested rows: "crû" (m/s) already correctly
#     has the circumflex, "crue" (f/s) and "crues" (f/p) already correctly
#     don't -- so this is purely a template fix (remove the circumflex from
#     m/p "ûs"->"us", f/s "ûe"->"ue", f/p "ûes"->"ues"); no lexicon row needs
#     to change.
#
# Dry-run by default: only reads and reports. --apply writes all
# corrections in place. Idempotent: a no-op (0 corrections needed) if run
# again after a successful --apply.
import argparse
import re

CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"

ACCROITRE_PRESENT_OLD = (
    "<présent>\n"
    "\t\t\t<p><i>oîs</i></p>\n"
    "\t\t\t<p><i>oîs</i></p>\n"
    "\t\t\t<p><i>oît</i></p>\n"
    "\t\t\t<p><i>oissons</i></p>\n"
    "\t\t\t<p><i>oissez</i></p>\n"
    "\t\t\t<p><i>oissent</i></p>\n"
    "\t\t</présent>"
)
ACCROITRE_PRESENT_NEW = (
    "<présent>\n"
    "\t\t\t<p><i>ois</i></p>\n"
    "\t\t\t<p><i>ois</i></p>\n"
    "\t\t\t<p><i>oît</i></p>\n"
    "\t\t\t<p><i>oissons</i></p>\n"
    "\t\t\t<p><i>oissez</i></p>\n"
    "\t\t\t<p><i>oissent</i></p>\n"
    "\t\t</présent>"
)

RECROITRE_PARTICIPE_PASSE_OLD = (
    "<participe-passé>\n"
    "\t\t\t<p><i>û</i></p>\n"
    "\t\t\t<p><i>ûs</i></p>\n"
    "\t\t\t<p><i>ûe</i></p>\n"
    "\t\t\t<p><i>ûes</i></p>\n"
    "\t\t</participe-passé>"
)
RECROITRE_PARTICIPE_PASSE_NEW = (
    "<participe-passé>\n"
    "\t\t\t<p><i>u</i></p>\n"
    "\t\t\t<p><i>us</i></p>\n"
    "\t\t\t<p><i>ue</i></p>\n"
    "\t\t\t<p><i>ues</i></p>\n"
    "\t\t</participe-passé>"
)

MOUVOIR_PARTICIPE_PASSE_MS_OLD = "<p><i>u</i><i>û</i></p>"
MOUVOIR_PARTICIPE_PASSE_MS_NEW = "<p><i>û</i><i>u</i></p>"

CROITRE_PARTICIPE_PASSE_OLD = (
    "<participe-passé>\n"
    "\t\t\t<p><i>û</i></p>\n"
    "\t\t\t<p><i>ûs</i></p>\n"
    "\t\t\t<p><i>ûe</i></p>\n"
    "\t\t\t<p><i>ûes</i></p>\n"
    "\t\t</participe-passé>"
)
CROITRE_PARTICIPE_PASSE_NEW = (
    "<participe-passé>\n"
    "\t\t\t<p><i>û</i></p>\n"
    "\t\t\t<p><i>us</i></p>\n"
    "\t\t\t<p><i>ue</i></p>\n"
    "\t\t\t<p><i>ues</i></p>\n"
    "\t\t</participe-passé>"
)

TEMPLATE_CORRECTIONS: dict[str, list[tuple[str, str]]] = {
    "accr:oître": [(ACCROITRE_PRESENT_OLD, ACCROITRE_PRESENT_NEW)],
    "recr:oître": [(ACCROITRE_PRESENT_OLD, ACCROITRE_PRESENT_NEW),
                    (RECROITRE_PARTICIPE_PASSE_OLD, RECROITRE_PARTICIPE_PASSE_NEW)],
    "m:ouvoir": [(MOUVOIR_PARTICIPE_PASSE_MS_OLD, MOUVOIR_PARTICIPE_PASSE_MS_NEW)],
    "cr:oître": [(CROITRE_PARTICIPE_PASSE_OLD, CROITRE_PARTICIPE_PASSE_NEW)],
}

# (ortho, lemme, cgram, oldInfoVerb) -> new ortho. Empty: croître's own
# "crue"/"crues" rows are already correct (confirmed against Bescherelle --
# see module docstring); this was a template bug, not a lexicon typo.
ROW_ORTHO_FIXES: dict[tuple[str, str, str, str], str] = {}


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


def fixTemplates(apply: bool) -> None:
    with open(CONJUGATIONS_PATH, encoding="utf-8") as f:
        content = f.read()

    totalApplied = 0
    for templateName, corrections in TEMPLATE_CORRECTIONS.items():
        block, start, end = extractTemplateBlock(content, templateName)
        corrected = block
        applied = 0
        warnings: list[str] = []
        for old, new in corrections:
            count = corrected.count(old)
            if count != 1:
                warnings.append(f"expected 1 occurrence, found {count}: {old!r}")
                continue
            print(f"  [{templateName}] {old!r} ->\n  {new!r}\n")
            corrected = corrected.replace(old, new, 1)
            applied += 1

        print(f"=== {templateName}: {applied}/{len(corrections)} section(s) corrected ===")
        for w in warnings:
            print(f"  WARNING: {w}")
        print()

        if apply and applied:
            content = content[:start] + corrected + content[end:]
            totalApplied += applied

    if apply and totalApplied:
        with open(CONJUGATIONS_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"--apply: wrote {totalApplied} section correction(s) to {CONJUGATIONS_PATH}")


def fixLexiconRows(path: str, apply: bool) -> tuple[list[str], int]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    lemmeIdx = header.index("lemme")
    cgramIdx = header.index("cgram")
    infoverIdx = header.index("infover")

    corrections: list[str] = []
    modified = 0
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        key = (fields[orthoIdx], fields[lemmeIdx], fields[cgramIdx], fields[infoverIdx])
        newOrtho = ROW_ORTHO_FIXES.get(key)
        if newOrtho is None:
            continue
        corrections.append(f"ortho={key[0]!r} lemme={key[1]!r}: -> ortho={newOrtho!r}")
        modified += 1
        if apply:
            fields[orthoIdx] = newOrtho
            lines[i] = "\t".join(fields) + ending

    if apply and modified:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return corrections, modified


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix accr:oître/recr:oître compound-verb circumflex "
        "over-application, m:ouvoir's u/û ordering, and croître's own "
        "crue/crues missing-circumflex data typos."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write the corrections to conjugations-fr.xml and both lexicon "
        "files (default: dry-run).",
    )
    args = parser.parse_args()

    fixTemplates(args.apply)

    for path in (LEXIQUE_383_PATH, LEXIQUE_MIXTE_PATH):
        corrections, modified = fixLexiconRows(path, args.apply)
        print(f"=== {path} ===")
        for c in corrections:
            print(f"  {c}")
        print(f"Total rows found: {modified} (expected {len(ROW_ORTHO_FIXES)})")
        if args.apply:
            print(f"--apply: updated {path}")
        print()


if __name__ == "__main__":
    main()
