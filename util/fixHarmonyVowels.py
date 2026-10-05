#!/bin/env python
#
# B2 residue, vowel-harmony batch 2 (docs/VOWEL_HARMONY_CANDIDATES.md, family 2). Same design
# choice as util/fixFirstSyllableE.py (docs/ARCHITECTURE.md decision 6): the harmony is ignored
# to protect the lemma's phonetics. Every /o/ or /O/ that a lemma's `o`/`au`/`ô` letter unit
# carries is set to the vowel fr.wiktionary lists for the lemma (checked 2026-09-26):
# /O/ for cosmologique, radiologique, radioscopique, étiologique, troglodytique, coronarien,
# ovoïdal, philosophal, cochonnée, corroborer, lobotomiser, monopoliser, autographier
# (both pronunciations attested, /O/ chosen); /o/ for rototo. Only the o/O symbol changes, so
# no syllable or unit count moves. Fields rewritten as in fixFirstSyllableE.py; the Infra
# regularity flag becomes 0 where a grapheme now maps to /O/. Dry-run by default.
import argparse

from util.fixFirstSyllableE import (
    LEXIQUE383_PATH, LEXIQUE_INFRA_PATH, LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH,
    readRows, rewriteTsv, splitUnits, joinUnits)

TARGET_VOWEL: dict[str, str] = {
    **{lemme: "O" for lemme in (
        "cosmologique radiologique radioscopique étiologique troglodytique coronarien "
        "ovoïdal philosophal cochonnée corroborer lobotomiser monopoliser autographier").split()},
    "rototo": "o",
}
O_LETTERS = frozenset({"o", "au", "ô", "O"})


def fixLexiconRow(row: dict[str, str]) -> tuple[str, str, list[int]] | None:
    target = TARGET_VOWEL.get(row["lemme"])
    if target is None:
        return None
    phon, ortho = splitUnits(row["syll_cv"]), splitUnits(row["orthosyll_cv"])
    if [len(s) for s in phon] != [len(s) for s in ortho]:
        return None
    newPhon = list(row["phon"])
    lastOffset = len(row["phon"]) - 1  # a word-final open vowel is aux/eau, never harmony
    indices, offset = [], 0
    for ps, os_ in zip(phon, ortho):
        for k, (p, o) in enumerate(zip(ps, os_)):
            if p in ("o", "O") and o.lower() in O_LETTERS and p != target and offset != lastOffset:
                if newPhon[offset] != p:
                    raise ValueError(f"{row['ortho']}: phon {row['phon']!r} misaligned at {offset}")
                newPhon[offset] = target
                ps[k] = target
                indices.append(offset)
            offset += len(p.replace("#", ""))
    return None if not indices else ("".join(newPhon), joinUnits(phon), indices)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standardize the o/O of the validated harmony lemmas.")
    parser.add_argument("--apply", action="store_true", help="Write the corrections (default: dry-run).")
    args = parser.parse_args()

    mixteFixes = {}
    for row in readRows(LEXIQUE_MIXTE_PATH):
        fix = fixLexiconRow(row)
        if fix is not None:
            mixteFixes[(row["ortho"], row["cgram"], row["phon"])] = (row["lemme"], *fix)

    def lexiconFix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = fixLexiconRow(fields)
        return None if fix is None else {"phon": fix[0], "syll_cv": fix[1]}

    totals = {}
    for path in (LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH):
        changes = rewriteTsv(path, lambda f: f["lemme"] in TARGET_VOWEL, lexiconFix, args.apply)
        totals[path] = len(changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
        for old, new in changes:
            print(f"  {old['phon']} -> {new['phon']}   {old['syll_cv']} -> {new['syll_cv']}")

    def lexique383Fix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = mixteFixes.get((fields["ortho"], fields["cgram"], fields["phon"]))
        if fix is None:
            return None
        _, newPhon, _, indices = fix
        syll, offsets = list(fields["syll"]), None
        offsets = [i for i, ch in enumerate(syll) if ch != "-"]
        for k in indices:
            syll[offsets[k]] = newPhon[k]
        return {"phon": newPhon, "syll": "".join(syll), "phonrenv": newPhon[::-1]}

    def infraFix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = mixteFixes.get((fields["item"], fields["cgram"], fields["phono"]))
        if fix is None:
            return None
        _, newPhon, _, indices = fix
        segments, regular, k = fields["assoc"].split("."), fields["regTo_GP"].split("."), 0
        for i, segment in enumerate(segments):
            grapheme, phoneme = segment.split("-", 1)
            if k in indices and phoneme in ("o", "O"):
                segments[i] = f"{grapheme}-{newPhon[k]}"
                regular[i] = "0" if newPhon[k] == "O" else "1"
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
