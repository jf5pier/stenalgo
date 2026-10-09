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
lessons of at most 4 keypresses. Each phoneme rule carries its keypress's hand group
("left"/"thumbs"/"right") for the intro view's "Main gauche"/"Les pouces"/"Main droite"
grouping, and attaches every phoneme's examples directly after that phoneme -- falling
back, when the lesson's own pool has no word for a phoneme, to the most frequent
unmarked stream records that press the keypress with it (the phoneme realized in the
keypress's own syllabic part -- an example whose phoneme sits in another part would
show a different keypress, possibly the other hand). `accord` introduces the gender/number Keypress Groups,
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
from collections.abc import Callable, Iterable
from typing import Any
import json
from functools import lru_cache

from src.grammar import Phoneme
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
MIN_NEW_WORDS = 30       # a phoneme lesson ideally unlocks this many words (§2.6)
MIN_NEW_LEMMAS = 15      # ... of at least this many different lemmas (§2.6)
TOP_WORDS = 20000        # ... all within the TOP_WORDS most frequent spellings (§2.6)
MAX_PER_LEMMA = 3        # pool diversity: records of one lemma before the relaxed fill (§2.6)
FIXED_PHONEME_LESSONS = 2          # lessons 1-2 keep their place
FIRST_LESSON_VOWELS = (("a",), ("e", "O"))  # the vowels lesson 1 keeps; lesson 2 gets the others (§2.6)
PHONEME_REORDER_SEGMENTS = ((2, 5), (5, 15))  # lessons 3-5, then 6-15, each permuted within
MIN_DROP_POOL = 10       # coverage-free lessons below this are dropped (§5)
MAX_LESSON_KEYPRESSES = 4  # phoneme-track chunk size (§2.5)

FINGER_RANK = {"lt": 0, "rt": 0, "li": 1, "ri": 1, "lm": 2, "rm": 2,
               "lr": 3, "rr": 3, "lp": 4, "rp": 4}
# The three hand groups of the intro view's rule grouping (gauche -> pouces ->
# droite), in display order; a keypress belongs to the group of its single
# finger (`Starboard._fingerAssignments`; the lt/rt keys 11-14 are the thumbs).
HANDS = ("left", "thumbs", "right")
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
    ("affixes", "Affixes", "Une règle d'abréviation par leçon : un contour court pour chaque mot, le long reste accepté."),
    ("expressions", "Abréviations d'expressions", "Les particules qui se joignent au mot voisin, leurs combinaisons et les abréviations d'expressions : un contour court, le long reste accepté."),
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


def handOfKeypress(keypress: Keypress, fingerAssignments: list[str]) -> str:
    """The hand group of a keypress: "left" or "right" for the non-thumb fingers,
    "thumbs" for the lt/rt keys (a keypress belongs to one finger). The intro view
    groups rules under the fixed French headers "Main gauche"/"Les pouces"/"Main
    droite" in this order (HANDS)."""
    finger = fingerAssignments[keypress[0]]
    if finger in ("lt", "rt"):
        return "thumbs"
    return "left" if finger.startswith("l") else "right"


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


def phonemeSteps(starboard: Starboard) -> list[tuple[int, int, list[dict[str, Any]]]]:
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
    steps: list[tuple[int, int, list[dict[str, Any]]]] = []
    for weightSum, nFingers in sorted(byStep):
        items = [{"keypress": tail[2], "phonemes": tail[3], "part": tail[4]}
                 for tail in sorted(byStep[(weightSum, nFingers)])]
        steps.append((weightSum, nFingers, items))
    return steps


