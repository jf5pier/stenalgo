"""Unit tests for the lesson generator `util/export_lessons.py`: the pure helpers
(finger decomposition, ordering key, steps, chunking, star/hash codes, tense
mapping, pool ranking), the French rule-text renderers, and one full
`buildLessons` run on a tiny in-memory theory. The real inputs (starboard3h.json,
the pickles, the realization report) are multi-MB repo artifacts the unit tests
must not depend on, so every fixture here is hand-built."""

import re
import types

import pytest
from ..keyboard import Starboard
from ..word import GramCat, Word
from typing import Any
from util.export_lessons import (
    MAX_LESSON_KEYPRESSES, RECORD_FIELDS, accordRule, buildLessons, chunkStep,
    eligible, examplesFallbackByKeypress, fingerKeypressesOfStroke,
    handOfKeypress, loadKeypressGroups, markRule, numberInFrench,
    phonemeOrderingKey, phonemePartsOfWord, phonemeRule, phonemeSteps,
    selectTopWords, selectUnlockedWords, reorderPhonemeChunks, topSpellings, starHashCodeOf, verbMarkerRule, verbTenseOf, verbTenseRule,
)

STAR_KEY = 10
HASH_KEY = 15


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def starboard() -> Starboard:
    return Starboard()


# A tiny 11-keypress layout: every key needed by the rule-text tests, plus the
# two chord keypresses (8, 9) and the two-thumb (11, 13), so the phoneme track
# spans four (weightSum, nFingers) steps.
TINY_LAYOUT = (
    ((3,), "p"), ((8,), "s"), ((9,), "l"),
    ((11,), "a"), ((12,), "i"), ((13,), "e"), ((14,), "o"),
    ((16,), "t"), ((17,), "R"), ((8, 9), "E"), ((11, 13), "ô"),
)


@pytest.fixture
def starboard_with_layout() -> Starboard:
    sb = Starboard()
    for stroke, phoneme in TINY_LAYOUT:
        sb.addToLayout(stroke, phoneme)
    return sb


def _make_word(**overrides) -> Word:
    """Create a Word with sensible defaults, overriding any field."""
    defaults: dict[str, Any] = dict(
        ortho="pat",
        phonology="pat",
        lemme="pat",
        gramCat=GramCat.NOM,
        orthoGramCat=[GramCat.NOM],
        gender="m",
        number="s",
        infoVerb=None,
        rawSyllCV="p_a_t",
        rawOrthosyllCV="pat",
        frequencyBook=1.0,
        frequencyFilm=1.0,
    )
    defaults.update(overrides)
    return Word(**defaults)


# The five lemma-homophone pairs of the buildLessons fixture: (canonical ortho,
# marked ortho, phonology, phonetic stroke, film frequency of both members).
_PAIRS = (
    ("pa", "pâ", "pa", (3, 11), 5.0),
    ("sa", "ça", "sa", (8, 11), 4.0),
    ("li", "lis", "li", (9, 12), 3.0),
    ("la", "là", "la", (9, 11), 2.0),
    ("pat", "pâte", "pat", (3, 11, 16), 1.0),
)


def _fixture_theory(starboard: Starboard):
    """`(disambiguatedTheory, wordToStrokes, readingsByWord, keypressGroups)` for
    `buildLessons`: 5 star-marked homophone pairs, 2 nouns carrying a feature
    discriminating stroke (the accord groups), 3 verb forms, 1 word without
    phonetic strokes (skipped) and 1 invalid record (non-trailing reserved-only
    stroke). Every reading list is aligned with its stroke list, so the real
    `wordFeatureCombinations` machinery is never needed."""
    disambiguated: dict[Any, Any] = {}
    wordToStrokes = {}
    readingsByWord = {}
    for canonOrtho, markOrtho, phon, stroke, freq in _PAIRS:
        canon = _make_word(ortho=canonOrtho, phonology=phon, lemme=canonOrtho,
                           rawSyllCV="_".join(phon), frequencyFilm=freq,
                           frequencyBook=freq)
        marked = _make_word(ortho=markOrtho, phonology=phon, lemme=markOrtho,
                            gender="f", rawSyllCV="_".join(phon),
                            frequencyFilm=freq, frequencyBook=freq)
        wordToStrokes[canon] = wordToStrokes[marked] = (stroke,)
        disambiguated[canon] = ((stroke,),)
        disambiguated[marked] = ((stroke + (STAR_KEY,),),)
        readingsByWord[canon] = [[frozenset({"s", "m"})]]
        readingsByWord[marked] = [[frozenset({"s", "f"})]]

    sate = _make_word(ortho="sate", phonology="sat", lemme="sate", gender="f",
                      rawSyllCV="s_a_t", frequencyFilm=6.0, frequencyBook=6.0)
    sates = _make_word(ortho="sates", phonology="sat", lemme="sate", number="p",
                       rawSyllCV="s_a_t", frequencyFilm=7.0, frequencyBook=7.0)
    wordToStrokes[sate] = wordToStrokes[sates] = ((8, 11, 16),)
    # The Realization Phase's feature discriminating stroke: a reserved-free
    # stroke of its own, whose keys the accord groups' chosenKeys are a subset of.
    disambiguated[sate] = (((8, 11, 16), (14,)),)
    disambiguated[sates] = (((8, 11, 16), (17,)),)
    readingsByWord[sate] = [[frozenset({"s", "f"})]]
    readingsByWord[sates] = [[frozenset({"p", "m"})]]

    lise = _make_word(ortho="lise", phonology="lizR", lemme="lire",
                      gramCat=GramCat.VER, infoVerb="ind:pre:3s",
                      rawSyllCV="l_i_z_R", frequencyFilm=9.0, frequencyBook=9.0)
    lire = _make_word(ortho="lire", phonology="liR", lemme="lire",
                      gramCat=GramCat.VER, infoVerb="inf",
                      rawSyllCV="l_i_R", frequencyFilm=8.0, frequencyBook=8.0)
    dis = _make_word(ortho="dis", phonology="di", lemme="dire",
                     gramCat=GramCat.VER, infoVerb="imp:pre:2s",
                     rawSyllCV="d_i", frequencyFilm=7.0, frequencyBook=7.0)
    for word, stroke, reading in (
            (lise, (9, 12, 17), frozenset({"indicatif", "présent", "pers_3", "nbr_s"})),
            (lire, (9, 12, 17), frozenset({"infinitif"})),
            (dis, (8, 12), frozenset({"impératif", "présent", "pers_2", "nbr_s"}))):
        wordToStrokes[word] = (stroke,)
        disambiguated[word] = ((stroke,),)
        readingsByWord[word] = [[reading]]

    fantome = _make_word(ortho="motfantome", phonology="fo", lemme="motfantome",
                         rawSyllCV="f_o")
    disambiguated[fantome] = (((8, 11),),)  # no wordToStrokes entry -> skipped

    invalide = _make_word(ortho="invalide", phonology="sa", lemme="invalide",
                          rawSyllCV="s_a")
    wordToStrokes[invalide] = ((8, 11),)
    disambiguated[invalide] = (((STAR_KEY,), (8, 11)),)  # code None -> invalid

    report = {"keypressGroups": {
        "g1": {"markers": ["f"], "affectedWords": 5, "chosenKeys": [14]},
        "g2": {"markers": ["p", "nbr_p"], "affectedWords": 3, "chosenKeys": [17]},
        "g3": {"markers": ["infinitif", "conditionnel"], "affectedWords": 2,
               "chosenKeys": [9]},
        "g4": {"markers": ["pers_2"], "affectedWords": 1, "chosenKeys": [12]},
    }}
    return disambiguated, wordToStrokes, readingsByWord, loadKeypressGroups(report)


