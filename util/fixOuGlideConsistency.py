#!/bin/env python
#
# B2 residue follow-up (TODO.md, "Close the B2 residue"): the "ou" grapheme
# before a vowel is transcribed inconsistently WITHIN a lemma. Lexique383 and
# LexiqueInfraCorrespondance mostly write the glide /w/ in its own syllable
# onset (jouer Z_w_e, évanouissait n_w_i), but scatter hiatus rows with the
# vowel /u/ closing a syllable of its own (jouez Z_u|e, réjouirai Z_u|i,
# évanouir n_u|i). The B2 generator learns its splits from the lemma's own
# attested rows, so the split surfaces as unreproducible finite forms, and the
# two readings put one lemma's forms on different strokes.
#
# Rule: French writes /u/ + vowel as a hiatus only after an obstruent+liquid
# cluster (trouer tRu-e, clouer klu-e); everywhere else it is the glide /w/.
# The scope is deliberately narrow -- only lemmas whose rows DISAGREE (some
# /u/, some /w/ at a non-cluster "ou"+vowel position) are normalized, all of
# them towards /w/. Lemmas that are uniformly /u/ (hindouisme, louisianais,
# ouïgour: morpheme-boundary hiatus the lexicon chose consistently) and the
# cluster lemmas are left untouched.
#
# Each corrected position turns "C u | V" into "C w V": the /u/ syllable and
# the following onsetless one merge (one syllable fewer). Fields rewritten:
#   Lexique383.tsv              phon, syll, nbsyll, cv-cv, p_cvcv, phonrenv
#   LexiqueInfraCorrespondance  phono, assoc ("ou-u" -> "ou-w"), regTo_GP
#   LexiqueMixte.tsv            phon, syll_cv, orthosyll_cv
#   LexiqueSynthetic.tsv        phon, syll_cv, orthosyll_cv
# matching what lexique.py derives for a /w/ row (réjouirais: syll Re-Zwi-RE,
# cv-cv CV-CYV-CV, assoc ou-w with regTo_GP 0 at that grapheme). Every other
# column, row and the line endings (Synthetic is CRLF) stay byte-for-byte.
#
# Dry-run by default: only reads and reports. --apply writes all four files.
# Idempotent: after --apply no lemma is split any more, so a rerun finds
# nothing.
import argparse
import collections
import csv
from dataclasses import dataclass

LEXIQUE383_PATH = "resources/Lexique383.tsv"
LEXIQUE_INFRA_PATH = "resources/LexiqueInfraCorrespondance.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"

VOWELS = frozenset("aeiouyEO29568@§1°")
LIQUIDS = frozenset("Rl")
OBSTRUENTS = frozenset("pbtdkgfv")
OU_GRAPHEMES = frozenset({"ou", "oû", "où"})


def splitUnits(syllCv: str) -> list[list[str]]:
    return [syllable.split("_") for syllable in syllCv.split("|")]


def joinUnits(syllables: list[list[str]]) -> str:
    return "|".join("_".join(syllable) for syllable in syllables)


def glidePositions(syllCv: str, orthosyllCv: str) -> list[tuple[int, int, str]]:
    """(syllable index, unit index, phoneme) of every "ou" unit before a vowel
    that is not preceded by an obstruent+liquid cluster; phoneme is "u"/"w"."""
    phon, ortho = splitUnits(syllCv), splitUnits(orthosyllCv)
    if [len(s) for s in phon] != [len(s) for s in ortho]:
        return []
    flat = [(si, ui, p, o) for si, (ps, os_) in enumerate(zip(phon, ortho))
            for ui, (p, o) in enumerate(zip(ps, os_))]
    positions = []
    for i, (si, ui, p, o) in enumerate(flat):
        if o.lower() not in OU_GRAPHEMES or p not in ("u", "w"):
            continue
        if i + 1 >= len(flat) or flat[i + 1][2][:1] not in VOWELS:
            continue
        if i >= 2 and flat[i - 1][2] in LIQUIDS and flat[i - 2][2] in OBSTRUENTS:
            continue
        positions.append((si, ui, p))
    return positions


