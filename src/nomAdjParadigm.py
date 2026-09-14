#!/usr/bin/python
# coding: utf-8
"""
Detection and generation for missing NOM (singular/plural) and ADJ
(masculine/feminine x singular/plural) forms in the lexicon.

Unlike verb conjugation (src/verbparadigm.py), a NOM or ADJ paradigm has a
small, fixed slot set, so detecting a gap is plain enumeration against
NOM_SLOTS/ADJ_SLOTS (see missingSlots) rather than the sibling-template
comparison detectUndersampledLemmas needs for verbs.

Generating the missing orthography/phonology/syllable-breakdown, however,
can't reuse a fixed suffix table the way spliceParticiplePhon/
PARTICIPE_PASSE_ORTHOSYLL_SUFFIX does for past participles: plural and
feminine formation in French has many productive-but-irregular classes
where pronunciation genuinely changes (cheval -> chevaux, heureux ->
heureuse, sec -> sèche, beau -> belle...). So this mirrors the *idea* of
verbparadigm.py's deriveConjugationEndingTables instead: group donor lemmas
by an orthographic ending class, empirically derive the (fromSuffix,
toSuffix) transformation for each field from every donor that already has
both slots attested, and only trust it when every donor in the class agrees.

crossLemmaFeatureSetCollisions/newlyCollidingLemmas from src/verbparadigm.py
are reused as-is for the collision safety check -- they're already generic
over Word/LemmeGramCat/WordFeature, not verb-specific.
"""

import csv
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from src.word import GramCat, Lemme, LemmeGramCat, Word

Slot = tuple[str, str]  # (gender, number), e.g. ("m", "s")

NOM_NUMBERS: tuple[str, ...] = ("s", "p")
ADJ_GENDERS: tuple[str, ...] = ("m", "f")
ADJ_SLOTS: tuple[Slot, ...] = tuple((g, n) for g in ADJ_GENDERS for n in ("s", "p"))

# Preference order for which attested slot to generate FROM, when several
# are available: the most canonical/unmarked form first (masculine singular
# for ADJ, singular for NOM of either gender).
ADJ_SOURCE_PRIORITY: tuple[Slot, ...] = (("m", "s"), ("f", "s"), ("m", "p"), ("f", "p"))

FIELDS: tuple[str, ...] = ("ortho", "phonology", "rawSyllCV", "rawOrthosyllCV")

# Longest class key tried first: an ortho ending like "al" is a much more
# specific (and reliable) morphological-class signal than a single trailing
# letter, but short words or an unseen 3-letter ending fall back to shorter
# keys.
CLASS_KEY_LENGTHS: tuple[int, ...] = (3, 2, 1)


@dataclass(frozen=True)
class NomAdjModelException:
    """
    One hand-reviewed exception row: `lemme` is invariable (no missing form
    to generate -- e.g. genuinely defective, pluralia tantum, or a form the
    donor-table approach can't confidently derive) or, when `overrideOrtho`
    is set, its correct generated forms are given directly (irregular
    plurals/feminines like cheval/chevaux, beau/belle) rather than derived.
    `overrideOrtho`/`overridePhonology` are ";"-joined per ADJ_SLOTS/NOM
    order (m_s;m_p;f_s;f_p for ADJ, s;p for NOM), "" for a slot that's
    genuinely absent (defective) rather than just uncommon.
    """
    lemme: Lemme
    gramCat: str
    status: str  # "invariable" or "irregular"
    overrideOrtho: str
    overridePhonology: str
    note: str


def loadNomAdjModelExceptions(tsvPath: str | Path) -> dict[tuple[Lemme, str], NomAdjModelException]:
    """
    Parse resources/nomAdjModelExceptions.tsv (comment lines starting with
    '#', a header row, then tab-separated lemme/gramCat/status/
    override_ortho/override_phonology/note rows) into a dict keyed by
    (lemme, gramCat name).
    """
    exceptions: dict[tuple[Lemme, str], NomAdjModelException] = {}
    with open(tsvPath, encoding="utf-8") as tsvFile:
        rows = [line.rstrip("\n") for line in tsvFile if not line.startswith("#")]
    if not rows:
        return exceptions
    for row in rows[1:]:  # skip header
        if not row.strip():
            continue
        fields = row.split("\t")
        fields += [""] * (6 - len(fields))
        lemme, gramCat, status, overrideOrtho, overridePhonology, note = fields[:6]
        exceptions[(lemme, gramCat)] = NomAdjModelException(
            lemme, gramCat, status, overrideOrtho, overridePhonology, note
        )
    return exceptions


