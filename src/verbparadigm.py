#!/usr/bin/python
# coding: utf-8
#
"""
Stages 3-4 of the undersampling-aware paradigm completion plan.

Stage 3: detect verb lemmas whose attested homophone-discriminating feature
space is a strict subset of their conjugation model's canonical space, i.e.
lemmas that are missing conjugated forms other verbs following the same model
have attested (detectUndersampledLemmas). This only performs the structural
"is this lemma's feature space undersampled relative to its siblings"
comparison (design plan Stage 3, first half) -- it deliberately does NOT
implement the "is the missing form actually a real homophone collision" filter
(Stage 3's second half), which requires synthesizing the missing form's
phonology first.

Stage 4: generate the orthographic form for a missing conjugation slot by
applying a Verbiste conjugation template to a lemma's radical
(parseConjugationTemplates, generateOrthoForm). Phonology/syllable-breakdown
generation has two paths: past-participle gender/number forms reuse phonology
(spliceParticiplePhon, generateMissingParticiple), since number doesn't change a
participle's pronunciation and gender only adds or drops the consonant of a
consonant-final feminine stem ("promis"/"promise"); finite conjugation slots (mood,
tense, person/number) genuinely change pronunciation, so those are generated
from an empirically-derived per-template ending table instead
(deriveConjugationEndingTables, generateMissingConjugatedForm).
"""

import difflib
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.grammar import Phoneme
from src.keyboard import Strokes
from src.word import GramCat, Lemme, LemmeGramCat, Word, WordFeature

VERBISTE_TRUSTED_STATUSES = {"regular", "family_template"}


@dataclass(frozen=True)
class VerbModelException:
    lemme: Lemme
    template: str
    modelSibling: str
    status: str
    note: str


def loadVerbisteTemplates(xmlPath: str | Path) -> dict[Lemme, str]:
    """
    Parse a Verbiste verbs-*.xml file into a dict mapping each infinitive to its
    conjugation template id (e.g. "garnir" -> "fin:ir").
    """
    templates: dict[Lemme, str] = {}
    root = ET.parse(xmlPath).getroot()
    for verbElement in root.findall("v"):
        infinitiveElement = verbElement.find("i")
        templateElement = verbElement.find("t")
        if infinitiveElement is None or templateElement is None:
            continue
        infinitive = infinitiveElement.text
        template = templateElement.text
        if infinitive and template:
            templates[infinitive] = template
    return templates


def loadVerbModelExceptions(tsvPath: str | Path) -> dict[Lemme, VerbModelException]:
    """
    Parse resources/verbModelExceptions.tsv (comment lines starting with '#',
    a header row, then tab-separated lemme/template/model_sibling/status/note
    rows) into a dict keyed by lemme.
    """
    exceptions: dict[Lemme, VerbModelException] = {}
    with open(tsvPath, encoding="utf-8") as tsvFile:
        rows = [line.rstrip("\n") for line in tsvFile if not line.startswith("#")]
    if not rows:
        return exceptions
    for row in rows[1:]:  # skip header
        if not row.strip():
            continue
        fields = row.split("\t")
        fields += [""] * (5 - len(fields))
        lemme, template, modelSibling, status, note = fields[:5]
        exceptions[lemme] = VerbModelException(lemme, template, modelSibling, status, note)
    return exceptions


def getTrustedTemplate(
    lemme: Lemme,
    verbisteTemplates: dict[Lemme, str],
    exceptions: dict[Lemme, VerbModelException],
) -> str | None:
    """
    Return the conjugation template id for `lemme` if it can be trusted:
    Verbiste's own mapping is always trusted; a verbModelExceptions.tsv entry
    is only trusted when its status is "regular" or "family_template" (i.e.
    has been manually reviewed and confirmed) and it names a non-empty
    template.
    """
    if lemme in verbisteTemplates:
        return verbisteTemplates[lemme]
    exception = exceptions.get(lemme)
    if exception is not None and exception.status in VERBISTE_TRUSTED_STATUSES and exception.template:
        return exception.template
    return None


def lemmeOfVerbLemmeGramCat(lemmeGramCat: LemmeGramCat) -> Lemme | None:
    """
    Extract the plain lemma from a "lemme_GramCat" key, only for verbs
    (see Word.lemmeGramCat / GramCat.VER). Returns None for non-verb entries.
    """
    suffix = f"_{GramCat.VER.name}"
    if not lemmeGramCat.endswith(suffix):
        return None
    return lemmeGramCat[: -len(suffix)]


def fullFeatureSpace(
    strokeLemmeDiscriminators: dict[tuple[Strokes, LemmeGramCat], dict[Word, list[WordFeature]]],
    lemmeGramCat: LemmeGramCat,
) -> set[WordFeature]:
    """
    fullSpace(lemme) as defined in the design plan: the union, across every
    homophone group and every word of that lemme, of every feature that
    discriminates that word from its homophones sharing the same lemme.
    """
    space: set[WordFeature] = set()
    for (_strokes, groupLemme), wordFeatures in strokeLemmeDiscriminators.items():
        if groupLemme != lemmeGramCat:
            continue
        for features in wordFeatures.values():
            space.update(features)
    return space


@dataclass(frozen=True)
class UndersampledLemma:
    lemmeGramCat: LemmeGramCat
    template: str
    missingFeatures: frozenset[WordFeature]
    siblingLemmeGramCats: frozenset[LemmeGramCat]


MOOD_TAG_TO_CODE = {
    "Infinitif": "inf",
    "Indicatif": "ind",
    "Conditionnel": "cnd",
    "Subjonctif": "sub",
    "Imperatif": "imp",
    "Participe": "par",
}

TENSE_TAG_TO_CODE = {
    "infinitif-présent": "pre",
    "présent": "pre",
    "imparfait": "imp",
    "futur-simple": "fut",
    "passé-simple": "pas",
    "imperatif-présent": "pre",
    "participe-présent": "pre",
    "participe-passé": "pas",
}

# Position of each person/number within a 6-entry Indicatif/Conditionnel/Subjonctif
# list, and within a 3-entry Imperatif list -- confirmed against Verbiste's own
# fin:ir/ten:dre templates and cross-checked against attested LexiqueMixte rows.
FINITE_PERSON_INDEX = {"1s": 0, "2s": 1, "3s": 2, "1p": 3, "2p": 4, "3p": 5}
IMPERATIVE_PERSON_INDEX = {"2s": 0, "1p": 1, "2p": 2}
PARTICIPE_PASSE_INDEX = {("m", "s"): 0, ("m", "p"): 1, ("f", "s"): 2, ("f", "p"): 3}


@dataclass(frozen=True)
class ConjugationTemplate:
    name: str
    # forms["inf"] / forms["par:pre"] are single-element lists (no person/gender
    # variation); forms["par:pas"] is a 4-element [m_s, m_p, f_s, f_p] list;
    # every other key ("ind:pre", "cnd:pre", "imp:pre", ...) is a 6-element list
    # in [1s, 2s, 3s, 1p, 2p, 3p] order, except "imp:pre" (Imperatif) which is a
    # 3-element [2s, 1p, 2p] list. An entry is None when a defective/impersonal
    # verb's template (e.g. "adv:enir") doesn't define that person at all --
    # as opposed to "", a legitimate empty-string ending.
    forms: dict[str, list[str | None]]

    @property
    def infinitiveSuffix(self) -> str:
        suffix = self.forms["inf"][0]
        assert suffix is not None
        return suffix


