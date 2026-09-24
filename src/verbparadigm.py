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
verbatim (spliceParticiplePhon, generateMissingParticiple), since gender/number
doesn't change a participle's pronunciation; finite conjugation slots (mood,
tense, person/number) genuinely change pronunciation, so those are generated
from an empirically-derived per-template ending table instead
(deriveConjugationEndingTables, generateMissingConjugatedForm).
"""

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

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
        return self.forms["inf"][0]


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
        forms: dict[str, list[str]] = {}
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
    if index is None or index >= len(endings) or endings[index] is None:
        return None
    return radical + endings[index]


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


def spliceParticiplePhon(attestedParticiple: Word) -> tuple[str, str]:
    """
    Given one attested past-participle Word of a lemma (any gender/number),
    return (phon, rawSyllCV) to reuse verbatim for any *other* gender/number
    slot of that same lemma's past participle.

    Validated empirically across ~200 fin:ir-style verbs in LexiqueMixte.tsv:
    a regular participle's phon does not vary by gender/number (~98% exact;
    the residual is vowel-transcription allophone noise, not a real
    phonological effect) -- only the written ending differs. Any trailing '#'
    in rawSyllCV is dropped: it's a silent-grapheme bookkeeping artifact of
    the source alignment data (see lexique.py), not a phonological signal --
    src/word.py already strips it before building the plain phoneme string.
    """
    return attestedParticiple.phonology, attestedParticiple.rawSyllCV.replace("_#", "").replace("#", "")


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
    phon, rawSyllCV = spliceParticiplePhon(attestedParticiple)
    rawOrthosyllCV = generateParticipeOrthosyll(attestedParticiple, gender, number)
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
    """
    infinitiveSuffixByKey: dict[tuple[str, str], str]
    slotEndingByKey: dict[tuple[str, str, str, str], str]
    slotMatchRateByKey: dict[tuple[str, str, str, str], float]
    slotDonorCountByKey: dict[tuple[str, str, str, str], int]


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
            infinitivesByTemplate[template].append(donorInfinitive)

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

    return ConjugationEndingTables(
        infinitiveSuffixByKey, slotEndingByKey, slotMatchRateByKey, slotDonorCountByKey
    )


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
    for field in CONJUGATION_STRING_FIELDS:
        suffix = endingTables.infinitiveSuffixByKey.get((field, template.name))
        endingKey = (field, template.name, code, personNumber)
        ending = endingTables.slotEndingByKey.get(endingKey)
        matchRate = endingTables.slotMatchRateByKey.get(endingKey, 0.0)
        if suffix is None or ending is None or matchRate < minMatchRate:
            return None
        infinitiveValue = getattr(infinitiveWord, field)
        radicalLen = len(infinitiveValue) - len(suffix)
        if radicalLen < 0:
            return None
        fieldValues[field] = infinitiveValue[:radicalLen] + ending

    return Word(
        ortho=ortho, phonology=fieldValues["phonology"], lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=None, number=None, infoVerb=f"{code}:{personNumber};",
        rawSyllCV=fieldValues["rawSyllCV"], rawOrthosyllCV=fieldValues["rawOrthosyllCV"],
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
