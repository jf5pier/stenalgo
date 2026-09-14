#!/bin/env python
#
# Generalizes util/fixPayerNonfuturVowelQuality.py per the user's explicit
# phonological rule: orthographic "ay" is NEVER pronounced closed /e/+glide
# ("ej" in this lexicon's alphabet) -- it is always open /ɛ/+glide ("Ej").
# The prior script only fixed the pa:yer verb-template's nonfutur dual-slot
# rows (25 rows) by majority vote within each lemma; PAYER_SYLLCV_AUDIT.md's
# finding #3 (a residual cross-lemma "e" vs "E" split in the futur/cnd
# stem, e.g. payer/essayer/déblayer using lowercase "e" while
# balayer/effrayer/rayer use "E") was left unresolved because majority vote
# has no verdict when the "e" side is a lemma's own unanimous transcription.
# The user's rule removes the ambiguity: the "e" side is simply wrong,
# regardless of how internally consistent that lemma's own rows are.
#
# This also turns out to be far bigger than the pa:yer verb-template family
# alone: any word (VER conjugated forms, but also NOM/ADJ derivatives like
# "bégayant"/ADJ, "rayure"/NOM, "essayiste"/NOM) whose "ay" grapheme was
# transcribed with lowercase "ej" has the same defect -- 161 rows in
# resources/LexiqueMixte.tsv, 169 in resources/Lexique383.tsv (verified: at
# most one "ej" substring per phon value in every affected row, so a direct
# substring replace is unambiguous; manually spot-checked every non-VER
# case to confirm each is a genuine "ay"-grapheme derivative, not a
# coincidental "ay"+unrelated-"ej" collision).
#
# Separately, this also standardizes syll_cv's tokenization of the "ay"
# glide: some rows write it as one merged token "Ej" within its syllable
# (e.g. braye "b_R_Ej_#"), others split it into two adjacent tokens within
# the SAME syllable "E_j" (e.g. fraye "f_R_E_j_#") -- confirmed pure
# notation noise, not a phonological distinction (same word shape, same
# environment, both sides attested for near-identical lemma pairs). Merged
# is the family's own dominant convention (250 vs 26 same-syllable
# occurrences among "ay" words) and matches what lexique.py's own
# Word.breakdownSyllables produces for this exact grapheme (see its
# "ay-Ej" skip_next_Y handling) -- so split forms are normalized to merged.
# This is safe to do as a plain "E_j" -> "Ej" substring replace *within
# syll_cv only* because genuine cross-syllable resyllabification (the glide
# reattaching as onset to a following suffix vowel, e.g. bégayais
# "b_e|g_e|j_E") always has a "|" syllable boundary between the E and the
# j, never a bare "_" -- so it can never contain the literal substring
# "E_j" and is structurally unaffected by this replace.
#
# Dry-run by default: only reads and reports. --apply writes phon
# corrections to resources/Lexique383.tsv and resources/LexiqueMixte.tsv,
# and phon + syll_cv corrections (vowel quality first, then tokenization)
# to resources/LexiqueMixte.tsv, all in place. orthosyll_cv and
# Lexique383.tsv's syll/orthosyll columns are deliberately left untouched,
# same rationale as fixPayerNonfuturVowelQuality.py (orthographic columns
# don't carry a phoneme-quality distinction; Lexique383's "syll" column
# isn't consumed downstream -- LexiqueMixte's syll_cv is derived from
# phon+assoc by lexique.py, not copied from it). Idempotent.
import argparse
import re

LEXIQUE_383_PATH = "resources/Lexique383.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def correctPhon(ortho: str, phon: str) -> str | None:
    if "ay" not in ortho or "ej" not in phon:
        return None
    corrected = phon.replace("ej", "Ej")
    return corrected if corrected != phon else None


def correctSyllCvTokenization(ortho: str, syllCv: str) -> str | None:
    if "ay" not in ortho or "E_j" not in syllCv:
        return None
    corrected = syllCv.replace("E_j", "Ej")
    return corrected if corrected != syllCv else None


