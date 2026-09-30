"""
Export the steno-trainer's lesson progression: `steno-trainer/public/data/lessons.json`,
a fixed, fully generated sequence of French lessons (newly introduced keys + a French
rule text + example words), so a learner no longer meets the whole 10,000-word drill
pool on day one. Spec: `docs/specs/lessons.md`.

Five tracks, in order. `phonemes` orders the layout's keypresses by raw per-finger
effort (the `PositionWeights` sum of `Starboard.getStrokeCost`'s decomposition, without
its shape-cost term and multi-finger discount), groups them into steps at each distinct
`(weightSum, nFingers)`, deals each step round-robin over syllabic part (so an early
lesson mixes a vowel with consonants and can already write words) and chunks it into
lessons of at most 4 keypresses. `accord` introduces the gender/number Keypress Groups,
`verbe` the conjugation groups (one marker lesson) then one lesson per mood/tense,
`desambiguation` the star/hash mark codes in mark-complexity order, and `affixes` is a
placeholder for the (separate) affix-abbreviation work.

Word pools are drawn from the FULL disambiguated theory rendered into
practice-words-shaped records (the same `buildReadingsByWord`/`chordsWithReadings`/
`formatReadingsLabel`/`formatContext`/`formatPhonology` helpers `util.export_practice_words`
uses, WITHOUT its 10,000-record limit), filtered to records whose phonetic keypresses
are all covered and whose extra content (feature discriminating strokes, star/hash
marks) is gated by the tracks that introduce it -- so a marked or conjugation-marked
word never appears before its introducing lesson.

Everything is generated, nothing hand-written: regeneration from the same inputs is
byte-identical (explicit final sorts only; no dict/pickle insertion order reaches the
output).

Run: python -m util.export_lessons
Requires the same inputs as `util.export_practice_words`, plus
`realization_report.json` (`python -m util.build_realization_report`).
"""
import json
from functools import lru_cache

from src.keyboard import Keypress, Starboard, Strokes, canonicalizeStrokes
from src.word import GramCat, Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from util.export_practice_words import (
    KEYBOARD_JSON, RESOLVED_PRESS_SETS_PATH, buildReadingsByWord, chordsWithReadings,
    formatContext, formatPhonology, formatReadingsLabel,
)

OUTPUT_PATH = "steno-trainer/public/data/lessons.json"
REALIZATION_REPORT_PATH = "realization_report.json"

# Starboard's two mark keys (keys 0/1 are held for a possible third mark, never used).
STAR_KEY = 10
HASH_KEY = 15
RESERVED_KEYS = frozenset({0, 1, STAR_KEY, HASH_KEY})

POOL_SIZE = 50           # records per lesson pool (§5)
MIN_DROP_POOL = 10       # coverage-free lessons below this are dropped (§5)
MAX_LESSON_KEYPRESSES = 4  # phoneme-track chunk size (§2.5)

FINGER_RANK = {"lt": 0, "rt": 0, "li": 1, "ri": 1, "lm": 2, "rm": 2,
               "lr": 3, "rr": 3, "lp": 4, "rp": 4}
PART_ORDER = ("nucleus", "onset", "coda")  # PART_RANK order; also the round-robin deal order
PART_RANK = {"nucleus": 0, "onset": 1, "coda": 2}
FINGER_FULL_NAME = {"lp": "leftPinky", "lr": "leftRing", "lm": "leftMiddle",
                    "li": "leftIndex", "lt": "leftThumb", "rt": "rightThumb",
                    "ri": "rightIndex", "rm": "rightMiddle", "rr": "rightRing",
                    "rp": "rightPinky"}

# The eight verbe-track tenses, in lesson order (§4.3): id, the reading atoms that
# identify them, and the French "mode_temps" of the §7.4 rule text.
TENSES = (
    ("ind-pre", ("indicatif", "présent"), "l'indicatif présent"),
    ("ind-imp", ("indicatif", "imparfait"), "l'imparfait de l'indicatif"),
    ("ind-fut", ("indicatif", "future"), "le futur de l'indicatif"),
    ("par-pas", ("participe", "passé"), "le participe passé, comme au passé composé"),
    ("inf", ("infinitif",), "l'infinitif"),
    ("cnd", ("conditionnel",), "le conditionnel présent"),
    ("sub", ("subjonctif",), "le subjonctif présent"),
    ("imp", ("impératif",), "l'impératif présent"),
)

ACCORD_MARKER_ATOMS = frozenset({"f", "m", "p", "nbr_s", "nbr_p"})
ACCORD_MARKER_LABELS = {"f": "le féminin", "p": "le pluriel", "m": "le masculin",
                        "nbr_s": "le singulier", "nbr_p": "le pluriel"}