def parseConjugationTemplates(xmlPath: str | Path) -> dict[str, ConjugationTemplate]:
    """
    Parse a Verbiste conjugation-*.xml file into a dict mapping each template
    id (e.g. "fin:ir") to its ConjugationTemplate.
    """
    templates: dict[str, ConjugationTemplate] = {}
    root = ET.parse(xmlPath).getroot()
    for templateElement in root.findall("template"):
        name = templateElement.get("name")
        if not name:
            continue
        forms: dict[str, list[str | None]] = {}
        for moodElement in templateElement:
            moodCode = MOOD_TAG_TO_CODE.get(moodElement.tag)
            if moodCode is None:
                continue
            for tenseElement in moodElement:
                tenseCode = TENSE_TAG_TO_CODE.get(tenseElement.tag)
                if tenseCode is None:
                    continue
                # Always append one entry per <p>, even when it has no <i>
                # child (a defective/impersonal verb's template, e.g.
                # "adv:enir" or "grêl:er", deliberately leaves most persons
                # empty) -- None marks "no such form", as opposed to a
                # legitimate empty-string ending. Skipping empty <p> entries
                # entirely (as this used to) silently shifts every later
                # person's index, so generateOrthoForm would look up the
                # wrong ending (or find none, when one genuinely exists).
                #
                # A <p><i></i></p> (an <i> element that exists but has no
                # text content, e.g. bat:tre/vêt:ir's 3s présent "il bat"/
                # "il vêt", or nui:re's par:pas m_s "nui") means a genuine
                # zero-length ending -- ElementTree gives back None for
                # .text on such an element, same as a <p> with no <i> at
                # all, so that case must be special-cased to "" rather than
                # falling through to the "no such form" None.
                endings: list[str | None] = []
                for inflectionElement in tenseElement.findall("p"):
                    infinitiveElement = inflectionElement.find("i")
                    if infinitiveElement is None:
                        endings.append(None)
                    else:
                        endings.append(infinitiveElement.text or "")
                code = moodCode if moodCode == "inf" else f"{moodCode}:{tenseCode}"
                forms[code] = endings
        templates[name] = ConjugationTemplate(name=name, forms=forms)
    return templates


def infinitiveRadical(infinitive: Lemme, template: ConjugationTemplate) -> str:
    """
    Strip the template's infinitive suffix off `infinitive` to get its radical
    (e.g. infinitiveRadical("regarnir", templates["fin:ir"]) == "regarn").
    """
    suffix = template.infinitiveSuffix
    if suffix and not infinitive.endswith(suffix):
        raise ValueError(
            f"{infinitive!r} does not end with template suffix {suffix!r}"
        )
    return infinitive[: len(infinitive) - len(suffix)] if suffix else infinitive


def generateOrthoForm(
    radical: str,
    template: ConjugationTemplate,
    code: str,
    personNumber: str | None = None,
    gender: str | None = None,
    number: str | None = None,
) -> str | None:
    """
    Generate the orthographic form for one conjugation slot by applying
    `template`'s ending for that slot to `radical`. Returns None when the slot
    doesn't exist for this template (e.g. a defective verb's template simply
    omits some forms) or when the given person/gender/number doesn't resolve
    to a valid index.
    """
    endings = template.forms.get(code)
    if not endings:
        return None
    index: int | None
    if code == "par:pas":
        index = PARTICIPE_PASSE_INDEX.get((gender, number)) if gender and number else None
    elif code in ("inf", "par:pre"):
        index = 0
    elif code == "imp:pre":
        index = IMPERATIVE_PERSON_INDEX.get(personNumber) if personNumber else None
    else:
        index = FINITE_PERSON_INDEX.get(personNumber) if personNumber else None
    if index is None or index >= len(endings):
        return None
    ending = endings[index]
    if ending is None:
        return None
    return radical + ending


# Literal written ending appended to the last syllable segment of the m_s
# (radical) orthographic-syllable breakdown to get each other gender/number
# form. Empirically confirmed exact (0 mismatches) against every fin:ir-style
# verb in LexiqueMixte.tsv with attested f_s/f_p forms (see conversation).
PARTICIPE_PASSE_ORTHOSYLL_SUFFIX = {
    ("m", "s"): "",
    ("m", "p"): "s",
    ("f", "s"): "e",
    ("f", "p"): "es",
}


# The consonant letter a feminine past participle's stem ends in, when it has
# one, is silent in the masculine and pronounced in the feminine ("promis"
# /pRomi/, "promise" /pRomiz/; "écrit" /ekRi/, "écrite" /ekRit/; "clos" /klo/,
# "close" /kloz/). A single intervocalic "s" is voiced; "ss" is not.
FEMININE_PARTICIPLE_CONSONANT = {"s": "z", "ss": "s", "t": "t"}
PARTICIPLE_VOWEL_LETTERS = set("aeiouyàâäéèêëîïôöùûüÿœæ")


def feminineParticipleConsonant(feminineOrtho: str) -> str | None:
    """
    The phoneme a feminine past participle pronounces and its masculine does
    not: None for a vowel-final stem ("garnie", "aimées", "vue"), else the
    stem's final consonant letter, voiced as spoken ("promises" -> "z",
    "éconduite" -> "t").
    """
    stem = feminineOrtho.removesuffix("s")
    if not stem.endswith("e"):
        raise ValueError(f"{feminineOrtho!r} is not a feminine past-participle spelling")
    stem = stem[:-1]
    if not stem or stem[-1] in PARTICIPLE_VOWEL_LETTERS:
        return None
    letters = "ss" if stem.endswith("ss") else stem[-1]
    consonant = FEMININE_PARTICIPLE_CONSONANT.get(letters)
    if consonant is None:
        raise ValueError(f"no feminine consonant rule for the participle stem of {feminineOrtho!r}")
    return consonant


def spliceParticiplePhon(attestedParticiple: Word, gender: str, ortho: str) -> tuple[str, str]:
    """
    Given one attested past-participle Word of a lemma (any gender/number),
    return (phon, rawSyllCV) for the `gender` slot spelled `ortho` of that
    same lemma's past participle.

    Validated empirically across ~200 fin:ir-style verbs in LexiqueMixte.tsv:
    a regular participle's phon does not vary by number, nor by gender when
    its stem ends in a vowel (~98% exact; the residual is vowel-transcription
    allophone noise, not a real phonological effect) -- only the written
    ending differs. Across genders, a consonant-final feminine stem adds its
    consonant (feminineParticipleConsonant) to the masculine's phon, as a coda
    of the last syllable, and the masculine drops it (item B45: "promis" had
    been given the /z/ of "promise"). Any trailing '#' in rawSyllCV is
    dropped: it's a silent-grapheme bookkeeping artifact of the source
    alignment data (see lexique.py), not a phonological signal --
    src/word.py already strips it before building the plain phoneme string.
    """
    phon = attestedParticiple.phonology
    rawSyllCV = attestedParticiple.rawSyllCV.replace("_#", "").replace("#", "")
    if gender == attestedParticiple.gender:
        return phon, rawSyllCV
    feminineOrtho = ortho if gender == "f" else attestedParticiple.ortho
    consonant = feminineParticipleConsonant(feminineOrtho)
    if consonant is None:
        return phon, rawSyllCV
    if gender == "f":
        if phon.endswith(consonant):
            return phon, rawSyllCV
        return phon + consonant, f"{rawSyllCV}_{consonant}"
    if not phon.endswith(consonant):
        return phon, rawSyllCV
    if rawSyllCV[-2:] not in (f"_{consonant}", f"|{consonant}"):
        raise ValueError(
            f"syll_cv {rawSyllCV!r} of {attestedParticiple.ortho!r} does not end with its phon's {consonant!r}"
        )
    return phon[:-1], rawSyllCV[:-2]