@pytest.fixture
def lessons(starboard_with_layout: Starboard):
    """One full `buildLessons` run over the tiny fixture theory: 5 phoneme
    lessons, 2 accord, 1 verbe (marker only; every tense pool is < 10), 1
    desambiguation (* only; # and *# pools are empty), 1 affixes stub."""
    document, counts = buildLessons(starboard_with_layout, *_fixture_theory(starboard_with_layout))
    return document, counts


def _lessonOf(document: dict, lessonId: str) -> dict:
    return next(lesson for lesson in document["lessons"] if lesson["id"] == lessonId)


def _orthosOf(lesson: dict) -> list[str]:
    return [record["ortho"] for record in lesson["words"]]


# A rule-text pool whose records need no Word objects (phonemeRule reads
# _keyps/_phonemeParts; markRule reads _code/_cluster; the verb renderers read
# nothing).
_RULE_POOL = [
    {"ortho": "sa", "steno": "s*a", "phonology": "sa",
     "_keyps": frozenset({(8,), (11,)}),
     "_phonemeParts": frozenset({("s", "onset"), ("a", "nucleus")}),
     "_code": "*", "_cluster": ((8, 11),)},
    {"ortho": "pa", "steno": "pa", "phonology": "pa",
     "_keyps": frozenset({(3,), (11,)}),
     "_phonemeParts": frozenset({("p", "onset"), ("a", "nucleus")}),
     "_code": "", "_cluster": ((8, 11),)},
    {"ortho": "mi", "steno": "mi", "phonology": "mi",
     "_keyps": frozenset({(12,)}),
     "_phonemeParts": frozenset({("m", "onset"), ("i", "nucleus")}),
     "_code": "", "_cluster": ((12,),)},
]

# A miniature full-stream fixture for the §7.1 example fallback: "te" is the
# most frequent unmarked record pressing (16,), "ta" the least frequent, and
# "ti" is marked (code "*") so it never serves as a fallback example. The
# phonologies put each word's /t/ in a coda ("at", "et", "it") -- a keypress
# only ever writes a phoneme the word holds in that keypress's syllabic part.
_FALLBACK_STREAM = [
    {"ortho": "ta", "steno": "ta", "phonology": "at", "frequency": 1.0,
     "_keyps": frozenset({(16,), (11,)}),
     "_phonemeParts": frozenset({("a", "nucleus"), ("t", "coda")}),
     "_code": "", "_cluster": ((16, 11),)},
    {"ortho": "te", "steno": "te", "phonology": "et", "frequency": 9.0,
     "_keyps": frozenset({(16,)}),
     "_phonemeParts": frozenset({("e", "nucleus"), ("t", "coda")}),
     "_code": "", "_cluster": ((16,),)},
    {"ortho": "ti", "steno": "t*i", "phonology": "it", "frequency": 8.0,
     "_keyps": frozenset({(16,)}),
     "_phonemeParts": frozenset({("i", "nucleus"), ("t", "coda")}),
     "_code": "*", "_cluster": ((16,),)},
]
_FALLBACK = examplesFallbackByKeypress(_FALLBACK_STREAM)


# ═══════════════════════════════════════════════════════════════════════════════
# fingerKeypressesOfStroke
# ═══════════════════════════════════════════════════════════════════════════════

class TestFingerKeypressesOfStroke:

    def test_single_key(self):
        assert fingerKeypressesOfStroke((2,), Starboard._fingerAssignments) == [(2,)]

    def test_same_finger_keys_group_into_one_sorted_keypress(self):
        assert fingerKeypressesOfStroke((3, 2), Starboard._fingerAssignments) == [(2, 3)]

    def test_two_fingers_ordered_by_finger_name(self):
        # key 2 -> leftPinky, key 16 -> rightIndex; "lp" sorts before "ri".
        assert fingerKeypressesOfStroke((16, 2), Starboard._fingerAssignments) \
            == [(2,), (16,)]

    def test_duplicate_keys_are_deduplicated(self):
        assert fingerKeypressesOfStroke((2, 2), Starboard._fingerAssignments) == [(2,)]

    def test_empty_stroke(self):
        assert fingerKeypressesOfStroke((), Starboard._fingerAssignments) == []

    def test_three_finger_stroke(self):
        assert fingerKeypressesOfStroke((8, 11, 16), Starboard._fingerAssignments) \
            == [(8,), (11,), (16,)]

    def test_matches_the_starboard_finger_map(self):
        # Same decomposition getStrokeCost performs: one keypress per used finger.
        sb = Starboard()
        keyps = fingerKeypressesOfStroke((8, 9, 11, 16), sb._fingerAssignments)
        assert keyps == [(8, 9), (11,), (16,)]


# ═══════════════════════════════════════════════════════════════════════════════
# phonemeOrderingKey (§2.2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemeOrderingKey:

    def test_left_thumb_nucleus(self, starboard: Starboard):
        # (11,) = thumb1key 100, one finger, rank 0, nucleus -> PART_RANK 0.
        assert phonemeOrderingKey((11,), starboard) == (100, 1, 0, 0, (11,))

    def test_index_onset(self, starboard: Starboard):
        assert phonemeOrderingKey((8,), starboard) == (100, 1, 1, 1, (8,))

    def test_index_coda(self, starboard: Starboard):
        # Same weightSum and nFingers as (8,), but coda sorts after onset.
        assert phonemeOrderingKey((16,), starboard) == (100, 1, 1, 2, (16,))

    def test_pinky_home_key_tier(self, starboard: Starboard):
        # (3,) = pinky1keyHome 125, FINGER_RANK lp = 4.
        assert phonemeOrderingKey((3,), starboard) == (125, 1, 4, 1, (3,))

    def test_same_finger_chord(self, starboard: Starboard):
        # (2, 3) = pinky2keysVertHome 175.
        assert phonemeOrderingKey((2, 3), starboard) == (175, 1, 4, 1, (2, 3))

    def test_two_finger_chord_sums_plain_per_finger_weights(self, starboard: Starboard):
        # (11,) 100 + (13,) 100; nFingers becomes the second ordering component.
        assert phonemeOrderingKey((11, 13), starboard) == (200, 2, 0, 0, (11, 13))

    def test_input_key_order_does_not_matter(self, starboard: Starboard):
        assert phonemeOrderingKey((13, 11), starboard) \
            == phonemeOrderingKey((11, 13), starboard)

    def test_illegal_sub_keypress_is_uncovered(self, starboard: Starboard):
        # (22, 25) is not a legal rightPinky keypress -> treated as uncovered.
        assert phonemeOrderingKey((22, 25), starboard) is None

    def test_plain_sum_has_no_shape_cost_and_no_discount(self, starboard: Starboard):
        # getStrokeCost adds the zigzag term (+100) then discounts 0.85**nFingers;
        # the ordering key is the raw per-finger sum.
        key = phonemeOrderingKey((2, 5), starboard)
        assert key is not None
        assert key[0] == 250
        assert starboard.getStrokeCost((2, 5), "onset") == 252
        key = phonemeOrderingKey((8, 9), starboard)
        assert key is not None
        assert key[0] == 150
        assert starboard.getStrokeCost((8, 9), "onset") == 127