def chunkStep(items: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Deal a step's tail-sorted keypresses round-robin over part (nucleus -> onset ->
    coda, skipping exhausted parts), then chunk the dealt sequence into consecutive
    lists of at most `MAX_LESSON_KEYPRESSES` keypresses (§2.5). The round-robin mixes a
    vowel with consonants in an early lesson so it can already write words."""
    queues = {part: [item for item in items if item["part"] == part] for part in PART_ORDER}
    dealt: list[dict[str, Any]] = []
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


def eligible(record: dict[str, Any], coveredKeypresses: frozenset[Keypress],
             introducedGroups: frozenset[int], introducedCodes: frozenset[str]) -> bool:
    """§3: every per-finger keypress of the word's phonetic strokes is covered, every
    Keypress Group a feature discriminating stroke needs is introduced, and the record's
    star/hash code is empty or introduced."""
    code = record["_code"]
    if code is None:
        return False
    if code != "" and code not in introducedCodes:
        return False
    return bool(record["_keyps"] <= coveredKeypresses
                and record["_groups"] <= introducedGroups)


def selectTopWords(records: list[dict[str, Any]], limit: int = POOL_SIZE) -> list[dict[str, Any]]:
    """The pool ranking of §5: top `limit` by `(-frequency, ortho, steno)`."""
    return sorted(records, key=lambda r: (-r["frequency"], r["ortho"], r["steno"]))[:limit]


def exchangeFirstLessonVowels(chunks: list[list[dict[str, Any]]]) -> list[list[dict[str, Any]]]:
    """§2.6: lessons 1-2 exchange vowel keypresses so that lesson 1 holds the vowels
    `FIRST_LESSON_VOWELS` (the pair that unlocks the most words with R, -j/-b/-w; 18
    against 12 for the unexchanged @/9 + a). The two lessons keep their sizes and their
    consonants; the keypresses stay in their dealt order. A layout without those two
    vowels in lessons 1-2 is left alone."""
    if len(chunks) < 2:
        return chunks
    dealt = chunks[0] + chunks[1]
    wanted = [item for item in dealt if item["part"] == "nucleus"
              and tuple(item["phonemes"]) in FIRST_LESSON_VOWELS]
    nuclei = [item for item in dealt if item["part"] == "nucleus"]
    if len(wanted) != len(FIRST_LESSON_VOWELS) or len(nuclei) != 2 * len(wanted):
        return chunks
    swapped = [[item for item in dealt if item in chunks[0] and item["part"] != "nucleus"
                or any(item is vowel for vowel in wanted)],
               [item for item in dealt if item in chunks[1] and item["part"] != "nucleus"
                or (item["part"] == "nucleus" and not any(item is vowel for vowel in wanted))]]
    return swapped + chunks[2:]


def topSpellings(stream: list[dict[str, Any]], limit: int = TOP_WORDS) -> frozenset[str]:
    """The `limit` most frequent distinct spellings of the stream (ties by spelling)."""
    best: dict[str, float] = {}
    for record in stream:
        if record["ortho"] not in best or record["frequency"] > best[record["ortho"]]:
            best[record["ortho"]] = record["frequency"]
    ranked = sorted(best, key=lambda ortho: (-best[ortho], ortho))
    return frozenset(ranked[:limit])


def chunkMasks(chunks: list[list[dict[str, Any]]], stream: list[dict[str, Any]]
               ) -> list[tuple[dict[str, Any], int]]:
    """§2.6: `(record, mask)` pairs. A phoneme record (empty star/hash code, no
    feature group) NEEDS the lessons of its per-finger keypresses and of every chord
    (a multi-key keypress) all of whose keys one of its strokes holds -- the trainer's
    own `usesNew` test -- as a bitmask over `chunks`; records with a keypress no lesson
    introduces are left out."""
    chunkOfKeypress = {item["keypress"]: i for i, chunk in enumerate(chunks) for item in chunk}
    chords = [(i, frozenset(item["keypress"])) for i, chunk in enumerate(chunks)
              for item in chunk if len(item["keypress"]) >= 2]
    records: list[tuple[dict[str, Any], int]] = []
    for record in stream:
        if record["_code"] != "" or record["_groups"]:
            continue
        if not all(keypress in chunkOfKeypress for keypress in record["_keyps"]):
            continue
        mask = 0
        for keypress in record["_keyps"]:
            mask |= 1 << chunkOfKeypress[keypress]
        for stroke in record["strokes"]:
            strokeKeys = frozenset(stroke)
            for i, keys in chords:
                if keys <= strokeKeys:
                    mask |= 1 << i
        records.append((record, mask))
    return records


def chunkDependencies(chunks: list[list[dict[str, Any]]], fingerAssignments: list[str]) -> list[int]:
    """Bitmask per lesson of the other lessons that introduce the per-finger
    components of its chords (a chord lesson comes after its components)."""
    chunkOfKeypress = {item["keypress"]: i for i, chunk in enumerate(chunks) for item in chunk}
    dependencies = [0] * len(chunks)
    for i, chunk in enumerate(chunks):
        for item in chunk:
            for part in fingerKeypressesOfStroke(item["keypress"], fingerAssignments):
                owner = chunkOfKeypress.get(part)
                if owner is not None and owner != i:
                    dependencies[i] |= 1 << owner
    return dependencies


def reorderPhonemeChunks(chunks: list[list[dict[str, Any]]],
                         masked: list[tuple[dict[str, Any], int]], top: frozenset[str],
                         dependencies: list[int]) -> list[int]:
    """§2.6: the order of the phoneme lessons (indexes into `chunks`). Lessons 1-2 stay,
    then each segment of `PHONEME_REORDER_SEGMENTS` is permuted on its own to maximize
    the words each lesson unlocks (a word is unlocked by the lesson that completes the
    lessons it needs, see `chunkMasks`): per lesson `min(n, MIN_NEW_WORDS) +
    min(lemmas, MIN_NEW_LEMMAS)` over the unlocked top-`TOP_WORDS` words, ties broken by
    `n`. The gain of a lesson depends only on the SET of lessons before it, so an exact
    DP over subsets finds the best order (ties: the smallest order). A lesson never
    precedes the lessons in its `dependencies`."""
    lemmasByMask: dict[int, set[str]] = {}
    countByMask: dict[int, int] = {}
    for record, mask in masked:
        if record["ortho"] in top:
            countByMask[mask] = countByMask.get(mask, 0) + 1
            lemmasByMask.setdefault(mask, set()).add(record["_word"].lemme)

    def gain(chunk: int, before: int) -> int:
        covered = before | 1 << chunk
        count = 0
        lemmas: set[str] = set()
        for mask, n in countByMask.items():
            if mask & ~covered == 0 and mask >> chunk & 1:
                count += n
                lemmas |= lemmasByMask[mask]
        return (min(count, MIN_NEW_WORDS) + min(len(lemmas), MIN_NEW_LEMMAS)) * 1000 + min(count, 999)

    order = list(range(FIXED_PHONEME_LESSONS))
    before = sum(1 << i for i in order)
    for start, stop in PHONEME_REORDER_SEGMENTS:
        members = list(range(start, min(stop, len(chunks))))
        best: dict[int, tuple[int, list[int]]] = {0: (0, [])}
        for subset in sorted(range(1 << len(members)), key=lambda m: (bin(m).count("1"), m)):
            if subset not in best:
                continue
            score, path = best[subset]
            covered = before | sum(1 << members[j] for j in range(len(members)) if subset >> j & 1)
            for j, chunk in enumerate(members):
                if subset >> j & 1 or dependencies[chunk] & ~covered:
                    continue
                candidate = (score + gain(chunk, covered), path + [chunk])
                target = subset | 1 << j
                if target not in best or candidate[0] > best[target][0] \
                        or (candidate[0] == best[target][0] and candidate[1] < best[target][1]):
                    best[target] = candidate
        order += best[(1 << len(members)) - 1][1]
        before |= sum(1 << chunk for chunk in members)
    return order


def selectUnlockedWords(unlocked: list[dict[str, Any]], top: frozenset[str]) -> list[dict[str, Any]]:
    """§2.6: the pool of a phoneme lesson from the records it unlocks, ranked by
    `(-frequency, ortho, steno)`. Tier 1: top-`TOP_WORDS` spellings, at most
    `MAX_PER_LEMMA` per lemma, up to `POOL_SIZE`. Tier 2 (only below `MIN_NEW_WORDS`):
    the remaining top spellings. Tier 3 (still below): the rarer unlocked words."""
    ranked = sorted(unlocked, key=lambda r: (-r["frequency"], r["ortho"], r["steno"]))
    common = [r for r in ranked if r["ortho"] in top]
    chosen: list[dict[str, Any]] = []
    perLemma: dict[str, int] = {}
    for record in common:
        lemma = record["_word"].lemme
        if len(chosen) < POOL_SIZE and perLemma.get(lemma, 0) < MAX_PER_LEMMA:
            chosen.append(record)
            perLemma[lemma] = perLemma.get(lemma, 0) + 1
    for tier in (common, [r for r in ranked if r["ortho"] not in top]):
        for record in tier:
            if len(chosen) >= MIN_NEW_WORDS:
                break
            if not any(record is picked for picked in chosen):
                chosen.append(record)
    return sorted(chosen, key=lambda r: (-r["frequency"], r["ortho"], r["steno"]))


def loadKeypressGroups(realizationReport: dict[str, Any]) -> list[dict[str, Any]]:
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
    keypressGroups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int]:
    """The FULL disambiguated theory rendered into practice-words-shaped records (no
    10,000-record cap): one record per independently-valid stroke, merged on
    `(ortho, steno)` exactly the way `util.export_practice_words` merges, plus the
    private `_`-prefixed analysis the eligibility filter and the rule texts read:
    `_word` (first Word), `_keyps` (per-finger keypresses of the phonetic strokes),
    `_phonemeParts` ((phoneme, part) pairs the word realizes in its syllables),
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

    byOrthoSteno: dict[tuple[str, str], dict[str, Any]] = {}
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
                existing["_phonemeParts"] = existing["_phonemeParts"] | phonemePartsOfWord(word)
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
                "_word": word, "_keyps": phoneticKeypresses,
                "_phonemeParts": phonemePartsOfWord(word),
                "_groups": neededGroups,
                "_code": code, "_cluster": tuple(unmarked),
                "_gramCats": {word.gramCat}, "_readings": list(readings),
            }
    records = sorted(byOrthoSteno.values(), key=lambda r: (r["ortho"], r["steno"]))
    return records, skippedWords, invalidRecords