def deriveParticipeRadicalOrthosyll(attestedParticiple: Word) -> str:
    """
    Recover the invariant (m_s-equivalent) radical orthosyllCV by stripping
    the literal gender/number ending letters off an attested participle's
    rawOrthosyllCV, handling both conventions observed in the corpus for
    where the segment boundary falls (a separate trailing "_"-delimited
    segment, or the letters concatenated onto the last grapheme).
    """
    gender, number = attestedParticiple.gender, attestedParticiple.number
    suffix = PARTICIPE_PASSE_ORTHOSYLL_SUFFIX.get((gender, number)) if gender and number else None
    if suffix is None:
        raise ValueError(f"{attestedParticiple.ortho!r} is not a past-participle gender/number form")
    orthosyll = attestedParticiple.rawOrthosyllCV
    if not suffix:
        return orthosyll
    if orthosyll.endswith("_" + suffix):
        return orthosyll[: -(len(suffix) + 1)]
    if orthosyll.endswith(suffix):
        return orthosyll[: -len(suffix)]
    raise ValueError(
        f"orthosyllCV {orthosyll!r} does not end with the expected {gender}_{number} suffix {suffix!r}"
    )


def _lastOrthosyllLetter(orthosyll: str) -> str:
    for char in reversed(orthosyll):
        if char not in "_|":
            return char
    return ""


def generateParticipeOrthosyll(attestedParticiple: Word, gender: str, number: str) -> str:
    """
    Generate the rawOrthosyllCV for a missing gender/number past-participle
    slot by splicing the literal ending letters onto the radical recovered
    from `attestedParticiple` (which may be any gender/number of the same
    lemma's participle, not necessarily m_s).
    """
    suffix = PARTICIPE_PASSE_ORTHOSYLL_SUFFIX.get((gender, number))
    if suffix is None:
        raise ValueError(f"{gender}_{number} is not a valid past-participle gender/number combination")
    radicalOrthosyll = deriveParticipeRadicalOrthosyll(attestedParticiple)
    if (gender, number) == ("m", "p") and _lastOrthosyllLetter(radicalOrthosyll) in "sxz":
        # French orthography: a masculine-singular participle already ending
        # in s/x/z takes no further mark in the masculine plural (e.g.
        # "épris" -> "épris", not "épriss") -- unlike the regular case, where
        # PARTICIPE_PASSE_ORTHOSYLL_SUFFIX's "s" is correct (e.g. "aimé" ->
        # "aimés"). Verbiste's own orthographic participle-passé endings
        # already encode this (m:ettre/pr:endre: "is"/"is"; cl:ore: "os"/"os"),
        # this table just didn't know to mirror it.
        suffix = ""
    return f"{radicalOrthosyll}_{suffix}" if suffix else radicalOrthosyll


def _padSilentUnits(rawSyllCV: str, rawOrthosyllCV: str) -> str:
    """
    Append one silent '#' unit per orthographic unit the phonemic breakdown is
    short of (item B46): the gender/number suffix adds an orthographic unit
    ("garnis" g_a_r|n_i_s) whose phonemic counterpart is silent, and attested
    rows mark it as a trailing '#' in the last syllable ("garnis" g_a_R|n_i_#,
    "garnie" g_a_R|n_i_#). Attested participle rows align unit for unit, and
    every unit-aligned reader (deriveSyllableSplitTable, deriveMidVowelTable,
    normalizeSplicedBreakdown's orthographic copy) skips a row that doesn't.
    """
    missing = _unitCount(rawOrthosyllCV) - _unitCount(rawSyllCV)
    if missing < 0:
        raise ValueError(
            f"syll_cv {rawSyllCV!r} has more units than its orthosyll_cv {rawOrthosyllCV!r}"
        )
    return rawSyllCV + "_#" * missing


def _unitCount(rawBreakdown: str) -> int:
    return len(rawBreakdown.replace("|", "_").split("_"))


def generateMissingParticiple(
    lemme: Lemme,
    template: ConjugationTemplate,
    attestedParticiple: Word,
    gender: str,
    number: str,
) -> Word:
    """
    Generate a full candidate Word for a missing past-participle gender/number
    slot of `lemme`, given one already-attested past-participle Word of that
    same lemma (any gender/number) to splice phonology/orthosyllCV from.
    Frequency is 0 for both book and film: this is a synthesized form, never
    a corpus observation (see design plan's provenance requirement -- callers
    writing this to a resource file must still tag it as synthetic there).
    """
    radical = infinitiveRadical(lemme, template)
    ortho = generateOrthoForm(radical, template, "par:pas", gender=gender, number=number)
    if ortho is None:
        raise ValueError(f"template {template.name!r} has no par:pas form for {gender}_{number}")
    phon, rawSyllCV = spliceParticiplePhon(attestedParticiple, gender, ortho)
    rawOrthosyllCV = generateParticipeOrthosyll(attestedParticiple, gender, number)
    rawSyllCV = _padSilentUnits(rawSyllCV, rawOrthosyllCV)
    return Word(
        ortho=ortho, phonology=phon, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=gender, number=number, infoVerb="par:pas;",
        rawSyllCV=rawSyllCV, rawOrthosyllCV=rawOrthosyllCV,
        frequencyBook=0.0, frequencyFilm=0.0,
    )


FINITE_SLOT_EXCLUDED_CODES = {
    "inf", "par:pre", "par:pas",
    # Subjonctif imparfait declared out of scope for the theory 2026-09-21 (see
    # ROADMAP.md, and src/elicitation.py's matching exclusion since 2026-09-19):
    # archaic/literary tense, not worth generating synthetic completions for.
    "sub:imp",
}
CONJUGATION_STRING_FIELDS = ("phonology", "rawSyllCV", "rawOrthosyllCV")


def allFiniteSlots(template: ConjugationTemplate) -> list[tuple[str, str]]:
    """
    Every (code, personNumber) finite conjugation slot a template defines --
    indicatif, subjonctif, conditionnel, imperatif -- excluding "inf" and
    "par:pre" (invariant single forms, no person/gender variation to be
    undersampled on) and "par:pas" (handled separately by the existing
    past-participle gender/number path).
    """
    slots: list[tuple[str, str]] = []
    for code, endings in template.forms.items():
        if code in FINITE_SLOT_EXCLUDED_CODES:
            continue
        personIndex = IMPERATIVE_PERSON_INDEX if code == "imp:pre" else FINITE_PERSON_INDEX
        for personNumber, index in personIndex.items():
            if index < len(endings) and endings[index] is not None:
                slots.append((code, personNumber))
    return slots


def _rawInfoVerbTags(word: Word) -> list[str]:
    """Raw ';'-separated infoVerb tags (e.g. "ind:pre:1s"), same split Word itself uses."""
    if word.infoVerb is None:
        return []
    return [tag for tag in word.infoVerb.split(";") if tag]