def attestedSlots(words: list[Word]) -> dict[LemmeGramCat, dict[Slot, Word]]:
    """
    Group every NOM/ADJ Word by lemmeGramCat, then by its (gender, number)
    slot. Words missing gender or number are skipped (nothing to slot them
    under -- e.g. an invariable-category ADV/ONO reading sharing the same
    orthography row).
    """
    result: dict[LemmeGramCat, dict[Slot, Word]] = defaultdict(dict)
    for word in words:
        if word.gramCat not in (GramCat.NOM, GramCat.ADJ):
            continue
        if word.gender is None or word.number is None:
            continue
        result[word.lemmeGramCat][(word.gender, word.number)] = word
    return dict(result)


def expectedSlots(gramCat: GramCat, attestedGenders: frozenset[str]) -> frozenset[Slot]:
    """
    The full slot set a lemmeGramCat is expected to have. A NOM's gender is
    fixed by the lexicon (attestedGenders is normally a single gender, or
    two for an epicene noun like "aide"), so only the numbers are enumerated
    per attested gender. An ADJ is expected to inflect for both genders
    regardless of which one happens to be attested already.
    """
    if gramCat == GramCat.NOM:
        return frozenset((g, n) for g in attestedGenders for n in NOM_NUMBERS)
    if gramCat == GramCat.ADJ:
        return frozenset(ADJ_SLOTS)
    raise ValueError(f"{gramCat} has no NOM/ADJ paradigm")


def missingSlots(slotMap: dict[Slot, Word], gramCat: GramCat) -> frozenset[Slot]:
    """The slots expected for this lemmeGramCat's attested gender(s) that aren't in slotMap."""
    attestedGenders = frozenset(gender for gender, _number in slotMap)
    return expectedSlots(gramCat, attestedGenders) - frozenset(slotMap)


# Common, near-exceptionless French ADJ endings whose masculine and feminine
# spelling are identical (any adjective already ending in one of these before
# the final mute "e" doesn't double a consonant or alternate the ending the
# way -eux/-euse, -er/-ère, -f/-ve, -on/-onne etc. do). Checked before
# donor-table generation because the donor pool is structurally biased
# *against* discovering this on its own: a genuinely invariant word usually
# has only ONE attested row (gender blank or a single tag), so it never
# contributes an (fromSuffix, toSuffix) pair to deriveNomAdjEndingTables in
# the first place -- only the minority of words that truly alternate (e.g.
# "clair"/"claire", "pair"/"paire") end up as donors for a same-looking
# "-aire" class, which would otherwise wrongly teach "-aire" -> "-air".
# Deliberately not exhaustive -- add a rare family here only once a flag
# surfaces it, same policy as resources/nomAdjModelExceptions.tsv. Note
# "ète" is the least safe entry here: it collides with a handful of genuine
# masc/fem alternations (complet/complète, discret/discrète) that just
# happen to already have both forms attested elsewhere in the lexicon (so
# this rule never fires for them) -- but a rare, currently-single-slot
# "-ète" word could in principle be a real alternation this wrongly treats
# as invariant. Confirmed safe against every "-ète" case Morphalou could
# check when this was added (see conversation); the Morphalou cross-check
# is the actual safety net here, not this suffix list.
ADJ_INVARIANT_GENDER_SUFFIXES = (
    "aire", "able", "ible", "iste", "ique", "oire", "ade", "ude", "ime",
    "ose", "ase", "ile", "ame", "aste", "iaque", "esque", "istique",
    "ide", "ïde", "ole", "ète", "yste",
)