# Person labels are spelled out (not "1re"/"2e"/"3e") because the digits 1 and 2
# are IPA-mapped in the trainer's Notation.elm table: the IPA toggle rewrites the
# whole rendered rule text, so a digit in prose would come out as an IPA glyph (§8).
VERB_MARKER_LABELS = {"pers_1": "la première personne", "pers_2": "la deuxième personne",
                      "pers_3": "la troisième personne", "infinitif": "l'infinitif",
                      "impératif": "l'impératif", "subjonctif": "le subjonctif",
                      "imparfait": "l'imparfait", "future": "le futur",
                      "passé": "le passé", "conditionnel": "le conditionnel"}

# Phoneme section titles per (weightSum, nFingers) step (§7.6); unknown steps fall back
# to "Complexité {weightSum}", shared by the steps of one weightSum.
SECTION_TITLES = {
    (100, 1): "Les premières touches",
    (125, 1): "Les autres doigts",
    (150, 1): "Accords à deux touches",
    (175, 1): "Accords à deux touches, suite",
    (200, 1): "Derniers accords d'un doigt",
    (200, 2): "Voyelles à deux pouces",
    (225, 2): "Consonnes à deux doigts",
    (250, 2): "Accords à deux doigts, suite",
    (300, 2): "La voyelle complète",
}

TRACKS = (
    ("phonemes", "Phonèmes", "Les touches et les sons, de la plus simple à la plus complexe."),
    ("accord", "Accord (genre et nombre)", "Les marques de genre et de nombre."),
    ("verbe", "Verbes", "Les marques de conjugaison, temps par temps."),
    ("desambiguation", "Désambiguïsation", "Les marques * et # qui distinguent les homophones."),
    ("affixes", "Affixes", "Abréviations d'affixes — à venir."),
)
TRACK_TITLES = {trackId: title for trackId, title, _description in TRACKS}

# --- Numbers in French prose ---------------------------------------------------
#
# Lesson titles ("Leçon 3 : ...") and the section-title fallback spell their
# numbers in words: the trainer's IPA toggle (Notation.elm `ipaByXSampa`) also
# maps the digits 1, 2, 5, 8 and 9, so a digit in prose would be rewritten into
# an IPA glyph ("Leçon 1" -> "Leçon œ̃"). French number words are lowercase and
# free of every mapped character (§8).

_FRENCH_UNITS = ("zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
                 "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze",
                 "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf")
_FRENCH_TENS = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante",
                6: "soixante", 8: "quatre-vingt"}


def numberInFrench(n: int) -> str:
    """The cardinal `n` in lowercase French words, 0-999 (standard rules: 21
    "vingt et un", 71 "soixante et onze", 80 "quatre-vingts", 91
    "quatre-vingt-onze", 125 "cent vingt-cinq"). Used wherever a number would
    otherwise sit in French prose the IPA toggle rewrites (§8)."""
    assert 0 <= n <= 999, n
    if n < 20:
        return _FRENCH_UNITS[n]
    if n < 100:
        tens, units = divmod(n, 10)
        if tens in (7, 9):  # soixante-dix… / quatre-vingt-dix… : rest is 1-19
            rest = n - (60 if tens == 7 else 80)
            joiner = " et " if n == 71 else "-"
            return _FRENCH_TENS[6 if tens == 7 else 8] + joiner + _FRENCH_UNITS[rest]
        if units == 0:
            return _FRENCH_TENS[tens] + ("s" if tens == 8 else "")
        # "et un" only with tens 20-60 ("vingt et un"), never "quatre-vingt et un".
        joiner = " et " if units == 1 and tens < 7 else "-"
        return _FRENCH_TENS[tens] + joiner + _FRENCH_UNITS[units]
    hundreds, rest = divmod(n, 100)
    hundredsWord = "cent" if hundreds == 1 else _FRENCH_UNITS[hundreds] + " cent"
    if rest == 0:
        return hundredsWord + ("s" if hundreds > 1 else "")
    return hundredsWord + " " + numberInFrench(rest)

# The practice-words.json record shape, verbatim (the trainer's Drill.elm decoders).
RECORD_FIELDS = ("ortho", "before", "after", "label", "phonology", "steno", "strokes",
                 "frequency")


def fingerKeypressesOfStroke(stroke: tuple[int, ...], fingerAssignments: list[str]) -> list[Keypress]:
    """The stroke's keys grouped per finger, each group sorted and deduplicated -- the
    same per-finger decomposition `Starboard.getStrokeCost` performs."""
    keysByFinger: dict[str, list[int]] = {}
    for key in set(stroke):
        keysByFinger.setdefault(fingerAssignments[key], []).append(key)
    return [tuple(sorted(keysByFinger[finger])) for finger in sorted(keysByFinger)]