# ═══════════════════════════════════════════════════════════════════════════════
# phonemeSteps (§2.3/§2.4)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemeSteps:

    def test_steps_sorted_by_weight_then_nfingers(self, starboard_with_layout: Starboard):
        assert [(weightSum, nFingers) for weightSum, nFingers, _ in
                phonemeSteps(starboard_with_layout)] \
            == [(100, 1), (125, 1), (150, 1), (200, 2)]

    def test_items_within_step_sorted_by_tail(self, starboard_with_layout: Starboard):
        _weightSum, _nFingers, items = phonemeSteps(starboard_with_layout)[0]
        # All four nuclei (finger rank 0) first, then onsets, then codas.
        assert [item["keypress"] for item in items] \
            == [(11,), (12,), (13,), (14,), (8,), (9,), (16,), (17,)]

    def test_item_shape(self, starboard_with_layout: Starboard):
        _weightSum, _nFingers, items = phonemeSteps(starboard_with_layout)[0]
        assert items[0] == {"keypress": (11,), "phonemes": ("a",), "part": "nucleus"}
        assert items[-1] == {"keypress": (17,), "phonemes": ("R",), "part": "coda"}

    def test_chord_steps(self, starboard_with_layout: Starboard):
        steps = phonemeSteps(starboard_with_layout)
        assert steps[2] == (150, 1, [{"keypress": (8, 9), "phonemes": ("E",),
                                      "part": "onset"}])
        assert steps[3] == (200, 2, [{"keypress": (11, 13), "phonemes": ("ô",),
                                      "part": "nucleus"}])

    def test_multiphone_keypress_is_atomic(self, starboard: Starboard):
        starboard.addToLayout((11,), "a")
        starboard.addToLayout((11,), "@")
        assert phonemeSteps(starboard) == [
            (100, 1, [{"keypress": (11,), "phonemes": ("a", "@"), "part": "nucleus"}])]

    def test_illegal_keypress_is_skipped(self, starboard: Starboard):
        starboard.addToLayout((22, 25), "X")
        assert phonemeSteps(starboard) == []


# ═══════════════════════════════════════════════════════════════════════════════
# chunkStep (§2.5)
# ═══════════════════════════════════════════════════════════════════════════════

def _itemsOf(parts: list[str]) -> list[dict]:
    return [{"part": part, "keypress": (i,)} for i, part in enumerate(parts)]


class TestChunkStep:

    def test_spec_worked_example(self):
        # §2.5: 4 nuclei, 2 onsets, 2 codas are dealt
        # nucleus, onset, coda, nucleus, onset, coda, nucleus, nucleus.
        items = _itemsOf(["nucleus"] * 4 + ["onset"] * 2 + ["coda"] * 2)
        chunks = chunkStep(items)
        assert [[item["keypress"] for item in chunk] for chunk in chunks] \
            == [[(0,), (4,), (6,), (1,)], [(5,), (7,), (2,), (3,)]]

    def test_chunks_have_at_most_four_keypresses(self):
        items = _itemsOf(["nucleus"] * 9)
        chunks = chunkStep(items)
        assert all(len(chunk) <= MAX_LESSON_KEYPRESSES for chunk in chunks)
        assert [len(chunk) for chunk in chunks] == [4, 4, 1]

    def test_exhausted_parts_are_skipped(self):
        # One nucleus, one onset, three codas: after nucleus and onset run out,
        # the remaining codas are dealt back to back.
        items = _itemsOf(["nucleus", "onset", "coda", "coda", "coda"])
        chunks = chunkStep(items)
        assert [[item["keypress"] for item in chunk] for chunk in chunks] \
            == [[(0,), (1,), (2,), (3,)], [(4,)]]

    def test_single_part_keeps_tail_order(self):
        items = _itemsOf(["coda", "coda", "coda"])
        assert chunkStep(items) == [items]

    def test_empty_step(self):
        assert chunkStep([]) == []


# ═══════════════════════════════════════════════════════════════════════════════
# starHashCodeOf (star-hash-marking.md §4 recomputed)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStarHashCodeOf:

    def test_no_mark_is_the_empty_code(self):
        assert starHashCodeOf(((2, 11),)) == ""

    def test_star_merged_into_the_phoneme_stroke(self):
        assert starHashCodeOf(((2, 11, STAR_KEY),)) == "*"

    def test_hash_merged_into_the_phoneme_stroke(self):
        assert starHashCodeOf(((2, 11, HASH_KEY),)) == "#"

    def test_star_and_hash_merged(self):
        assert starHashCodeOf(((2, 11, STAR_KEY, HASH_KEY),)) == "*#"

    def test_one_escalation(self):
        # First *# merged into the phoneme stroke, one trailing *# stroke.
        assert starHashCodeOf(((2, 11, STAR_KEY, HASH_KEY), (STAR_KEY, HASH_KEY))) \
            == "*# *#"

    def test_two_escalations(self):
        assert starHashCodeOf(
            ((2, 11, STAR_KEY, HASH_KEY), (STAR_KEY,), (HASH_KEY,))) == "*# *# *#"

    def test_mark_on_a_non_final_phoneme_stroke(self):
        assert starHashCodeOf(((8, HASH_KEY), (16, 17))) == "#"

    def test_multi_stroke_word_with_star_on_last_stroke(self):
        assert starHashCodeOf(((8, 11), (16, STAR_KEY))) == "*"

    def test_non_trailing_reserved_only_stroke_is_invalid(self):
        assert starHashCodeOf(((STAR_KEY,), (2, 11))) is None

    def test_lone_trailing_star_is_invalid(self):
        # A trailing reserved-only stroke escalates *# codes only: a bare * is
        # never left alone on a stroke of its own.
        assert starHashCodeOf(((2, 11, STAR_KEY), (STAR_KEY,))) is None


# ═══════════════════════════════════════════════════════════════════════════════
# verbTenseOf (§4.3)
# ═══════════════════════════════════════════════════════════════════════════════

class TestVerbTenseOf:

    @pytest.mark.parametrize("reading, tense", [
        (("indicatif", "présent"), "ind-pre"),
        (("indicatif", "imparfait"), "ind-imp"),
        (("indicatif", "future"), "ind-fut"),
        (("participe", "passé"), "par-pas"),
        (("infinitif",), "inf"),
        (("conditionnel",), "cnd"),
        (("subjonctif",), "sub"),
        (("impératif",), "imp"),
        # Person/number atoms ride along without breaking the mapping.
        (("indicatif", "présent", "pers_1", "nbr_s"), "ind-pre"),
    ])
    def test_the_eight_tenses(self, reading, tense):
        assert verbTenseOf(frozenset(reading)) == tense

    @pytest.mark.parametrize("reading", [
        ("participe",),        # participe without passé
        ("indicatif",),        # no tense atom
        (),                    # not a verb reading at all
        ("f", "p"),            # a noun's gender/number atoms
    ])
    def test_non_tense_readings(self, reading):
        assert verbTenseOf(frozenset(reading)) is None

    def test_infinitif_wins_over_later_moods(self):
        assert verbTenseOf(frozenset({"infinitif", "conditionnel"})) == "inf"


# ═══════════════════════════════════════════════════════════════════════════════
# selectTopWords (§5) and loadKeypressGroups
# ═══════════════════════════════════════════════════════════════════════════════

class TestSelectTopWords:

    def test_ranks_by_frequency_then_ortho_then_steno(self):
        records = [
            {"frequency": 1.0, "ortho": "zz", "steno": "a"},
            {"frequency": 3.0, "ortho": "bb", "steno": "x"},
            {"frequency": 3.0, "ortho": "aa", "steno": "y"},
            {"frequency": 3.0, "ortho": "aa", "steno": "x"},
        ]
        assert [r["steno"] for r in selectTopWords(records)] == ["x", "y", "x", "a"]

    def test_limit(self):
        records = [{"frequency": float(i), "ortho": str(i), "steno": ""} for i in range(9)]
        assert len(selectTopWords(records, limit=2)) == 2
        assert [r["ortho"] for r in selectTopWords(records, limit=2)] == ["8", "7"]

    def test_default_limit_is_the_pool_size(self):
        records = [{"frequency": float(i), "ortho": str(i), "steno": ""} for i in range(51)]
        assert len(selectTopWords(records)) == 50

    def test_empty(self):
        assert selectTopWords([]) == []