# --- Rule-text rendering (§7) -------------------------------------------------

def _exampleOrthos(pool: list[dict[str, Any]], count: int = 3) -> list[str]:
    return [record["ortho"] for record in pool[:count]]


def _quotedExamples(orthos: list[str]) -> str:
    return ", ".join(f"« {ortho} »" for ortho in orthos)


def _keyNames(starboard: Starboard, keys: Iterable[int]) -> str:
    return ", ".join(starboard.keyDisplayName(key) for key in keys)


def phonemePartsOfWord(word: Word) -> frozenset[tuple[str, str]]:
    """The `(phoneme, syllabic part)` pairs the word's syllables realize, with the
    same onset/nucleus/coda split `Syllable.__init__` performs (consonants before
    the first vowel of a syllable go to the onset, vowels to the nucleus,
    consonants after it to the coda; a vowel-less syllable is all onset). A
    keypress's keys all sit in one part's bank, so it can only write a phoneme
    the word holds in THAT part: "voyez" realizes /w/ in its onset (left-hand
    key 9), so it is no example for the coda /w/ of -j (right-hand key 16)."""
    pairs: set[tuple[str, str]] = set()
    for syllable in word.phonemesToSyllableNames(withSilent=False):
        seenVowel = False
        for phoneme in syllable:
            if phoneme in Phoneme.nucleusPhonemes:
                pairs.add((phoneme, "nucleus"))
                seenVowel = True
            else:
                pairs.add((phoneme, "coda" if seenVowel else "onset"))
    return frozenset(pairs)