def phonemeIndex(syllables: list[list[str]], si: int, ui: int) -> int:
    units = [u for s in syllables[:si] for u in s] + syllables[si][:ui]
    return sum(len(u.replace("#", "")) for u in units)


@dataclass
class RowFix:
    ortho: str
    cgram: str
    oldPhon: str
    newPhon: str
    phonIndices: list[int]            # phoneme offsets of the corrected /u/
    oldSyllCv: str
    newSyllCv: str
    oldOrthosyllCv: str
    newOrthosyllCv: str


def fixLexiconRow(row: dict[str, str]) -> RowFix | None:
    """Merge every /u/ + onsetless-vowel pair of a Mixte/Synthetic row."""
    positions = [(si, ui) for si, ui, p in glidePositions(row["syll_cv"], row["orthosyll_cv"])
                 if p == "u"]
    if not positions:
        return None
    phon, ortho = splitUnits(row["syll_cv"]), splitUnits(row["orthosyll_cv"])
    indices = [phonemeIndex(phon, si, ui) for si, ui in positions]
    # Right to left so earlier syllable indices stay valid after a merge.
    for si, ui in reversed(positions):
        if ui != len(phon[si]) - 1:
            raise ValueError(f"{row['ortho']}: /u/ does not close its syllable in {row['syll_cv']}")
        phon[si][ui] = "w"
        phon[si:si + 2] = [phon[si] + phon[si + 1]]
        ortho[si:si + 2] = [ortho[si] + ortho[si + 1]]
    newPhon = list(row["phon"])
    for k in indices:
        if newPhon[k] != "u":
            raise ValueError(f"{row['ortho']}: phon {row['phon']!r} has no /u/ at {k}")
        newPhon[k] = "w"
    return RowFix(row["ortho"], row["cgram"], row["phon"], "".join(newPhon), indices,
                  row["syll_cv"], joinUnits(phon), row["orthosyll_cv"], joinUnits(ortho))


def readRows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def findSplitLemmas(rows: list[dict[str, str]]) -> dict[str, collections.Counter[str]]:
    counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in rows:
        for _, _, p in glidePositions(row["syll_cv"], row["orthosyll_cv"]):
            counts[row["lemme"]][p] += 1
    return {lemme: c for lemme, c in counts.items() if len(c) == 2}


def fixLexique383Fields(fields: dict[str, str], indices: list[int], newPhon: str) -> dict[str, str]:
    syll, cvCv, pCvcv = fields["syll"], list(fields["cv-cv"]), list(fields["p_cvcv"])
    if len(syll) != len(cvCv) or fields["phonrenv"] != fields["phon"][::-1]:
        raise ValueError(f"{fields['ortho']}: syll/cv-cv/phonrenv not aligned")
    # Char offsets of each phoneme within syll (cv-cv shares them).
    offsets = [i for i, ch in enumerate(syll) if ch != "-"]
    syllChars = list(syll)
    for k in sorted(indices, reverse=True):
        at = offsets[k]
        if syllChars[at] != "u" or syllChars[at + 1] != "-":
            raise ValueError(f"{fields['ortho']}: syll {syll!r} has no u-| at {k}")
        syllChars[at] = "w"
        cvCv[at] = "Y"
        pCvcv[k] = "Y"
        del syllChars[at + 1]
        del cvCv[at + 1]
    return {
        "phon": newPhon, "syll": "".join(syllChars), "cv-cv": "".join(cvCv),
        "p_cvcv": "".join(pCvcv), "phonrenv": newPhon[::-1],
        "nbsyll": str(int(fields["nbsyll"]) - len(indices)),
    }