def attestedInfinitiveWordByLemme(theory: dict[Strokes, list[Word]]) -> dict[Lemme, Word]:
    """
    lemma -> attested infinitive Word, for every VER lemma with one attested.

    Requires ortho == lemme in addition to an "inf" tag: the source lexicon has a
    handful of rows where "inf" is spuriously combined with other tags on a
    genuinely conjugated/participle form (e.g. "réprimés" carries
    infover="inf;par:pas;" despite being a participle, "dois"/"reprenons" carry
    "inf" alongside their real finite tags). Trusting those poisons
    deriveConjugationEndingTables for every OTHER lemma sharing that template --
    a single bad donor can zero out the common-suffix derivation for an entire
    template (e.g. "aim:er", used by thousands of regular verbs).
    """
    result: dict[Lemme, Word] = {}
    for words in theory.values():
        for word in words:
            if word.gramCat == GramCat.VER and word.ortho == word.lemme \
                    and "inf" in _rawInfoVerbTags(word):
                result[word.lemme] = word
    return result


# A word-final glide after a consonant is pronounced as its vowel: dénier's radical
# "denj" gives "dénie" /deni/, jouer's "Zw" gives "joue" /Zu/, tuer's "t8" gives "tue"
# /ty/. After a vowel the glide stays (couraille /kuRaj/).
FINAL_GLIDE_VOWEL = {"j": "i", "w": "u", "8": "y"}


def _hasNucleus(unit: str) -> bool:
    return any(phoneme in Phoneme.nucleusPhonemes for phoneme in unit)


def _unitsAndBoundaries(rawBreakdown: str) -> tuple[list[str], set[int]]:
    """Flat units of a "|"/"_" breakdown, and the unit indexes a new syllable starts at."""
    units: list[str] = []
    boundaries: set[int] = set()
    for syllable in rawBreakdown.split("|"):
        if units:
            boundaries.add(len(units))
        units += syllable.split("_")
    return units, boundaries


def _joinBreakdown(units: list[str], boundaries: set[int]) -> str:
    return "".join(("|" if i in boundaries else "_" if i else "") + unit for i, unit in enumerate(units))


ClusterKey = tuple[str, ...]

# A run between two given nuclei must be seen this often before its own boundary
# position overrides the one of the bare run (deriveSyllableSplitTable).
MIN_CONTEXT_SPLIT_COUNT = 5


def _clusterKeys(units: list[str], before: int, after: int) -> tuple[ClusterKey, ...]:
    """
    The units between the nucleus units at `before` and `after`, with and without the two
    nuclei around them: "j" splits after "wa" (voyez "v_wa_j|e") but before most vowels
    (payer "p_E|j_e"). Adjacent nuclei get the first key only: the vowels are all there
    is to go on ("8_i" never splits, "e|e" does).
    """
    run = tuple(units[before + 1:after])
    withNuclei = (units[before], *run, units[after])
    return (withNuclei, ("", *run)) if run else (withNuclei,)


def deriveSyllableSplitTable(words: list[Word]) -> dict[ClusterKey, int | None]:
    """
    For every run of units between two nucleus units in `words`' phonemic breakdowns
    (_clusterKeys), the most common syllable-boundary position: the number of units of
    the run that stay in the first syllable ("R_t" -> 1, "p_o_R|t_e"; "t_R" -> 0,
    "a|t_R_a"), or None when no boundary falls in it ("t_8_a"). Runs holding more than
    one boundary are not counted. Keyed both with the two nuclei around the run (kept
    when seen MIN_CONTEXT_SPLIT_COUNT times) and, for a non-empty run, without them.
    """
    positionsByKey: dict[ClusterKey, Counter[int | None]] = defaultdict(Counter)
    for word in words:
        units, boundaries = _unitsAndBoundaries(word.rawSyllCV)
        nuclei = [i for i, unit in enumerate(units) if _hasNucleus(unit)]
        for before, after in zip(nuclei, nuclei[1:]):
            inside = [i for i in boundaries if before < i <= after]
            if len(inside) <= 1:
                position = inside[0] - before - 1 if inside else None
                for key in _clusterKeys(units, before, after):
                    positionsByKey[key][position] += 1
    return {
        key: positions.most_common(1)[0][0]
        for key, positions in positionsByKey.items()
        if key[0] == "" or positions.total() >= MIN_CONTEXT_SPLIT_COUNT
    }


# Mid vowels whose quality the spelling decides, in any syllable (achètera /aSEtRa/
# beside acheter /aS°te/), in a closed final one before /z/ or not (abonne /abOn/
# beside abonner /abone/), or in a non-final one, closed (aguerrira /agEriRa/ beside
# the coarse aguerrir /ageriR/) or open (affaiblira /afEblira/ beside the coarse
# affaiblir /afebliR/) — and how settled the spelling must leave it for
# deriveMidVowelTable to keep the rule. Non-final rules rewrite the coarse symbols
# only ("e", "o"): the others are committed qualities, and the schwa is a different
# phoneme altogether, not a laxer one (devriez /d°vRje/ keeps its °).
COARSE_VOWELS = set("eo")
COARSE_OF = {"E": "e", "O": "o"}
MID_VOWELS = set("eE°29oO")
VOWEL_LETTERS = set("aàâäeéèêëiîïoôöuùûüyœæ")
MIN_MID_VOWEL_COUNT = 20
MIN_ANY_SYLLABLE_VOWEL_SHARE = 0.99
MIN_CLOSED_VOWEL_SHARE = 0.9

# (orthographic unit, context): "any" syllable, a closed final one before /z/ or not,
# or a non-final one, closed or open.
MidVowelKey = tuple[str, str]
ANY_SYLLABLE, CLOSED, CLOSED_BEFORE_Z = "any", "closed", "closed before z"
NON_FINAL_CLOSED, NON_FINAL_OPEN = "nonfinal-closed", "nonfinal-open"
# Before a doubled consonant letter, in a syllable another one precedes: the prefix
# vowels of the word's first syllable keep their quality there (dessécher /deseSe/,
# effacer /efase/), the root ones lax (aguerrir /agERiR/, pressentir /pREs@tiR/ — 92%
# of the committed corpus rows). Not "sc": descend keeps /des@d/.
NON_FINAL_DOUBLED = "nonfinal before a doubled consonant"


def _isDoubledConsonant(unit: str) -> bool:
    return (
        len(unit) == 2 and unit[0] == unit[1]
        and unit[0].isalpha() and unit[0] not in VOWEL_LETTERS
    )


def _midVowelContexts(
    units: list[str],
    boundaries: set[int] | None = None,
    orthoUnits: list[str] | None = None,
) -> dict[int, str]:
    """
    The syllable context of the nuclei: the word's last one is closed final, before
    /z/ or not (it needs no `boundaries`: everything after it is its coda). The others
    — only when `boundaries` are given, for they alone tell a syllable's own coda from
    the next syllable's onset — are non-final, closed when their syllable ends in a
    sounded consonant, and — when `orthoUnits` align with `units` — before a doubled
    consonant letter (NON_FINAL_DOUBLED) in any syllable but the word's first. Without
    `boundaries` only the last nucleus is judged.
    """
    nuclei = [i for i, unit in enumerate(units) if _hasNucleus(unit)]
    contexts: dict[int, str] = {}
    if not nuclei:
        return contexts
    coda = [unit for unit in units[nuclei[-1] + 1:] if unit != "#"]
    for position, nucleus in enumerate(nuclei):
        if position == len(nuclei) - 1:
            if coda:
                contexts[nucleus] = CLOSED_BEFORE_Z if coda[0] == "z" else CLOSED
        elif boundaries is not None and any(boundary > nucleus for boundary in boundaries):
            following = next(
                (unit for unit in orthoUnits[nucleus + 1:] if unit != "#"), None
            ) if orthoUnits is not None else None
            if following is not None and _isDoubledConsonant(following) and any(
                boundary <= nucleus for boundary in boundaries
            ):
                contexts[nucleus] = NON_FINAL_DOUBLED
                continue
            syllableEnd = min(boundary for boundary in boundaries if boundary > nucleus)
            ownCoda = [
                unit for unit in units[nucleus + 1:syllableEnd]
                if unit != "#" and not _hasNucleus(unit)
            ]
            contexts[nucleus] = NON_FINAL_CLOSED if ownCoda else NON_FINAL_OPEN
    return contexts


