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
from typing import Any
import argparse
import csv
import hashlib
import os
from collections import Counter, defaultdict

from src.nomAdjParadigm import (
    ADJ_SLOTS,
    NOM_NUMBERS,
    Slot,
    attestedSlots,
    chooseSourceSlot,
    NomAdjEndingTables,
    MorphalouIndex,
    deriveNomAdjEndingTables,
    generateAuthoritativeForm,
    isSuspectedInvariableForm,
    loadAllOrthosByLemme,
    loadMorphalouForms,
    loadMorphalouIndex,
    loadNomAdjModelExceptions,
    loadWords,
    missingSlots,
    morphalouOrthos,
)
from src.word import GramCat, Word
from util._timing import timedCall

LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"
LEXIQUE_SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
EXCEPTIONS_PATH = "resources/nomAdjModelExceptions.tsv"
MORPHALOU_PATH_DEFAULT = "morphalou/Morphalou3.1_CSV.csv"
MORPHALOU_FORMS_PATH = "resources/morphalouNomAdjForms.tsv"  # committed distillate, see util/build_morphalou_forms.py

SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)


STATE_ENV = "S2_NOMADJ_STATE"  # set by util.build_synthetic_lexicon for the length of one run, see inputsFingerprint
NOM_ADJ = ("NOM", "ADJ")


def _fileDigest(path: str) -> str:
    if not os.path.exists(path):
        return "absent"
    digest = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def inputsFingerprint(morphalouPath: str = MORPHALOU_PATH_DEFAULT) -> str:
    """A digest of everything the generation reads, for the Synthetic Lexicon Building (S2) loop to tell that a later
    round has nothing new for this appender (the other appenders add verb rows). It reads: the NOM/ADJ rows of both
    lexicons, the spellings already present under any NOM/ADJ lemma (any category: `boire` is a verb and a noun), the
    exceptions table, Morphalou and the exclusion list. The Synthetic rows are taken as a set, so the order the
    driver sorts them in does not matter."""
    digest = hashlib.md5()
    for path in (LEXIQUE_MIXTE_PATH, EXCEPTIONS_PATH, MORPHALOU_FORMS_PATH, morphalouPath, "excluded_words.txt"):
        digest.update(f"{path}:{_fileDigest(path)}\n".encode())
    nomAdjLemmes: set[str] = set()
    with open(LEXIQUE_MIXTE_PATH, encoding="utf-8", newline="") as f:
        nomAdjLemmes.update(row["lemme"] for row in csv.DictReader(f, delimiter="\t") if row["cgram"] in NOM_ADJ)
    syntheticRows: list[dict[str, str]] = []
    if os.path.exists(LEXIQUE_SYNTHETIC_PATH):
        with open(LEXIQUE_SYNTHETIC_PATH, encoding="utf-8", newline="") as f:
            syntheticRows = list(csv.DictReader(f, delimiter="\t"))
    nomAdjLemmes.update(row["lemme"] for row in syntheticRows if row["cgram"] in NOM_ADJ)
    nomAdjRows = sorted(tuple(row.values()) for row in syntheticRows if row["cgram"] in NOM_ADJ)
    spellings = sorted({(row["lemme"], row["ortho"]) for row in syntheticRows if row["lemme"] in nomAdjLemmes})
    digest.update(repr((nomAdjRows, spellings)).encode())
    return digest.hexdigest()


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


