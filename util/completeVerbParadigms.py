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
# PhoneticTheory.pickle when present), resources/verbiste/*, and
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
from typing import Any
import argparse
import gc
import os
import pickle
import resource
from contextlib import contextmanager
from collections import Counter
from collections.abc import Callable
from typing import Iterator

from src.featureextractor import buildDiscriminatorSelection, extractDiscriminatingFeatures
from src.keyboard import Starboard, Strokes
from dataclasses import dataclass, field
from src.verbparadigm import (
    ConjugationEndingTables,
    ConjugationTemplate,
    ParticipleEndingTables,
    UndersampledLemma,
    allFiniteSlots,
    attestedInfinitiveWordByLemme,
    deriveConjugationEndingTables,
    deriveParticipleEndingTables,
    deriveParticiplePresentTables,
    deriveSlotBorrowIndex,
    detectUndersampledLemmas,
    getTrustedTemplate,
    generateMissingConjugatedForm,
    generateBorrowedForm,
    generateMissingParticiple,
    generateOrthoForm,
    generateParticipleFromInfinitive,
    generateParticiplePresent,
    infinitiveRadical,
    lemmeOfVerbLemmeGramCat,
    loadVerbisteTemplates,
    reinsertLostNasalUnit,
    repairLostNasalInfinitive,
    loadVerbModelExceptions,
    newlyCollidingLemmas,
    parseConjugationTemplates,
    pseudoInfinitive,
)
from src.synthrules import UNVALIDATED_MODES, isRuleActive, loadDecisionsIfPresent, parseForcedRules
from src.word import GramCat, Lemme, LemmeGramCat, Word
from util._pronunciation import compare
from util._verbreferences import VerbReferences, loadVerbReferences

VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
THEORY_CACHE_PATH = "PhoneticTheory.pickle"
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

BAR_REJECTIONS_PATH = "synthetic_bar_rejections.tsv"
BAR_REJECTIONS_HEADER = "lemme\tortho\ttag\tours\trefs\tstatus\ttemplate\trate\tmechanism\n"

SYNTHETIC_HEADER = (
    "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\t"
    "syll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2\tsource\n"
)

# (lemme, slot, reason): a missing slot the generator could not fill. The slots are the census names (`ind:pre:3s`,
# `par:pas:fs`); `finite:*` stands for every finite slot of a lemma and `par:pas:*` for every participle.
SkipReason = tuple[str, str, str]
SKIP_REASONS_PATH = "synthetic_skip_reasons.tsv"
SKIP_REASONS_HEADER = "lemme\ttag\treason\n"
SKIP_REASONS = (
    "no_majority_above_floor", "splice_rejected", "reference_differs", "no_reference", "unattested_ending",
    "homograph_tag", "lost_nasal", "no_participle_donor", "no_infinitive", "below_bar", "infinitive_outlier", "no_source_form", "other",
)
INFINITIVE_PRESENT_RULE = "infinitive-participle-present"
GLIDE_FUTURE_RULE = "glide-future-stem"

Candidate = tuple[LemmeGramCat, UndersampledLemma, Word, Word]  # (..., generated, referenceWord)


class ReferenceBar:
    """
    The reference-validated agreement bar (rule `reference-bar`, src/synthrules.py): `floor` is the lowest majority-ending
    rate a below-bar finite slot may be built from, and `validate` (a FiniteValidator) accepts a candidate only when its
    phonology is `exact` or `equivalent` (util._pronunciation.compare) to the references of (lemme, ortho, tag) --
    the exact slot (RefSet.preferred when the two sources conflict, else all variants), else the checker's
    lemma-and-tag match. No reference, or `differs`: refused, and the first refused attempt of the slot is kept in
    `rejections` unless a later competing ending of the slot is accepted.
    """

    def __init__(self, references: VerbReferences, floor: float) -> None:
        self.references = references
        self.floor = floor
        self.attempts: dict[tuple[str, str, str], tuple[str, str, str, str, float]] = {}
        self.acceptedByRank: Counter[int] = Counter()

    def referencesOf(self, word: Word) -> set[str]:
        tags = [tag for tag in (word.infoVerb or "").split(";") if tag]
        exact = self.references.forRow(word.lemme, word.ortho, tags)
        if exact is not None:
            return set(exact.preferred if exact.conflict else exact.variants)
        matched = self.references.matchRow(word.lemme, tags)
        return set(matched[1]) if matched is not None else set()

    def validate(self, word: Word, tableTemplate: str, rank: int, rate: float) -> bool:
        tag = (word.infoVerb or "").rstrip(";")
        slot = (word.lemme, word.ortho, tag)
        refs = self.referencesOf(word)
        status = compare(word.phonology, refs)[0] if refs else "no-reference"
        if status in ("exact", "equivalent"):
            self.attempts.pop(slot, None)
            self.acceptedByRank[rank] += 1
            return True
        self.attempts.setdefault(slot, (word.phonology, "|".join(sorted(refs)), status, tableTemplate, rate))
        return False

    def rejections(self) -> list[tuple[str, str, str, str, str, str, str, float]]:
        """(lemme, ortho, tag, ours, refs, status, template, rate), sorted."""
        return sorted(
            (lemme, ortho, tag, *attempt) for (lemme, ortho, tag), attempt in self.attempts.items()
        )

    def rejectionLines(self) -> list[str]:
        """The rows of synthetic_bar_rejections.tsv: the rejections, mechanism `reference-bar`."""
        return ["\t".join(row[:-1]) + f"\t{row[-1]:.3f}\treference-bar\n" for row in self.rejections()]

    def summary(self) -> str:
        byStatus = Counter(attempt[2] for attempt in self.attempts.values())
        accepted = ", ".join(f"rank {rank}: {count}" for rank, count in sorted(self.acceptedByRank.items())) or "none"
        return (f"reference-bar (floor {self.floor}): accepted {sum(self.acceptedByRank.values())} ({accepted}); "
                f"rejected by reference {len(self.attempts)} ({dict(sorted(byStatus.items()))})")


