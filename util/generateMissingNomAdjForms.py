#!/bin/env python
#
# Generates the missing NOM ("s"/"p") or ADJ (m_s/m_p/f_s/f_p) rows flagged
# MISSING_FORM by util/validateLexiconAgainstNomAdjParadigms.py.
#
# Morphalou (ATILF/CNRTL, LGPL-LR) is the AUTHORITATIVE source for
# orthography whenever it has an answer -- src/nomAdjParadigm.py's
# empirically-derived donor-ending-class splicing (cross-lemma agreement
# within our own sampled lexicon) is only a confidence proxy, not linguistic
# validation, and hand-checking against Morphalou found and fixed several
# donor-table mistakes it would otherwise have silently generated (see the
# conversation). generateAuthoritativeForm (src/nomAdjParadigm.py) is the
# single place this policy lives: Morphalou overrides the donor table's
# ortho on disagreement, phon/syllable-breakdown still comes from the donor
# table either way (Morphalou's own phonetic transcription uses a different
# notation and no syllable segmentation -- not converted, future work).
# resources/nomAdjModelExceptions.tsv's hand-given override remains the
# final tier, for the individual words neither source can confidently
# resolve alone.
#
# Per the project's established convention for synthetic rows (see
# util/fixPayerDualFormGaps.py, util/fixAsseoirDualFormGapsManual.py):
# generated rows are appended to resources/LexiqueSynthetic.tsv
# (source=synthetic), NEVER written into resources/LexiqueMixte.tsv.
#
# Dry-run by default: only reads, prints what would be generated/skipped.
# --apply appends to resources/LexiqueSynthetic.tsv. Idempotent: a slot
# already present in either TSV is treated as satisfied, not regenerated.
import argparse
import os
from collections import Counter, defaultdict

from src.nomAdjParadigm import (
    ADJ_SLOTS,
    NOM_NUMBERS,
    Slot,
    attestedSlots,
    chooseSourceSlot,
    deriveNomAdjEndingTables,
    generateAuthoritativeForm,
    isSuspectedInvariableForm,
    loadAllOrthosByLemme,
    loadMorphalouIndex,
    loadNomAdjModelExceptions,
    loadWords,
    missingSlots,
    morphalouOrthos,
)
from src.word import GramCat, Word

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
EXCEPTIONS_PATH = "resources/nomAdjModelExceptions.tsv"
MORPHALOU_PATH_DEFAULT = "morphalou/Morphalou3.1_CSV.csv"

SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)


def wordToSyntheticRow(word: Word) -> str:
    cgramortho = ",".join(gc.name for gc in word.orthoGramCat)
    return "\t".join([
        word.ortho, word.phonology, word.lemme, word.gramCat.name, cgramortho,
        word.gender or "", word.number or "", word.infoVerb or "",
        word.rawSyllCV, word.rawOrthosyllCV,
        f"{word.frequencyBook}", f"{word.frequencyFilm}", "synthetic",
    ]) + "\n"


def slotOrderFor(gramCat: GramCat, gender: str) -> tuple[Slot, ...]:
    """ADJ_SLOTS order for ADJ; (gender, "s")/(gender, "p") for NOM, since a NOM's gender is fixed."""
    return ADJ_SLOTS if gramCat == GramCat.ADJ else tuple((gender, n) for n in NOM_NUMBERS)