def isSuspectedInvariableForm(fromWord: Word, toSlot: Slot) -> bool:
    """
    True when the missing slot is regular-French-orthography invariable, so
    there is no orthographically distinct form to generate at all -- the
    expected spelling is simply `fromWord.ortho` unchanged:

    - NOM/ADJ number ending in "s"/"z": safe in either direction -- unlike
      "x", these endings are never produced by an irregular plural
      alternation (cheval/chevaux, chou/choux...), only by a genuinely
      invariant word (bras, nez, gris...), so a plural already ending in
      "s"/"z" just as reliably implies an identical singular as the reverse.
    - NOM number ending in "x": only checked singular -> plural (souris,
      prix...). NOT plural -> singular: a plural ending in "x" is routinely
      the *irregular* -al/-eau/-eu/-ou -> -aux/-eaux/-eaux/-oux alternation
      (cheval -> chevaux), whose singular does NOT end in "x" at all -- so
      this direction must fall through to the donor-table check instead of
      assuming invariance.
    - ADJ number ending in "x": safe in EITHER direction -- an adjective's
      masculine already ending in "x" (heureux, chitineux...) has no
      competing irregular pattern the way NOM's -al/-eau/-eu/-ou family
      does, so it's plural-invariant on that same masculine side regardless
      of which slot is the known one (confirmed against Morphalou -- see
      conversation).
    - ADJ gender: `fromWord.ortho` ends in one of ADJ_INVARIANT_GENDER_SUFFIXES
      (solaire, valable, sensible, sadique, dérisoire...).
    """
    fromGender, fromNumber = fromWord.gender, fromWord.number
    toGender, toNumber = toSlot
    if fromGender == toGender and {fromNumber, toNumber} == {"s", "p"}:
        if not fromWord.ortho:
            return False
        lastLetter = fromWord.ortho[-1]
        if lastLetter in ("s", "z"):
            return True
        if lastLetter == "x":
            # NOM: only forward (singular -> plural) -- an x-ending PLURAL is
            # routinely the *irregular* -al/-eau/-eu/-ou alternation (cheval
            # -> chevaux), whose singular does NOT end in "x" at all, so that
            # direction must fall through to the donor-table check instead.
            # ADJ: safe in both directions -- an ADJ whose masculine already
            # ends in "x" (heureux, chitineux...) is plural-invariant on
            # that same masculine side with no competing irregular pattern
            # landing on "x" from a different ending the way NOM has.
            if fromWord.gramCat == GramCat.NOM:
                return fromNumber == "s"
            if fromWord.gramCat == GramCat.ADJ:
                return True
        return False
    if fromWord.gramCat == GramCat.ADJ and fromNumber == toNumber and fromGender != toGender:
        return fromWord.ortho.endswith(ADJ_INVARIANT_GENDER_SUFFIXES)
    return False


