#!/bin/env python
#
# Stage 5 of the "Undersampling-aware paradigm completion for sparse verb
# homophone groups" design plan: detects VER lemmas whose paradigm is
# undersampled relative to their conjugation-model siblings
# (src/verbparadigm.py's detectUndersampledLemmas), generates the missing
# forms -- past-participle gender/number via template + verbatim phonology
# splicing (generateMissingParticiple), and full finite conjugation
# (indicatif/subjonctif/conditionnel/impératif person/number slots) via an
# empirically-derived per-template ending table (deriveConjugationEndingTables
# / generateMissingConjugatedForm, gated by MIN_FINITE_MATCH_RATE) -- and
# keeps only the candidates that actually cause a NEW "conflicting feature
# set" collision -- two unrelated lemmas independently getting assigned the
# identical minimal discriminator by greedyOptimizeDiscriminator
# (crossLemmaFeatureSetCollisions / newlyCollidingLemmas). This is the
# collision that originally motivated this plan (rechampir vs regarnir both
# landing on ('p', 'indicatif')); it lives in the discriminator-*feature*
# space, not in raw keystroke (Strokes) collisions.
#
# Dry-run by default: only reads resources/LexiqueMixte.tsv (via the cached
# FirstTheory.pickle when present), resources/verbiste/*, and
# resources/verbModelExceptions.tsv, and prints a report of what it would
# generate. --apply additionally appends the confirmed candidate rows to
# resources/LexiqueSynthetic.tsv (created with a header if it doesn't exist
# yet), each tagged source=synthetic.
#
# NOTE: resources/LexiqueSynthetic.tsv is not yet wired into lexique.py's
# merge step. Running --apply only produces/extends that file; it does not
# yet flow into LexiqueMixte.tsv or the rest of the pipeline. That wiring is
# the remaining half of Stage 5 and is deliberately left for a separate,
# explicitly-approved change.
import argparse
import gc
import os
import pickle
import resource
from contextlib import contextmanager
from typing import Iterator

from src.featureextractor import extractDiscriminatingFeatures
from src.greedyoptimizer import greedyOptimizeDiscriminator
from src.keyboard import Starboard, Strokes
from src.verbparadigm import (
    ConjugationEndingTables,
    UndersampledLemma,
    allFiniteSlots,
    attestedInfinitiveWordByLemme,
    deriveConjugationEndingTables,
    detectUndersampledLemmas,
    generateMissingConjugatedForm,
    generateMissingParticiple,
    lemmeOfVerbLemmeGramCat,
    loadVerbisteTemplates,
    loadVerbModelExceptions,
    newlyCollidingLemmas,
    parseConjugationTemplates,
)
from src.word import GramCat, Lemme, LemmeGramCat, Word

VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
THEORY_CACHE_PATH = "FirstTheory.pickle"
KEYBOARD_JSON_PATH = "starboard3h.json"

GENDER_NUMBER_SLOTS = [("m", "s"), ("m", "p"), ("f", "s"), ("f", "p")]

# Minimum empirical match rate (see deriveConjugationEndingTables) a finite-conjugation
# slot must have across attested donor lemmas before a candidate is generated for it.
# 1.0 means only slots with zero disagreement among every attested donor are trusted --
# see the design plan's note that phonology is exactly where regressions are easiest to
# introduce, so this default deliberately errs on the side of skipping over guessing.
MIN_FINITE_MATCH_RATE = 1.0

# Safety cap: a prior version of this script held two full-corpus
# extractDiscriminatingFeatures results in memory simultaneously and swapped
# the whole machine to a crawl (see conversation) on a machine with ~7.7GB
# RAM. Capping this process's own address space makes it fail with a clear
# MemoryError instead of triggering OS-level swap thrashing again, in case
# some other path still uses more memory than expected.
MEMORY_LIMIT_BYTES = 4 * 1024 ** 3

SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)

Candidate = tuple[LemmeGramCat, UndersampledLemma, Word, Word]  # (..., generated, referenceWord)