def _syllabicPartOf(starboard: Starboard, key: int) -> str | None:
    for part, keys in starboard.keyIDinSyllabicPart.items():
        if key in keys:
            return part
    return None


def phonemeOrderingKey(keypress: Keypress, starboard: Starboard) -> tuple[int, int, int, int, Keypress] | None:
    """`(weightSum, nFingers, maxFingerRank, partRank, sortedKeypress)` (§2.2), or None
    when some finger's sub-keypress is not legal (`_possibleKeypress`) -- the keypress is
    then treated as uncovered. `weightSum` is the plain per-finger `PositionWeights`
    sum: no `getStrokeShapeCost` term, no `0.85 ** nFingers` discount."""
    keysByFinger: dict[str, list[int]] = {}
    for key in keypress:
        keysByFinger.setdefault(starboard._fingerAssignments[key], []).append(key)
    weightSum = 0
    for finger, keys in keysByFinger.items():
        subKeypress = tuple(sorted(set(keys)))
        weight = starboard._possibleKeypress[FINGER_FULL_NAME[finger]].get(subKeypress)
        if weight is None:
            return None
        weightSum += weight
    part = _syllabicPartOf(starboard, keypress[0])
    assert part is not None, f"keypress {keypress} has no syllabic part"
    maxFingerRank = max(FINGER_RANK[f] for f in keysByFinger)
    return (weightSum, len(keysByFinger), maxFingerRank, PART_RANK[part], tuple(sorted(keypress)))


def phonemeSteps(starboard: Starboard) -> list[tuple[int, int, list[dict]]]:
    """The layout's keypresses grouped into steps at each distinct `(weightSum,
    nFingers)` of the §2.2 ordering; within a step, keypresses are sorted by the tail
    `(maxFingerRank, partRank, sortedKeypress)`. Each keypress item is
    `{keypress, phonemes, part}` (the phoneme set of a keypress is atomic)."""
    byStep: dict[tuple[int, int], list[tuple[int, int, Keypress, tuple[str, ...], str]]] = {}
    for keypress, phonemes in starboard.phonemesAssignedToStroke.items():
        orderingKey = phonemeOrderingKey(keypress, starboard)
        if orderingKey is None:
            continue  # not pressable: never introduced, so never covered (§2.2/§3)
        weightSum, nFingers, maxFingerRank, partRank, sortedKeypress = orderingKey
        part = _syllabicPartOf(starboard, sortedKeypress[0])
        assert part is not None
        byStep.setdefault((weightSum, nFingers), []).append(
            (maxFingerRank, partRank, sortedKeypress, tuple(phonemes), part))
    steps: list[tuple[int, int, list[dict]]] = []
    for weightSum, nFingers in sorted(byStep):
        items = [{"keypress": tail[2], "phonemes": tail[3], "part": tail[4]}
                 for tail in sorted(byStep[(weightSum, nFingers)])]
        steps.append((weightSum, nFingers, items))
    return steps


def chunkStep(items: list[dict]) -> list[list[dict]]:
    """Deal a step's tail-sorted keypresses round-robin over part (nucleus -> onset ->
    coda, skipping exhausted parts), then chunk the dealt sequence into consecutive
    lists of at most `MAX_LESSON_KEYPRESSES` keypresses (§2.5). The round-robin mixes a
    vowel with consonants in an early lesson so it can already write words."""
    queues = {part: [item for item in items if item["part"] == part] for part in PART_ORDER}
    dealt: list[dict] = []
    nextIndex = {part: 0 for part in PART_ORDER}
    while True:
        took = False
        for part in PART_ORDER:
            if nextIndex[part] < len(queues[part]):
                dealt.append(queues[part][nextIndex[part]])
                nextIndex[part] += 1
                took = True
        if not took:
            break
    return [dealt[i:i + MAX_LESSON_KEYPRESSES] for i in range(0, len(dealt), MAX_LESSON_KEYPRESSES)]


@lru_cache(maxsize=None)
def starHashCodeOf(strokes: Strokes) -> str | None:
    """The star/hash code of star-hash-marking.md §4 recomputed from the record's
    physical strokes: the `*`/`#` keys present anywhere (the code's first symbol is
    merged into the last phoneme stroke) plus the count of reserved-only trailing
    marker strokes. "" is no mark; None marks a shape the composition rules never
    produce (such a record is never eligible)."""
    star = any(STAR_KEY in stroke for stroke in strokes)
    hash_ = any(HASH_KEY in stroke for stroke in strokes)
    trailing = 0
    for stroke in reversed(strokes):
        if stroke and frozenset(stroke) <= RESERVED_KEYS:
            trailing += 1
        else:
            break
    # Every reserved-only stroke must sit in the trailing run.
    if any(stroke and frozenset(stroke) <= RESERVED_KEYS for stroke in strokes[:len(strokes) - trailing]):
        return None
    if trailing == 0 and not star and not hash_:
        return ""
    if trailing > 0:
        # An escalated code merges its first *# into the phoneme stroke, then one
        # trailing *# stroke per further repetition.
        return " ".join(["*#"] * (1 + trailing)) if star and hash_ else None
    if star and hash_:
        return "*#"
    return "*" if star else "#"