def deriveMidVowelTable(words: list[Word]) -> dict[MidVowelKey, str]:
    """
    The mid vowel (MID_VOWELS) a nucleus gets from its orthographic unit: in any syllable
    ("è" -> E, "é" -> e, "au" -> o), kept at a MIN_ANY_SYLLABLE_VOWEL_SHARE share of the
    most common vowel; in a closed final syllable, before /z/ or not ("o" -> O, "o"
    before /z/ -> o, "eu" before /z/ -> 2); or in a non-final syllable, closed or open,
    where the spelling picks the lax member ("e" and "ai" -> E, "o" -> O), or before a
    doubled consonant letter past the word's first syllable ("e" -> E, aguerrir) — all
    kept at MIN_CLOSED_VOWEL_SHARE. All need MIN_MID_VOWEL_COUNT occurrences. Nuclei that
    are not themselves a mid vowel ("wa", a glide and a vowel) do not vote: they say
    nothing about which mid vowel the spelling picks. And when a non-final key's most
    common vowel is a lax one, its coarse counterpart abstains too: a coarse row never
    committed to a quality (Lexique383's "e" beside LexiqueInfra's "E"), so it cannot
    outvote the committed readings (affaiblira's "ai" -> E at 96% of the committed
    rows, 75% of all of them). Only words whose breakdowns align unit for unit and
    spell out their phonology count.
    """
    vowelsByKey: dict[MidVowelKey, Counter[str]] = defaultdict(Counter)
    for word in words:
        units, boundaries = _unitsAndBoundaries(word.rawSyllCV)
        orthoUnits, _ = _unitsAndBoundaries(word.rawOrthosyllCV)
        if len(units) != len(orthoUnits) or _joinPhonology(units) != word.phonology:
            continue
        contexts = _midVowelContexts(units, boundaries, orthoUnits)
        for i, unit in enumerate(units):
            if unit in MID_VOWELS:
                vowelsByKey[(orthoUnits[i], ANY_SYLLABLE)][unit] += 1
                if i in contexts:
                    vowelsByKey[(orthoUnits[i], contexts[i])][unit] += 1
    table: dict[MidVowelKey, str] = {}
    for key, vowels in vowelsByKey.items():
        vowel, count = vowels.most_common(1)[0]
        total = vowels.total()
        if key[1] in (NON_FINAL_CLOSED, NON_FINAL_OPEN, NON_FINAL_DOUBLED) and vowel in COARSE_OF:
            # The coarse counterpart of the lax winner abstains (docstring above).
            total -= vowels[COARSE_OF[vowel]]
        minShare = MIN_ANY_SYLLABLE_VOWEL_SHARE if key[1] == ANY_SYLLABLE else MIN_CLOSED_VOWEL_SHARE
        if total >= MIN_MID_VOWEL_COUNT and count / total >= minShare:
            table[key] = vowel
    return table


def _joinPhonology(units: list[str]) -> str:
    return "".join(unit for unit in units if unit != "#")


def normalizeSplicedBreakdown(
        phonology: str,
        rawSyllCV: str,
        rawOrthosyllCV: str,
        syllableSplitByCluster: dict[ClusterKey, int | None],
        midVowelByOrtho: dict[MidVowelKey, str],
    ) -> tuple[str, str, str]:
    """
    Repair the phonology and syllable breakdowns that generateMissingConjugatedForm
    builds by cutting the infinitive at a fixed character count (item B2). The cut keeps
    the infinitive's syllable boundaries, which move once the ending changes: a
    word-final form gets a vowel-less last syllable (canner "k_a|n_e" -> cannes "k_a|n_#",
    where the attested canne is "k_a_n_#") and a vowel-initial ending misses its onset
    (attendre "a|t_@_d_R_#" -> attendez "a|t_@_d_e", attested "a|t_@|d_e"). It also cuts
    each field on its own, so the two breakdowns drift apart (place "p_l_a_s_#" beside
    "p_l_a|c_e").

    The cut also keeps the infinitive's vowel quality where the finite form changes it
    (abonner /abone/ -> abonne "abon", attested /abOn/; acheter /aS°te/ -> achètera
    "aS°tRa", attested /aSEtRa/).

    Re-places every syllable boundary: one per run of units between two nuclei, where
    `syllableSplitByCluster` (deriveSyllableSplitTable) puts it, or where the spliced
    breakdowns had one for a run the table has never seen. The orthographic breakdown
    gets the same boundaries when it has as many units as the phonemic one (attested rows
    keep them aligned unit for unit), and is returned unchanged otherwise. When the
    phonology spells out the phonemic breakdown's units (all but B3's rows do), it also
    vocalizes a word-final glide after a consonant (FINAL_GLIDE_VOWEL) and, when the
    breakdowns are aligned, gives every mid vowel the quality its spelling calls for
    (`midVowelByOrtho`, deriveMidVowelTable: the closed-final rule of the vowel's
    syllable first, then the any-syllable one; the non-final rules run only after the
    boundaries are re-placed, for only they say which syllables are non-final and
    which closed), in the phonology and the phonemic breakdown alike.
    """
    units, boundaries = _unitsAndBoundaries(rawSyllCV)
    orthoUnits, orthoBoundaries = _unitsAndBoundaries(rawOrthosyllCV)
    aligned = len(units) == len(orthoUnits)
    if aligned:
        boundaries |= orthoBoundaries

    sounded = [i for i, unit in enumerate(units) if unit != "#"]
    spelledOut = bool(sounded) and _joinPhonology(units) == phonology
    if spelledOut:
        vowel = FINAL_GLIDE_VOWEL.get(units[sounded[-1]])
        afterConsonant = len(sounded) == 1 or not _hasNucleus(units[sounded[-2]])
        if vowel is not None and afterConsonant:
            units[sounded[-1]] = vowel
        if aligned:
            contexts = _midVowelContexts(units)
            for i, unit in enumerate(units):
                if unit in MID_VOWELS:
                    keys = [(orthoUnits[i], context) for context in (contexts.get(i, ANY_SYLLABLE), ANY_SYLLABLE)]
                    units[i] = next((midVowelByOrtho[key] for key in keys if key in midVowelByOrtho), unit)

    nuclei = [i for i, unit in enumerate(units) if _hasNucleus(unit)]
    newBoundaries: set[int] = set()
    for before, after in zip(nuclei, nuclei[1:]):
        key = next((k for k in _clusterKeys(units, before, after) if k in syllableSplitByCluster), None)
        if key is not None:
            position = syllableSplitByCluster[key]
            if position is not None:
                newBoundaries.add(before + 1 + position)
        else:
            newBoundaries.update(i for i in boundaries if before < i <= after)

    if spelledOut and aligned:
        # Which syllables are non-final, and which of them closed, is only knowable
        # now, after the re-placement; and a non-final rule rewrites the coarse
        # symbols only — the others are committed (devriez keeps its °).
        contexts = _midVowelContexts(units, newBoundaries, orthoUnits)
        for i, unit in enumerate(units):
            if unit in COARSE_VOWELS and contexts.get(i) in (
                NON_FINAL_CLOSED, NON_FINAL_OPEN, NON_FINAL_DOUBLED
            ):
                key = (orthoUnits[i], contexts[i])
                if key in midVowelByOrtho:
                    units[i] = midVowelByOrtho[key]
    if spelledOut:
        phonology = _joinPhonology(units)

    rawSyllCV = _joinBreakdown(units, newBoundaries)
    if aligned:
        rawOrthosyllCV = _joinBreakdown(orthoUnits, newBoundaries)
    return phonology, rawSyllCV, rawOrthosyllCV