OK_STATUSES = ("exact", "equivalent")
NO_REFERENCE = "no-reference"


class ReferenceJudge:
    """
    The reference comparison of the mechanisms other than the bar (T3.2-T3.6): `check` gives the status of a candidate's
    phonology against the references of its (lemme, ortho, tag) slot (exact / equivalent / differs / no-reference, as
    util._pronunciation.compare), `accept` and `reject` count the verdicts per mechanism and keep the first refusal of a
    slot for the rejection file (a column `mechanism`).
    """

    def __init__(self, references: VerbReferences) -> None:
        self.references = references
        self.accepted: Counter[str] = Counter()
        self.unvalidated: Counter[str] = Counter()
        self.refused: Counter[tuple[str, str]] = Counter()
        self.attempts: dict[tuple[str, str, str, str], tuple[str, str, str, str, float]] = {}

    def referencesOf(self, lemme: str, ortho: str, tag: str) -> set[str]:
        exact = self.references.forRow(lemme, ortho, [tag]) or self.references.forOrtho(lemme, ortho)
        if exact is None:
            return set()
        return set(exact.preferred if exact.conflict else exact.variants)

    def check(self, word: Word, tag: str) -> tuple[str, set[str]]:
        refs = self.referencesOf(word.lemme, word.ortho, tag)
        return (compare(word.phonology, refs)[0] if refs else NO_REFERENCE), refs

    def accept(self, mechanism: str, unvalidated: bool = False) -> None:
        self.accepted[mechanism] += 1
        if unvalidated:
            self.unvalidated[mechanism] += 1
        # a slot accepted after an earlier refusal of the same mechanism (another ending, another donor) is no rejection

    def reject(self, mechanism: str, word: Word, tag: str, status: str, refs: set[str], detail: str, rate: float) -> None:
        self.refused[(mechanism, status)] += 1
        self.attempts.setdefault((mechanism, word.lemme, word.ortho, tag),
                                 (word.phonology, "|".join(sorted(refs)), status, detail, rate))

    def forgive(self, mechanism: str, word: Word, tag: str) -> None:
        self.attempts.pop((mechanism, word.lemme, word.ortho, tag), None)

    def rejectionLines(self) -> list[str]:
        return [f"{lemme}\t{ortho}\t{tag}\t{ours}\t{refs}\t{status}\t{detail}\t{rate:.3f}\t{mechanism}\n"
                for (mechanism, lemme, ortho, tag), (ours, refs, status, detail, rate) in sorted(self.attempts.items())]

    def summary(self) -> str:
        parts = []
        for mechanism in sorted({m for m in self.accepted} | {m for m, _s in self.refused}):
            refusals = {status: n for (m, status), n in sorted(self.refused.items()) if m == mechanism}
            parts.append(f"{mechanism}: accepted {self.accepted[mechanism]} (unvalidated {self.unvalidated[mechanism]}), "
                         f"refused {refusals}")
        return "; ".join(parts) or "no mechanism ran"