def verbTenseOf(reading: frozenset[str]) -> str | None:
    """Which of the eight §4.3 tenses a reading (a `src.elicitation` feature
    combination) belongs to, or None when it is not a verb reading of one of them."""
    if "infinitif" in reading:
        return "inf"
    if "conditionnel" in reading:
        return "cnd"
    if "subjonctif" in reading:
        return "sub"
    if "impératif" in reading:
        return "imp"
    if "participe" in reading:
        return "par-pas" if "passé" in reading else None
    if "indicatif" in reading:
        if "présent" in reading:
            return "ind-pre"
        if "imparfait" in reading:
            return "ind-imp"
        if "future" in reading:
            return "ind-fut"
    return None


def eligible(record: dict, coveredKeypresses: frozenset[Keypress],
             introducedGroups: frozenset[int], introducedCodes: frozenset[str]) -> bool:
    """§3: every per-finger keypress of the word's phonetic strokes is covered, every
    Keypress Group a feature discriminating stroke needs is introduced, and the record's
    star/hash code is empty or introduced."""
    code = record["_code"]
    if code is None:
        return False
    if code != "" and code not in introducedCodes:
        return False
    return (record["_keyps"] <= coveredKeypresses
            and record["_groups"] <= introducedGroups)


def selectTopWords(records: list[dict], limit: int = POOL_SIZE) -> list[dict]:
    """The pool ranking of §5: top `limit` by `(-frequency, ortho, steno)`."""
    return sorted(records, key=lambda r: (-r["frequency"], r["ortho"], r["steno"]))[:limit]


def loadKeypressGroups(realizationReport: dict) -> list[dict]:
    """The Keypress Groups of `realization_report.json`'s `keypressGroups`, normalized
    and deterministically ordered (descending affectedWords, ties by the sorted marker
    tuple then id) -- group ids are not stable across runs, so code never orders by id
    alone. The group's index in this list is its identity for `eligible`."""
    groups = [{"markers": tuple(sorted(g["markers"])), "affectedWords": g["affectedWords"],
               "chosenKeys": tuple(sorted(g["chosenKeys"])), "id": gid}
              for gid, g in realizationReport["keypressGroups"].items()]
    groups.sort(key=lambda g: (-g["affectedWords"], g["markers"], g["id"]))
    return groups


def _wordSortKey(word: Word) -> tuple[str, str, str, str, str, str]:
    return (word.ortho, word.phonology, word.lemme, word.gramCat.name,
            word.gender or "", word.number or "")