def _longestCommonSuffix(strings: list[str]) -> str:
    if not strings:
        return ""
    shortest = min(strings, key=len)
    for length in range(len(shortest), 0, -1):
        suffix = shortest[-length:]
        if all(s.endswith(suffix) for s in strings):
            return suffix
    return ""


@dataclass(frozen=True)
class ConjugationEndingTables:
    """
    Empirically-derived phonemic/syllable-breakdown material for finite conjugation
    slots, keyed by field name ("phonology", "rawSyllCV", "rawOrthosyllCV"):

    - infinitiveSuffixByKey[(field, template)]: the common trailing substring shared by
      every attested infinitive's `field` value for that template (the phonological
      analog of ConjugationTemplate.infinitiveSuffix, which is orthographic-only).
    - slotEndingByKey[(field, template, code, personNumber)]: the ending to splice onto
      a lemma's own radical (its infinitive `field` value with the template's
      infinitiveSuffixByKey stripped) to build that slot's `field` value.
    - slotMatchRateByKey[(field, template, code, personNumber)]: fraction of attested
      donor lemmas for that slot whose own derived ending agreed with the chosen one --
      the confidence a caller should require before trusting a generated form (see
      generateMissingConjugatedForm's minMatchRate).
    - slotDonorCountByKey[(field, template, code, personNumber)]: how many attested
      donor lemmas contributed to that slot's match rate -- a rate of 1.0 from a single
      donor is far less trustworthy than 1.0 from fifty, so callers reporting confidence
      should look at both.
    - syllableSplitByCluster: where a syllable boundary falls between two nuclei, over
      the theory's corpus (nonzero-frequency) Words (deriveSyllableSplitTable); a generated form's
      breakdowns get their boundaries from it (normalizeSplicedBreakdown).
    - midVowelByOrtho: the mid vowel a nucleus gets from its spelling, over the same
      Words (deriveMidVowelTable).
    """
    infinitiveSuffixByKey: dict[tuple[str, str], str]
    slotEndingByKey: dict[tuple[str, str, str, str], str]
    slotMatchRateByKey: dict[tuple[str, str, str, str], float]
    slotDonorCountByKey: dict[tuple[str, str, str, str], int]
    syllableSplitByCluster: dict[ClusterKey, int | None]
    midVowelByOrtho: dict[MidVowelKey, str]


def endingTemplateKey(template: str, infinitiveWord: Word) -> str:
    """
    The key the ending tables use for a lemma: its template, split by the glide-aware
    class of its infinitive. An -ier verb whose infinitive ends in the vowel+glide unit
    "ij" (crier "k_R_ij|e", trier, plier, oublier) has a radical shaped unlike the
    "d_j_e" of étudier, so the two must not share endings (crierions spliced from the
    étudier donors lost its R and doubled its glide).
    """
    return template + "#ij" if infinitiveWord.phonology.endswith("ije") else template


def deriveConjugationEndingTables(
        theory: dict[Strokes, list[Word]],
        verbisteTemplates: dict[Lemme, str],
        exceptions: dict[Lemme, VerbModelException],
    ) -> ConjugationEndingTables:
    """
    Derive, for every (template, code, personNumber) finite-conjugation slot, the
    phonemic/syllable-breakdown ending appended to a lemma's radical -- the phonological
    analog of the orthographic endings Verbiste's conjugation templates already give for
    free (Stage 4's orthography half, generateOrthoForm).

    Method: for each attested finite form of a verb with a trusted template and an
    attested infinitive, estimate the radical length for each string field as that
    lemma's infinitive value with the template's empirically-derived common infinitive
    suffix (infinitiveSuffixByKey, a per-template constant) stripped, then take the
    remainder of the slot's own value as a candidate ending. The returned ending per
    slot is the most common (mode) candidate across every attested donor lemma; the
    match rate is the fraction of donors that agreed with it -- callers should require a
    high match rate before trusting a generated form for that slot (see
    generateMissingConjugatedForm), mirroring the empirical validation already applied to
    participle splicing (see spliceParticiplePhon / PARTICIPE_PASSE_ORTHOSYLL_SUFFIX).
    """
    infinitiveByLemme = attestedInfinitiveWordByLemme(theory)

    infinitivesByTemplate: dict[str, list[Word]] = defaultdict(list)
    for lemme, donorInfinitive in infinitiveByLemme.items():
        template = getTrustedTemplate(lemme, verbisteTemplates, exceptions)
        if template is not None:
            infinitivesByTemplate[endingTemplateKey(template, donorInfinitive)].append(donorInfinitive)

    infinitiveSuffixByKey: dict[tuple[str, str], str] = {
        (field, template): _longestCommonSuffix([getattr(w, field) for w in infinitiveWords])
        for template, infinitiveWords in infinitivesByTemplate.items()
        for field in CONJUGATION_STRING_FIELDS
    }

    candidatesByKey: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for words in theory.values():
        for word in words:
            if word.gramCat != GramCat.VER:
                continue
            # A word whose infoVerb also carries an "inf" tag is untrustworthy for any
            # *other* tag it carries too (see attestedInfinitiveWordByLemme's docstring):
            # resources/LexiqueMixte.tsv has ~90 rows where "inf" is spuriously combined
            # with a finite tag on a genuine infinitive row (e.g. "excuser" carrying
            # "ind:pre:2p;inf;" despite ortho == lemme). Trusting that finite tag here
            # would candidate the infinitive's own field value against itself, always
            # yielding the template's infinitiveSuffix as the "ending" -- a degenerate,
            # self-referential candidate that silently drags a slot's empirical match
            # rate below 1.0 for the whole template.
            if "inf" in _rawInfoVerbTags(word):
                continue
            template = getTrustedTemplate(word.lemme, verbisteTemplates, exceptions)
            infinitiveWord = infinitiveByLemme.get(word.lemme)
            if template is None or infinitiveWord is None:
                continue
            template = endingTemplateKey(template, infinitiveWord)
            for tag in _rawInfoVerbTags(word):
                parts = tag.split(":")
                if len(parts) != 3:
                    continue  # "inf" (1 part) and "par:pre"/"par:pas" (2 parts) aren't finite slots
                code, personNumber = f"{parts[0]}:{parts[1]}", parts[2]
                for field in CONJUGATION_STRING_FIELDS:
                    suffix = infinitiveSuffixByKey.get((field, template), "")
                    infinitiveValue = getattr(infinitiveWord, field)
                    radicalLen = len(infinitiveValue) - len(suffix)
                    if radicalLen < 0:
                        continue
                    slotValue = getattr(word, field)
                    candidatesByKey[(field, template, code, personNumber)].append(slotValue[radicalLen:])

    slotEndingByKey: dict[tuple[str, str, str, str], str] = {}
    slotMatchRateByKey: dict[tuple[str, str, str, str], float] = {}
    slotDonorCountByKey: dict[tuple[str, str, str, str], int] = {}
    for key, candidates in candidatesByKey.items():
        mode, modeCount = Counter(candidates).most_common(1)[0]
        slotEndingByKey[key] = mode
        slotMatchRateByKey[key] = modeCount / len(candidates)
        slotDonorCountByKey[key] = len(candidates)

    # Corpus Words only: synthetic rows (all zero-frequency, like 3 of LexiqueMixte's
    # 136k) carry the very breakdowns these tables repair.
    corpusWords = [
        word for words in theory.values() for word in words
        if word.frequencyBook > 0 or word.frequencyFilm > 0
    ]
    return ConjugationEndingTables(
        infinitiveSuffixByKey, slotEndingByKey, slotMatchRateByKey, slotDonorCountByKey,
        deriveSyllableSplitTable(corpusWords), deriveMidVowelTable(corpusWords),
    )