def examplesFallbackByKeypress(stream: list[dict[str, Any]]) -> dict[Keypress, tuple[dict[str, Any], ...]]:
    """Per keypress, the unmarked records of the FULL candidate stream that press it,
    most frequent first (`(-frequency, ortho, steno)`): the §7.1 example fallback for
    a phoneme the lesson's own pool covers with no word -- every phoneme of every
    introduced keypress must get at least one example. Marked records (`_code` != "")
    never serve as fallback examples: a marked word must not appear before the
    desambiguation track (§8)."""
    byFrequency = sorted(stream, key=lambda r: (-r["frequency"], r["ortho"], r["steno"]))
    index: dict[Keypress, list[dict[str, Any]]] = {}
    for record in byFrequency:
        if record["_code"] != "":
            continue
        for keypress in sorted(record["_keyps"]):
            index.setdefault(keypress, []).append(record)
    return {keypress: tuple(records) for keypress, records in index.items()}


def _examplesByPhoneme(item: dict[str, Any], pool: list[dict[str, Any]],
                       fallbackByKeypress: dict[Keypress, tuple[dict[str, Any], ...]]) -> dict[str, list[str]]:
    """Up to 3 example orthographies per phoneme of the keypress (§7.1): first the
    lesson's own pool records that press the keypress and realize the phoneme in
    the keypress's syllabic part (`_phonemeParts` -- a keypress's keys sit in one
    part's bank, so it only ever writes the phoneme there); when a phoneme has
    none, the most frequent fallback records (`examplesFallbackByKeypress`) that
    do. A record holding the phoneme in another part must not qualify: that
    occurrence is written by a different keypress, possibly the other hand
    ("voyez" realizes /w/ in its onset, so it never exemplifies the coda /w/ of
    -j)."""
    keypress, phonemes, part = item["keypress"], item["phonemes"], item["part"]
    examples: dict[str, list[str]] = {}
    for phoneme in phonemes:
        pair = (phoneme, part)
        orthos: list[str] = []
        for record in pool:
            if keypress in record["_keyps"] and pair in record["_phonemeParts"] \
                    and record["ortho"] not in orthos:
                orthos.append(record["ortho"])
        if not orthos:
            for record in fallbackByKeypress.get(keypress, ()):
                if pair in record["_phonemeParts"] and record["ortho"] not in orthos:
                    orthos.append(record["ortho"])
        examples[phoneme] = orthos[:3]
    return examples