def buildRecordStream(
    starboard: Starboard,
    disambiguatedTheory: dict[Word, list[Strokes]],
    wordToStrokes: dict[Word, Strokes],
    readingsByWord: dict[Word, list[list[frozenset[str]]]],
    keypressGroups: list[dict],
) -> tuple[list[dict], int, int]:
    """The FULL disambiguated theory rendered into practice-words-shaped records (no
    10,000-record cap): one record per independently-valid stroke, merged on
    `(ortho, steno)` exactly the way `util.export_practice_words` merges, plus the
    private `_`-prefixed analysis the eligibility filter and the rule texts read:
    `_word` (first Word), `_keyps` (per-finger keypresses of the phonetic strokes),
    `_groups` (Keypress Group indexes the feature discriminating strokes need),
    `_code` (star/hash code, None when invalid), `_cluster` (the record's final induced
    strokes with the marks removed -- its lemma-homophone group identity),
    `_gramCats`, `_readings`. Returns `(records, skippedWords, invalidRecords)`."""
    groupsByStroke: dict[frozenset[int], frozenset[int]] = {}

    def groupsOf(strokeKeys: frozenset[int]) -> frozenset[int]:
        cached = groupsByStroke.get(strokeKeys)
        if cached is None:
            # The Realization Phase composes a group union into one stroke, so a
            # group's chosenKeys being a subset of the stroke's keys is the reverse
            # mapping (§3, rule 2).
            cached = frozenset(i for i, g in enumerate(keypressGroups)
                               if set(g["chosenKeys"]) <= strokeKeys)
            groupsByStroke[strokeKeys] = cached
        return cached

    byOrthoSteno: dict[tuple[str, str], dict] = {}
    skippedWords = 0
    invalidRecords = 0
    for word in sorted(disambiguatedTheory, key=_wordSortKey):
        phonetic = wordToStrokes.get(word)
        if phonetic is None:
            skippedWords += 1
            continue
        phoneticCanon = frozenset(canonicalizeStrokes(phonetic))
        phoneticKeypresses = frozenset(
            keypress for stroke in phonetic
            for keypress in fingerKeypressesOfStroke(stroke, starboard._fingerAssignments))
        chords, _aligned = chordsWithReadings(word, disambiguatedTheory[word], readingsByWord)
        for strokes, readings in chords:
            code = starHashCodeOf(strokes)
            neededGroups: frozenset[int] = frozenset()
            unmarked: list[tuple[int, ...]] = []
            if code is not None:
                valid = True
                for stroke in canonicalizeStrokes(strokes):
                    keys = frozenset(stroke)
                    residue = tuple(sorted(keys - RESERVED_KEYS))
                    if not residue:
                        continue  # a reserved-only marker stroke
                    unmarked.append(residue)
                    if residue in phoneticCanon:
                        continue  # a phonetic stroke, with or without a merged mark
                    if keys & RESERVED_KEYS:
                        # Reserved keys mixed with non-phonetic, non-mark content: the
                        # S6/S7 composition never produces this (§3 asserts it).
                        valid = False
                        break
                    neededGroups = neededGroups | groupsOf(keys)
                if not valid:
                    code = None
            if code is None:
                invalidRecords += 1
                continue
            steno = renderFinalStrokesToRTFCRE(starboard, strokes)
            label = formatReadingsLabel(word.gramCat, readings)
            existing = byOrthoSteno.get((word.ortho, steno))
            if existing is not None:
                # Same spelling AND same chord from two Words (an exempted homograph
                # pair): one record, labelled with both -- the practice-words merge.
                if label not in existing["label"].split(" · "):
                    existing["label"] += f" · {label}"
                before, after = formatContext(word, readings)
                if (before or after) and (existing["after"] == "!" or not (existing["before"] or existing["after"])) \
                        and after != "!":
                    existing["before"], existing["after"] = before, after
                existing["frequency"] = max(existing["frequency"], round(word.frequency, 3))
                existing["_keyps"] = existing["_keyps"] | phoneticKeypresses
                existing["_groups"] = existing["_groups"] | neededGroups
                existing["_gramCats"] = existing["_gramCats"] | {word.gramCat}
                for reading in readings:
                    if reading not in existing["_readings"]:
                        existing["_readings"].append(reading)
                continue
            before, after = formatContext(word, readings)
            byOrthoSteno[(word.ortho, steno)] = {
                "ortho": word.ortho, "before": before, "after": after,
                "label": label, "phonology": formatPhonology(word), "steno": steno,
                "strokes": [sorted(set(stroke)) for stroke in strokes],
                "frequency": round(word.frequency, 3),
                "_word": word, "_keyps": phoneticKeypresses, "_groups": neededGroups,
                "_code": code, "_cluster": tuple(unmarked),
                "_gramCats": {word.gramCat}, "_readings": list(readings),
            }
    records = sorted(byOrthoSteno.values(), key=lambda r: (r["ortho"], r["steno"]))
    return records, skippedWords, invalidRecords


# --- Rule-text rendering (§7) -------------------------------------------------

def _exampleOrthos(pool: list[dict], count: int = 3) -> list[str]:
    return [record["ortho"] for record in pool[:count]]


def _quotedExamples(orthos: list[str]) -> str:
    return ", ".join(f"« {ortho} »" for ortho in orthos)


def _keyNames(starboard: Starboard, keys) -> str:
    return ", ".join(starboard.keyDisplayName(key) for key in keys)


def _phonemeList(phonemes: tuple[str, ...]) -> str:
    return ", ".join(f"/{p}/" for p in phonemes[:-1]) + f" ou /{phonemes[-1]}/"


def phonemeRule(item: dict, starboard: Starboard, pool: list[dict]) -> dict:
    """One key, one part, one phoneme (§7.1). A multi-phoneme keypress is atomic, so it
    gets one rule; chord keypresses name every key."""
    keypress, phonemes, part = item["keypress"], item["phonemes"], item["part"]
    examples = [record["ortho"] for record in pool if keypress in record["_keyps"]][:3]
    suffix = f" ({_quotedExamples(examples)})" if examples else ""
    names = _keyNames(starboard, keypress)
    if len(phonemes) > 1:
        phonemeText = _phonemeList(phonemes)
        if len(keypress) == 1:
            text = f"La touche {names} écrit {phonemeText} selon la position{suffix}."
        else:
            text = f"Les touches {names} pressées ensemble écrivent {phonemeText} selon la position{suffix}."
    elif part == "nucleus":
        if len(keypress) == 1:
            text = f"La touche {names} écrit la voyelle /{phonemes[0]}/{suffix}."
        else:
            text = f"Les touches {names} pressées ensemble écrivent la voyelle /{phonemes[0]}/{suffix}."
    else:
        position = "début" if part == "onset" else "fin"
        if len(keypress) == 1:
            text = f"La touche {names} écrit le son /{phonemes[0]}/ en {position} de syllabe{suffix}."
        else:
            text = f"Les touches {names} pressées ensemble écrivent /{phonemes[0]}/ en {position} de syllabe{suffix}."
    return {"kind": "phoneme", "text": text, "examples": examples}