def _commonPrefixLen(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def orthoClassKeys(ortho: str) -> list[str]:
    """Candidate class keys for `ortho`, longest (most specific) first."""
    return [ortho[-n:] for n in CLASS_KEY_LENGTHS if len(ortho) >= n]


EndingKey = tuple[str, str, Slot, Slot, str]  # (field, gramCatName, fromSlot, toSlot, classKey)


@dataclass(frozen=True)
class NomAdjEndingTables:
    """
    Empirically-derived (fromSuffix, toSuffix) transformation per
    (field, fromSlot, toSlot, orthoClassKey), plus the confidence a caller
    should require before trusting it (see generateMissingForm):
    matchRateByKey is the fraction of donor lemmas in that class that agreed
    on the transformation, donorCountByKey how many donors contributed (a
    1.0 rate from a single donor is far less trustworthy than from fifty).
    """
    endingByKey: dict[EndingKey, tuple[str, str]]
    matchRateByKey: dict[EndingKey, float]
    donorCountByKey: dict[EndingKey, int]


def deriveNomAdjEndingTables(words: list[Word]) -> NomAdjEndingTables:
    """
    For every lemmeGramCat with >=2 slots attested, and every ordered pair
    of its attested slots, derive the per-field (fromSuffix, toSuffix)
    transformation: the common prefix between the fromSlot and toSlot
    values (per field) gives the radical, the remainders are the candidate
    suffixes. Candidates are grouped by every ortho class key the fromSlot
    word's `ortho` matches (see orthoClassKeys), so a generation lookup can
    try the most specific key first and fall back to a shorter one. NOM and
    ADJ donors are kept in separate tables (the key includes gramCat) --
    NOM and ADJ morphology for a shared ortho ending can genuinely differ
    (e.g. "maire"/"mairesse" is a legitimate NOM pair, but would otherwise
    wrongly teach the "-ire" class to add "-esse" for the ADJ "papillaire",
    which is actually gender-invariant).
    """
    slotsByLemme = attestedSlots(words)
    candidatesByKey: dict[EndingKey, list[tuple[str, str]]] = defaultdict(list)
    for slotMap in slotsByLemme.values():
        slots = list(slotMap)
        for fromSlot in slots:
            fromWord = slotMap[fromSlot]
            classKeys = orthoClassKeys(fromWord.ortho)
            for toSlot in slots:
                if toSlot == fromSlot:
                    continue
                toWord = slotMap[toSlot]
                for field in FIELDS:
                    fromVal, toVal = getattr(fromWord, field), getattr(toWord, field)
                    prefixLen = _commonPrefixLen(fromVal, toVal)
                    pair = (fromVal[prefixLen:], toVal[prefixLen:])
                    for classKey in classKeys:
                        key: EndingKey = (field, fromWord.gramCat.name, fromSlot, toSlot, classKey)
                        candidatesByKey[key].append(pair)

    endingByKey: dict[EndingKey, tuple[str, str]] = {}
    matchRateByKey: dict[EndingKey, float] = {}
    donorCountByKey: dict[EndingKey, int] = {}
    for key, candidates in candidatesByKey.items():
        mode, modeCount = Counter(candidates).most_common(1)[0]
        endingByKey[key] = mode
        matchRateByKey[key] = modeCount / len(candidates)
        donorCountByKey[key] = len(candidates)

    return NomAdjEndingTables(endingByKey, matchRateByKey, donorCountByKey)


# Minimum donor count required to trust a class key, indexed by the key's
# length (see orthoClassKeys/CLASS_KEY_LENGTHS): a more specific class (more
# trailing letters shared) needs fewer independent donors to be trustworthy,
# since French morphology genuinely groups by ending -- a single donor
# agreeing at 3 letters is normally a real shared paradigm, but a single
# donor agreeing at just 1 letter is likely a coincidence (see "maire" ->
# "mairesse" spuriously "confirming" a 1-letter "e" class before the
# gramCat-scoping fix; even NOM-only, a single 1-letter-class donor is still
# too big a leap to trust on its own). Empirically checked by hand against a
# random sample of generated candidates (see conversation).
MIN_DONOR_COUNT_BY_CLASS_KEY_LENGTH: dict[int, int] = {3: 1, 2: 2, 1: 4}


def generateMissingForm(
    fromWord: Word,
    toSlot: Slot,
    tables: NomAdjEndingTables,
    minMatchRate: float = 1.0,
    minDonorCountByClassKeyLength: dict[int, int] = MIN_DONOR_COUNT_BY_CLASS_KEY_LENGTH,
) -> Word | None:
    """
    Generate a full candidate Word for `toSlot`, splicing tables' learned
    per-field ending onto `fromWord`. Tries class keys from most to least
    specific (see orthoClassKeys) and returns the first that has a
    confident (matchRate/donorCount above threshold), consistent (fromWord's
    own field value actually ends with the learned fromSuffix) entry for
    every field. Returns None when no class key clears the bar for all
    fields -- callers should treat that as "not confident enough to
    synthesize", never silently accept a partial/guessed candidate.
    """
    assert fromWord.gender is not None and fromWord.number is not None
    toGender, toNumber = toSlot
    if (
        fromWord.gramCat == GramCat.ADJ and fromWord.gender != toGender and fromWord.number != toNumber
        and fromWord.ortho.endswith(ADJ_INVARIANT_GENDER_SUFFIXES)
    ):
        # Both axes differ at once (e.g. attested only as f_s, need m_p) --
        # don't trust a direct cross-axis donor lookup for this: it has a
        # much smaller, noisier donor pool than the same-gender number
        # transformation (confirmed against Morphalou: "aramide"/f_s -> m_p
        # was wrongly generated as "aramids", stripping the "e", from just 2
        # cross-axis donors, when the correct "aramides" falls straight out
        # of "add s only" once gender-invariance is taken into account).
        # Since this word's ending is already known gender-invariant, get
        # the target number in fromWord's OWN gender first (a same-gender
        # move, which the class-key tables handle reliably) and just relabel
        # the gender -- the spelling doesn't change with gender for these.
        sameGenderCandidate = generateMissingForm(
            fromWord, (fromWord.gender, toNumber), tables, minMatchRate, minDonorCountByClassKeyLength
        )
        if sameGenderCandidate is not None:
            # dataclasses.replace (not a plain attribute mutation) so
            # __post_init__ reruns and recomputes _hash/lemmeGramCat for the
            # new gender -- a direct `.gender = toGender` would leave _hash
            # stale, silently breaking this Word's __eq__/__hash__.
            return replace(sameGenderCandidate, gender=toGender)
        return None
    fromSlot: Slot = (fromWord.gender, fromWord.number)
    for classKey in orthoClassKeys(fromWord.ortho):
        fieldValues: dict[str, str] = {}
        for field in FIELDS:
            key: EndingKey = (field, fromWord.gramCat.name, fromSlot, toSlot, classKey)
            entry = tables.endingByKey.get(key)
            if entry is None:
                break
            minDonorCount = minDonorCountByClassKeyLength.get(len(classKey), 999)
            if tables.matchRateByKey[key] < minMatchRate or tables.donorCountByKey[key] < minDonorCount:
                break
            fromSuffix, toSuffix = entry
            val = getattr(fromWord, field)
            if not val.endswith(fromSuffix):
                break
            fieldValues[field] = val[: len(val) - len(fromSuffix)] + toSuffix
        else:
            gender, number = toSlot
            return Word(
                ortho=fieldValues["ortho"], phonology=fieldValues["phonology"], lemme=fromWord.lemme,
                gramCat=fromWord.gramCat, orthoGramCat=fromWord.orthoGramCat,
                gender=gender, number=number, infoVerb=None,
                rawSyllCV=fieldValues["rawSyllCV"], rawOrthosyllCV=fieldValues["rawOrthosyllCV"],
                frequencyBook=0.0, frequencyFilm=0.0,
            )
    return None


EXCLUDED_WORDS_PATH_DEFAULT = "excluded_words.txt"


def loadExcludedWords(path: str = EXCLUDED_WORDS_PATH_DEFAULT) -> set[str]:
    """Same file/format dictionary.py's Dictionary.readCorpus reads (one ortho per line, '#'-comments)."""
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as excludedFile:
        return {line.strip() for line in excludedFile if line.strip() and not line.strip().startswith("#")}


def loadAllOrthosByLemme(paths: list[str]) -> dict[Lemme, set[str]]:
    """
    Every ortho ever seen for each lemme in `paths`, EXCLUDED words included
    -- unlike loadWords (which must exclude a word from the donor/detection
    pool), a caller deciding whether an ortho is "already present" needs to
    see excluded rows too. Concretely: "laponne" is in excluded_words.txt as
    a deprecated alternate spelling of "lapone" (see the conversation), so
    loadWords correctly hides it from attestedSlots -- but that then makes
    the (f, s) slot for "lapon_NOM" look genuinely missing on every run,
    and without this check the generator would re-derive and re-append a
    brand-new "laponne" row forever, never recognizing its own prior output
    (also named "laponne") as already covering that slot, since that row
    is *also* filtered out of the excluded-aware word list it dedupes
    against. Checking against the unfiltered ortho set catches both: a
    pre-existing excluded row, and the generator's own previously-written
    but excluded-ortho output.
    """
    orthosByLemme: dict[Lemme, set[str]] = defaultdict(set)
    for word in loadWords(paths, excludedWords=set()):
        orthosByLemme[word.lemme].add(word.ortho)
    return dict(orthosByLemme)


def loadWords(paths: list[str], excludedWords: set[str] | None = None) -> list[Word]:
    """
    Lightweight standalone lexicon reader (row->Word mapping mirrors
    dictionary.py's Dictionary.readCorpus), independent of the full
    Dictionary class -- detection/generation here needs no keyboard, theory,
    or frequency-ranking machinery, only the raw Word rows.

    `excludedWords` defaults to loadExcludedWords() -- applying the same
    exclusion list the real pipeline (dictionary.py) uses is not optional:
    a word excluded there (e.g. "juan", whose /x/ phoneme has no keyboard
    key assignment -- found via the conversation's dictionary.py crash) must
    never be used as a donor/source for generation either, or a *derived*
    word (e.g. "juans") ends up in resources/LexiqueSynthetic.tsv carrying
    the same problem without itself being on the exclusion list.
    """
    if excludedWords is None:
        excludedWords = loadExcludedWords()
    words: list[Word] = []
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as tsvFile:
            for row in csv.DictReader(tsvFile, delimiter="\t"):
                if not row.get("ortho") or row["ortho"].startswith("#") or row["ortho"] in excludedWords:
                    continue
                words.append(Word(
                    ortho=row["ortho"], phonology=row["phon"], lemme=row["lemme"],
                    gramCat=GramCat[row["cgram"]],
                    orthoGramCat=[GramCat[gc] for gc in row["cgramortho"].split(",")],
                    gender=row["genre"] or None, number=row["nombre"] or None,
                    infoVerb=row["infover"] or None,
                    rawSyllCV=row["syll_cv"], rawOrthosyllCV=row["orthosyll_cv"],
                    frequencyBook=float(row["freqlivres"]), frequencyFilm=float(row["freqfilms2"]),
                ))
    return words


# --- Morphalou (ATILF/CNRTL, LGPL-LR) cross-reference -----------------------
#
# An external, human-curated inflected-forms dictionary, used as the
# authoritative source of truth for generated ortho whenever it has an
# answer -- donor-agreement within our own sampled lexicon (everything
# above) is only a confidence *proxy*, not linguistic validation (see the
# conversation). generateAuthoritativeForm below is the actual entry point
# callers should use; it consults Morphalou first and falls back to the
# donor-table heuristic only when Morphalou has nothing to say.
MORPHALOU_CATEGORY_TO_GRAMCAT = {"Nom commun": GramCat.NOM, "Adjectif qualificatif": GramCat.ADJ}
# Morphalou's GENRE/NOMBRE columns can themselves say "invariable" (a huge
# fraction of ADJ rows -- ~29,000 flexion-level GENRE="invariable" alone,
# e.g. "irascible"/"aulique": one form covers both m and f) -- mapping that
# to "no gender info" was a real bug found in this project (see the
# conversation): it silently filed most gender-invariant ADJ forms under a
# key nothing ever looks up.
MORPHALOU_GENDER_MAP = {"masculine": ("m",), "feminine": ("f",), "invariable": ("m", "f")}
MORPHALOU_NUMBER_MAP = {"singular": ("s",), "plural": ("p",), "invariable": ("s", "p")}

# (lemme, gramCat.name) -> {(gender, number): {ortho, ...}} ; a row whose
# GENRE and/or NOMBRE is itself "invariable" is stored under both values of
# that axis (see MORPHALOU_GENDER_MAP/MORPHALOU_NUMBER_MAP above).
MorphalouIndex = dict[tuple[str, str], dict[Slot, set[str]]]


def loadMorphalouIndex(path: str | Path) -> MorphalouIndex:
    """
    Parse a Morphalou 3.1 CSV export (semicolon-separated; LEMME columns are
    forward-filled -- blank on a continuation row means "same lemma as the
    previous non-blank row", Morphalou's own convention for a lemma's
    additional inflected forms) into a MorphalouIndex, keeping only NOM/ADJ
    rows (MORPHALOU_CATEGORY_TO_GRAMCAT).
    """
    index: dict[tuple[str, str], dict[Slot, set[str]]] = defaultdict(lambda: defaultdict(set))
    lemme: str | None = None
    category: str | None = None
    lemmeGenre: str | None = None
    with open(path, encoding="utf-8", errors="replace", newline="") as csvFile:
        reader = csv.reader(csvFile, delimiter=";")
        for row in reader:
            if len(row) < 18:
                continue
            if row[0] == "GRAPHIE" and row[9] == "GRAPHIE":
                continue  # header row
            if row[0]:  # new lemma entry -- refresh forward-fill state
                lemme, category, lemmeGenre = row[0], row[2], row[5]
            if category not in MORPHALOU_CATEGORY_TO_GRAMCAT or lemme is None:
                continue
            gramCat = MORPHALOU_CATEGORY_TO_GRAMCAT[category]
            flexionOrtho, flexionNombre, flexionGenre = row[9], row[11], row[13]
            if not flexionOrtho:
                continue
            genres = MORPHALOU_GENDER_MAP.get(flexionGenre) or MORPHALOU_GENDER_MAP.get(lemmeGenre or "")
            numbers = MORPHALOU_NUMBER_MAP.get(flexionNombre)
            if not genres or not numbers:
                continue
            for genre in genres:
                for number in numbers:
                    index[(lemme, gramCat.name)][(genre, number)].add(flexionOrtho)
    return {k: dict(v) for k, v in index.items()}


def morphalouOrthos(morphalou: MorphalouIndex, lemme: Lemme, gramCat: GramCat, slot: Slot) -> set[str] | None:
    """Morphalou's attested ortho(s) for this exact (lemme, gramCat, slot), or None if it has no entry there."""
    slotsByGender = morphalou.get((lemme, gramCat.name))
    if slotsByGender is None:
        return None
    return slotsByGender.get(slot)


def generateAuthoritativeForm(
    fromWord: Word,
    toSlot: Slot,
    tables: NomAdjEndingTables,
    morphalou: MorphalouIndex | None,
) -> tuple[Word | None, str]:
    """
    The single entry point callers (util/generateMissingNomAdjForms.py,
    util/validateLexiconAgainstNomAdjParadigms.py) should use to fill a
    missing slot -- Morphalou-authoritative-when-available, donor-table
    fallback otherwise. Returns (candidate, source) where source is one of:
      "morphalou"        -- ortho from Morphalou, phon/syll from the donor
                             table (which independently agreed with it).
      "morphalou_override" -- ortho from Morphalou, OVERRIDING a donor-table
                             ortho that disagreed; phon/syll still from the
                             donor table (see the conversation: Morphalou is
                             far more reliable for spelling specifically,
                             every hand-checked disagreement was a donor-
                             table mistake, never a Morphalou one).
      "donor_table"       -- no Morphalou entry for this slot; donor-table
                             candidate used as-is (unverified against an
                             external source).
      "morphalou_no_phon" -- Morphalou confirms the ortho but the donor
                             table has no confident phon/syllable-breakdown
                             for this slot -- candidate is None; a human
                             needs to supply phon (resources/
                             nomAdjModelExceptions.tsv's override_phonology)
                             before this can be generated at all, since
                             Morphalou's own phonetic transcription uses a
                             different notation and no syllable
                             segmentation (not converted -- future work).
      "none"              -- neither source has an answer.
    """
    donorCandidate = generateMissingForm(fromWord, toSlot, tables)
    morphOrthos = morphalouOrthos(morphalou, fromWord.lemme, fromWord.gramCat, toSlot) if morphalou else None
    if morphOrthos is None:
        return donorCandidate, ("donor_table" if donorCandidate is not None else "none")
    if donorCandidate is not None and donorCandidate.ortho in morphOrthos:
        return donorCandidate, "morphalou"
    if donorCandidate is not None:
        return replace(donorCandidate, ortho=sorted(morphOrthos)[0]), "morphalou_override"
    return None, "morphalou_no_phon"


def chooseSourceSlot(slotMap: dict[Slot, Word], gramCat: GramCat) -> Slot | None:
    """The most canonical attested slot to generate other forms from, or None if slotMap is empty."""
    if gramCat == GramCat.ADJ:
        for slot in ADJ_SOURCE_PRIORITY:
            if slot in slotMap:
                return slot
    elif gramCat == GramCat.NOM:
        for gender, _ in slotMap:
            if (gender, "s") in slotMap:
                return (gender, "s")
    return next(iter(slotMap), None)