def _inlinePhoneme(phoneme: str, orthos: list[str]) -> str:
    """`/{phoneme}/` immediately followed by its own parenthesized examples."""
    return f"/{phoneme}/" + (f" ({_quotedExamples(orthos)})" if orthos else "")


def _multiPhonemeText(phonemes: tuple[str, ...],
                      examplesByPhoneme: dict[str, list[str]]) -> str:
    """Each phoneme of an atomic multi-phoneme keypress with its own examples, one per
    line (the trainer shows the line breaks), "," ending every line but the last two and
    "ou" opening the last: `/j/ (« oeil »),\n/b/ (« arabe »)\nou /w/ (« watt »)`."""
    parts = [_inlinePhoneme(phoneme, examplesByPhoneme[phoneme]) for phoneme in phonemes]
    return ",\n".join(parts[:-1]) + f"\nou {parts[-1]}"


def phonemeRule(item: dict[str, Any], starboard: Starboard, pool: list[dict[str, Any]],
                fallbackByKeypress: dict[Keypress, tuple[dict[str, Any], ...]]) -> dict[str, Any]:
    """One key, one part, one phoneme (§7.1); each phoneme's examples sit directly
    after it. A multi-phoneme keypress is atomic, so it gets one rule listing every
    phoneme with its own examples; chord keypresses name every key. The rule carries
    its keypress's hand group (left/thumbs/right) for the intro view's grouping."""
    keypress, phonemes, part = item["keypress"], item["phonemes"], item["part"]
    examples = _examplesByPhoneme(item, pool, fallbackByKeypress)
    names = _keyNames(starboard, keypress)
    hand = handOfKeypress(keypress, starboard._fingerAssignments)
    if len(phonemes) > 1:
        detail = _multiPhonemeText(phonemes, examples)
        if len(keypress) == 1:
            text = f"La touche {names} écrit {detail}."
        else:
            text = f"Les touches {names} pressées ensemble écrivent {detail}."
    elif part == "nucleus":
        ex0 = examples[phonemes[0]]
        suffix = f" ({_quotedExamples(ex0)})" if ex0 else ""
        if len(keypress) == 1:
            text = f"La touche {names} écrit la voyelle /{phonemes[0]}/{suffix}."
        else:
            text = f"Les touches {names} pressées ensemble écrivent la voyelle /{phonemes[0]}/{suffix}."
    else:
        position = "début" if part == "onset" else "fin"
        ex0 = examples[phonemes[0]]
        suffix = f" ({_quotedExamples(ex0)})" if ex0 else ""
        if len(keypress) == 1:
            text = f"La touche {names} écrit le son /{phonemes[0]}/ en {position} de syllabe{suffix}."
        else:
            text = f"Les touches {names} pressées ensemble écrivent /{phonemes[0]}/ en {position} de syllabe{suffix}."
    return {"kind": "phoneme", "hand": hand, "text": text}


def _accordMarkerText(markers: tuple[str, ...]) -> str:
    labels: list[str] = []
    for marker in markers:
        label = ACCORD_MARKER_LABELS[marker]
        if label not in labels:
            labels.append(label)
    return " et ".join(labels)