@dataclass
class Mechanisms:
    """The synthesis mechanisms of src/synthrules.py beyond the reference bar that are active in this run (all off by
    default: the generator then behaves as before). `participle` and `homograph` hold their mode ("strict" or
    "unvalidated"), None when off."""
    judge: ReferenceJudge | None = None
    participle: str | None = None
    lostNasal: bool = False
    homograph: str | None = None
    slotMap: bool = False
    infinitivePresent: bool = False
    glideFutureStem: bool = False

    def anyActive(self) -> bool:
        return (self.participle is not None or self.lostNasal or self.homograph is not None or self.slotMap
                or self.infinitivePresent or self.glideFutureStem)

    def accepts(self, mechanism: str, word: Word, tag: str, mode: str | None, plain: bool = True, rate: float = 1.0,
                detail: str = "") -> bool:
        """Judge `word` against the references: exact or equivalent is accepted; no reference only in `unvalidated` mode and
        when the evidence is `plain`; anything else is refused and logged."""
        assert self.judge is not None
        status, refs = self.judge.check(word, tag)
        if status in OK_STATUSES:
            self.judge.accept(mechanism)
            self.judge.forgive(mechanism, word, tag)
            return True
        if status == NO_REFERENCE and mode == "unvalidated" and plain:
            self.judge.accept(mechanism, unvalidated=True)
            self.judge.forgive(mechanism, word, tag)
            return True
        self.judge.reject(mechanism, word, tag, status, refs, detail, rate)
        return False


def buildMechanisms(forceSpecs: list[str], references: VerbReferences | None = None) -> Mechanisms:
    """The active mechanisms (accepted decision or forced); loads the references (GLÀFF required) when one runs."""
    forced = parseForcedRules(forceSpecs)
    decisions = loadDecisionsIfPresent()
    active: dict[str, str] = {}
    for name in ("participle-from-infinitive", "lost-nasal", "homograph-tag", "slot-map", INFINITIVE_PRESENT_RULE,
                 GLIDE_FUTURE_RULE):
        isActive, param = isRuleActive(name, decisions, forced)
        if isActive:
            active[name] = param
    if not active:
        return Mechanisms()
    for name in ("participle-from-infinitive", "homograph-tag"):
        if name in active and active[name] not in UNVALIDATED_MODES:
            raise ValueError(f"{name} takes one of {UNVALIDATED_MODES}, got {active[name]!r}")
    judge = ReferenceJudge(references if references is not None else loadVerbReferences(requireGlaff=True))
    return Mechanisms(
        judge=judge, participle=active.get("participle-from-infinitive"), lostNasal="lost-nasal" in active,
        homograph=active.get("homograph-tag"), slotMap="slot-map" in active,
        infinitivePresent=INFINITIVE_PRESENT_RULE in active, glideFutureStem=GLIDE_FUTURE_RULE in active)


def buildReferenceBar(forceSpecs: list[str], references: VerbReferences | None = None) -> ReferenceBar | None:
    """The bar when the `reference-bar` rule is active (accepted decision, or forced), else None. Needs GLÀFF."""
    active, param = isRuleActive("reference-bar", loadDecisionsIfPresent(), parseForcedRules(forceSpecs))
    if not active:
        return None
    floor = float(param)
    if not 0.0 < floor <= 1.0:
        raise ValueError(f"reference-bar floor must be in (0, 1], got {param!r}")
    return ReferenceBar(references if references is not None else loadVerbReferences(requireGlaff=True), floor)


def classifySkip(engineReason: str, referenceStatus: str | None, losesNasal: bool, isHomograph: bool) -> str:
    """The SKIP_REASONS cause of a finite slot generateMissingConjugatedForm refused with `engineReason`:
    lost_nasal (the infinitive lost an n/m unit) and homograph_tag (the spelling is an attested row of the lemma)
    outrank the engine's own reason; validation_failed splits by the reference status of the first refused attempt."""
    if losesNasal:
        return "lost_nasal"
    if isHomograph:
        return "homograph_tag"
    if engineReason == "validation_failed":
        return "no_reference" if referenceStatus == "no-reference" else "reference_differs"
    if engineReason in SKIP_REASONS:
        return engineReason
    if engineReason in ("unattested_ending", "radical_too_short", "no_template_ortho"):
        return "unattested_ending" if engineReason == "unattested_ending" else "other"
    return "other"