def generateRows(
    words: list[Word],
    morphalou: MorphalouIndex | None,
    exceptions: dict[tuple[str, str], Any],
    tables: NomAdjEndingTables,
    existingOrthoByLemme: dict[str, set[str]],
) -> tuple[list[Word], Counter[str], Counter[str]]:
    """The generation loop of main(), callable on its own: (generated rows, count by source, skip reasons).
    `tables` is passed in so a caller can learn them from other rows than `words` (see the TODO on the
    NOM/ADJ cascade); main() derives them from `words`."""
    slotsByLemme = attestedSlots(words)
    generated: list[Word] = []
    sourceCounts: Counter[str] = Counter()
    skippedReasons: Counter[str] = Counter()

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
            # No memory of the spelling just generated: the same spelling is a legitimate row for another
            # slot (allèles m.p. and f.p.) or the other category (audiovisuels NOM and ADJ). The slot itself
            # is attested in the next iteration; excluded spellings are caught by the file-based set above.

    return generated, sourceCounts, skippedReasons


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

    statePath = os.environ.get(STATE_ENV) if args.apply else None
    if statePath and os.path.exists(statePath):
        with timedCall("phase", "util.generateMissingNomAdjForms: inputs fingerprint"):
            unchanged = open(statePath, encoding="utf-8").read() == inputsFingerprint(args.morphalou)
        if unchanged:
            print("Nothing this appender reads changed since its previous round: skipped (nothing to generate).")
            return

    morphalou = None
    if args.no_morphalou:
        print("--no-morphalou: generating from the donor table alone, unverified against an external source.")
    elif os.path.exists(args.morphalou):
        print(f"Loading Morphalou from {args.morphalou} ...")
        morphalou = loadMorphalouIndex(args.morphalou)
        print(f"Indexed {len(morphalou)} NOM/ADJ lemma groups from Morphalou.")
    elif os.path.exists(MORPHALOU_FORMS_PATH):
        print(f"Morphalou CSV not found; loading the committed distillate {MORPHALOU_FORMS_PATH} ...")
        morphalou = loadMorphalouForms(MORPHALOU_FORMS_PATH)
        print(f"Loaded {len(morphalou)} NOM/ADJ lemma groups.")
    else:
        print(f"WARNING: Morphalou not found at {args.morphalou!r} -- generating from the donor table alone, "
              f"unverified against an external source. Pass --morphalou PATH or --no-morphalou to silence this.")

    with timedCall("phase", "util.generateMissingNomAdjForms: parse the lexicons"):
        # Each file is parsed once: the donor pool is Mixte then Synthetic, the donor tables use Mixte alone.
        # Only NOM/ADJ rows are read (attestedSlots, the donor tables): the other categories are not even built.
        nomAdj = frozenset(NOM_ADJ)
        mixteWords = loadWords([LEXIQUE_MIXTE_PATH], gramCats=nomAdj)
        words = mixteWords + loadWords([LEXIQUE_SYNTHETIC_PATH], gramCats=nomAdj)
    exceptions = loadNomAdjModelExceptions(EXCEPTIONS_PATH)
    # The donor tables are learned from the mixed lexicon alone: learning them from this appender's
    # own earlier rows let generated rows promote rare ending classes (the cross-round cascade).
    with timedCall("phase", "util.generateMissingNomAdjForms: donor tables"):
        tables = deriveNomAdjEndingTables(mixteWords)
    # Deliberately built from the UNFILTERED files (excluded rows included --
    # see loadAllOrthosByLemme) rather than from `words`: a slot whose only
    # attested spelling is itself excluded (e.g. "laponne", a deprecated
    # alternate of "lapone") still looks genuinely missing to attestedSlots,
    # and without this the generator would re-derive and re-append that same
    # excluded ortho every run, never recognizing its own prior output as
    # already covering it (found via the conversation).
    with timedCall("phase", "util.generateMissingNomAdjForms: existing spellings by lemme"):
        existingOrthoByLemme: dict[str, set[str]] = defaultdict(
            set, loadAllOrthosByLemme([LEXIQUE_MIXTE_PATH, LEXIQUE_SYNTHETIC_PATH])
        )

    # A generated row can be the source slot of another missing slot of its lemma: iterate to the
    # fixed point here, not in the caller's rounds.
    generated: list[Word] = []
    sourceCounts: Counter[str] = Counter()
    roundWords = words
    while True:
        with timedCall("phase", "util.generateMissingNomAdjForms: generateRows"):
            newRows, roundSourceCounts, skippedReasons = generateRows(
                roundWords, morphalou, exceptions, tables, existingOrthoByLemme)
        if not newRows:
            break
        generated += newRows
        sourceCounts += roundSourceCounts
        roundWords = roundWords + newRows

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
    if statePath:
        # taken after the append: a later round whose inputs still match has nothing left to generate (the loop above
        # runs to its own fixed point)
        with open(statePath, "w", encoding="utf-8") as stateFile:
            stateFile.write(inputsFingerprint(args.morphalou))


if __name__ == "__main__":
    main()