class TestLoadKeypressGroups:

    def test_ordered_by_affected_words_then_markers_then_id(self):
        report = {"keypressGroups": {
            "gid-b": {"markers": ["pers_2"], "affectedWords": 1, "chosenKeys": [12, 9]},
            "gid-a": {"markers": ["f"], "affectedWords": 5, "chosenKeys": [14]},
            "gid-c": {"markers": ["nbr_s", "m"], "affectedWords": 5, "chosenKeys": [16]},
        }}
        groups = loadKeypressGroups(report)
        assert [g["id"] for g in groups] == ["gid-a", "gid-c", "gid-b"]

    def test_normalizes_markers_and_chosen_keys_to_sorted_tuples(self):
        report = {"keypressGroups": {
            "gid-b": {"markers": ["pers_2"], "affectedWords": 1, "chosenKeys": [12, 9]},
            "gid-a": {"markers": ["f"], "affectedWords": 5, "chosenKeys": [14]},
            "gid-c": {"markers": ["nbr_s", "m"], "affectedWords": 5, "chosenKeys": [16]},
        }}
        groups = loadKeypressGroups(report)
        assert groups[0]["markers"] == ("f",)
        assert groups[0]["chosenKeys"] == (14,)
        assert groups[1]["markers"] == ("m", "nbr_s")
        assert groups[2]["chosenKeys"] == (9, 12)


# ═══════════════════════════════════════════════════════════════════════════════
# eligible (§3)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEligible:

    def test_eligible_when_everything_is_covered(self):
        record = {"_code": "", "_keyps": frozenset({(8,)}), "_groups": frozenset({1})}
        assert eligible(record, frozenset({(8,)}), frozenset({1}), frozenset())

    def test_uncovered_keypress(self):
        record = {"_code": "", "_keyps": frozenset({(8,)}), "_groups": frozenset({1})}
        assert not eligible(record, frozenset({(9,)}), frozenset({1}), frozenset())

    def test_unintroduced_group(self):
        record = {"_code": "", "_keyps": frozenset({(8,)}), "_groups": frozenset({1})}
        assert not eligible(record, frozenset({(8,)}), frozenset(), frozenset())

    def test_unintroduced_code_is_gated(self):
        record = {"_code": "*", "_keyps": frozenset({(8,)}), "_groups": frozenset()}
        assert not eligible(record, frozenset({(8,)}), frozenset(), frozenset())
        assert eligible(record, frozenset({(8,)}), frozenset(), frozenset({"*"}))

    def test_invalid_code_is_never_eligible(self):
        record = {"_code": None, "_keyps": frozenset({(8,)}), "_groups": frozenset()}
        assert not eligible(record, frozenset({(8,)}), frozenset(), frozenset({"*"}))

    def test_empty_code_always_passes_the_code_gate(self):
        record = {"_code": "", "_keyps": frozenset({(8,)}), "_groups": frozenset()}
        assert eligible(record, frozenset({(8,)}), frozenset(), frozenset())


# ═══════════════════════════════════════════════════════════════════════════════
# numberInFrench (§7.6/§8: digits 1, 2, 5, 8, 9 are IPA-mapped, so numbers in
# prose are spelled out)
# ═══════════════════════════════════════════════════════════════════════════════

class TestNumberInFrench:

    @pytest.mark.parametrize("n, words", [
        (0, "zéro"), (1, "un"), (8, "huit"), (9, "neuf"), (11, "onze"),
        (16, "seize"), (17, "dix-sept"), (20, "vingt"), (21, "vingt et un"),
        (22, "vingt-deux"), (30, "trente"), (55, "cinquante-cinq"),
        (61, "soixante et un"), (70, "soixante-dix"), (71, "soixante et onze"),
        (79, "soixante-dix-neuf"), (80, "quatre-vingts"),
        (81, "quatre-vingt-un"), (91, "quatre-vingt-onze"),
        (99, "quatre-vingt-dix-neuf"), (100, "cent"), (101, "cent un"),
        (125, "cent vingt-cinq"), (200, "deux cents"), (300, "trois cents"),
        (999, "neuf cent quatre-vingt-dix-neuf"),
    ])
    def test_cardinals(self, n, words):
        assert numberInFrench(n) == words

    @pytest.mark.parametrize("n", [-1, 1000])
    def test_out_of_range(self, n):
        with pytest.raises(AssertionError):
            numberInFrench(n)

    @pytest.mark.parametrize("n", range(100))
    def test_no_ipa_mapped_character(self, n):
        # The whole point (spec §8): French number words never contain a
        # character of Notation.elm's ipaByXSampa table.
        ipaByXSampa = set("E@°§5O9821RZSNG")
        assert not (set(numberInFrench(n)) & ipaByXSampa)


# ═══════════════════════════════════════════════════════════════════════════════
# handOfKeypress (§6/§7.1: left / thumbs / right)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHandOfKeypress:

    def test_finger_to_hand(self):
        fa = Starboard._fingerAssignments
        assert handOfKeypress((3,), fa) == "left"      # lp: left pinky
        assert handOfKeypress((8,), fa) == "left"      # li: left index
        assert handOfKeypress((11,), fa) == "thumbs"   # lt: left thumb
        assert handOfKeypress((13,), fa) == "thumbs"   # rt: right thumb
        assert handOfKeypress((16,), fa) == "right"    # ri: right index
        assert handOfKeypress((24,), fa) == "right"    # rp: right pinky

    def test_chord_keypress_takes_its_single_fingers_hand(self):
        fa = Starboard._fingerAssignments
        assert handOfKeypress((8, 9), fa) == "left"     # both keys on li
        assert handOfKeypress((11, 13), fa) == "thumbs"  # lt + rt


# ═══════════════════════════════════════════════════════════════════════════════
# phonemePartsOfWord (the (phoneme, syllabic part) pairs a word realizes)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemePartsOfWord:

    def test_consonants_split_onset_then_coda_around_the_vowels(self):
        # "voyez" = v w a | j e: the /v w/ cluster precedes its syllable's vowel
        # (onset), while the /j/ of "je" precedes its own syllable's vowel (also
        # an onset) -- /w/ and /j/ are consonants, so each takes its syllable's
        # position, not the word's.
        word = _make_word(ortho="voyez", phonology="vwaje", rawSyllCV="v_w_a|j_e")
        assert phonemePartsOfWord(word) == frozenset(
            {("v", "onset"), ("w", "onset"), ("a", "nucleus"),
             ("j", "onset"), ("e", "nucleus")})

    def test_a_consonant_after_its_syllables_vowel_is_coda(self):
        # "oeil" = 8 j: the /j/ follows its syllable's vowel -> coda (the -j
        # keypress of the real layout).
        word = _make_word(ortho="oeil", phonology="8j", rawSyllCV="8_j")
        assert phonemePartsOfWord(word) == frozenset({("8", "nucleus"), ("j", "coda")})

    def test_vowelless_syllable_is_entirely_onset(self):
        word = _make_word(ortho="ab", phonology="ba", rawSyllCV="b|a")
        assert phonemePartsOfWord(word) == frozenset({("b", "onset"), ("a", "nucleus")})

    def test_silent_phonemes_are_dropped(self):
        # "#" is the silent marker: withSilent=False strips it before splitting.
        word = _make_word(ortho="pat", phonology="pat", rawSyllCV="p_a_t_#")
        assert ("#", "coda") not in phonemePartsOfWord(word)
        assert phonemePartsOfWord(word) == frozenset(
            {("p", "onset"), ("a", "nucleus"), ("t", "coda")})