def loadTheoryAndKeyboard() -> tuple[dict[Strokes, list[Word]], Starboard]:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON_PATH)
    if starboard is None:
        raise RuntimeError(f"Could not load keyboard from {KEYBOARD_JSON_PATH!r}")
    if os.path.exists(THEORY_CACHE_PATH):
        with open(THEORY_CACHE_PATH, "rb") as pickleFile:
            return pickle.load(pickleFile), starboard
    import dictionary as dictionary_module
    from src.grammar import Syllable
    dictionary = dictionary_module.Dictionary()
    # buildTheory reads dictionary.syllableCollection, which only
    # analyseSyllabification() populates -- dictionary.py's own __main__
    # always runs it (or unpickles the post-analysis state) before ever
    # calling buildTheory. Skipping it here reproduces a KeyError in
    # buildTheory (self.syllableCollection.syllable_names[syllableName]) the
    # first time this runs without a cached FirstTheory.pickle.
    dictionary.analyseSyllabification()
    Syllable.optimizeBiphonemeOrder()
    return dictionary.buildTheory(starboard), starboard


def attestedParticipleFormsByLemme(
    theory: dict[Strokes, list[Word]]
) -> dict[Lemme, dict[tuple[str, str], Word]]:
    """
    lemma -> {(gender, number): attested past-participle Word}, for every VER
    lemma with at least one attested "par:pas" gender/number form.
    """
    result: dict[Lemme, dict[tuple[str, str], Word]] = {}
    for words in theory.values():
        for word in words:
            if word.gramCat != GramCat.VER or word.gender is None or word.number is None:
                continue
            if word.infoVerb is None or "par:pas" not in word.infoVerb:
                continue
            result.setdefault(word.lemme, {})[(word.gender, word.number)] = word
    return result


def attestedFiniteFormsByLemme(
    theory: dict[Strokes, list[Word]]
) -> dict[Lemme, dict[tuple[str, str], Word]]:
    """
    lemma -> {(code, personNumber): attested Word}, for every finite conjugation
    slot (indicatif/subjonctif/conditionnel/impératif) attested for a VER lemma.
    Excludes "inf", "par:pre" and "par:pas" tags (1- or 2-part, not 3-part).
    """
    result: dict[Lemme, dict[tuple[str, str], Word]] = {}
    for words in theory.values():
        for word in words:
            if word.gramCat != GramCat.VER or word.infoVerb is None:
                continue
            tags = word.infoVerb.split(";")
            # A word whose infoVerb also carries "inf" is untrustworthy for its
            # other tags too (see attestedInfinitiveWordByLemme's docstring):
            # resources/LexiqueMixte.tsv has rows where a genuine infinitive
            # (e.g. "aduler") is spuriously also tagged with a finite slot
            # (e.g. "ind:pre:2p"). Trusting that here would make
            # findStructuralCandidates believe the lemma's real "adulez" form
            # is already attested -- pointing at the infinitive's own
            # orthography -- and skip generating it.
            if "inf" in tags:
                continue
            for tag in tags:
                if not tag:
                    continue
                parts = tag.split(":")
                if len(parts) != 3:
                    continue
                code, personNumber = f"{parts[0]}:{parts[1]}", parts[2]
                result.setdefault(word.lemme, {})[(code, personNumber)] = word
    return result


def findStructuralCandidates(
    strokeLemmeDiscriminators: dict,
    theory: dict[Strokes, list[Word]],
    verbisteTemplates: dict[Lemme, str],
    exceptions: dict,
    conjugationTemplates: dict,
    endingTables: ConjugationEndingTables,
    minFiniteMatchRate: float = MIN_FINITE_MATCH_RATE,
) -> tuple[list[Candidate], list[tuple[Lemme, str]]]:
    """
    Stage 3 (undersampling detection) + Stage 4 (orthography/phonology
    generation) only -- no collision filtering yet. Every generated
    candidate is paired with the attested reference Word its phonology was
    spliced from, so its Strokes can be found by simple lookup instead of
    recomputed. Covers both past-participle gender/number slots
    (generateMissingParticiple) and finite conjugation slots
    (generateMissingConjugatedForm, gated by minFiniteMatchRate).
    """
    undersampled = detectUndersampledLemmas(strokeLemmeDiscriminators, verbisteTemplates, exceptions)
    participleForms = attestedParticipleFormsByLemme(theory)
    finiteForms = attestedFiniteFormsByLemme(theory)
    infinitiveWords = attestedInfinitiveWordByLemme(theory)

    candidates: list[Candidate] = []
    skipped: list[tuple[Lemme, str]] = []
    for lemmeGramCat, info in undersampled.items():
        lemme = lemmeOfVerbLemmeGramCat(lemmeGramCat)
        if lemme is None:
            continue
        template = conjugationTemplates.get(info.template)
        if template is None:
            skipped.append((lemme, f"template {info.template!r} not found in conjugations-fr.xml"))
            continue

        attestedSlots = participleForms.get(lemme, {})
        if attestedSlots:
            referenceWord = next(iter(attestedSlots.values()))
            for gender, number in GENDER_NUMBER_SLOTS:
                if (gender, number) in attestedSlots:
                    continue
                try:
                    generated = generateMissingParticiple(lemme, template, referenceWord, gender, number)
                except ValueError as error:
                    skipped.append((lemme, str(error)))
                    continue
                candidates.append((lemmeGramCat, info, generated, referenceWord))
        else:
            skipped.append((lemme, "no attested past-participle form to splice phonology from"))

        infinitiveWord = infinitiveWords.get(lemme)
        if infinitiveWord is None:
            skipped.append((lemme, "no attested infinitive to derive finite conjugation radicals from"))
            continue
        attestedFinite = finiteForms.get(lemme, {})
        for code, personNumber in allFiniteSlots(template):
            if (code, personNumber) in attestedFinite:
                continue
            generatedFinite = generateMissingConjugatedForm(
                lemme, template, infinitiveWord, code, personNumber, endingTables,
                minMatchRate=minFiniteMatchRate,
            )
            if generatedFinite is None:
                skipped.append((
                    lemme,
                    f"{code}:{personNumber} has no template ending or no confident-enough "
                    "empirical phonology for template " + template.name,
                ))
                continue
            candidates.append((lemmeGramCat, info, generatedFinite, infinitiveWord))
    return candidates, skipped


