"""Unit tests for the lesson generator `util/export_lessons.py`: the pure helpers
(finger decomposition, ordering key, steps, chunking, star/hash codes, tense
mapping, pool ranking), the French rule-text renderers, and one full
`buildLessons` run on a tiny in-memory theory. The real inputs (starboard3h.json,
the pickles, the realization report) are multi-MB repo artifacts the unit tests
must not depend on, so every fixture here is hand-built."""

import pytest
from ..keyboard import Starboard
from ..word import GramCat, Word
from util.export_lessons import (
    MAX_LESSON_KEYPRESSES, RECORD_FIELDS, accordRule, buildLessons, chunkStep,
    eligible, fingerKeypressesOfStroke, loadKeypressGroups, markRule,
    phonemeOrderingKey, phonemeRule, phonemeSteps, selectTopWords,
    starHashCodeOf, verbMarkerRule, verbTenseOf, verbTenseRule,
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
    defaults = dict(
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
    disambiguated = {}
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


# A rule-text pool whose records need no Word objects (only phonemeRule reads
# _keyps; markRule reads _code/_cluster; the verb renderers read nothing).
_RULE_POOL = [
    {"ortho": "sa", "steno": "s*a", "_keyps": frozenset({(8,), (11,)}),
     "_code": "*", "_cluster": ((8, 11),)},
    {"ortho": "pa", "steno": "pa", "_keyps": frozenset({(3,), (11,)}),
     "_code": "", "_cluster": ((8, 11),)},
]


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
        assert phonemeOrderingKey((2, 5), starboard)[0] == 250
        assert starboard.getStrokeCost((2, 5), "onset") == 252
        assert phonemeOrderingKey((8, 9), starboard)[0] == 150
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
# Rule-text renderers (§7)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemeRule:

    def test_onset(self, starboard_with_layout: Starboard):
        item = {"keypress": (8,), "phonemes": ("s",), "part": "onset"}
        assert phonemeRule(item, starboard_with_layout, _RULE_POOL) == {
            "kind": "phoneme",
            "text": "La touche s- écrit le son /s/ en début de syllabe (« sa »).",
            "examples": ["sa"]}

    def test_nucleus(self, starboard_with_layout: Starboard):
        item = {"keypress": (11,), "phonemes": ("a",), "part": "nucleus"}
        assert phonemeRule(item, starboard_with_layout, _RULE_POOL) == {
            "kind": "phoneme",
            "text": "La touche a- écrit la voyelle /a/ (« sa », « pa »).",
            "examples": ["sa", "pa"]}

    def test_coda_without_examples(self, starboard_with_layout: Starboard):
        item = {"keypress": (16,), "phonemes": ("t",), "part": "coda"}
        assert phonemeRule(item, starboard_with_layout, []) == {
            "kind": "phoneme",
            "text": "La touche -t écrit le son /t/ en fin de syllabe.",
            "examples": []}

    def test_multiphone_keypress_names_every_phoneme(self, starboard_with_layout: Starboard):
        item = {"keypress": (12,), "phonemes": ("i", "e", "o"), "part": "nucleus"}
        assert phonemeRule(item, starboard_with_layout, []) == {
            "kind": "phoneme",
            "text": "La touche i- écrit /i/, /e/ ou /o/ selon la position.",
            "examples": []}

    def test_chord_onset(self, starboard_with_layout: Starboard):
        item = {"keypress": (8, 9), "phonemes": ("E",), "part": "onset"}
        assert phonemeRule(item, starboard_with_layout, []) == {
            "kind": "phoneme",
            "text": "Les touches s-, l- pressées ensemble écrivent /E/ en début de syllabe.",
            "examples": []}

    def test_two_thumb_nucleus_chord(self, starboard_with_layout: Starboard):
        item = {"keypress": (11, 13), "phonemes": ("ô",), "part": "nucleus"}
        assert phonemeRule(item, starboard_with_layout, []) == {
            "kind": "phoneme",
            "text": "Les touches a-, -e pressées ensemble écrivent la voyelle /ô/.",
            "examples": []}

    def test_examples_come_from_records_touching_the_keypress(self,
                                                              starboard_with_layout: Starboard):
        item = {"keypress": (3,), "phonemes": ("p",), "part": "onset"}
        # "sa" does not press key 3, so only "pa" is an example.
        rule = phonemeRule(item, starboard_with_layout, _RULE_POOL)
        assert rule["examples"] == ["pa"]
        assert rule["text"].endswith("(« pa »).")


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
            "text": "La touche -o marque le féminin : sate → sat/o par rapport à sat.",
            "examples": ["sate"]}

    def test_empty_pool(self, starboard_with_layout: Starboard):
        _first, wordToStrokes = self._pool()
        group = {"chosenKeys": (14,), "markers": ("f",)}
        assert accordRule(group, starboard_with_layout, wordToStrokes, []) == {
            "kind": "accord", "text": "La touche -o marque le féminin.", "examples": []}

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
                     "« sa », « pa »."),
            "examples": ["sa", "pa"]}

    def test_without_examples(self, starboard_with_layout: Starboard):
        group = {"chosenKeys": (9,), "markers": ("conditionnel", "infinitif")}
        assert verbMarkerRule(group, starboard_with_layout, []) == {
            "kind": "verb-markers",
            "text": "La touche l- marque le conditionnel et l'infinitif.",
            "examples": []}