def overrideCandidate(sourceWord: Word, slot: Slot, gramCat: GramCat, overrideOrtho: str, overridePhonology: str) -> Word | None:
    """Build a candidate straight from an exceptions-table override_ortho row. `overridePhonology` is the same
    ";"-joined-by-slot string as `overrideOrtho`; when this slot's entry is blank, falls back to reusing
    sourceWord's phon verbatim (a placeholder -- adding a real override_phonology entry is preferred)."""
    assert sourceWord.gender is not None
    slotOrder = slotOrderFor(gramCat, sourceWord.gender)
    orthoBySlot = dict(zip(slotOrder, overrideOrtho.split(";")))
    ortho = orthoBySlot.get(slot)
    if not ortho:
        return None
    phonBySlot = dict(zip(slotOrder, overridePhonology.split(";"))) if overridePhonology else {}
    phonology = phonBySlot.get(slot) or sourceWord.phonology
    gender, number = slot
    return Word(
        ortho=ortho, phonology=phonology, lemme=sourceWord.lemme,
        gramCat=gramCat, orthoGramCat=sourceWord.orthoGramCat,
        gender=gender, number=number, infoVerb=None,
        rawSyllCV=sourceWord.rawSyllCV, rawOrthosyllCV=sourceWord.rawOrthosyllCV,
        frequencyBook=0.0, frequencyFilm=0.0,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                         help="Append generated rows to resources/LexiqueSynthetic.tsv (default: dry-run report only).")
    parser.add_argument("--morphalou", default=MORPHALOU_PATH_DEFAULT,
                         help="Path to Morphalou3.1_CSV.csv (authoritative ortho source). "
                              "If missing, falls back to the donor table alone with a loud warning.")
    parser.add_argument("--no-morphalou", action="store_true",
                         help="Skip Morphalou entirely and trust the donor table alone (not recommended).")
    args = parser.parse_args()

    morphalou = None
    if args.no_morphalou:
        print("--no-morphalou: generating from the donor table alone, unverified against an external source.")
    elif os.path.exists(args.morphalou):
        print(f"Loading Morphalou from {args.morphalou} ...")
        morphalou = loadMorphalouIndex(args.morphalou)
        print(f"Indexed {len(morphalou)} NOM/ADJ lemma groups from Morphalou.")
    else:
        print(f"WARNING: Morphalou not found at {args.morphalou!r} -- generating from the donor table alone, "
              f"unverified against an external source. Pass --morphalou PATH or --no-morphalou to silence this.")

    words = loadWords([LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH])
    exceptions = loadNomAdjModelExceptions(EXCEPTIONS_PATH)
    tables = deriveNomAdjEndingTables(words)
    slotsByLemme = attestedSlots(words)
    # Deliberately built from the UNFILTERED files (excluded rows included --
    # see loadAllOrthosByLemme) rather than from `words`: a slot whose only
    # attested spelling is itself excluded (e.g. "laponne", a deprecated
    # alternate of "lapone") still looks genuinely missing to attestedSlots,
    # and without this the generator would re-derive and re-append that same
    # excluded ortho every run, never recognizing its own prior output as
    # already covering it (found via the conversation).
    existingOrthoByLemme: dict[str, set[str]] = defaultdict(
        set, loadAllOrthosByLemme([LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH])
    )

    generated: list[Word] = []
    sourceCounts: Counter = Counter()
    skippedReasons: Counter = Counter()

    for lemmeGramCat, slotMap in sorted(slotsByLemme.items()):
        gramCat = next(iter(slotMap.values())).gramCat
        for slot in sorted(missingSlots(slotMap, gramCat)):
            sourceSlot = chooseSourceSlot(slotMap, gramCat)
            assert sourceSlot is not None
            sourceWord = slotMap[sourceSlot]
            lemme = sourceWord.lemme
            exception = exceptions.get((lemme, gramCat.name))

            if exception is not None and exception.status == "invariable":
                skippedReasons["exception: invariable"] += 1
                continue
            if isSuspectedInvariableForm(sourceWord, slot):
                skippedReasons["suspected invariable (s/x/z NOM plural, or invariant ADJ gender ending)"] += 1
                continue

            candidate: Word | None
            source: str
            if exception is not None and exception.status == "irregular" and exception.overrideOrtho:
                candidate = overrideCandidate(
                    sourceWord, slot, gramCat, exception.overrideOrtho, exception.overridePhonology
                )
                source = "exception_override"
                if candidate is not None and morphalou is not None:
                    known = morphalouOrthos(morphalou, lemme, gramCat, slot)
                    if known is not None and candidate.ortho not in known:
                        print(f"  NOTE: exceptions-table override for {lemme}_{gramCat.name} {slot} "
                              f"({candidate.ortho!r}) disagrees with Morphalou ({sorted(known)!r}) -- "
                              f"double check that exceptions row.")
            else:
                candidate, source = generateAuthoritativeForm(sourceWord, slot, tables, morphalou)

            if candidate is None:
                skippedReasons[f"not generated ({source})"] += 1
                continue
            if candidate.ortho in existingOrthoByLemme.get(lemme, set()):
                skippedReasons["ortho already exists (likely a tag gap, not a missing form)"] += 1
                continue

            generated.append(candidate)
            sourceCounts[source] += 1
            existingOrthoByLemme[lemme].add(candidate.ortho)

    print(f"\nGenerated: {len(generated)}")
    for source, count in sourceCounts.most_common():
        print(f"  from {source}: {count}")
    for reason, count in skippedReasons.most_common():
        print(f"Skipped ({reason}): {count}")

    if args.apply and generated:
        fileExists = os.path.exists(LEXIQUE_SYNTHETIC_PATH)
        with open(LEXIQUE_SYNTHETIC_PATH, "a", encoding="utf-8") as syntheticFile:
            if not fileExists:
                syntheticFile.write(SYNTHETIC_HEADER)
            for word in generated:
                syntheticFile.write(wordToSyntheticRow(word))
        print(f"Appended {len(generated)} rows to {LEXIQUE_SYNTHETIC_PATH}")
    elif generated:
        print("Dry-run: pass --apply to append these rows.")


if __name__ == "__main__":
    main()