@contextmanager
def temporarilyAugmented(
    theory: dict[Strokes, list[Word]], candidates: list[Candidate]
) -> Iterator[dict[Strokes, list[Word]]]:
    """
    Temporarily appends each candidate's generated Word into its reference
    word's existing stroke group (every candidate's phon is spliced verbatim
    from an already-attested word of the same lemma, so that word's stroke
    group always already exists -- never a brand new key), then removes them
    again on exit. Avoids a full shallow copy of `theory` (tens of thousands
    of stroke-group lists), which combined with holding two full
    extractDiscriminatingFeatures results at once is what caused this script
    to exhaust memory and swap the whole machine to a crawl on a prior run.
    """
    strokesByWord: dict[Word, Strokes] = {
        word: strokes for strokes, words in theory.items() for word in words
    }
    appendedStrokes: list[Strokes] = []
    try:
        for _lemmeGramCat, _info, generated, referenceWord in candidates:
            strokes = strokesByWord[referenceWord]
            theory[strokes].append(generated)
            appendedStrokes.append(strokes)
        yield theory
    finally:
        for strokes in reversed(appendedStrokes):
            theory[strokes].pop()


def confirmCandidates(
    candidates: list[Candidate],
    theory: dict[Strokes, list[Word]],
    starboard: Starboard,
    baselineFeaturesetWords: dict,
) -> tuple[list[Candidate], list[tuple[Lemme, str]]]:
    """
    Keeps only the candidates that actually cause a NEW cross-lemma
    "conflicting feature set" collision when added -- the real mechanism
    behind the design plan's motivating bug (see module docstring).
    """
    if not candidates:
        return [], []

    with temporarilyAugmented(theory, candidates):
        augmentedDiscBy, augmentedOrdered, _ = extractDiscriminatingFeatures(theory)
        augmentedFeaturesetWords = greedyOptimizeDiscriminator(theory, augmentedDiscBy, augmentedOrdered, starboard)
        del augmentedDiscBy, augmentedOrdered
        gc.collect()

    newlyColliding = newlyCollidingLemmas(baselineFeaturesetWords, augmentedFeaturesetWords)

    confirmed: list[Candidate] = []
    skipped: list[tuple[Lemme, str]] = []
    for lemmeGramCat, info, generated, referenceWord in candidates:
        if lemmeGramCat in newlyColliding:
            confirmed.append((lemmeGramCat, info, generated, referenceWord))
        else:
            lemme = lemmeOfVerbLemmeGramCat(lemmeGramCat) or lemmeGramCat
            skipped.append((
                lemme,
                f"{generated.ortho!r} ({generated.gender}_{generated.number}) doesn't cause a new "
                "cross-lemma discriminator collision -- irrelevant to disambiguation today",
            ))
    return confirmed, skipped