class TestVerbTenseRule:

    def test_names_the_touched_marker_keys(self, starboard_with_layout: Starboard):
        rule = verbTenseRule("l'indicatif présent", [12, 14], starboard_with_layout,
                             _RULE_POOL)
        assert rule == {
            "kind": "verb-tense",
            "text": ("Pour l'indicatif présent, les marques de conjugaison sont "
                     "i-, -o : « sa », « pa »."),
            "examples": ["sa", "pa"]}


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
            "text": "La marque * (*) distingue sa (s*a) de pa (pa).",
            "examples": ["sa", "pa"]}

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
            "text": "La marque # (#) s'ajoute à la fin du mot : lis (l*i).",
            "examples": ["lis"]}

    def test_empty_pool(self, starboard: Starboard):
        assert markRule("*#", starboard, []) == {
            "kind": "mark", "text": "La marque *# (*, #).", "examples": []}


# ═══════════════════════════════════════════════════════════════════════════════
# buildLessons (§4-§6)
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildLessonsDocument:

    def test_five_tracks_in_order(self, lessons):
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
             "description": "Abréviations d'affixes — à venir."},
        ]

    def test_per_track_counts_and_stream_counters(self, lessons):
        _document, counts = lessons
        assert counts == {"phonemes": 5, "accord": 2, "verbe": 1, "desambiguation": 1,
                          "affixes": 1, "_records": 15, "_skippedWords": 1,
                          "_invalidRecords": 1}

    def test_lesson_ids_are_dense_and_generation_ordered(self, lessons):
        document, counts = lessons
        byTrack = {}
        for lesson in document["lessons"]:
            byTrack.setdefault(lesson["track"], []).append(lesson["id"])
        assert byTrack == {trackId: [f"{trackId}-{index:02d}" for index in range(
            1, counts[trackId] + 1)] for trackId in
            ("phonemes", "accord", "verbe", "desambiguation", "affixes")}
        # Flat list in track order: the track of each lesson never goes back.
        trackOrder = [lesson["track"] for lesson in document["lessons"]]
        assert trackOrder == sorted(trackOrder, key=[
            "phonemes", "accord", "verbe", "desambiguation", "affixes"].index)

    def test_words_reuse_the_practice_words_record_shape(self, lessons):
        document, _counts = lessons
        for lesson in document["lessons"]:
            for record in lesson["words"]:
                assert tuple(record.keys()) == RECORD_FIELDS

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