def repairSpliceUnits(rawSyllCV: str) -> str:
    """
    Turn the empty units a fixed-length cut leaves (a trailing one: cloue "k_l_u|" cut
    for the silent e; a leading one: halées "_a|l_e") and the fused "u#"/"ij#" units they
    were stored as into a sounded unit plus a silent "#" unit, as the attested rows write
    them (troue "t_R_u_#", hâler "#_a|l_e").
    """
    units, boundaries = _unitsAndBoundaries(rawSyllCV)
    repaired: list[str] = []
    shift = 0
    newBoundaries: set[int] = set()
    for i, unit in enumerate(units):
        if i in boundaries:
            newBoundaries.add(i + shift)
        if unit == "":
            repaired.append("#")
        elif len(unit) > 1 and unit.endswith("#"):
            repaired += [unit[:-1], "#"]
            shift += 1
        else:
            repaired.append(unit)
    return _joinBreakdown(repaired, newBoundaries)


def isWellFormedSplice(phonology: str, rawSyllCV: str) -> bool:
    """
    Whether a spliced row is worth emitting: no empty unit left, and a phonology that is
    the sounded units of its phonemic breakdown, up to the mid-vowel symbols (the
    normalizer sharpens the two fields' vowels independently: enserre "@sER" beside
    "@|s_e|R"). The endings are mined by string length, so a target whose radical is
    shaped unlike its donors' (an -ouer/-uer/-éer verb spliced with the -ier donors of
    étudi:er: clouerions "kluj§" for "kluRj§") gets a wrong phonology; such a slot is
    skipped, not repaired.
    """
    units, _ = _unitsAndBoundaries(rawSyllCV)
    if "" in units:
        return False
    strip = str.maketrans("", "", "eEo O2 9°".replace(" ", ""))
    return _joinPhonology(units).translate(strip) == phonology.translate(strip)


def reinsertLostNasalUnit(
        phonology: str, rawSyllCV: str, rawOrthosyllCV: str) -> tuple[str, str] | None:
    """
    Repair a row whose syll_cv lost one "n"/"m" unit that the orthosyll_cv still carries
    fused in the previous unit (enorgueillis: phon "@nORg9ji", syll "@|O_R|g_9|j_i_#",
    ortho "en|o_r|gu_e|ill_i_s"; the attested rows write "@|n_O_R|..." and
    "e|n_o_r|..."). The unit is reinserted at the start of the next syllable in both
    fields, and the ortho unit "en" becomes "e". Returns (syll_cv, orthosyll_cv), or None
    unless exactly one (position, letter) makes the sounded join equal the phon (up to
    mid-vowel symbols) and both fields have the same unit count and no empty unit.
    """
    units, bounds = _unitsAndBoundaries(rawSyllCV)
    oUnits, oBounds = _unitsAndBoundaries(rawOrthosyllCV)
    if len(units) != len(oUnits) or "" in units or "" in oUnits or bounds != oBounds:
        return None
    strip = str.maketrans("", "", "eEoO29°")
    target = phonology.translate(strip)
    found = [
        (k, c) for k in range(1, len(units)) for c in "nm"
        if len(oUnits[k - 1]) == 2 and oUnits[k - 1].endswith(c) and units[k - 1] != c
        and _joinPhonology(units[:k] + [c] + units[k:]).translate(strip) == target
    ]
    if len(found) != 1:
        return None
    k, c = found[0]
    newBounds = {b if b <= k else b + 1 for b in bounds}
    newUnits = units[:k] + [c] + units[k:]
    newOUnits = oUnits[:k - 1] + [oUnits[k - 1][0]] + [c] + oUnits[k:]
    return _joinBreakdown(newUnits, newBounds), _joinBreakdown(newOUnits, newBounds)


def rewriteSplicePhon(phonology: str, rawSyllCV: str) -> str | None:
    """
    The sounded join of a repaired syll_cv, offered as the phonology of a row whose
    syll_cv is right but whose stored phon lost a phoneme (clouerions "kluj§" beside
    "k_l_u_#|R_j_§": the radical's R). Returns None unless the rewrite is safe: the join
    differs from the stored phon, up to mid-vowel symbols, only by inserted characters
    (the phon lost a phoneme; a deletion or substitution means the syll_cv lost one:
    enivre "@|i_v_R" for "@nivR"), no unit is a vowel+glide unit ("ij", "Ej", "8j": those
    rows have a genuinely wrong syllable too, oublieriez "u|b_l_ij#|R_j_e"), no unit is
    empty, and the join has no doubled "jj".
    """
    units, _ = _unitsAndBoundaries(rawSyllCV)
    if "" in units or any(len(u) > 1 and u.endswith("j") for u in units):
        return None
    joined = _joinPhonology(units)
    if "jj" in joined:
        return None
    strip = str.maketrans("", "", "eEoO29°")
    a, b = phonology.translate(strip), joined.translate(strip)
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    if any(tag != "equal" and tag != "insert" for tag, *_ in ops):
        return None
    return joined


def generateMissingConjugatedForm(
        lemme: Lemme,
        template: ConjugationTemplate,
        infinitiveWord: Word,
        code: str,
        personNumber: str,
        endingTables: ConjugationEndingTables,
        minMatchRate: float = 1.0,
    ) -> Word | None:
    """
    Generate a full candidate Word for a missing finite conjugation slot (mood:tense +
    person/number), using deriveConjugationEndingTables's empirically-derived material.
    Returns None when: the template has no orthographic ending for this slot; no ending
    table entry exists for it (never attested for this template); or the entry's
    empirical match rate across donor lemmas is below `minMatchRate` -- callers should
    treat that as "not confident enough to synthesize", never silently accept it.
    """
    radical = infinitiveRadical(lemme, template)
    ortho = generateOrthoForm(radical, template, code, personNumber=personNumber)
    if ortho is None:
        return None

    fieldValues: dict[str, str] = {}
    tableTemplate = endingTemplateKey(template.name, infinitiveWord)
    for field in CONJUGATION_STRING_FIELDS:
        suffix = endingTables.infinitiveSuffixByKey.get((field, tableTemplate))
        endingKey = (field, tableTemplate, code, personNumber)
        ending = endingTables.slotEndingByKey.get(endingKey)
        matchRate = endingTables.slotMatchRateByKey.get(endingKey, 0.0)
        if suffix is None or ending is None or matchRate < minMatchRate:
            return None
        infinitiveValue = getattr(infinitiveWord, field)
        radicalLen = len(infinitiveValue) - len(suffix)
        if radicalLen < 0:
            return None
        fieldValues[field] = infinitiveValue[:radicalLen] + ending

    phonology, rawSyllCV, rawOrthosyllCV = normalizeSplicedBreakdown(
        fieldValues["phonology"], fieldValues["rawSyllCV"], fieldValues["rawOrthosyllCV"],
        endingTables.syllableSplitByCluster, endingTables.midVowelByOrtho,
    )
    rawSyllCV = repairSpliceUnits(rawSyllCV)
    if not isWellFormedSplice(phonology, rawSyllCV):
        return None
    return Word(
        ortho=ortho, phonology=phonology, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=None, number=None, infoVerb=f"{code}:{personNumber};",
        rawSyllCV=rawSyllCV, rawOrthosyllCV=rawOrthosyllCV,
        frequencyBook=0.0, frequencyFilm=0.0,
    )


