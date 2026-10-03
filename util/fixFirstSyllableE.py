#!/bin/env python
#
# B2 residue follow-up (TODO.md, "Close the B2 residue"): the plain-`e` non-final
# syllables the generator cannot decide from spelling (descendre /des@dR/ vs
# condescendre /dEs@dR/, essayer /esEje/ vs essaie /EsE/, ...). The lexicon
# writes /e/ in some rows of a lemma and /E/ in others; the /e/ rows are errors or
# the vowel harmony (harmonisation vocalique: /E/ -> /e/ before a similar-sounding
# syllable). Design choice (docs/ARCHITECTURE.md): the harmony is ignored when that
# protects the lemma's phonetics and keeps the number of strokes needed to express
# the declension down; every form of the lemma gets the lax vowel.
#
# Scope: the lemmas listed in TARGET_LEMMAS (validated by the user 2026-09-26). Verbs made
# of a re-/dé- prefix on a known lemma (restructurer, resuivre, restabiliser) are NOT
# in it: the prefix keeps its schwa, the base lemma keeps its own vowel. In
# each row of the lemma, the first orthographic unit `e` within the first three
# units that is followed by a consonant unit and has phoneme /e/, /°/, /2/ or
# (dessaper) a silent `#`, becomes /E/. Nothing else moves; the syllable count only
# changes for the dessaper `#` case ("d_#_s_a|p_e" -> "d_E|s_a|p_e").
#
# Fields rewritten (like fixOuGlideConsistency.py):
#   Lexique383.tsv              phon, syll, cv-cv, phonrenv (+ nbsyll/nbphons/p_cvcv for dessaper)
#   LexiqueInfraCorrespondance  phono, assoc ("e-e" -> "e-E"), regTo_GP -> 0
#   LexiqueMixte.tsv            phon, syll_cv
#   LexiqueSynthetic.tsv        phon, syll_cv
# Dry-run by default; --apply writes all four files. Idempotent.
import argparse
import csv
from dataclasses import dataclass
from typing import Callable

LEXIQUE383_PATH = "resources/Lexique383.tsv"
LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"

TARGET_LEMMAS = frozenset("""
essayer essuyer essorer essouffler greffer lessiver tresser tressauter tressaillir blettir
flemmarder desceller nettoyer
descendre condescendre redescendre
dessiner dessaisir dessaler desserrer desservir dessécher desseller dessouder dessouler
dessertir dessiller dessoucher
pressentir pressurer ressusciter hennir flemmer verrouiller sectionner
effacer effarer effaroucher effectuer effeuiller effiler effilocher effleurer effondrer
efforcer effrayer effranger effriter efféminer
voir dessaper destiner destituer ester nerver
""".split())
MISSING_E_PHONEMES = frozenset({"e", "°", "2", "#"})


def splitUnits(syllCv: str) -> list[list[str]]:
    return [syllable.split("_") for syllable in syllCv.split("|")]


def joinUnits(syllables: list[list[str]]) -> str:
    return "|".join("_".join(syllable) for syllable in syllables)


@dataclass
class RowFix:
    ortho: str
    cgram: str
    lemme: str
    oldPhon: str
    newPhon: str
    phonIndex: int          # phoneme offset of the corrected vowel (in the NEW phon)
    wasSilent: bool
    oldSyllCv: str
    newSyllCv: str


def fixLexiconRow(row: dict[str, str]) -> RowFix | None:
    phon, ortho = splitUnits(row["syll_cv"]), splitUnits(row["orthosyll_cv"])
    if [len(s) for s in phon] != [len(s) for s in ortho]:
        return None
    flat = [(si, ui, p, o) for si, (ps, os_) in enumerate(zip(phon, ortho))
            for ui, (p, o) in enumerate(zip(ps, os_))]
    # A re- prefix on a targeted lemma (redescendre) keeps its schwa: skip its `e`.
    prefixed = row["lemme"].startswith("re") and row["lemme"][2:] in TARGET_LEMMAS
    for i, (si, ui, p, o) in enumerate(flat[:5 if prefixed else 3]):
        if o.lower() != "e" or p not in MISSING_E_PHONEMES or i + 1 >= len(flat):
            continue
        if prefixed and i < 2 and flat[i][3].lower() == "e" and \
                all(u[3] != "e" for u in flat[:i]):
            continue
        following = flat[i + 1][3]
        if following[0] in "aeiouyéèêëàâîïôûùœ":
            continue
        before = sum(len(u.replace("#", "")) for s in phon[:si] for u in s) + \
            sum(len(u.replace("#", "")) for u in phon[si][:ui])
        silent = p == "#"
        newPhonChars = list(row["phon"])
        if silent:
            newPhonChars.insert(before, "E")
            phon[si][ui] = "E"
            # the units after the new vowel open the next syllable
            rest, phon[si] = phon[si][ui + 1:], phon[si][:ui + 1]
            phon.insert(si + 1, rest)
            orthoRest, ortho[si] = ortho[si][ui + 1:], ortho[si][:ui + 1]
            ortho.insert(si + 1, orthoRest)
        else:
            if newPhonChars[before] != p:
                raise ValueError(f"{row['ortho']}: phon {row['phon']!r} has no {p!r} at {before}")
            newPhonChars[before] = "E"
            phon[si][ui] = "E"
        return RowFix(row["ortho"], row["cgram"], row["lemme"], row["phon"], "".join(newPhonChars), before,
                      silent, row["syll_cv"], joinUnits(phon))
    return None