# ═══════════════════════════════════════════════════════════════════════════════
# examplesFallbackByKeypress (§7.1 example fallback)
# ═══════════════════════════════════════════════════════════════════════════════

class TestExamplesFallbackByKeypress:

    def test_most_frequent_unmarked_first(self):
        index = examplesFallbackByKeypress(_FALLBACK_STREAM)
        assert [r["ortho"] for r in index[(16,)]] == ["te", "ta"]

    def test_marked_records_never_serve_as_fallback(self):
        index = examplesFallbackByKeypress(_FALLBACK_STREAM)
        assert "ti" not in [r["ortho"] for r in index[(16,)]]

    def test_indexed_by_every_keypress_of_the_record(self):
        index = examplesFallbackByKeypress(_FALLBACK_STREAM)
        assert set(index) == {(11,), (16,)}

    def test_frequency_ties_break_on_ortho_then_steno(self):
        stream = [
            {"ortho": "zz", "steno": "b", "phonology": "t", "frequency": 2.0,
             "_keyps": frozenset({(16,)}), "_code": ""},
            {"ortho": "aa", "steno": "z", "phonology": "t", "frequency": 2.0,
             "_keyps": frozenset({(16,)}), "_code": ""},
            {"ortho": "aa", "steno": "a", "phonology": "t", "frequency": 2.0,
             "_keyps": frozenset({(16,)}), "_code": ""},
        ]
        assert [r["steno"] for r in examplesFallbackByKeypress(stream)[(16,)]] \
            == ["a", "z", "b"]


# ═══════════════════════════════════════════════════════════════════════════════
# Rule-text renderers (§7)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemeRule:

    def test_onset(self, starboard_with_layout: Starboard):
        item = {"keypress": (8,), "phonemes": ("s",), "part": "onset"}
        assert phonemeRule(item, starboard_with_layout, _RULE_POOL, _FALLBACK) == {
            "kind": "phoneme", "hand": "left",
            "text": "La touche s- écrit le son /s/ en début de syllabe (« sa »)."}

    def test_nucleus(self, starboard_with_layout: Starboard):
        item = {"keypress": (11,), "phonemes": ("a",), "part": "nucleus"}
        assert phonemeRule(item, starboard_with_layout, _RULE_POOL, _FALLBACK) == {
            "kind": "phoneme", "hand": "thumbs",
            "text": "La touche a- écrit la voyelle /a/ (« sa », « pa »)."}

    def test_coda_falls_back_to_frequent_stream_words(self, starboard_with_layout: Starboard):
        # No pool word presses (16,): the §7.1 fallback supplies the most
        # frequent unmarked stream records pressing it with /t/ -- "ti" is
        # marked (code "*") and never shows up.
        item = {"keypress": (16,), "phonemes": ("t",), "part": "coda"}
        assert phonemeRule(item, starboard_with_layout, [], _FALLBACK) == {
            "kind": "phoneme", "hand": "right",
            "text": "La touche -t écrit le son /t/ en fin de syllabe (« te », « ta »)."}

    def test_no_examples_anywhere_leaves_the_phoneme_bare(self, starboard_with_layout: Starboard):
        item = {"keypress": (16,), "phonemes": ("v",), "part": "coda"}
        assert phonemeRule(item, starboard_with_layout, [], _FALLBACK) == {
            "kind": "phoneme", "hand": "right",
            "text": "La touche -t écrit le son /v/ en fin de syllabe."}

    def test_multiphone_keypress_carries_each_phonemes_own_examples(
            self, starboard_with_layout: Starboard):
        # "mi" presses (12,) and contains /i/, so /i/ alone gets examples.
        item = {"keypress": (12,), "phonemes": ("i", "e", "o"), "part": "nucleus"}
        assert phonemeRule(item, starboard_with_layout, _RULE_POOL, _FALLBACK) == {
            "kind": "phoneme", "hand": "thumbs",
            "text": "La touche i- écrit /i/ (« mi »),\n/e/\nou /o/."}

    def test_two_phonemes_join_with_ou(self, starboard_with_layout: Starboard):
        # /e/ never occurs in a coda (it is a vowel), so only /t/ gets examples.
        item = {"keypress": (16,), "phonemes": ("t", "e"), "part": "coda"}
        assert phonemeRule(item, starboard_with_layout, [], _FALLBACK) == {
            "kind": "phoneme", "hand": "right",
            "text": "La touche -t écrit /t/ (« te », « ta »)\nou /e/."}

    def test_chord_onset(self, starboard_with_layout: Starboard):
        item = {"keypress": (8, 9), "phonemes": ("E",), "part": "onset"}
        assert phonemeRule(item, starboard_with_layout, [], _FALLBACK) == {
            "kind": "phoneme", "hand": "left",
            "text": "Les touches s-, l- pressées ensemble écrivent /E/ en début de syllabe."}

    def test_two_thumb_nucleus_chord(self, starboard_with_layout: Starboard):
        item = {"keypress": (11, 13), "phonemes": ("ô",), "part": "nucleus"}
        assert phonemeRule(item, starboard_with_layout, [], _FALLBACK) == {
            "kind": "phoneme", "hand": "thumbs",
            "text": "Les touches a-, -e pressées ensemble écrivent la voyelle /ô/."}

    def test_examples_come_from_pool_records_pressing_the_keypress_with_the_phoneme(
            self, starboard_with_layout: Starboard):
        item = {"keypress": (3,), "phonemes": ("p",), "part": "onset"}
        # "sa" does not press key 3 and the fallback has nothing for (3,), so
        # only "pa" is an example.
        rule = phonemeRule(item, starboard_with_layout, _RULE_POOL, _FALLBACK)
        assert rule["text"].endswith("(« pa »).")

    def test_a_phoneme_held_in_another_part_is_not_an_example(
            self, starboard_with_layout: Starboard):
        # Regression: the coda keypress (16,) of the real layout writes /j/, /b/
        # and /w/, and the old match ("presses the keypress" AND "phoneme
        # anywhere in the phonology") served "voyez"-like words as /w/ examples
        # even though their /w/ sits in the onset, written by the OTHER hand's
        # key -- here "croyais" presses (16,) with its coda /j/ but holds /w/ in
        # its onset, so /w/ stays bare while /j/ takes the example.
        stream = [
            {"ortho": "croyais", "steno": "croyais", "phonology": "kRwajE",
             "frequency": 7.0, "_keyps": frozenset({(16,), (9,)}),
             "_phonemeParts": frozenset({("k", "onset"), ("R", "onset"),
                                         ("w", "onset"), ("a", "nucleus"),
                                         ("j", "coda"), ("E", "nucleus")}),
             "_code": "", "_cluster": ((16,),)},
        ]
        fallback = examplesFallbackByKeypress(stream)
        item = {"keypress": (16,), "phonemes": ("j", "w"), "part": "coda"}
        rule = phonemeRule(item, starboard_with_layout, [], fallback)
        assert rule["text"] == "La touche -t écrit /j/ (« croyais »)\nou /w/."


