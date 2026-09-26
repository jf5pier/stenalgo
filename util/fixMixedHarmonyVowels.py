#!/bin/env python
#
# B2 residue, vowel-harmony batch 3 (docs/VOWEL_HARMONY_CANDIDATES.md, the `mixed` rows). Same
# design choice as util/fixFirstSyllableE.py and util/fixHarmonyVowels.py (docs/ARCHITECTURE.md
# decision 6): the harmony is ignored when that protects the lemma's phonetics. The 243
# (lemma, position) targets of util/harmonyVowelTargets.tsv were validated by hand against
# fr.wiktionary on 2026-09-26 (E before a doubled consonant or `sc`; the masculine -o(t) /
# feminine -Ot(te) pairs, boeuf/oeuf and the family 1 loi de position verbs are NOT in it).
# In every row of a target lemma, the mid vowel at the target's unit position and orthographic
# unit is set to the target vowel, provided it is the tense/lax counterpart (e/E, o/O). Only
# that symbol changes, so no syllable or unit count moves. Fields rewritten as in
# fixHarmonyVowels.py; the Infra regularity flag becomes 0 for a lax vowel, 1 for a tense one.
# Dry-run by default; --apply writes all four files. Idempotent.
import argparse
import csv

from util.fixFirstSyllableE import (
    LEXIQUE383_PATH, LEXIQUE_INFRA_PATH, LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH,
    readRows, rewriteTsv, splitUnits, joinUnits)

TARGETS_PATH = "util/harmonyVowelTargets.tsv"
COUNTERPART = {"E": "e", "e": "E", "O": "o", "o": "O"}


def loadTargets() -> dict[str, dict[tuple[int, str], str]]:
    targets: dict[str, dict[tuple[int, str], str]] = {}
    with open(TARGETS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            targets.setdefault(row["lemme"], {})[(int(row["position"]), row["ortho_unit"])] = row["vowel"]
    return targets


TARGETS = loadTargets()


def fixLexiconRow(row: dict[str, str]) -> tuple[str, str, dict[int, str]] | None:
    """(new phon, new syll_cv, {phoneme offset: new vowel}) or None."""
    wanted = TARGETS.get(row["lemme"])
    if wanted is None:
        return None
    phon, ortho = splitUnits(row["syll_cv"]), splitUnits(row["orthosyll_cv"])
    if [len(s) for s in phon] != [len(s) for s in ortho]:
        return None
    newPhon = list(row["phon"])
    changed: dict[int, str] = {}
    offset, unit = 0, 0
    for ps, os_ in zip(phon, ortho):
        for k, (p, o) in enumerate(zip(ps, os_)):
            target = wanted.get((unit, o.lower()))
            if target is not None and p != target and COUNTERPART.get(p) == target:
                if newPhon[offset] != p:
                    raise ValueError(f"{row['ortho']}: phon {row['phon']!r} misaligned at {offset}")
                newPhon[offset] = target
                ps[k] = target
                changed[offset] = target
            offset += len(p.replace("#", ""))
            unit += 1
    return None if not changed else ("".join(newPhon), joinUnits(phon), changed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standardize the e/E and o/O of the validated mixed-harmony lemmas.")
    parser.add_argument("--apply", action="store_true", help="Write the corrections (default: dry-run).")
    args = parser.parse_args()

    mixteFixes = {}
    for row in readRows(LEXIQUE_MIXTE_PATH):
        fix = fixLexiconRow(row)
        if fix is not None:
            # Lexique383 and Infra sometimes carry the lax vowel in phon/phono already while their
            # syllabified column does not (antiprotons): match on the old or the new phon.
            mixteFixes[(row["ortho"], row["cgram"], row["phon"])] = fix
            mixteFixes[(row["ortho"], row["cgram"], fix[0])] = fix

    def lexiconFix(fields):
        fix = fixLexiconRow(fields)
        return None if fix is None else {"phon": fix[0], "syll_cv": fix[1]}

    totals = {}
    for path in (LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH):
        changes = rewriteTsv(path, lambda f: f["lemme"] in TARGETS, lexiconFix, args.apply)
        totals[path] = len(changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
        for old, new in changes[:60]:
            print(f"  {old['phon']} -> {new['phon']}   {old['syll_cv']} -> {new['syll_cv']}")

    def lexique383Fix(fields):
        fix = mixteFixes.get((fields["ortho"], fields["cgram"], fields["phon"]))
        if fix is None:
            return None
        newPhon, _, changed = fix
        syll = list(fields["syll"])
        offsets = [i for i, ch in enumerate(syll) if ch != "-"]
        for k, vowel in changed.items():
            syll[offsets[k]] = vowel
        return {"phon": newPhon, "syll": "".join(syll), "phonrenv": newPhon[::-1]}

    def infraFix(fields):
        fix = mixteFixes.get((fields["item"], fields["cgram"], fields["phono"]))
        if fix is None:
            return None
        newPhon, _, changed = fix
        segments, regular, k = fields["assoc"].split("."), fields["regTo_GP"].split("."), 0
        for i, segment in enumerate(segments):
            grapheme, phoneme = segment.split("-", 1)
            chars = list(phoneme)  # a unit may carry two phonemes (coopter: `oo` -> `oO`)
            for j, ch in enumerate(chars):
                if k + j in changed and COUNTERPART.get(ch) == changed[k + j]:
                    chars[j] = changed[k + j]
                    regular[i] = "0" if changed[k + j] in "EO" else "1"
            segments[i] = f"{grapheme}-{''.join(chars)}"
            k += len(phoneme.replace("#", ""))
        return {"assoc": ".".join(segments), "regTo_GP": ".".join(regular),
                "phono": "".join(s.split("-", 1)[1] for s in segments).replace("#", "")}

    for path, fixOf in ((LEXIQUE383_PATH, lexique383Fix), (LEXIQUE_INFRA_PATH, infraFix)):
        changes = rewriteTsv(path, lambda f: True, fixOf, args.apply)
        totals[path] = len(changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
    print("\nTotals: " + ", ".join(f"{p.split('/')[-1]} {n}" for p, n in totals.items()))
    if args.apply:
        print("--apply: files updated")


if __name__ == "__main__":
    main()