def printReport(candidates: list[Candidate], skipped: list[tuple[Lemme, str]]) -> None:
    print("=== Confirmed candidates (dry-run, no files modified) ===\n")
    for lemmeGramCat, info, word, _referenceWord in candidates[:15]:
        siblingSample = sorted(info.siblingLemmeGramCats)[:3]
        slotLabel = f"{word.gender}_{word.number}" if word.gender and word.number else (word.infoVerb or "")
        print(f"lemme: {lemmeGramCat}  template: {info.template}  siblings (sample): {siblingSample}")
        print(f"  generated: {word.ortho!r}  ({slotLabel})")
        print(f"  phon: {word.phonology!r}  orthosyll: {word.rawOrthosyllCV!r}  syll: {word.rawSyllCV!r}")
        print()

    flaggedLemmas = {lemmeGramCat for lemmeGramCat, _info, _word, _ref in candidates}
    skippedLemmas = {lemme for lemme, _reason in skipped}
    print("=== Summary ===")
    print(f"Undersampled VER lemmas confirmed to cause a new discriminator collision: {len(flaggedLemmas)}")
    print(f"Candidate rows confirmed: {len(candidates)}")
    print(f"Lemmas/candidates skipped (see reasons): {len(skippedLemmas)}")
    for lemme, reason in skipped[:20]:
        print(f"  {lemme}: {reason}")
    if len(skippedLemmas) > 20:
        print(f"  ... and {len(skippedLemmas) - 20} more")


def writeSynthetic(path: str, candidates: list[Candidate]) -> int:
    fileExists = os.path.exists(path)
    written = 0
    with open(path, "a", newline="") as syntheticFile:
        if not fileExists:
            syntheticFile.write(SYNTHETIC_HEADER)
        for _lemmeGramCat, _info, word, _referenceWord in candidates:
            fields = [
                word.ortho, word.phonology, word.lemme, word.gramCat.name,
                ",".join(gramCat.name for gramCat in word.orthoGramCat),
                word.gender or "", word.number or "", word.infoVerb or "",
                word.rawSyllCV, word.rawOrthosyllCV,
                str(word.frequencyBook), str(word.frequencyFilm), "synthetic",
            ]
            syntheticFile.write("\t".join(fields) + "\n")
            written += 1
    return written


def _capMemory() -> None:
    try:
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    except (ValueError, OSError):
        pass  # best-effort; not supported on every platform


def main() -> None:
    _capMemory()
    parser = argparse.ArgumentParser(
        description="Detect undersampled VER paradigms (Stage 3), generate "
        "their missing past-participle forms (Stage 4), and keep only the "
        "candidates that cause a new cross-lemma discriminator collision."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Append confirmed rows to resources/LexiqueSynthetic.tsv "
        "(default: dry-run report only, no files modified).",
    )
    args = parser.parse_args()

    print("Loading theory (uses FirstTheory.pickle if present)...")
    theory, starboard = loadTheoryAndKeyboard()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)

    baselineDiscBy, baselineOrdered, strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)

    endingTables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)

    structuralCandidates, structuralSkipped = findStructuralCandidates(
        strokeLemmeDiscriminators, theory, verbisteTemplates, exceptions, conjugationTemplates,
        endingTables,
    )
    # Reduce down to the (much smaller) featuresetWords structure and drop
    # the full-corpus extraction results before the augmented pass builds its
    # own copy of them -- never hold two of these at once (see
    # temporarilyAugmented's docstring for why this matters).
    baselineFeaturesetWords = greedyOptimizeDiscriminator(theory, baselineDiscBy, baselineOrdered, starboard)
    del baselineDiscBy, baselineOrdered, strokeLemmeDiscriminators
    gc.collect()

    confirmedCandidates, collisionSkipped = confirmCandidates(
        structuralCandidates, theory, starboard, baselineFeaturesetWords
    )
    skipped = structuralSkipped + collisionSkipped

    printReport(confirmedCandidates, skipped)

    if os.environ.get("COMPLETE_VERB_PARADIGMS_DEBUG_DUMP"):
        with open(os.environ["COMPLETE_VERB_PARADIGMS_DEBUG_DUMP"], "w") as debugFile:
            for lemmeGramCat, info, word, _ref in confirmedCandidates:
                debugFile.write(f"CANDIDATE\t{lemmeGramCat}\t{info.template}\t{word.ortho}\t{word.gender}_{word.number}\n")
            for lemme, reason in skipped:
                debugFile.write(f"SKIPPED\t{lemme}\t{reason}\n")

    if args.apply:
        written = writeSynthetic(SYNTHETIC_PATH, confirmedCandidates)
        print(f"\n--apply: appended {written} rows to {SYNTHETIC_PATH}")
        print(
            "NOTE: resources/LexiqueSynthetic.tsv is not yet merged into "
            "LexiqueMixte.tsv by lexique.py -- this file alone does not yet "
            "affect the rest of the pipeline."
        )


if __name__ == "__main__":
    main()