class TestAccordRule:

    def _pool(self):
        word = _make_word(ortho="sate", phonology="sat", gender="f")
        record = {"ortho": "sate", "steno": "sat/o", "_word": word}
        return record, {word: ((8, 11, 16),)}

    def test_contrast_with_the_phonetic_steno(self, starboard_with_layout: Starboard):
        first, wordToStrokes = self._pool()
        group = {"chosenKeys": (14,), "markers": ("f",)}
        assert accordRule(group, starboard_with_layout, wordToStrokes, [first]) == {
            "kind": "accord",
            "text": "La touche -o marque le féminin : sate → sat/o par rapport à sat."}

    def test_empty_pool(self, starboard_with_layout: Starboard):
        _first, wordToStrokes = self._pool()
        group = {"chosenKeys": (14,), "markers": ("f",)}
        assert accordRule(group, starboard_with_layout, wordToStrokes, []) == {
            "kind": "accord", "text": "La touche -o marque le féminin."}

    def test_duplicate_marker_labels_are_deduplicated(self, starboard_with_layout: Starboard):
        # {nbr_p, p} both render as "le pluriel".
        first, wordToStrokes = self._pool()
        group = {"chosenKeys": (14,), "markers": ("nbr_p", "p")}
        rule = accordRule(group, starboard_with_layout, wordToStrokes, [first])
        assert rule["text"] == ("La touche -o marque le pluriel : "
                                "sate → sat/o par rapport à sat.")

    def test_distinct_markers_join_with_et(self, starboard_with_layout: Starboard):
        first, wordToStrokes = self._pool()
        group = {"chosenKeys": (14,), "markers": ("f", "p")}
        rule = accordRule(group, starboard_with_layout, wordToStrokes, [first])
        assert rule["text"].startswith("La touche -o marque le féminin et le pluriel :")


class TestVerbMarkerRule:

    def test_with_examples(self, starboard_with_layout: Starboard):
        group = {"chosenKeys": (9,), "markers": ("conditionnel", "infinitif")}
        assert verbMarkerRule(group, starboard_with_layout, _RULE_POOL) == {
            "kind": "verb-markers",
            "text": ("La touche l- marque le conditionnel et l'infinitif : "
                     "« sa », « pa », « mi ».")}

    def test_without_examples(self, starboard_with_layout: Starboard):
        group = {"chosenKeys": (9,), "markers": ("conditionnel", "infinitif")}
        assert verbMarkerRule(group, starboard_with_layout, []) == {
            "kind": "verb-markers",
            "text": "La touche l- marque le conditionnel et l'infinitif."}

    def test_person_labels_are_spelled_out(self, starboard_with_layout: Starboard):
        # "1re"/"2e"/"3e" are forbidden: the digits 1 and 2 are IPA-mapped in the
        # trainer's Notation.elm table, and the IPA toggle rewrites the whole rule
        # text (spec §8).
        group = {"chosenKeys": (9,), "markers": ("pers_1", "pers_2", "pers_3")}
        rule = verbMarkerRule(group, starboard_with_layout, [])
        assert rule["text"] == ("La touche l- marque la première personne et "
                                "la deuxième personne et la troisième personne.")


class TestVerbTenseRule:

    def test_names_the_touched_marker_keys(self, starboard_with_layout: Starboard):
        rule = verbTenseRule("l'indicatif présent", [12, 14], starboard_with_layout,
                             _RULE_POOL)
        assert rule == {
            "kind": "verb-tense",
            "text": ("Pour l'indicatif présent, les marques de conjugaison sont "
                     "i-, -o : « sa », « pa », « mi ».")}


class TestMarkRule:

    def test_first_complete_contrast(self, starboard: Starboard):
        # markRule only reads _code/_cluster/ortho/steno; reserved key names
        # don't need a loaded layout.
        pool = [
            {"ortho": "sa", "steno": "s*a", "_code": "*", "_cluster": ((8, 11),)},
            {"ortho": "pa", "steno": "pa", "_code": "", "_cluster": ((8, 11),)},
        ]
        assert markRule("*", starboard, pool) == {
            "kind": "mark",
            "text": "La marque * (*) distingue sa (s*a) de pa (pa)."}

    def test_prefers_a_complete_contrast_over_an_unpaired_marked_record(self,
                                                                       starboard: Starboard):
        pool = [
            {"ortho": "zoz", "steno": "z", "_code": "*", "_cluster": ((9, 12),)},
            {"ortho": "sa", "steno": "s*a", "_code": "*", "_cluster": ((8, 11),)},
            {"ortho": "pa", "steno": "pa", "_code": "", "_cluster": ((8, 11),)},
        ]
        rule = markRule("*", starboard, pool)
        assert rule["text"] == "La marque * (*) distingue sa (s*a) de pa (pa)."

    def test_fallback_to_the_marked_record_alone(self, starboard: Starboard):
        pool = [{"ortho": "lis", "steno": "l*i", "_code": "#", "_cluster": ((9, 12),)}]
        assert markRule("#", starboard, pool) == {
            "kind": "mark",
            "text": "La marque # (#) s'ajoute à la fin du mot : lis (l*i)."}

    def test_empty_pool(self, starboard: Starboard):
        assert markRule("*#", starboard, []) == {
            "kind": "mark", "text": "La marque *# (*, #)."}