def fixInfraFields(fields: dict[str, str], indices: list[int]) -> dict[str, str]:
    segments = fields["assoc"].split(".")
    regular = fields["regTo_GP"].split(".")
    k = 0
    for i, segment in enumerate(segments):
        grapheme, phoneme = segment.split("-", 1)
        if k in indices:
            if grapheme.lower() not in OU_GRAPHEMES or phoneme != "u":
                raise ValueError(f"{fields['item']}: assoc {fields['assoc']!r} has no ou-u at {k}")
            segments[i] = f"{grapheme}-w"
            regular[i] = "0"
        k += len(phoneme.replace("#", ""))
    assoc = ".".join(segments)
    phono = "".join(s.split("-", 1)[1] for s in segments).replace("#", "")
    return {"assoc": assoc, "phono": phono, "regTo_GP": ".".join(regular)}


def rewriteTsv(path: str, keyOf, fixOf, apply: bool) -> list[tuple[dict[str, str], dict[str, str]]]:
    """Rewrite the fields fixOf(fields) returns in the rows keyOf selects,
    preserving every other byte of the file. Returns (old, new) field pairs."""
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
        description="Normalize within-lemma /u/ vs /w/ splits of 'ou' before a vowel to /w/ "
        "in Lexique383, LexiqueInfraCorrespondance, LexiqueMixte and LexiqueSynthetic.")
    parser.add_argument("--apply", action="store_true",
                        help="Write the corrections (default: dry-run).")
    args = parser.parse_args()

    mixteRows = readRows(LEXIQUE_MIXTE_PATH)
    syntheticRows = readRows(LEXIQUE_SYNTHETIC_PATH)
    splitLemmas = findSplitLemmas(mixteRows + syntheticRows)
    print(f"=== {len(splitLemmas)} lemmas split between /u/ and /w/ ===")
    for lemme, c in sorted(splitLemmas.items()):
        print(f"  {lemme}: w={c['w']} u={c['u']}")

    def lexiconFix(fields: dict[str, str]) -> dict[str, str] | None:
        if fields["lemme"] not in splitLemmas:
            return None
        fix = fixLexiconRow(fields)
        if fix is None:
            return None
        return {"phon": fix.newPhon, "syll_cv": fix.newSyllCv, "orthosyll_cv": fix.newOrthosyllCv}

    # The Mixte fixes key the source rows: same ortho + cgram + old phon.
    mixteFixes = {(f.ortho, f.cgram, f.oldPhon): f
                  for row in mixteRows if row["lemme"] in splitLemmas
                  for f in [fixLexiconRow(row)] if f is not None}

    totals = {}
    for path in (LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH):
        changes = rewriteTsv(path, lambda f: f["lemme"] in splitLemmas, lexiconFix, args.apply)
        totals[path] = len(changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
        for old, new in changes:
            print(f"  {old['phon']} -> {new['phon']}   {old['syll_cv']} -> {new['syll_cv']}"
                  f"   {new['orthosyll_cv']}")

    def lexique383Fix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = mixteFixes.get((fields["ortho"], fields["cgram"], fields["phon"]))
        return None if fix is None else fixLexique383Fields(fields, fix.phonIndices, fix.newPhon)

    def infraFix(fields: dict[str, str]) -> dict[str, str] | None:
        fix = mixteFixes.get((fields["item"], fields["cgram"], fields["phono"]))
        return None if fix is None else fixInfraFields(fields, fix.phonIndices)

    for path, fixOf, shown in ((LEXIQUE383_PATH, lexique383Fix, ("phon", "syll", "cv-cv")),
                               (LEXIQUE_INFRA_PATH, infraFix, ("phono", "assoc"))):
        changes = rewriteTsv(path, lambda f: True, fixOf, args.apply)
        totals[path] = len(changes)
        print(f"\n=== {path}: {len(changes)} rows ===")
        for old, new in changes:
            print("  " + "   ".join(f"{old[c]} -> {new[c]}" for c in shown))

    print("\nTotals: " + ", ".join(f"{p.split('/')[-1]} {n}" for p, n in totals.items()))
    if args.apply:
        print("--apply: files updated")


if __name__ == "__main__":
    main()