class TestBuildLessonsPhonemesTrack:

    def test_first_lesson(self, lessons):
        document, _counts = lessons
        lesson = _lessonOf(document, "phonemes-01")
        assert lesson["sectionTitle"] == "Les premières touches"
        assert lesson["title"] == "Leçon 1 : a, s, t, i"
        assert lesson["kind"] == "phonemes"
        # Round-robin deal: nucleus (11), onset (8), coda (16), nucleus (12).
        assert lesson["newKeys"] == [8, 11, 12, 16]
        assert lesson["newChords"] == []

    def test_first_lesson_rules_in_deal_order(self, lessons):
        document, _counts = lessons
        rules = _lessonOf(document, "phonemes-01")["rules"]
        assert rules == [
            {"kind": "phoneme",
             "text": "La touche a- écrit la voyelle /a/ (« sa »).", "examples": ["sa"]},
            {"kind": "phoneme",
             "text": "La touche s- écrit le son /s/ en début de syllabe (« dis », « sa »).",
             "examples": ["dis", "sa"]},
            {"kind": "phoneme",
             "text": "La touche -t écrit le son /t/ en fin de syllabe.", "examples": []},
            {"kind": "phoneme",
             "text": "La touche i- écrit la voyelle /i/ (« dis »).", "examples": ["dis"]},
        ]

    def test_lesson_words_use_only_covered_keypresses(self, lessons):
        document, _counts = lessons
        # Only "dis" (keys 8, 12) and "sa" (8, 11) are writable with lesson 1's
        # four keypresses: the marked pairs are code-gated, the accord nouns
        # group-gated, and lise/lire/li/la wait for keys 9 and 17.
        assert _orthosOf(_lessonOf(document, "phonemes-01")) == ["dis", "sa"]
        # Lesson 2 adds keys 9, 13, 14, 17: lise and lire become writable.
        assert _orthosOf(_lessonOf(document, "phonemes-02")) \
            == ["lise", "lire", "dis", "sa", "li", "la"]
        # Lesson 3 adds key 3: the pa/pat pair's canonical members join.
        assert _orthosOf(_lessonOf(document, "phonemes-03")) \
            == ["lise", "lire", "dis", "pa", "sa", "li", "la", "pat"]

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
        assert lesson4["title"] == "Leçon 4 : E"
        assert lesson4["newKeys"] == [8, 9]
        assert lesson4["newChords"] == [[8, 9]]
        assert lesson4["rules"][0]["text"] \
            == "Les touches s-, l- pressées ensemble écrivent /E/ en début de syllabe."
        lesson5 = _lessonOf(document, "phonemes-05")
        assert lesson5["title"] == "Leçon 5 : ô"
        assert lesson5["newKeys"] == [11, 13]
        assert lesson5["newChords"] == [[11, 13]]
        assert lesson5["rules"][0]["text"] \
            == "Les touches a-, -e pressées ensemble écrivent la voyelle /ô/."


class TestBuildLessonsAccordTrack:

    def test_one_lesson_per_gender_number_group_in_affected_words_order(self, lessons):
        document, _counts = lessons
        lesson1 = _lessonOf(document, "accord-01")
        assert lesson1["title"] == "Leçon 1 : le féminin"
        assert lesson1["newKeys"] == [14]
        assert _orthosOf(lesson1) == ["sate"]
        assert lesson1["rules"] == [{
            "kind": "accord",
            "text": "La touche -o marque le féminin : sate → sat/o par rapport à sat.",
            "examples": ["sate"]}]
        lesson2 = _lessonOf(document, "accord-02")
        assert lesson2["title"] == "Leçon 2 : le pluriel"
        assert lesson2["newKeys"] == [17]
        assert _orthosOf(lesson2) == ["sates"]
        assert lesson2["rules"] == [{
            "kind": "accord",
            "text": "La touche -R marque le pluriel : sates → sat/-R par rapport à sat.",
            "examples": ["sates"]}]

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
        assert lesson["title"] == "Leçon 1 : les marques de conjugaison"
        assert lesson["newKeys"] == [9, 12]  # union of the two verb groups' chosenKeys
        assert _orthosOf(lesson) == ["lise", "lire", "dis"]
        assert lesson["rules"] == [
            {"kind": "verb-markers",
             "text": ("La touche l- marque le conditionnel et l'infinitif : "
                      "« lise », « lire », « dis »."),
             "examples": ["lise", "lire", "dis"]},
            {"kind": "verb-markers",
             "text": "La touche i- marque la 2e personne : « lise », « lire », « dis ».",
             "examples": ["lise", "lire", "dis"]},
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
        assert lesson["title"] == "Leçon 1 : la marque *"
        assert lesson["newKeys"] == [STAR_KEY]
        assert lesson["newChords"] == []
        # Whole lemma-homophone groups side by side, ranked by max frequency.
        assert _orthosOf(lesson) == ["pa", "pâ", "sa", "ça", "li", "lis", "la", "là",
                                     "pat", "pâte"]
        assert lesson["rules"] == [{
            "kind": "mark",
            "text": "La marque * (*) distingue pâ (p*a) de pa (pa).",
            "examples": ["pa", "pâ", "sa"]}]

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
                          "sectionTitle": "Affixes", "title": "Leçon 1 : à venir",
                          "kind": "affixes", "newKeys": [], "newChords": [],
                          "rules": [{"kind": "affixes",
                                     "text": "Règles d'abréviation des affixes : à venir.",
                                     "examples": []}],
                          "words": []}
        assert counts["affixes"] == 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