def correctSyllCvCrossSyllableVowel(ortho: str, phon: str, syllCv: str) -> str | None:
    # Companion to correctPhon's "ej"->"Ej", for the case where the glide resyllabifies
    # onto a following-vowel suffix (e.g. bégayais "b_e|g_e|j_E") -- there the vowel and
    # glide sit in different syllables, separated by "|" instead of "_", so a plain
    # "ej"->"Ej" substring replace (used for phon and for the same-syllable "E_j"->"Ej"
    # case above) never matches it, silently leaving the lowercase vowel uncorrected
    # even after phon was already fixed to "Ej". Scoped the same way as correctPhon.
    if "ay" not in ortho or "Ej" not in phon:
        return None
    corrected = re.sub(r"e(\|j)", r"E\1", syllCv)
    return corrected if corrected != syllCv else None


def processFile(path: str, hasSyllCv: bool, apply: bool) -> list[tuple[str, dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split("\t")
    orthoIdx = header.index("ortho")
    phonIdx = header.index("phon")
    syllCvIdx = header.index("syll_cv") if hasSyllCv else None

    report: list[tuple[str, dict[str, str]]] = []
    for i in range(1, len(lines)):
        if not lines[i].strip():
            continue
        ending = "\n" if lines[i].endswith("\n") else ""
        fields = lines[i].rstrip("\n").split("\t")
        ortho = fields[orthoIdx]
        changes: dict[str, str] = {}

        newPhon = correctPhon(ortho, fields[phonIdx])
        if newPhon is not None:
            changes["phon"] = newPhon

        if syllCvIdx is not None:
            # Vowel-quality fix first (phon's own "ej"->"Ej" rule, applied to
            # syll_cv's lowercase "e" the same way fixPayerNonfuturVowelQuality.py
            # did: syll_cv shares phon's alphabet, so replacing "ej"->"Ej" in it
            # directly is equally unambiguous here since we've already scoped to
            # "ay" ortho and the same one-occurrence-per-row guarantee holds).
            syllCv = fields[syllCvIdx]
            if "ay" in ortho and "ej" in syllCv:
                candidate = syllCv.replace("ej", "Ej")
                if candidate != syllCv:
                    syllCv = candidate
                    changes["syll_cv"] = syllCv
            newSyllCv = correctSyllCvTokenization(ortho, syllCv)
            if newSyllCv is not None:
                syllCv = newSyllCv
                changes["syll_cv"] = syllCv
            newSyllCv = correctSyllCvCrossSyllableVowel(ortho, changes.get("phon", fields[phonIdx]), syllCv)
            if newSyllCv is not None:
                changes["syll_cv"] = newSyllCv

        if changes:
            report.append((ortho, changes))
            if apply:
                for field, value in changes.items():
                    fields[header.index(field)] = value
                lines[i] = "\t".join(fields) + ending

    if apply:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix the 'ay' grapheme's lowercase-e/ej vowel-quality "
        "defect and same-syllable Ej/E_j tokenization noise lexicon-wide."
    )
    parser.add_argument("--apply", action="store_true",
                         help="Write corrections in place (default: dry-run).")
    args = parser.parse_args()

    report383 = processFile(LEXIQUE_383_PATH, hasSyllCv=False, apply=args.apply)
    reportMixte = processFile(LEXIQUE_MIXTE_PATH, hasSyllCv=True, apply=args.apply)

    for name, report in ((LEXIQUE_383_PATH, report383), (LEXIQUE_MIXTE_PATH, reportMixte)):
        print(f"=== {name}: {len(report)} rows to correct ===")
        for ortho, changes in report[:15]:
            print(f"  {ortho}: {changes}")
        if len(report) > 15:
            print(f"  ... and {len(report) - 15} more")
        print()

    if args.apply:
        print(f"--apply: corrected {len(report383)} rows in {LEXIQUE_383_PATH}")
        print(f"--apply: corrected {len(reportMixte)} rows in {LEXIQUE_MIXTE_PATH}")


if __name__ == "__main__":
    main()