def _accordMarkerText(markers: tuple[str, ...]) -> str:
    labels: list[str] = []
    for marker in markers:
        label = ACCORD_MARKER_LABELS[marker]
        if label not in labels:
            labels.append(label)
    return " et ".join(labels)


def accordRule(group: dict, starboard: Starboard, wordToStrokes: dict[Word, Strokes],
               pool: list[dict]) -> dict:
    """§7.2: the marked form contrasted with the same word's phonetic-theory steno."""
    touche = _keyNames(starboard, group["chosenKeys"])
    marker = _accordMarkerText(group["markers"])
    examples = _exampleOrthos(pool)
    if not pool:
        return {"kind": "accord",
                "text": f"La touche {touche} marque {marker}.", "examples": []}
    first = pool[0]
    base = starboard.strokesToRTFCRE(canonicalizeStrokes(wordToStrokes[first["_word"]]))
    text = (f"La touche {touche} marque {marker} : "
            f"{first['ortho']} → {first['steno']} par rapport à {base}.")
    return {"kind": "accord", "text": text, "examples": examples}


def verbMarkerRule(group: dict, starboard: Starboard, pool: list[dict]) -> dict:
    """§7.3."""
    touche = _keyNames(starboard, group["chosenKeys"])
    markers = " et ".join(VERB_MARKER_LABELS[m] for m in group["markers"])
    examples = _exampleOrthos(pool)
    quoted = _quotedExamples(examples)
    text = (f"La touche {touche} marque {markers} : {quoted}." if quoted
            else f"La touche {touche} marque {markers}.")
    return {"kind": "verb-markers", "text": text, "examples": examples}


def verbTenseRule(tenseLabel: str, touchedKeys: list[int], starboard: Starboard,
                  pool: list[dict]) -> dict:
    """§7.4: {touches} are the marker keys the tense's selected records actually press."""
    examples = _exampleOrthos(pool)
    touches = _keyNames(starboard, touchedKeys)
    text = (f"Pour {tenseLabel}, les marques de conjugaison sont {touches} : "
            f"{_quotedExamples(examples)}.")
    return {"kind": "verb-tense", "text": text, "examples": examples}


def markRule(code: str, starboard: Starboard, pool: list[dict]) -> dict:
    """§7.5: the first complete lemma-homophone contrast of the pool (the marked record
    and the canonical member of its group); without a canonical member in the pool, the
    first marked record alone."""
    keys = [STAR_KEY] if code == "*" else [HASH_KEY] if code == "#" else [STAR_KEY, HASH_KEY]
    touches = _keyNames(starboard, keys)
    canonicalInPool = {}
    for record in pool:
        if record["_code"] == "" and record["_cluster"] not in canonicalInPool:
            canonicalInPool[record["_cluster"]] = record
    marked = next((r for r in pool if r["_code"] == code), None)
    pair = next((r for r in pool if r["_code"] == code and r["_cluster"] in canonicalInPool), None)
    if pair is not None:
        reference = canonicalInPool[pair["_cluster"]]
        text = (f"La marque {code} ({touches}) distingue {pair['ortho']} ({pair['steno']}) "
                f"de {reference['ortho']} ({reference['steno']}).")
    elif marked is not None:
        text = (f"La marque {code} ({touches}) s'ajoute à la fin du mot : "
                f"{marked['ortho']} ({marked['steno']}).")
    else:
        text = f"La marque {code} ({touches})."
    return {"kind": "mark", "text": text, "examples": _exampleOrthos(pool)}


# --- Lesson assembly (§4, §5, §6) ----------------------------------------------

def _emitLesson(lessons: list[dict], counters: dict[str, int], track: str, title: str,
                kind: str, sectionTitle: str, newKeys: list[int], newChords: list[list[int]],
                rules: list[dict], words: list[dict]) -> None:
    index = counters.get(track, 0) + 1
    counters[track] = index
    lessons.append({
        "id": f"{track}-{index:02d}", "track": track, "index": index,
        "sectionTitle": sectionTitle, "title": title, "kind": kind,
        "newKeys": newKeys, "newChords": newChords, "rules": rules, "words": words,
    })


def _wordsOf(pool: list[dict]) -> list[dict]:
    return [{field: record[field] for field in RECORD_FIELDS} for record in pool]