def accordRule(group: dict[str, Any], starboard: Starboard, wordToStrokes: dict[Word, Strokes],
               pool: list[dict[str, Any]]) -> dict[str, Any]:
    """§7.2: the marked form contrasted with the same word's phonetic-theory steno."""
    touche = _keyNames(starboard, group["chosenKeys"])
    marker = _accordMarkerText(group["markers"])
    if not pool:
        return {"kind": "accord", "text": f"La touche {touche} marque {marker}."}
    first = pool[0]
    base = starboard.strokesToRTFCRE(canonicalizeStrokes(wordToStrokes[first["_word"]]))
    text = (f"La touche {touche} marque {marker} : "
            f"{first['ortho']} → {first['steno']} par rapport à {base}.")
    return {"kind": "accord", "text": text}


def verbMarkerRule(group: dict[str, Any], starboard: Starboard, pool: list[dict[str, Any]]) -> dict[str, Any]:
    """§7.3."""
    touche = _keyNames(starboard, group["chosenKeys"])
    markers = " et ".join(VERB_MARKER_LABELS[m] for m in group["markers"])
    quoted = _quotedExamples(_exampleOrthos(pool))
    text = (f"La touche {touche} marque {markers} : {quoted}." if quoted
            else f"La touche {touche} marque {markers}.")
    return {"kind": "verb-markers", "text": text}


def verbTenseRule(tenseLabel: str, touchedKeys: list[int], starboard: Starboard,
                  pool: list[dict[str, Any]]) -> dict[str, Any]:
    """§7.4: {touches} are the marker keys the tense's selected records actually press."""
    touches = _keyNames(starboard, touchedKeys)
    text = (f"Pour {tenseLabel}, les marques de conjugaison sont {touches} : "
            f"{_quotedExamples(_exampleOrthos(pool))}.")
    return {"kind": "verb-tense", "text": text}


def markRule(code: str, starboard: Starboard, pool: list[dict[str, Any]]) -> dict[str, Any]:
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
    return {"kind": "mark", "text": text}


# --- Lesson assembly (§4, §5, §6) ----------------------------------------------

def _emitLesson(lessons: list[dict[str, Any]], counters: dict[str, int], track: str, title: str,
                kind: str, sectionTitle: str, newKeys: list[int], newChords: list[list[int]],
                rules: list[dict[str, Any]], words: list[dict[str, Any]]) -> None:
    index = counters.get(track, 0) + 1
    counters[track] = index
    lessons.append({
        "id": f"{track}-{index:02d}", "track": track, "index": index,
        "sectionTitle": sectionTitle, "title": title, "kind": kind,
        "newKeys": newKeys, "newChords": newChords, "rules": rules, "words": words,
    })


def _wordsOf(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{field: record[field] for field in RECORD_FIELDS} for record in pool]