# ═══════════════════════════════════════════════════════════════════════════════
# buildLessons (§4-§6)
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildLessonsDocument:

    def test_six_tracks_in_order(self, lessons):
        document, _counts = lessons
        assert document["tracks"] == [
            {"id": "phonemes", "title": "Phonèmes",
             "description": "Les touches et les sons, de la plus simple à la plus complexe."},
            {"id": "accord", "title": "Accord (genre et nombre)",
             "description": "Les marques de genre et de nombre."},
            {"id": "verbe", "title": "Verbes",
             "description": "Les marques de conjugaison, temps par temps."},
            {"id": "desambiguation", "title": "Désambiguïsation",
             "description": "Les marques * et # qui distinguent les homophones."},
            {"id": "affixes", "title": "Affixes",
             "description": "Une règle d'abréviation par leçon : un contour court pour chaque mot, le long reste accepté."},
            {"id": "expressions", "title": "Abréviations d'expressions",
             "description": "Les particules qui se joignent au mot voisin, leurs combinaisons et les abréviations d'expressions : un contour court, le long reste accepté."},
        ]

    def test_per_track_counts_and_stream_counters(self, lessons):
        _document, counts = lessons
        assert counts == {"phonemes": 5, "accord": 2, "verbe": 1, "desambiguation": 1,
                          "affixes": 1, "expressions": 1, "_records": 15, "_skippedWords": 1,
                          "_invalidRecords": 1}

    def test_lesson_ids_are_dense_and_generation_ordered(self, lessons):
        document, counts = lessons
        byTrack: dict[str, list[str]] = {}
        for lesson in document["lessons"]:
            byTrack.setdefault(lesson["track"], []).append(lesson["id"])
        assert byTrack == {trackId: [f"{trackId}-{index:02d}" for index in range(
            1, counts[trackId] + 1)] for trackId in
            ("phonemes", "accord", "verbe", "desambiguation", "affixes", "expressions")}
        # Flat list in track order: the track of each lesson never goes back.
        trackOrder = [lesson["track"] for lesson in document["lessons"]]
        assert trackOrder == sorted(trackOrder, key=[
            "phonemes", "accord", "verbe", "desambiguation", "affixes", "expressions"].index)

    def test_words_reuse_the_practice_words_record_shape(self, lessons):
        document, _counts = lessons
        for lesson in document["lessons"]:
            for record in lesson["words"]:
                assert tuple(record.keys()) == RECORD_FIELDS

    def test_only_phoneme_rules_carry_a_hand(self, lessons):
        document, _counts = lessons
        for lesson in document["lessons"]:
            for rule in lesson["rules"]:
                if lesson["track"] == "phonemes":
                    assert rule["hand"] in ("left", "thumbs", "right")
                else:
                    assert "hand" not in rule

    def test_new_keys_stay_inside_the_keyboard_and_skip_the_unused_marks(self, lessons):
        document, _counts = lessons
        for lesson in document["lessons"]:
            for key in lesson["newKeys"]:
                assert 0 <= key < 26
                assert key not in (0, 1)
            for chord in lesson["newChords"]:
                assert all(key not in (0, 1) for key in chord)

    def test_no_marked_word_before_the_desambiguation_track(self, lessons):
        document, _counts = lessons
        for lesson in document["lessons"]:
            if lesson["track"] in ("phonemes", "accord", "verbe"):
                for record in lesson["words"]:
                    for stroke in record["strokes"]:
                        assert STAR_KEY not in stroke
                        assert HASH_KEY not in stroke

    def test_regeneration_is_identical(self, starboard_with_layout: Starboard):
        theory = _fixture_theory(starboard_with_layout)
        document1, counts1 = buildLessons(starboard_with_layout, *theory)
        document2, counts2 = buildLessons(starboard_with_layout, *theory)
        assert document1 == document2
        assert counts1 == counts2

    def test_ipa_unsafe_wording_is_gone(self, lessons):
        # Spec §8: the digits 1 and 2 are IPA-mapped in the trainer's
        # Notation.elm table and the IPA toggle rewrites whole strings, so the
        # person labels and the affixes stub must use the new spellings.
        document, _counts = lessons
        strings = [t["title"] for t in document["tracks"]] \
            + [t["description"] for t in document["tracks"]]
        for lesson in document["lessons"]:
            strings += [lesson["title"], lesson["sectionTitle"]]
            strings += [rule["text"] for rule in lesson["rules"]]
            strings += [rule.get("hand", "") for rule in lesson["rules"]]
        for s in strings:
            assert "1re" not in s and "2e personne" not in s and "3e personne" not in s
            assert "Règles d'abréviation" not in s
        assert any("la deuxième personne" in s for s in strings)
        assert any("Abréviations d'affixes : à venir." in s for s in strings)

    def test_lesson_numbers_are_spelled_out(self, lessons):
        # Titles may carry digits only as phonemes (e.g. "Leçon quinze : 1" on
        # the real layout); the lesson number itself is a French word.
        document, _counts = lessons
        for lesson in document["lessons"]:
            assert not re.match(r"Leçon \d", lesson["title"])
            assert lesson["title"].startswith("Leçon ")


class TestBuildLessonsPhonemesTrack:

    def test_first_lesson(self, lessons):
        document, _counts = lessons
        lesson = _lessonOf(document, "phonemes-01")
        assert lesson["sectionTitle"] == "Les premières touches"
        # The title names the PHONEMES the introduced keypresses write, ordered by
        # hand group gauche -> pouces -> droite, within a group in deal order:
        # s (left), a and i (thumbs), t (right).
        assert lesson["title"] == "Leçon un : les phonèmes s- a i -t"
        assert lesson["kind"] == "phonemes"
        # Round-robin deal: nucleus (11), onset (8), coda (16), nucleus (12).
        assert lesson["newKeys"] == [8, 11, 12, 16]
        assert lesson["newChords"] == []

    def test_titles_order_key_names_by_hand_group(self, lessons):
        document, _counts = lessons
        assert _lessonOf(document, "phonemes-02")["title"] \
            == "Leçon deux : les phonèmes l- e o -R"
        assert _lessonOf(document, "phonemes-03")["title"] == "Leçon trois : les phonèmes p-"

    def test_first_lesson_rules_in_deal_order_with_hands(self, lessons):
        document, _counts = lessons
        rules = _lessonOf(document, "phonemes-01")["rules"]
        assert rules == [
            {"kind": "phoneme", "hand": "thumbs",
             "text": "La touche a- écrit la voyelle /a/ (« sa »)."},
            {"kind": "phoneme", "hand": "left",
             "text": "La touche s- écrit le son /s/ en début de syllabe (« sa »)."},
            # No pool word presses (16,): the §7.1 fallback supplies the most
            # frequent unmarked stream words pressing it with /t/ ("pâte" is
            # star-marked and never shows).
            {"kind": "phoneme", "hand": "right",
             "text": ("La touche -t écrit le son /t/ en fin de syllabe "
                      "(« sates », « sate », « pat »).")},
            {"kind": "phoneme", "hand": "thumbs",
             "text": "La touche i- écrit la voyelle /i/ (« dis »)."},
        ]

    def test_lesson_words_use_only_covered_keypresses(self, lessons):
        document, _counts = lessons
        # Only "dis" (keys 8, 12) and "sa" (8, 11) are writable with lesson 1's
        # four keypresses: the marked pairs are code-gated, the accord nouns
        # group-gated, and lise/lire/li/la wait for keys 9 and 17.
        assert _orthosOf(_lessonOf(document, "phonemes-01")) == ["dis", "sa"]
        # A phoneme lesson's pool is the words it UNLOCKS (§2.6): lesson 2 adds keys 9,
        # 13, 14, 17, so lise and lire become writable (dis and sa stay lesson 1's).
        assert _orthosOf(_lessonOf(document, "phonemes-02")) == ["lise", "lire", "li", "la"]
        # Lesson 3 adds key 3: the pa/pat pair's canonical members join.
        assert _orthosOf(_lessonOf(document, "phonemes-03")) == ["pa", "pat"]

    def test_sections_follow_the_weight_tiers(self, lessons):
        document, _counts = lessons
        assert _lessonOf(document, "phonemes-01")["sectionTitle"] == "Les premières touches"
        assert _lessonOf(document, "phonemes-02")["sectionTitle"] == "Les premières touches"
        assert _lessonOf(document, "phonemes-03")["sectionTitle"] == "Les autres doigts"
        assert _lessonOf(document, "phonemes-04")["sectionTitle"] == "Accords à deux touches"
        assert _lessonOf(document, "phonemes-05")["sectionTitle"] == "Voyelles à deux pouces"

    def test_chord_lessons_declare_new_chords(self, lessons):
        document, _counts = lessons
        lesson4 = _lessonOf(document, "phonemes-04")
        assert lesson4["title"] == "Leçon quatre : les phonèmes E-"
        assert lesson4["newKeys"] == [8, 9]
        assert lesson4["newChords"] == [[8, 9]]
        assert lesson4["rules"][0] == {
            "kind": "phoneme", "hand": "left",
            "text": "Les touches s-, l- pressées ensemble écrivent /E/ en début de syllabe."}
        lesson5 = _lessonOf(document, "phonemes-05")
        assert lesson5["title"] == "Leçon cinq : les phonèmes ô"
        assert lesson5["newKeys"] == [11, 13]
        assert lesson5["newChords"] == [[11, 13]]
        assert lesson5["rules"][0] == {
            "kind": "phoneme", "hand": "thumbs",
            "text": "Les touches a-, -e pressées ensemble écrivent la voyelle /ô/."}