def readRows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def fixLexique383Fields(fields: dict[str, str], fix: RowFix) -> dict[str, str]:
    if not fix.wasSilent:
        syll = list(fields["syll"])
        offsets = [i for i, ch in enumerate(syll) if ch != "-"]
        at = offsets[fix.phonIndex]
        if syll[at] != fields["phon"][fix.phonIndex]:
            raise ValueError(f"{fields['ortho']}: syll {fields['syll']!r} misaligned at {fix.phonIndex}")
        syll[at] = "E"
        return {"phon": fix.newPhon, "syll": "".join(syll), "phonrenv": fix.newPhon[::-1]}
    if fields["ortho"] != "dessaper":
        raise ValueError(f"{fields['ortho']}: silent-e repair is only defined for dessaper")
    return {"phon": fix.newPhon, "syll": "dE-sa-pe", "nbsyll": "3", "cv-cv": "CV-CV-CV",
            "p_cvcv": "CVCVCV", "nbphons": "6", "phonrenv": fix.newPhon[::-1]}


def fixInfraFields(fields: dict[str, str], fix: RowFix) -> dict[str, str]:
    segments = fields["assoc"].split(".")
    regular = fields["regTo_GP"].split(".")
    k = 0
    for i, segment in enumerate(segments):
        grapheme, phoneme = segment.split("-", 1)
        if k == fix.phonIndex and grapheme.lower() == "e" and \
                (phoneme in MISSING_E_PHONEMES):
            segments[i] = "e-E"
            regular[i] = "0"
            break
        if phoneme == "#" and grapheme.lower() == "e" and fix.wasSilent and k == fix.phonIndex:
            segments[i] = "e-E"
            regular[i] = "0"
            break
        k += len(phoneme.replace("#", ""))
    else:
        raise ValueError(f"{fields['item']}: assoc {fields['assoc']!r} has no e at {fix.phonIndex}")
    assoc = ".".join(segments)
    phono = "".join(s.split("-", 1)[1] for s in segments).replace("#", "")
    return {"assoc": assoc, "phono": phono, "regTo_GP": ".".join(regular)}


def rewriteTsv(path: str, keyOf: Callable[[dict[str, str]], bool],
               fixOf: Callable[[dict[str, str]], dict[str, str] | None], apply: bool) -> list[tuple[dict[str, str], dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0].rstrip("\r\n").split("\t")
    changes = []
    for i in range(1, len(lines)):
        body = lines[i].rstrip("\r\n")
        if not body:
            continue
        ending = lines[i][len(body):]
        values = body.split("\t")
        fields = dict(zip(header, values))
        if not keyOf(fields):
            continue
        new = fixOf(fields)
        if new is None:
            continue
        changes.append(({k: fields[k] for k in new}, new))
        for column, value in new.items():
            values[header.index(column)] = value
        lines[i] = "\t".join(values) + ending
    if apply and changes:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set the lax /E/ in the first-syllable `e` of the TARGET_LEMMAS in "
        "Lexique383, LexiqueInfraCorrespondance, LexiqueMixte and LexiqueSynthetic.")
    parser.add_argument("--apply", action="store_true", help="Write the corrections (default: dry-run).")
    args = parser.parse_args()

    mixteRows = readRows(LEXIQUE_MIXTE_PATH)
    mixteFixes = {(f.ortho, f.cgram, f.oldPhon): f
                  for row in mixteRows if row["lemme"] in TARGET_LEMMAS
                  for f in [fixLexiconRow(row)] if f is not None}

    variantFixes = {(f.cgram, f.oldPhon): f for f in mixteFixes.values()}

    def lexiconFix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = fixLexiconRow(fields)
        return None if fix is None else {"phon": fix.newPhon, "syll_cv": fix.newSyllCv}

    totals = {}
    touched: set[str] = set()
    for path in (LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH):
        changes = rewriteTsv(path, lambda f: f["lemme"] in TARGET_LEMMAS, lexiconFix, args.apply)
        totals[path] = len(changes)
        touched.update(old["phon"] for old, _ in changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
        for old, new in changes:
            print(f"  {old['phon']} -> {new['phon']}   {old['syll_cv']} -> {new['syll_cv']}")

    def lexique383Fix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = mixteFixes.get((fields["ortho"], fields["cgram"], fields["phon"]))
        return None if fix is None else fixLexique383Fields(fields, fix)

    def infraFix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = mixteFixes.get((fields["item"], fields["cgram"], fields["phono"]))
        if fix is None:
            # Variant spellings (dessoûle, dessaoule) exist only in Infra; Mixte folds
            # them into the lemma. Match them by phon + the lemma's stem.
            item = fields["item"].replace("û", "u").replace("aou", "ou")
            fix = variantFixes.get((fields["cgram"], fields["phono"]))
            if fix is not None and not item.startswith(fix.lemme[:-2]):
                fix = None
        return None if fix is None else fixInfraFields(fields, fix)

    for path, fixOf, shown in ((LEXIQUE383_PATH, lexique383Fix, ("phon", "syll")),
                               (LEXIQUE_INFRA_PATH, infraFix, ("phono", "assoc"))):
        changes = rewriteTsv(path, lambda f: True, fixOf, args.apply)
        totals[path] = len(changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
        for old, new in changes[:40]:
            print("  " + "   ".join(f"{old[c]} -> {new[c]}" for c in shown))

    print("\nTotals: " + ", ".join(f"{p.split('/')[-1]} {n}" for p, n in totals.items()))
    if args.apply:
        print("--apply: files updated")


if __name__ == "__main__":
    main()