def writeSkipReasons(path: str, skipLog: list[SkipReason]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as out:
        out.write(SKIP_REASONS_HEADER)
        for row in sorted(set(skipLog)):
            out.write("\t".join(row) + "\n")


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
    # buildPhoneticTheory reads dictionary.syllableCollection, which only
    # analyseSyllabification() populates -- dictionary.py's own __main__
    # always runs it (or unpickles the post-analysis state) before ever
    # calling buildPhoneticTheory. Skipping it here reproduces a KeyError in
    # buildPhoneticTheory (self.syllableCollection.syllable_names[syllableName]) the
    # first time this runs without a cached PhoneticTheory.pickle.
    dictionary.analyseSyllabification()
    Syllable.optimizeBiphonemeOrder()
    return dictionary.buildPhoneticTheory(starboard), starboard


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


def allTemplatedVerbLemmas(
    theory: dict[Strokes, list[Word]],
    verbisteTemplates: dict[Lemme, str],
    exceptions: dict[Any, Any],
) -> dict[LemmeGramCat, UndersampledLemma]:
    """
    Every VER lemma of the theory with a trusted conjugation template, whether or not its
    missing forms would change a discriminator: the lexicon wants full conjugations (the
    phonetics must be in the theory for a form to be typable). Same shape as
    detectUndersampledLemmas' result, with no missing features or siblings.
    """
    result: dict[LemmeGramCat, UndersampledLemma] = {}
    for words in theory.values():
        for word in words:
            if word.gramCat != GramCat.VER or word.lemmeGramCat in result:
                continue
            template = getTrustedTemplate(word.lemme, verbisteTemplates, exceptions)
            if template is not None:
                result[word.lemmeGramCat] = UndersampledLemma(
                    lemmeGramCat=word.lemmeGramCat, template=template,
                    missingFeatures=frozenset(), siblingLemmeGramCats=frozenset(),
                )
    return result


def attestedPresentParticipleByLemme(theory: dict[Strokes, list[Word]]) -> dict[Lemme, Word]:
    """lemma -> its attested present participle row (infover `par:pre`; the first in the theory's order)."""
    result: dict[Lemme, Word] = {}
    for words in theory.values():
        for word in words:
            if word.gramCat in (GramCat.VER, GramCat.AUX) and word.infoVerb is not None:
                tags = word.infoVerb.split(";")
                if "par:pre" in tags and "inf" not in tags:
                    result.setdefault(word.lemme, word)
    return result


def addPresentParticiple(
    lemmeGramCat: LemmeGramCat, info: UndersampledLemma, lemme: Lemme, template: ConjugationTemplate,
    source: Word | None, reference: Word | None, presentTables: ParticipleEndingTables,
    endingTables: ConjugationEndingTables, attestedOrthos: set[str], mech: Mechanisms,
    candidates: list[Candidate], noteSkip: Callable[[Lemme, str, str], None],
) -> None:
    """Rule `infinitive-participle-present`: the `par:pre` row of a lemma that has none, built from `source` (its attested or
    derived infinitive) and judged against the references (strict)."""
    if source is None or reference is None:
        noteSkip(lemme, "par:pre", "no_infinitive")
        return
    engineReasons: list[str] = []
    built = generateParticiplePresent(lemme, template, source, presentTables, endingTables, engineReasons.append)
    if built is None:
        reason = engineReasons[-1] if engineReasons else "other"
        noteSkip(lemme, "par:pre", reason if reason in SKIP_REASONS else "other")
        return
    if built.word.ortho in attestedOrthos:
        noteSkip(lemme, "par:pre", "homograph_tag")
        return
    if not mech.accepts(INFINITIVE_PRESENT_RULE, built.word, "par:pre", "strict", plain=built.plain, rate=built.rate,
                        detail=f"donors={built.donors}"):
        assert mech.judge is not None
        noteSkip(lemme, "par:pre", "no_reference" if mech.judge.check(built.word, "par:pre")[0] == NO_REFERENCE
                 else "reference_differs")
        return
    candidates.append((lemmeGramCat, info, built.word, reference))


def findStructuralCandidates(
    strokeLemmeDiscriminators: dict[Any, Any],
    theory: dict[Strokes, list[Word]],
    verbisteTemplates: dict[Lemme, str],
    exceptions: dict[Any, Any],
    conjugationTemplates: dict[Any, Any],
    endingTables: ConjugationEndingTables,
    minFiniteMatchRate: float = MIN_FINITE_MATCH_RATE,
    fullParadigms: bool = True,
    referenceBar: ReferenceBar | None = None,
    skipLog: list[SkipReason] | None = None,
    mechanisms: Mechanisms | None = None,
) -> tuple[list[Candidate], list[tuple[Lemme, str]]]:
    """
    Stage 3 (undersampling detection; every templated lemma when fullParadigms) + Stage 4 (orthography/phonology
    generation) only -- no collision filtering yet. Every generated
    candidate is paired with the attested reference Word its phonology was
    spliced from, so its Strokes can be found by simple lookup instead of
    recomputed. Covers both past-participle gender/number slots
    (generateMissingParticiple) and finite conjugation slots
    (generateMissingConjugatedForm, gated by minFiniteMatchRate; below it, by the reference-validated
    agreement bar when `referenceBar` is given).

    `mechanisms` (src/synthrules.py rules beyond the bar, all off when None) adds, in this order for a lemma:
    `participle-from-infinitive` (a lemma with no attested participle gets one built from its infinitive), `lost-nasal`
    (the infinitive of an en-/em- verb gets its n unit back before splicing), `homograph-tag` (a finite slot spelled like
    an attested row of the lemma copies that row's phonology). Each candidate they make is judged against the references.

    `skipLog`, when given, receives a (lemme, slot, reason) per missing slot the generator could not fill, with the
    reasons of SKIP_REASONS (the finite ones classified by classifySkip), for synthetic_skip_reasons.tsv.
    """
    def noteSkip(lemme: Lemme, slot: str, reason: str) -> None:
        if skipLog is not None:
            skipLog.append((lemme, slot, reason))

    mech = mechanisms if mechanisms is not None else Mechanisms()
    if fullParadigms:
        undersampled = allTemplatedVerbLemmas(theory, verbisteTemplates, exceptions)
    else:
        undersampled = detectUndersampledLemmas(strokeLemmeDiscriminators, verbisteTemplates, exceptions)
    participleForms = attestedParticipleFormsByLemme(theory)
    finiteForms = attestedFiniteFormsByLemme(theory)
    infinitiveWords = attestedInfinitiveWordByLemme(theory)
    corpusTheory = {strokes: [w for w in words if w.frequencyBook > 0 or w.frequencyFilm > 0] for strokes, words in theory.items()}
    participleTables = (
        deriveParticipleEndingTables(corpusTheory, verbisteTemplates, exceptions, endingTables)
        if mech.participle is not None or mech.slotMap or mech.infinitivePresent else None)
    presentTables = (
        deriveParticiplePresentTables(corpusTheory, verbisteTemplates, exceptions, endingTables)
        if mech.infinitivePresent else None)
    del corpusTheory
    presentParticiples = attestedPresentParticipleByLemme(theory) if mech.infinitivePresent else {}

    borrowIndex = deriveSlotBorrowIndex(endingTables) if mech.slotMap else None

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

        infinitiveWord = infinitiveWords.get(lemme)
        referenceInfinitive = infinitiveWord  # the attested Word the candidates are paired with (the donor form of a pseudo-infinitive)
        pseudoDerived = False
        presentSource, presentReference = infinitiveWord, infinitiveWord  # what rule `infinitive-participle-present` builds par:pre from
        if infinitiveWord is None and (mech.slotMap or mech.infinitivePresent):
            # rules `slot-map` and `infinitive-participle-present`: no attested infinitive, so derive one from another form of
            # the lemma, if the references agree. The first rule that is on owns the row (no duplicate); only `slot-map` also
            # lets the finite forms follow in this round, the other waits for the next round, where the row is attested.
            ruleName = "slot-map" if mech.slotMap else INFINITIVE_PRESENT_RULE
            infinitiveReason = "no_source_form"
            for pseudo, donorForm in pseudoInfinitive(
                    lemme, template, finiteForms.get(lemme, {}), endingTables, participleForms.get(lemme),
                    participleTables, presentParticiples.get(lemme), presentTables):
                if mech.accepts(ruleName, pseudo, "inf", "strict", detail=f"pseudo-infinitive from {donorForm.ortho}"):
                    if mech.slotMap:
                        infinitiveWord, referenceInfinitive, pseudoDerived = pseudo, donorForm, True
                    presentSource, presentReference = pseudo, donorForm
                    candidates.append((lemmeGramCat, info, pseudo, donorForm))
                    infinitiveReason = ""
                    break
                assert mech.judge is not None
                infinitiveReason = "no_reference" if mech.judge.check(pseudo, "inf")[0] == NO_REFERENCE else "reference_differs"
            if infinitiveReason:
                noteSkip(lemme, "inf", infinitiveReason)
        if mech.infinitivePresent and presentTables is not None and lemme not in presentParticiples:
            addPresentParticiple(
                lemmeGramCat, info, lemme, template, presentSource, presentReference, presentTables, endingTables,
                {word.ortho for word in [*participleForms.get(lemme, {}).values(), *finiteForms.get(lemme, {}).values()]},
                mech, candidates, noteSkip)
        repaired = repairLostNasalInfinitive(infinitiveWord) if infinitiveWord is not None else None
        donorInfinitive = repaired if (repaired is not None and mech.lostNasal) else infinitiveWord
        attestedSlots = participleForms.get(lemme, {})
        attestedByOrtho: dict[str, list[Word]] = {}
        for attestedWord in [*attestedSlots.values(), *finiteForms.get(lemme, {}).values()]:
            attestedByOrtho.setdefault(attestedWord.ortho, []).append(attestedWord)
        if attestedSlots:
            for gender, number in GENDER_NUMBER_SLOTS:
                if (gender, number) in attestedSlots:
                    continue
                # A same-gender participle shares the slot's phon outright; only
                # a cross-gender one needs spliceParticiplePhon's consonant rule.
                referenceWord = next(
                    (word for (wordGender, _n), word in attestedSlots.items() if wordGender == gender),
                    next(iter(attestedSlots.values())),
                )
                try:
                    generated = generateMissingParticiple(lemme, template, referenceWord, gender, number)
                except ValueError as error:
                    skipped.append((lemme, str(error)))
                    noteSkip(lemme, f"par:pas:{gender}{number}", "splice_rejected")
                    continue
                if generated.ortho in {word.ortho for word in attestedSlots.values()}:
                    noteSkip(lemme, f"par:pas:{gender}{number}", "homograph_tag")
                    # Homographic slot (dissous m_s/m_p): the dictionary loader keeps one Word for
                    # both, so the slot would never look attested and be re-appended every round.
                    continue
                if mech.participle is not None and referenceWord.frequencyBook == 0 and referenceWord.frequencyFilm == 0:
                    # the donor is a participle this rule synthesized in an earlier round: its siblings meet the same bar
                    if not mech.accepts("participle-from-infinitive", generated, f"par:pas:{gender}{number}",
                                        mech.participle, plain=False):
                        noteSkip(lemme, f"par:pas:{gender}{number}", "reference_differs")
                        continue
                candidates.append((lemmeGramCat, info, generated, referenceWord))
        else:
            skipped.append((lemme, "no attested past-participle form to splice phonology from"))
            built = None
            if mech.participle is not None and participleTables is not None and donorInfinitive is not None:
                engineReasons: list[str] = []
                built = generateParticipleFromInfinitive(
                    lemme, template, donorInfinitive, participleTables, endingTables, engineReasons.append)
                if built is None:
                    noteSkip(lemme, "par:pas:*", engineReasons[-1] if engineReasons else "other")
            else:
                noteSkip(lemme, "par:pas:*", "no_participle_donor")
            if built is not None and infinitiveWord is not None:
                for gender, number in GENDER_NUMBER_SLOTS:
                    slotName = f"par:pas:{gender}{number}"
                    if (gender, number) == ("m", "s"):
                        generated = built.word
                    else:
                        try:
                            generated = generateMissingParticiple(lemme, template, built.word, gender, number)
                        except ValueError:
                            noteSkip(lemme, slotName, "splice_rejected")
                            continue
                        if generated.ortho == built.word.ortho:
                            noteSkip(lemme, slotName, "homograph_tag")
                            continue
                    if not mech.accepts("participle-from-infinitive", generated, slotName, mech.participle,
                                        plain=built.plain, rate=built.rate, detail=f"donors={built.donors}"):
                        assert mech.judge is not None
                        status = mech.judge.check(generated, slotName)[0]
                        noteSkip(lemme, slotName, "no_reference" if status == NO_REFERENCE else "reference_differs")
                        continue
                    candidates.append((lemmeGramCat, info, generated, referenceInfinitive or infinitiveWord))

        if infinitiveWord is None or donorInfinitive is None:
            skipped.append((lemme, "no attested infinitive to derive finite conjugation radicals from"))
            noteSkip(lemme, "finite:*", "no_infinitive")
            continue
        losesNasal = repaired is not None and not mech.lostNasal
        attestedFinite = finiteForms.get(lemme, {})
        for code, personNumber in allFiniteSlots(template):
            if (code, personNumber) in attestedFinite:
                continue
            slotName = f"{code}:{personNumber}"
            slotOrtho = generateOrthoForm(
                infinitiveRadical(lemme, template), template, code, personNumber=personNumber)
            generatedFinite = None
            judged = False  # a mechanism has already judged the form against the references
            if repaired is not None and mech.lostNasal:
                viaRepair = generateMissingConjugatedForm(
                    lemme, template, repaired, code, personNumber, endingTables,
                    minMatchRate=minFiniteMatchRate,
                    barFloor=referenceBar.floor if referenceBar is not None else None,
                    validate=referenceBar.validate if referenceBar is not None else None,
                    glideFutureStem=mech.glideFutureStem,
                )
                if viaRepair is not None and mech.accepts("lost-nasal", viaRepair, slotName, "strict"):
                    generatedFinite, judged = viaRepair, True
            engineReasons = []
            if generatedFinite is None:
                generatedFinite = generateMissingConjugatedForm(
                    lemme, template, infinitiveWord, code, personNumber, endingTables,
                    minMatchRate=minFiniteMatchRate,
                    barFloor=referenceBar.floor if referenceBar is not None else None,
                    validate=referenceBar.validate if referenceBar is not None else None,
                    onSkip=engineReasons.append,
                    glideFutureStem=mech.glideFutureStem,
                )
            if generatedFinite is None and mech.homograph is not None and slotOrtho in attestedByOrtho:
                generatedFinite = copyHomographRow(lemme, code, personNumber, attestedByOrtho[slotOrtho], mech)
                judged = generatedFinite is not None
            if generatedFinite is None and borrowIndex is not None:
                def validateBorrowed(word: Word, tableTemplate: str, rank: int, rate: float, slot: str = slotName) -> bool:
                    return mech.accepts("slot-map", word, slot, "strict", rate=rate, detail=f"borrowed rank {rank} {tableTemplate}")
                generatedFinite = generateBorrowedForm(
                    lemme, template, infinitiveWord, code, personNumber, endingTables, borrowIndex, validateBorrowed)
                judged = generatedFinite is not None
            if generatedFinite is not None and pseudoDerived and not judged and not mech.accepts(
                    "slot-map", generatedFinite, slotName, "strict", detail="from a pseudo-infinitive"):
                generatedFinite = None
            if generatedFinite is None:
                attempt = referenceBar.attempts.get((lemme, slotOrtho, slotName)) if referenceBar and slotOrtho else None
                noteSkip(lemme, slotName, classifySkip(
                    engineReasons[-1] if engineReasons else "other", attempt[2] if attempt else None,
                    losesNasal, slotOrtho in attestedByOrtho))
                skipped.append((
                    lemme,
                    f"{code}:{personNumber} has no template ending or no confident-enough "
                    "empirical phonology for template " + template.name,
                ))
                continue
            candidates.append((lemmeGramCat, info, generatedFinite, referenceInfinitive or infinitiveWord))
    return candidates, skipped


def copyHomographRow(
    lemme: Lemme, code: str, personNumber: str, carriers: list[Word], mech: Mechanisms,
) -> Word | None:
    """
    Rule `homograph-tag`: the finite slot `code`:`personNumber` is spelled like attested rows of the lemma (`regrées`,
    sub:pre:2s, beside ind:pre:2s): the same spelling of a lemma is pronounced and broken down the same way, so the slot
    takes the row's phonology and breakdowns under its own tag. None when the carriers disagree on them, or when the copy
    is refused by the references (`strict`: exact or equivalent; `unvalidated`: also no reference).
    """
    breakdowns = sorted({(word.phonology, word.rawSyllCV, word.rawOrthosyllCV) for word in carriers})
    if len(breakdowns) != 1:
        return None
    carrier = min(carriers, key=lambda word: word.infoVerb or "")
    copy = Word(
        ortho=carrier.ortho, phonology=carrier.phonology, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=None, number=None, infoVerb=f"{code}:{personNumber};",
        rawSyllCV=carrier.rawSyllCV, rawOrthosyllCV=carrier.rawOrthosyllCV,
        frequencyBook=0.0, frequencyFilm=0.0,
    )
    if mech.accepts("homograph-tag", copy, f"{code}:{personNumber}", mech.homograph):
        return copy
    return None


@contextmanager
def temporarilyAugmented(
    theory: dict[Strokes, list[Word]], candidates: list[Candidate]
) -> Iterator[dict[Strokes, list[Word]]]:
    """
    Temporarily appends each candidate's generated Word into its reference
    word's existing stroke group (an approximation: the reference word is an
    already-attested word of the same lemma, so its stroke group always
    already exists -- never a brand new key -- but a finite form's or a
    cross-gender participle's own phon can differ from it), then removes them
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
    baselineFeaturesetWords: dict[Any, Any],
    onlyColliding: bool = False,
) -> tuple[list[Candidate], list[tuple[Lemme, str]]]:
    """
    By default keeps every candidate: a valid form of a real verb belongs in the
    lexicon whether or not it helps discriminator selection (the filtered-out ones
    were otherwise missing words, e.g. every finite form of confédérer).
    With onlyColliding (--only-colliding), keeps only the candidates that actually
    cause a NEW cross-lemma "conflicting feature set" collision when added -- the
    mechanism behind the design plan's motivating bug (see module docstring), which
    leaves out the lemmas the current discriminator selection no longer needs.
    """
    if not candidates:
        return [], []
    if not onlyColliding:
        return list(candidates), []

    with temporarilyAugmented(theory, candidates):
        augmentedDiscBy, _augmentedOrdered, _ = extractDiscriminatingFeatures(theory)
        augmentedFeaturesetWords = buildDiscriminatorSelection(theory, augmentedDiscBy)
        del augmentedDiscBy
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
    print(f"Undersampled VER lemmas with confirmed candidates: {len(flaggedLemmas)}")
    print(f"Candidate rows confirmed: {len(candidates)}")
    print(f"Lemmas/candidates skipped (see reasons): {len(skippedLemmas)}")
    for lemme, reason in skipped[:20]:
        print(f"  {lemme}: {reason}")
    if len(skippedLemmas) > 20:
        print(f"  ... and {len(skippedLemmas) - 20} more")


def writeSynthetic(path: str, candidates: list[Candidate]) -> int:
    fileExists = os.path.exists(path)
    written = 0
    # A row the dictionary loader drops stays invisible in the theory (varias, a form of varier that the spelling
    # variants of `varia` drop once the Synthetic file carries varier's own `varia`), so the generator proposes
    # it again every round: never append a line the file already has, or the rounds never converge.
    existing: set[str] = set()
    if fileExists:
        with open(path, encoding="utf-8", newline="") as syntheticRead:
            existing = {line.rstrip("\r\n") for line in syntheticRead}
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
            line = "\t".join(fields)
            if line in existing:
                continue
            existing.add(line)
            syntheticFile.write(line + "\n")
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
    parser.add_argument(
        "--only-colliding", action="store_true",
        help="Keep only the candidates whose lemma newly collides in discriminator-feature "
        "space (the historical filter; default: keep every generated candidate).",
    )
    parser.add_argument(
        "--undersampled-only", action="store_true",
        help="Complete only the lemmas whose discriminator features are a strict subset of their template "
        "siblings' (the historical detection; default: complete every templated verb).",
    )
    parser.add_argument(
        "--force-rule", action="append", default=[], metavar="NAME[=PARAM]",
        help="Run a lexicon-decision synthesis mechanism (src/synthrules.py) without an accepted decision, e.g. "
        "reference-bar, reference-bar=0.6, participle-from-infinitive=unvalidated, lost-nasal, homograph-tag, slot-map, infinitive-participle-present "
        "(default: only the accepted decisions of resources/lexiconDecisions.tsv).",
    )
    args = parser.parse_args()
    references: VerbReferences | None = None
    mechanisms = buildMechanisms(args.force_rule)
    if mechanisms.judge is not None:
        references = mechanisms.judge.references
    referenceBar = buildReferenceBar(args.force_rule, references)

    print("Loading theory (uses PhoneticTheory.pickle if present)...")
    theory, _starboard = loadTheoryAndKeyboard()

    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)

    baselineDiscBy, baselineOrdered, strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)

    endingTables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
    if endingTables.infinitiveOutliers:
        print(f"{len(endingTables.infinitiveOutliers)} infinitive outliers kept out of the ending tables "
              f"(sample: {', '.join(sorted(endingTables.infinitiveOutliers)[:10])})")

    skipLog: list[SkipReason] = []
    structuralCandidates, structuralSkipped = findStructuralCandidates(
        strokeLemmeDiscriminators, theory, verbisteTemplates, exceptions, conjugationTemplates,
        endingTables, fullParadigms=not args.undersampled_only,
        referenceBar=referenceBar, skipLog=skipLog, mechanisms=mechanisms,
    )
    writeSkipReasons(SKIP_REASONS_PATH, skipLog)
    if referenceBar is not None or mechanisms.judge is not None:
        with open(BAR_REJECTIONS_PATH, "w", encoding="utf-8", newline="") as rejectionsFile:
            rejectionsFile.write(BAR_REJECTIONS_HEADER)
            rejectionsFile.writelines((referenceBar.rejectionLines() if referenceBar is not None else [])
                                      + (mechanisms.judge.rejectionLines() if mechanisms.judge is not None else []))
        if referenceBar is not None:
            print(referenceBar.summary())
        if mechanisms.judge is not None:
            print(mechanisms.judge.summary())
        print(f"rejections in {BAR_REJECTIONS_PATH}")
    # Reduce down to the (much smaller) featuresetWords structure and drop
    # the full-corpus extraction results before the augmented pass builds its
    # own copy of them -- never hold two of these at once (see
    # temporarilyAugmented's docstring for why this matters).
    baselineFeaturesetWords = buildDiscriminatorSelection(theory, baselineDiscBy)
    del baselineDiscBy, baselineOrdered, strokeLemmeDiscriminators
    gc.collect()

    confirmedCandidates, collisionSkipped = confirmCandidates(
        structuralCandidates, theory, baselineFeaturesetWords, args.only_colliding
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