class TestBuildLessonsAccordTrack:

    def test_one_lesson_per_gender_number_group_in_affected_words_order(self, lessons):
        document, _counts = lessons
        lesson1 = _lessonOf(document, "accord-01")
        assert lesson1["title"] == "Leçon un : le féminin"
        assert lesson1["newKeys"] == [14]
        assert _orthosOf(lesson1) == ["sate"]
        assert lesson1["rules"] == [{
            "kind": "accord",
            "text": "La touche -o marque le féminin : sate → sat/o par rapport à sat."}]
        lesson2 = _lessonOf(document, "accord-02")
        assert lesson2["title"] == "Leçon deux : le pluriel"
        assert lesson2["newKeys"] == [17]
        assert _orthosOf(lesson2) == ["sates"]
        assert lesson2["rules"] == [{
            "kind": "accord",
            "text": "La touche -R marque le pluriel : sates → sat/-R par rapport à sat."}]

    def test_acced_record_ships_its_marked_strokes(self, lessons):
        document, _counts = lessons
        record = _lessonOf(document, "accord-01")["words"][0]
        assert record == {"ortho": "sate", "before": "la", "after": "",
                          "label": "nom, f. sg.", "phonology": "sat", "steno": "sat/o",
                          "strokes": [[8, 11, 16], [14]], "frequency": 6.0}


class TestBuildLessonsVerbeTrack:

    def test_marker_lesson_always_ships(self, lessons):
        document, counts = lessons
        lesson = _lessonOf(document, "verbe-01")
        assert lesson["title"] == "Leçon un : les marques de conjugaison"
        assert lesson["newKeys"] == [9, 12]  # union of the two verb groups' chosenKeys
        assert _orthosOf(lesson) == ["lise", "lire", "dis"]
        assert lesson["rules"] == [
            {"kind": "verb-markers",
             "text": "La touche l- marque le conditionnel et l'infinitif : "
                     "« lise », « lire », « dis »."},
            {"kind": "verb-markers",
             "text": "La touche i- marque la deuxième personne : « lise », « lire », « dis »."},
        ]
        # Every tense pool has fewer than 10 records: all 8 tense lessons drop.
        assert counts["verbe"] == 1

    def test_verb_record_keeps_its_reading_label(self, lessons):
        document, _counts = lessons
        record = _lessonOf(document, "verbe-01")["words"][0]
        assert record == {"ortho": "lise", "before": "il", "after": "",
                          "label": "indicatif présent, 3e sg.", "phonology": "lizR",
                          "steno": "liR", "strokes": [[9, 12, 17]], "frequency": 9.0}


class TestBuildLessonsDesambiguationTrack:

    def test_star_lesson(self, lessons):
        document, counts = lessons
        lesson = _lessonOf(document, "desambiguation-01")
        assert lesson["sectionTitle"] == "Désambiguïsation"
        assert lesson["title"] == "Leçon un : la marque *"
        assert lesson["newKeys"] == [STAR_KEY]
        assert lesson["newChords"] == []
        # Whole lemma-homophone groups side by side, ranked by max frequency.
        assert _orthosOf(lesson) == ["pa", "pâ", "sa", "ça", "li", "lis", "la", "là",
                                     "pat", "pâte"]
        assert lesson["rules"] == [{
            "kind": "mark",
            "text": "La marque * (*) distingue pâ (p*a) de pa (pa)."}]

    def test_empty_codes_drop(self, lessons):
        # No record carries # or *#: both lessons drop (pool < 10), leaving the
        # single * lesson as the whole track.
        document, counts = lessons
        assert counts["desambiguation"] == 1
        assert [lesson["id"] for lesson in document["lessons"]
                if lesson["track"] == "desambiguation"] == ["desambiguation-01"]

    def test_marked_record_shape(self, lessons):
        document, _counts = lessons
        record = _lessonOf(document, "desambiguation-01")["words"][1]
        assert record == {"ortho": "pâ", "before": "la", "after": "",
                          "label": "nom, f. sg.", "phonology": "pa", "steno": "p*a",
                          "strokes": [[3, 10, 11]], "frequency": 5.0}


class TestBuildLessonsAffixesTrack:

    def test_stub_lesson(self, lessons):
        document, counts = lessons
        lesson = _lessonOf(document, "affixes-01")
        assert lesson == {"id": "affixes-01", "track": "affixes", "index": 1,
                          "sectionTitle": "Affixes", "title": "Leçon un : à venir",
                          "kind": "affixes", "newKeys": [], "newChords": [],
                          "rules": [{"kind": "affixes",
                                     "text": "Abréviations d'affixes : à venir."}],
                          "words": []}
        assert counts["affixes"] == 1


class TestBuildLessonsExpressionsTrack:

    def test_stub_lesson(self, lessons):
        document, counts = lessons
        lesson = _lessonOf(document, "expressions-01")
        assert lesson == {"id": "expressions-01", "track": "expressions", "index": 1,
                          "sectionTitle": "Abréviations d'expressions", "title": "Leçon un : à venir",
                          "kind": "expressions", "newKeys": [], "newChords": [],
                          "rules": [{"kind": "expressions",
                                     "text": "Abréviations d'expressions : à venir."}],
                          "words": []}
        assert counts["expressions"] == 1

    def test_wording_has_no_ipa_mapped_character(self, lessons):
        document, _counts = lessons
        track = next(t for t in document["tracks"] if t["id"] == "expressions")
        lesson = _lessonOf(document, "expressions-01")
        strings = [track["title"], track["description"], lesson["title"], lesson["sectionTitle"],
                   *(rule["text"] for rule in lesson["rules"])]
        for text in strings:
            assert not set(text) & set("E@°§5O9821RZSNG"), text


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))


class TestUnlockedWords:
    @staticmethod
    def _record(ortho: str, frequency: float, lemme: str) -> dict[str, Any]:
        return {"ortho": ortho, "steno": ortho, "frequency": frequency,
                "_word": types.SimpleNamespace(lemme=lemme)}

    def test_per_lemma_cap_and_fill_to_minimum(self) -> None:
        records = [self._record(f"a{i}", 100 - i, "same") for i in range(10)]
        top = topSpellings(records)
        pool = selectUnlockedWords(records, top)
        assert len(pool) == 30 or len(pool) == 10  # no more than exist
        assert [r["ortho"] for r in pool[:3]] == ["a0", "a1", "a2"]

    def test_diverse_lemmas_capped_at_pool_size(self) -> None:
        records = [self._record(f"w{i:03d}", 1000 - i, f"l{i}") for i in range(80)]
        pool = selectUnlockedWords(records, topSpellings(records))
        assert len(pool) == 50
        assert pool[0]["ortho"] == "w000"

    def test_rare_words_only_top_up_below_minimum(self) -> None:
        records = [self._record(f"w{i:03d}", 1000 - i, f"l{i}") for i in range(40)]
        top = frozenset(r["ortho"] for r in records[:10])
        pool = selectUnlockedWords(records, top)
        assert len(pool) == 30

    def test_reorder_keeps_fixed_lessons_and_respects_dependencies(self) -> None:
        chunks = [[{"keypress": (i,)}] for i in range(15)]
        word = types.SimpleNamespace(lemme="x")
        records = [({"ortho": f"w{k}", "_word": word}, 1 << 13 | 1 << 5) for k in range(40)]
        top = frozenset(str(r["ortho"]) for r, _ in records)
        order = reorderPhonemeChunks(chunks, records, top, [0] * 15)
        assert order[:2] == [0, 1]
        assert sorted(order[2:5]) == [2, 3, 4] and sorted(order[5:]) == list(range(5, 15))
        assert order.index(5) < order.index(13)  # ties: the smallest order
        dependencies = [0] * 15
        dependencies[5] = 1 << 13  # lesson 6 needs lesson 14's keys first
        order = reorderPhonemeChunks(chunks, records, top, dependencies)
        assert order.index(13) < order.index(5)