def buildLessons(
    starboard: Starboard,
    disambiguatedTheory: dict[Word, list[Strokes]],
    wordToStrokes: dict[Word, Strokes],
    readingsByWord: dict[Word, list[list[frozenset[str]]]],
    keypressGroups: list[dict],
) -> tuple[dict, dict[str, int]]:
    """The whole `lessons.json` document: the five tracks (§4) and the flat lesson list
    in generation order, per-track indexes dense after drops (§5). Returns
    `(document, perTrackLessonCounts)`."""
    stream, skippedWords, invalidRecords = buildRecordStream(
        starboard, disambiguatedTheory, wordToStrokes, readingsByWord, keypressGroups)
    clusterMaxFrequency: dict[tuple, float] = {}
    for record in stream:
        cluster = record["_cluster"]
        clusterMaxFrequency[cluster] = max(clusterMaxFrequency.get(cluster, 0.0),
                                           record["frequency"])

    accordGroupIndexes = [i for i, g in enumerate(keypressGroups)
                          if set(g["markers"]) <= ACCORD_MARKER_ATOMS]
    verbGroupIndexes = [i for i in range(len(keypressGroups)) if i not in accordGroupIndexes]

    lessons: list[dict] = []
    counters: dict[str, int] = {}
    coveredKeypresses: frozenset[Keypress] = frozenset()
    introducedGroups: frozenset[int] = frozenset()
    introducedCodes: frozenset[str] = frozenset()

    def poolTop(predicate) -> list[dict]:
        return selectTopWords([record for record in stream
                               if predicate(record)
                               and eligible(record, coveredKeypresses, introducedGroups,
                                            introducedCodes)])

    # 4.1 phonemes
    for weightSum, nFingers, items in phonemeSteps(starboard):
        sectionTitle = SECTION_TITLES.get((weightSum, nFingers),
                                         f"Complexité {numberInFrench(weightSum)}")
        for chunk in chunkStep(items):
            newCovered = coveredKeypresses | {item["keypress"] for item in chunk}
            coveredKeypresses = newCovered  # the lesson's own pool may use its new keys
            pool = poolTop(lambda record: True)
            index = counters.get("phonemes", 0) + 1
            title = "Leçon {0} : {1}".format(
                numberInFrench(index), ", ".join(item["phonemes"][0] for item in chunk))
            _emitLesson(lessons, counters, "phonemes", title, "phonemes", sectionTitle,
                        sorted({key for item in chunk for key in item["keypress"]}),
                        [sorted(item["keypress"]) for item in chunk if len(item["keypress"]) >= 2],
                        [phonemeRule(item, starboard, pool) for item in chunk],
                        _wordsOf(pool))

    # 4.2 accord
    for groupIndex in accordGroupIndexes:
        group = keypressGroups[groupIndex]
        introducedGroups = introducedGroups | {groupIndex}
        pool = poolTop(lambda record: bool(record["_gramCats"] & {GramCat.ADJ, GramCat.NOM})
                       and groupIndex in record["_groups"])
        _emitLesson(lessons, counters, "accord",
                    f"Leçon {numberInFrench(counters.get('accord', 0) + 1)} : "
                    f"{_accordMarkerText(group['markers'])}",
                    "accord", TRACK_TITLES["accord"],
                    sorted(group["chosenKeys"]),
                    [list(group["chosenKeys"])] if len(group["chosenKeys"]) >= 2 else [],
                    [accordRule(group, starboard, wordToStrokes, pool)],
                    _wordsOf(pool))

    # 4.3 verbe
    introducedGroups = introducedGroups | frozenset(verbGroupIndexes)
    markerPool = poolTop(lambda record: bool(record["_gramCats"] & {GramCat.VER, GramCat.AUX}))
    markerNewKeys = sorted({key for i in verbGroupIndexes for key in keypressGroups[i]["chosenKeys"]})
    _emitLesson(lessons, counters, "verbe",
                f"Leçon {numberInFrench(counters.get('verbe', 0) + 1)} : "
                "les marques de conjugaison",
                "verbe", TRACK_TITLES["verbe"], markerNewKeys, [],
                [verbMarkerRule(keypressGroups[i], starboard, markerPool)
                 for i in verbGroupIndexes],
                _wordsOf(markerPool))
    for tenseId, _atoms, tenseLabel in TENSES:
        pool = poolTop(lambda record, tid=tenseId:
                       record["_gramCats"] & {GramCat.VER, GramCat.AUX}
                       and any(verbTenseOf(reading) == tid for reading in record["_readings"]))
        if len(pool) < MIN_DROP_POOL:
            continue  # introduces no coverage (§5)
        touchedGroups = frozenset().union(*[record["_groups"] for record in pool]) if pool else frozenset()
        touchedKeys = sorted({key for i in touchedGroups for key in keypressGroups[i]["chosenKeys"]})
        _emitLesson(lessons, counters, "verbe",
                    f"Leçon {numberInFrench(counters.get('verbe', 0) + 1)} : {tenseLabel}",
                    "verbe", TRACK_TITLES["verbe"], [], [],
                    [verbTenseRule(tenseLabel, touchedKeys, starboard, pool)],
                    _wordsOf(pool))

    # 4.4 desambiguation
    presentCodes = {record["_code"] for record in stream if record["_code"]}
    escalated = sorted((code for code in presentCodes if code.count("*#") >= 2),
                       key=lambda code: code.count("*#"))
    for code in ["*", "#", "*#"] + escalated:
        introducedCodes = introducedCodes | {code}
        eligibleRecords = [record for record in stream
                           if eligible(record, coveredKeypresses, introducedGroups, introducedCodes)]
        byCode: dict[tuple, list[dict]] = {}
        canonicalByCluster: dict[tuple, list[dict]] = {}
        for record in eligibleRecords:
            if record["_code"] == code:
                byCode.setdefault(record["_cluster"], []).append(record)
            elif record["_code"] == "":
                canonicalByCluster.setdefault(record["_cluster"], []).append(record)
        rankKey = lambda record: (-record["frequency"], record["ortho"], record["steno"])
        clusters = []
        for cluster, members in byCode.items():
            canonical = canonicalByCluster.get(cluster, [])
            block = sorted(members + canonical, key=rankKey)
            clusters.append((-(clusterMaxFrequency[cluster]), block[0]["ortho"],
                             block[0]["steno"], block))
        clusters.sort(key=lambda c: c[:3])
        # Whole lemma-homophone groups in rank order; the cap never splits a pair (§5).
        pool: list[dict] = []
        for _maxFreq, _ortho, _steno, block in clusters:
            if len(pool) + len(block) > POOL_SIZE:
                break
            pool.extend(block)
        if len(pool) < MIN_DROP_POOL:
            introducedCodes = introducedCodes - {code}  # dropped: its words stay ineligible
            continue
        if code == "*":
            newKeys, newChords = [STAR_KEY], []
        elif code == "#":
            newKeys, newChords = [HASH_KEY], []
        elif code == "*#":
            newKeys, newChords = [STAR_KEY, HASH_KEY], [[STAR_KEY, HASH_KEY]]
        else:
            newKeys, newChords = [], []
        _emitLesson(lessons, counters, "desambiguation",
                    f"Leçon {numberInFrench(counters.get('desambiguation', 0) + 1)} : "
                    f"la marque {code}",
                    "desambiguation", TRACK_TITLES["desambiguation"], newKeys, newChords,
                    [markRule(code, starboard, pool)],
                    _wordsOf(pool))

    # 4.5 affixes (stub)
    _emitLesson(lessons, counters, "affixes", "Leçon un : à venir", "affixes",
                TRACK_TITLES["affixes"], [], [],
                [{"kind": "affixes", "text": "Abréviations d'affixes : à venir.",
                  "examples": []}],
                [])

    trackOrder = {trackId: i for i, (trackId, _t, _d) in enumerate(TRACKS)}
    lessons.sort(key=lambda lesson: (trackOrder[lesson["track"]], lesson["index"]))
    document = {"tracks": [{"id": trackId, "title": title, "description": description}
                           for trackId, title, description in TRACKS],
                "lessons": lessons}
    counts = {trackId: 0 for trackId, _t, _d in TRACKS}
    for lesson in lessons:
        counts[lesson["track"]] += 1
    counts["_records"] = len(stream)
    counts["_skippedWords"] = skippedWords
    counts["_invalidRecords"] = invalidRecords
    return document, counts


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")
    theory, disambiguatedTheory, wordToStrokes, wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(starboard)
    with open(RESOLVED_PRESS_SETS_PATH, encoding="utf-8") as f:
        readingsByWord = buildReadingsByWord(json.load(f), theory,
                                             wordToStrokes=wordToStrokes,
                                             wordsByOrthoLemme=wordsByOrthoLemme)
    with open(REALIZATION_REPORT_PATH, encoding="utf-8") as f:
        keypressGroups = loadKeypressGroups(json.load(f))

    document, counts = buildLessons(starboard, disambiguatedTheory, wordToStrokes,
                                    readingsByWord, keypressGroups)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=1)
        f.write("\n")

    trackSummary = ", ".join(f"{trackId} {counts[trackId]}"
                             for trackId, _title, _description in TRACKS)
    print(f"Wrote {OUTPUT_PATH}: {len(document['lessons'])} lessons ({trackSummary})"
          f" over {counts['_records']} candidate records"
          f" ({counts['_skippedWords']} words without phonetic strokes,"
          f" {counts['_invalidRecords']} invalid records skipped).")


if __name__ == "__main__":
    main()