def crossLemmaFeatureSetCollisions(
    featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]
) -> dict[tuple[WordFeature, ...], set[LemmeGramCat]]:
    """
    The literal "conflicting feature set" bug motivating this whole design
    plan: a discriminator feature-set chosen for one lemma's homophone group
    (by the shared adaptive selection, src/featureextractor.py's
    buildDiscriminatorSelection, or by greedyOptimizeDiscriminator) is only
    returned here when it was independently chosen for at least one *other*,
    unrelated lemma too (e.g.
    both rechampir and regarnir landing on the exact same minimal
    discriminator ('p', 'indicatif')). This is a real-homophone-collision
    check in the sense the design plan means it -- not a raw keystroke
    (Strokes) collision, which is a different, unrelated notion -- and
    requires no CP-SAT solve, only greedyOptimizeDiscriminator's own output.
    """
    collisions: dict[tuple[WordFeature, ...], set[LemmeGramCat]] = {}
    for featureSet, wordTuples in featuresetWords.items():
        lemmes = {word.lemmeGramCat for wordTuple in wordTuples for word in wordTuple}
        if len(lemmes) > 1:
            collisions[featureSet] = lemmes
    return collisions


def newlyCollidingLemmas(
    baselineFeaturesetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]],
    augmentedFeaturesetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]],
) -> set[LemmeGramCat]:
    """
    Lemmas that participate in a cross-lemma feature-set collision in
    `augmentedFeaturesetWords` (theory + generated candidate rows) that did
    NOT already exist, as a lemma pair, in `baselineFeaturesetWords` -- i.e.
    lemmas a generated candidate actually drags into a *new* collision, not
    ones already colliding with something regardless of the candidate.

    Avoids materializing lemma pairs (an earlier version enumerated every
    pairwise combination within each collision group, which is quadratic in
    group size and is what exhausted memory on a feature shared by thousands
    of unrelated lemmas, e.g. a plural marker). Per feature-set key: if at
    least one lemma is new to that key (`augLemmes - baseLemmes` non-empty)
    and the key still has >= 2 lemmas, then every lemma at that key now
    participates in at least one new pair -- either it's the new lemma
    itself pairing with anyone else present, or it's an old lemma newly
    paired with the new one. Pairs made up entirely of lemmas already
    present at that key in the baseline are unchanged and correctly
    excluded. This is linear in the total number of lemmas across collision
    groups, regardless of how large any single group is.
    """
    baselineCollisions = crossLemmaFeatureSetCollisions(baselineFeaturesetWords)
    augmentedCollisions = crossLemmaFeatureSetCollisions(augmentedFeaturesetWords)

    newlyColliding: set[LemmeGramCat] = set()
    for featureSet, augLemmes in augmentedCollisions.items():
        baseLemmes = baselineCollisions.get(featureSet, set())
        if (augLemmes - baseLemmes) and len(augLemmes) > 1:
            newlyColliding.update(augLemmes)
    return newlyColliding


def detectUndersampledLemmas(
    strokeLemmeDiscriminators: dict[tuple[Strokes, LemmeGramCat], dict[Word, list[WordFeature]]],
    verbisteTemplates: dict[Lemme, str],
    exceptions: dict[Lemme, VerbModelException],
) -> dict[LemmeGramCat, UndersampledLemma]:
    """
    For every VER lemmeGramCat present in strokeLemmeDiscriminators with a
    trusted conjugation template, compare its fullFeatureSpace against the
    leave-one-out union of every *other* lemmeGramCat sharing that template
    (its "siblings"). A lemma is flagged undersampled when its own space is a
    strict subset of its siblings' combined space -- i.e. every sibling
    following the same model collectively exhibits at least one discriminating
    feature this lemma's attested forms never needed, because the lexicon is
    missing the conjugated form that would have needed it.

    Lemmas with no siblings sharing a trusted template (nothing to compare
    against) are skipped, not flagged.
    """
    lemmeGramCats = {
        lemmeGramCat for (_strokes, lemmeGramCat) in strokeLemmeDiscriminators
    }

    templateByLemmeGramCat: dict[LemmeGramCat, str] = {}
    for lemmeGramCat in lemmeGramCats:
        lemme = lemmeOfVerbLemmeGramCat(lemmeGramCat)
        if lemme is None:
            continue
        template = getTrustedTemplate(lemme, verbisteTemplates, exceptions)
        if template is not None:
            templateByLemmeGramCat[lemmeGramCat] = template

    lemmeGramCatsByTemplate: dict[str, list[LemmeGramCat]] = {}
    for lemmeGramCat, template in templateByLemmeGramCat.items():
        lemmeGramCatsByTemplate.setdefault(template, []).append(lemmeGramCat)

    # fullFeatureSpace for every templated lemmeGramCat in one pass over
    # strokeLemmeDiscriminators (calling it per lemma rescans the whole dict each time).
    featureSpaceByLemmeGramCat: dict[LemmeGramCat, set[WordFeature]] = {
        lemmeGramCat: set() for lemmeGramCat in templateByLemmeGramCat
    }
    for (_strokes, groupLemme), wordFeatures in strokeLemmeDiscriminators.items():
        space = featureSpaceByLemmeGramCat.get(groupLemme)
        if space is not None:
            for features in wordFeatures.values():
                space.update(features)

    undersampled: dict[LemmeGramCat, UndersampledLemma] = {}
    for template, siblingGroup in lemmeGramCatsByTemplate.items():
        # Leave-one-out union of the siblings' spaces from per-template feature counts
        # (a feature is in the others' union iff some sibling other than this one has it),
        # instead of re-unioning every other sibling for each lemma.
        featureCounts: Counter[WordFeature] = Counter()
        for lemmeGramCat in siblingGroup:
            featureCounts.update(featureSpaceByLemmeGramCat[lemmeGramCat])
        for lemmeGramCat in siblingGroup:
            others = [other for other in siblingGroup if other != lemmeGramCat]
            if not others:
                continue
            ownSpace = featureSpaceByLemmeGramCat[lemmeGramCat]
            canonicalSpace: set[WordFeature] = {
                feature for feature, count in featureCounts.items()
                if count - (feature in ownSpace) > 0
            }
            if ownSpace < canonicalSpace:
                undersampled[lemmeGramCat] = UndersampledLemma(
                    lemmeGramCat=lemmeGramCat,
                    template=template,
                    missingFeatures=frozenset(canonicalSpace - ownSpace),
                    siblingLemmeGramCats=frozenset(others),
                )

    return undersampled