def buildLessons(
    starboard: Starboard,
    disambiguatedTheory: dict[Word, list[Strokes]],
    wordToStrokes: dict[Word, Strokes],
    readingsByWord: dict[Word, list[list[frozenset[str]]]],
    keypressGroups: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, int]]:
    """The whole `lessons.json` document: the five tracks (§4) and the flat lesson list
    in generation order, per-track indexes dense after drops (§5). Returns
    `(document, perTrackLessonCounts)`."""
    stream, skippedWords, invalidRecords = buildRecordStream(
        starboard, disambiguatedTheory, wordToStrokes, readingsByWord, keypressGroups)
    fallbackByKeypress = examplesFallbackByKeypress(stream)
    clusterMaxFrequency: dict[tuple[Any, ...], float] = {}
    for record in stream:
        cluster = record["_cluster"]
        clusterMaxFrequency[cluster] = max(clusterMaxFrequency.get(cluster, 0.0),
                                           record["frequency"])

    accordGroupIndexes = [i for i, g in enumerate(keypressGroups)
                          if set(g["markers"]) <= ACCORD_MARKER_ATOMS]
    verbGroupIndexes = [i for i in range(len(keypressGroups)) if i not in accordGroupIndexes]

    lessons: list[dict[str, Any]] = []
    counters: dict[str, int] = {}
    coveredKeypresses: frozenset[Keypress] = frozenset()
    introducedGroups: frozenset[int] = frozenset()
    introducedCodes: frozenset[str] = frozenset()

    def poolTop(predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
        return selectTopWords([record for record in stream
                               if predicate(record)
                               and eligible(record, coveredKeypresses, introducedGroups,
                                            introducedCodes)])

    # 4.1 phonemes
    chunkEntries: list[tuple[str, list[dict[str, Any]]]] = []
    for weightSum, nFingers, items in phonemeSteps(starboard):
        sectionTitle = SECTION_TITLES.get((weightSum, nFingers),
                                         f"Complexité {numberInFrench(weightSum)}")
        chunkEntries.extend((sectionTitle, chunk) for chunk in chunkStep(items))
    exchanged = exchangeFirstLessonVowels([chunk for _title, chunk in chunkEntries])
    chunkEntries = [(title, chunk) for (title, _old), chunk in zip(chunkEntries, exchanged)]
    topSet = topSpellings(stream)
    chunkList = [chunk for _title, chunk in chunkEntries]
    masked = chunkMasks(chunkList, stream)
    chunkOrder = reorderPhonemeChunks(chunkList, masked, topSet,
                                      chunkDependencies(chunkList, starboard._fingerAssignments))
    coveredMask = 0
    for chunkIndex in chunkOrder:
        sectionTitle, chunk = chunkEntries[chunkIndex]
        coveredKeypresses = coveredKeypresses | {item["keypress"] for item in chunk}
        # The pool is what the lesson UNLOCKS: eligible now, not eligible before it.
        previousMask = coveredMask
        coveredMask |= 1 << chunkIndex
        pool = selectUnlockedWords(
            [record for record, mask in masked
             if mask & ~coveredMask == 0 and mask & ~previousMask],
            topSet)
        index = counters.get("phonemes", 0) + 1
        # The title lists the phonemes the introduced keypresses write, one by one
        # ("les phonèmes R- @ 9 a -j -b -w"): an onset phoneme with a trailing
        # hyphen, a coda phoneme with a leading one, a vowel bare, as the key names
        # mark the syllable part. Ordered by hand group (gauche -> pouces -> droite),
        # within a group in the exporter's step order (§7.6), without repeats.
        def phonemeLabel(phoneme: str, part: str) -> str:
            return phoneme + "-" if part == "onset" else "-" + phoneme if part == "coda" else phoneme

        phonemesByHand = list(dict.fromkeys(
            phonemeLabel(phoneme, item["part"])
            for hand in HANDS
            for item in chunk
            if handOfKeypress(item["keypress"], starboard._fingerAssignments) == hand
            for phoneme in item["phonemes"]))
        title = f"Leçon {numberInFrench(index)} : les phonèmes {' '.join(phonemesByHand)}"
        _emitLesson(lessons, counters, "phonemes", title, "phonemes", sectionTitle,
                    sorted({key for item in chunk for key in item["keypress"]}),
                    [sorted(item["keypress"]) for item in chunk if len(item["keypress"]) >= 2],
                    [phonemeRule(item, starboard, pool, fallbackByKeypress)
                     for item in chunk],
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
        def hasTense(record: dict[str, Any], tid: Any = tenseId) -> bool:
            return bool(record["_gramCats"] & {GramCat.VER, GramCat.AUX}
                        and any(verbTenseOf(reading) == tid for reading in record["_readings"]))

        pool = poolTop(hasTense)
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
        byCode: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        canonicalByCluster: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
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
        pool = []
        for _maxFreq, _ortho, _steno, block in clusters:
            if len(pool) + len(block) > POOL_SIZE:
                break
            pool.extend(block)
        if len(pool) < MIN_DROP_POOL:
            introducedCodes = introducedCodes - {code}  # dropped: its words stay ineligible
            continue
        if code == "*":
            newKeys: list[int]
            newChords: list[list[int]]
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
                [{"kind": "affixes", "text": "Abréviations d'affixes : à venir."}],
                [])

    # 4.6 expressions (stub)
    _emitLesson(lessons, counters, "expressions", "Leçon un : à venir", "expressions",
                TRACK_TITLES["expressions"], [], [],
                [{"kind": "expressions", "text": "Abréviations d'expressions : à venir."}],
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
