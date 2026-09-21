import pytest
import json
import os
from ..keyboard import (
    Keyboard, Starboard, FingerWeights, PositionWeights,
    Keypress, Stroke, Strokes,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def starboard() -> Starboard:
    return Starboard()


@pytest.fixture
def starboard_with_layout() -> Starboard:
    """Starboard with Ireland English layout loaded."""
    sb = Starboard()
    sb.setIrelandEnglishLayout()
    return sb


# ═══════════════════════════════════════════════════════════════════════════════
# FingerWeights
# ═══════════════════════════════════════════════════════════════════════════════

class TestFingerWeights:

    def test_no_press_is_zero(self):
        fw = FingerWeights()
        assert fw.noPress == 0

    def test_home_keys_cheaper_than_off_home(self):
        fw = FingerWeights()
        assert fw.pinky1keyHome < fw.pinky1keyOffHome
        assert fw.index1keyHome < fw.index1keyOffHome

    def test_single_key_cheaper_than_multi_key(self):
        fw = FingerWeights()
        assert fw.pinky1keyHome < fw.pinky2keysVertHome
        assert fw.index1keyHome < fw.index2keysVert
        assert fw.thumb1key < fw.thumb2keys

    def test_multi_key_weight_ordering(self):
        fw = FingerWeights()
        assert fw.pinky2keysVertHome < fw.pinky2keysVertOffHome
        assert fw.pinky2keysHorzBottom < fw.pinky4keys


# ═══════════════════════════════════════════════════════════════════════════════
# PositionWeights
# ═══════════════════════════════════════════════════════════════════════════════

class TestPositionWeights:

    def test_to_list(self, starboard: Starboard):
        items = starboard._possibleKeypress.toList()
        assert isinstance(items, list)
        assert all(isinstance(kp, tuple) and len(kp) == 2 for kp in items)
        # Each item is (Keypress, int)
        assert all(isinstance(kp[0], tuple) and isinstance(kp[1], int) for kp in items)

    def test_iter_yields_all_finger_dicts(self, starboard: Starboard):
        finger_dicts = list(starboard._possibleKeypress)
        assert len(finger_dicts) == 10  # 10 fingers

    def test_getitem(self, starboard: Starboard):
        left_pinky = starboard._possibleKeypress["leftPinky"]
        assert isinstance(left_pinky, dict)
        assert () in left_pinky  # noPress entry

    def test_every_finger_has_no_press(self, starboard: Starboard):
        """Every finger should have an empty-tuple (no press) option."""
        for finger_dict in starboard._possibleKeypress:
            assert () in finger_dict


# ═══════════════════════════════════════════════════════════════════════════════
# Starboard.__init__
# ═══════════════════════════════════════════════════════════════════════════════

class TestStarboardInit:

    def test_default_partition(self, starboard: Starboard):
        """Default is onset=8, nucleus=4, coda=10 keys."""
        assert len(starboard.keyIDinSyllabicPart["onset"]) == 8
        assert len(starboard.keyIDinSyllabicPart["nucleus"]) == 4
        assert len(starboard.keyIDinSyllabicPart["coda"]) == 10

    def test_reserved_keys_excluded(self, starboard: Starboard):
        """Keys 0, 1, 10, 15 are reserved and should not be in allowedKeys."""
        for k in [0, 1, 10, 15]:
            assert k not in starboard.allowedKeys

    def test_allowed_keys_count(self, starboard: Starboard):
        assert len(starboard.allowedKeys) == 22  # 26 - 4 reserved

    def test_partition_keys_are_disjoint(self, starboard: Starboard):
        onset = set(starboard.keyIDinSyllabicPart["onset"])
        nucleus = set(starboard.keyIDinSyllabicPart["nucleus"])
        coda = set(starboard.keyIDinSyllabicPart["coda"])
        assert onset & nucleus == set()
        assert onset & coda == set()
        assert nucleus & coda == set()

    def test_partition_covers_all_allowed_keys(self, starboard: Starboard):
        all_partitioned = (
            set(starboard.keyIDinSyllabicPart["onset"])
            | set(starboard.keyIDinSyllabicPart["nucleus"])
            | set(starboard.keyIDinSyllabicPart["coda"])
        )
        assert all_partitioned == set(starboard.allowedKeys)

    def test_mismatched_partition_raises(self):
        with pytest.raises(ValueError, match="does not match"):
            Starboard(nbKeysPerSyllabicPart=(("onset", 5), ("nucleus", 4), ("coda", 10)))

    def test_custom_partition(self):
        sb = Starboard(nbKeysPerSyllabicPart=(("onset", 6), ("nucleus", 6), ("coda", 10)))
        assert len(sb.keyIDinSyllabicPart["onset"]) == 6
        assert len(sb.keyIDinSyllabicPart["nucleus"]) == 6
        assert len(sb.keyIDinSyllabicPart["coda"]) == 10

    def test_nb_keys(self, starboard: Starboard):
        assert starboard.nbKeys == 26


# ═══════════════════════════════════════════════════════════════════════════════
# Keyboard.strokeIsLowerThen (static)
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrokeIsLowerThen:

    def test_empty_vs_nonempty(self):
        assert Keyboard.strokeIsLowerThen((), (1,)) == -1

    def test_nonempty_vs_empty(self):
        assert Keyboard.strokeIsLowerThen((1,), ()) == 1

    def test_both_empty(self):
        assert Keyboard.strokeIsLowerThen((), ()) == 1

    def test_first_key_lower(self):
        assert Keyboard.strokeIsLowerThen((1, 5), (2, 5)) == -1

    def test_first_key_higher(self):
        assert Keyboard.strokeIsLowerThen((3, 5), (2, 5)) == 1

    def test_same_first_last_key_lower(self):
        assert Keyboard.strokeIsLowerThen((1, 3), (1, 5)) == -1

    def test_same_first_last_key_higher(self):
        assert Keyboard.strokeIsLowerThen((1, 5), (1, 3)) == 1

    def test_identical_single_key(self):
        """Identical single-key strokes: recurse to ((), ()) → 1."""
        assert Keyboard.strokeIsLowerThen((5,), (5,)) == 1

    def test_recurse_to_middle(self):
        """Same first and last, differs in middle."""
        assert Keyboard.strokeIsLowerThen((1, 2, 5), (1, 3, 5)) == -1
        assert Keyboard.strokeIsLowerThen((1, 4, 5), (1, 3, 5)) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Layout management: addToLayout, removeFromLayout, clearLayout
# ═══════════════════════════════════════════════════════════════════════════════

class TestLayoutManagement:

    def test_add_and_get_phoneme(self, starboard: Starboard):
        starboard.addToLayout((2,), "s")
        assert starboard.getPhonemesOfStroke((2,)) == ["s"]

    def test_add_multiple_phonemes_to_same_stroke(self, starboard: Starboard):
        starboard.addToLayout((2,), "s")
        starboard.addToLayout((2,), "z")
        result = starboard.getPhonemesOfStroke((2,))
        assert "s" in result
        assert "z" in result

    def test_add_with_ordering(self, starboard: Starboard):
        """When phonemeOrder is given, phonemes are inserted in that order."""
        order = ["a", "b", "c"]
        starboard.addToLayout((2,), "c", phonemeOrder=order)
        starboard.addToLayout((2,), "a", phonemeOrder=order)
        starboard.addToLayout((2,), "b", phonemeOrder=order)
        assert starboard.getPhonemesOfStroke((2,)) == ["a", "b", "c"]

    def test_add_with_ordering_unordered_at_end(self, starboard: Starboard):
        """Phonemes not in phonemeOrder list go at the end."""
        order = ["a", "b"]
        starboard.addToLayout((2,), "a", phonemeOrder=order)
        starboard.addToLayout((2,), "x")  # no order
        starboard.addToLayout((2,), "b", phonemeOrder=order)
        # "b" should be inserted before "x" (unordered)
        result = starboard.getPhonemesOfStroke((2,))
        assert result.index("a") < result.index("b")
        assert result.index("b") < result.index("x")

    def test_remove_only_phoneme_deletes_stroke(self, starboard: Starboard):
        starboard.addToLayout((2,), "s")
        starboard.removeFromLayout((2,), "s")
        assert starboard.getPhonemesOfStroke((2,)) == []

    def test_remove_one_of_many(self, starboard: Starboard):
        starboard.addToLayout((2,), "s")
        starboard.addToLayout((2,), "z")
        starboard.removeFromLayout((2,), "s")
        assert starboard.getPhonemesOfStroke((2,)) == ["z"]

    def test_remove_nonexistent_stroke_raises(self, starboard: Starboard):
        with pytest.raises(KeyError, match="not found in the layout"):
            starboard.removeFromLayout((99,), "s")

    def test_remove_nonexistent_phoneme_raises(self, starboard: Starboard):
        starboard.addToLayout((2,), "s")
        with pytest.raises(KeyError, match="not found in keypress"):
            starboard.removeFromLayout((2,), "z")

    def test_clear_layout(self, starboard: Starboard):
        starboard.addToLayout((2,), "s")
        starboard.addToLayout((4,), "t")
        starboard.clearLayout()
        assert starboard.getPhonemesOfStroke((2,)) == []
        assert starboard.getPhonemesOfStroke((4,)) == []

    def test_get_phonemes_returns_copy(self, starboard: Starboard):
        """getPhonemesOfStroke should return a copy, not the internal list."""
        starboard.addToLayout((2,), "s")
        result = starboard.getPhonemesOfStroke((2,))
        result.append("MUTATED")
        assert starboard.getPhonemesOfStroke((2,)) == ["s"]


# ═══════════════════════════════════════════════════════════════════════════════
# getStrokesOfPhoneme
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetStrokesOfPhoneme:

    def test_find_stroke_in_onset(self, starboard_with_layout: Starboard):
        strokes = starboard_with_layout.getStrokesOfPhoneme("s", "onset")
        assert len(strokes) >= 1
        # All returned strokes should have their first key in onset partition
        for stroke in strokes:
            assert stroke[0] in starboard_with_layout.keyIDinSyllabicPart["onset"]

    def test_phoneme_not_found(self, starboard_with_layout: Starboard):
        strokes = starboard_with_layout.getStrokesOfPhoneme("NONEXISTENT", "onset")
        assert strokes == []

    def test_returns_copy(self, starboard_with_layout: Starboard):
        result = starboard_with_layout.getStrokesOfPhoneme("s", "onset")
        original_len = len(result)
        result.append((99,))
        assert len(starboard_with_layout.getStrokesOfPhoneme("s", "onset")) == original_len


# ═══════════════════════════════════════════════════════════════════════════════
# getSinglekeyKeypress / getFingersInSyllabicPart
# ═══════════════════════════════════════════════════════════════════════════════

class TestKeyboardHelpers:

    def test_single_key_keypresses(self, starboard: Starboard):
        onset_keys = starboard.getSinglekeyKeypress("onset")
        assert all(len(kp) == 1 for kp in onset_keys)
        assert len(onset_keys) == len(starboard.keyIDinSyllabicPart["onset"])

    def test_fingers_in_onset(self, starboard: Starboard):
        fingers = starboard.getFingersInSyllabicPart("onset")
        assert isinstance(fingers, list)
        assert len(fingers) > 0
        # Onset keys are on the left hand
        assert all(f.startswith("left") for f in fingers)

    def test_fingers_in_coda(self, starboard: Starboard):
        fingers = starboard.getFingersInSyllabicPart("coda")
        assert len(fingers) > 0
        assert all(f.startswith("right") for f in fingers)

    def test_fingers_in_nucleus(self, starboard: Starboard):
        fingers = starboard.getFingersInSyllabicPart("nucleus")
        assert len(fingers) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# getPossibleStrokes / getPossibleStrokesInRange
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetPossibleStrokes:

    def test_single_key_strokes(self, starboard: Starboard):
        strokes = starboard.getPossibleStrokes("onset", 1)
        assert len(strokes) == len(starboard.keyIDinSyllabicPart["onset"])
        assert all(len(s) == 1 for s in strokes)

    def test_two_key_strokes(self, starboard: Starboard):
        strokes = starboard.getPossibleStrokes("onset", 2)
        assert all(len(s) == 2 for s in strokes)
        assert len(strokes) > 0

    def test_strokes_only_use_partition_keys(self, starboard: Starboard):
        """All keys in generated strokes should belong to the requested partition."""
        onset_keys = set(starboard.keyIDinSyllabicPart["onset"])
        strokes = starboard.getPossibleStrokes("onset", 2)
        for stroke in strokes:
            for key in stroke:
                assert key in onset_keys

    def test_no_duplicate_strokes(self, starboard: Starboard):
        strokes = starboard.getPossibleStrokes("onset", 2)
        assert len(strokes) == len(set(strokes))

    def test_strokes_in_range(self, starboard: Starboard):
        strokes = starboard.getPossibleStrokesInRange("onset", 1, 2)
        sizes = set(len(s) for s in strokes)
        assert sizes == {1, 2}

    def test_strokes_in_range_single(self, starboard: Starboard):
        """Range of 1 to 1 should equal single-key strokes."""
        range_strokes = starboard.getPossibleStrokesInRange("onset", 1, 1)
        single_strokes = starboard.getPossibleStrokes("onset", 1)
        assert range_strokes == single_strokes


# ═══════════════════════════════════════════════════════════════════════════════
# getStrokeCost
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetStrokeCost:

    def test_single_key_cost_positive(self, starboard: Starboard):
        """Any single-key stroke should have a positive cost."""
        for key_id in starboard.keyIDinSyllabicPart["onset"]:
            cost = starboard.getStrokeCost((key_id,), "onset")
            assert cost is not None and cost > 0

    def test_multi_key_more_expensive(self, starboard: Starboard):
        """A two-key stroke should generally cost more than any single key
        from the same finger (before discount)."""
        # leftRing: keys 4,5 — single key is 125, both is 175
        cost_single = starboard.getStrokeCost((4,), "onset")
        cost_double = starboard.getStrokeCost((4, 5), "onset")
        assert cost_single is not None and cost_double is not None
        assert cost_double > cost_single

    def test_nucleus_no_shape_cost(self, starboard: Starboard):
        """Nucleus strokes don't get shape cost added."""
        nucleus_keys = starboard.keyIDinSyllabicPart["nucleus"]
        cost = starboard.getStrokeCost((nucleus_keys[0],), "nucleus")
        assert cost is not None and cost > 0

    def test_illegal_key_combo_returns_none(self, starboard: Starboard):
        """(22, 25) isn't in rightPinky's _possibleKeypress table (only (22,23)/(24,25)/
        (22,24)/(23,25) are) -- infeasible, not a crash."""
        assert starboard.getStrokeCost((22, 25), "coda") is None
        assert starboard.getStrokeCost((23, 24), "coda") is None

    def test_legal_key_combo_still_returns_int(self, starboard: Starboard):
        assert isinstance(starboard.getStrokeCost((22, 23), "coda"), int)


# ═══════════════════════════════════════════════════════════════════════════════
# Stroke shape costs
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrokeShapeCost:

    def test_zigzag_cost(self, starboard: Starboard):
        # Keys on top-left then bottom-right (or vice-versa)
        assert starboard._strokeZigZagCost((2, 5)) == 100  # even, odd, diff=3
        assert starboard._strokeZigZagCost((3, 4)) == 100  # odd, even, diff=1

    def test_no_zigzag(self, starboard: Starboard):
        assert starboard._strokeZigZagCost((2, 3)) == 0  # vertical, not zigzag
        assert starboard._strokeZigZagCost((2, 4)) == 0  # horizontal same row

    def test_gap_cost(self, starboard: Starboard):
        assert starboard._strokeGapCost((2, 6)) == 100  # even, gap >= 4
        assert starboard._strokeGapCost((3, 6)) == 100  # odd, gap >= 3

    def test_no_gap(self, starboard: Starboard):
        assert starboard._strokeGapCost((2, 4)) == 0  # even, gap = 2 < 4
        assert starboard._strokeGapCost((3, 5)) == 0  # odd, gap = 2 < 3

    def test_shape_cost_single_key(self, starboard: Starboard):
        """Single key strokes have no shape cost."""
        assert starboard.getStrokeShapeCost((2,)) == 0

    def test_shape_cost_two_keys(self, starboard: Starboard):
        cost = starboard.getStrokeShapeCost((2, 5))
        assert cost == 100 + 0  # zigzag=100, gap=0 (diff=3 for even but checking gap: 3<4)

    def test_shape_cost_three_keys(self, starboard: Starboard):
        """Three-key stroke cost combines pairwise costs with adjustments."""
        cost = starboard.getStrokeShapeCost((2, 3, 4))
        # Recursion: cost(2,3) + cost(3,4) + adjustment for (2,3,4)
        # s1=2 even, s3-s1=2 → -50 discount
        assert isinstance(cost, int)


# ═══════════════════════════════════════════════════════════════════════════════
# Ireland English layout
# ═══════════════════════════════════════════════════════════════════════════════

class TestIrelandEnglishLayout:

    def test_layout_loaded(self, starboard_with_layout: Starboard):
        assert len(starboard_with_layout.phonemesAssignedToStroke) > 0

    def test_onset_s_on_key_2(self, starboard_with_layout: Starboard):
        phonemes = starboard_with_layout.getPhonemesOfStroke((2,))
        assert "s" in phonemes

    def test_nucleus_vowels(self, starboard_with_layout: Starboard):
        assert "a" in starboard_with_layout.getPhonemesOfStroke((11,))
        assert "o" in starboard_with_layout.getPhonemesOfStroke((12,))
        assert "e" in starboard_with_layout.getPhonemesOfStroke((13,))
        assert "u" in starboard_with_layout.getPhonemesOfStroke((14,))

    def test_coda_phonemes_present(self, starboard_with_layout: Starboard):
        """Coda should have some phonemes assigned."""
        coda_keys = starboard_with_layout.keyIDinSyllabicPart["coda"]
        has_phonemes = any(
            starboard_with_layout.getPhonemesOfStroke((k,)) != []
            for k in coda_keys
        )
        assert has_phonemes


# ═══════════════════════════════════════════════════════════════════════════════
# getStrokeOfSyllableByPart
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetStrokeOfSyllableByPart:

    def test_simple_syllable(self, starboard_with_layout: Starboard):
        """CVC syllable should produce a stroke with keys from all 3 parts."""
        phonemes_by_part = {
            "onset": ["s"],
            "nucleus": ["a"],
            "coda": ["t"],
        }
        stroke = starboard_with_layout.getStrokeOfSyllableByPart(phonemes_by_part)
        assert isinstance(stroke, tuple)
        assert len(stroke) >= 3  # at least one key per part

    def test_vowel_only(self, starboard_with_layout: Starboard):
        phonemes_by_part = {
            "onset": [],
            "nucleus": ["a"],
            "coda": [],
        }
        stroke = starboard_with_layout.getStrokeOfSyllableByPart(phonemes_by_part)
        assert len(stroke) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# strokesToString
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrokesToString:

    def test_single_stroke(self, starboard_with_layout: Starboard):
        """A stroke with onset/nucleus/coda should produce a readable string."""
        sb = starboard_with_layout
        phonemes_by_part = {"onset": ["s"], "nucleus": ["a"], "coda": ["t"]}
        stroke = sb.getStrokeOfSyllableByPart(phonemes_by_part)
        result = sb.strokesToString((stroke,))
        assert isinstance(result, str)
        assert "s" in result
        assert "a" in result
        assert "t" in result

    def test_multiple_strokes_separated_by_slash(self, starboard_with_layout: Starboard):
        sb = starboard_with_layout
        stroke1 = sb.getStrokeOfSyllableByPart({"onset": ["s"], "nucleus": ["a"], "coda": []})
        stroke2 = sb.getStrokeOfSyllableByPart({"onset": [], "nucleus": ["e"], "coda": ["t"]})
        result = sb.strokesToString((stroke1, stroke2))
        assert "/" in result

    def test_no_nucleus_inserts_dash(self, starboard_with_layout: Starboard):
        """When nucleus is empty, a '-' placeholder is inserted."""
        sb = starboard_with_layout
        # Build a stroke with only onset keys
        onset_key = sb.keyIDinSyllabicPart["onset"][0]
        sb.addToLayout((onset_key,), "TEST_PHONEME")
        coda_key = sb.keyIDinSyllabicPart["coda"][0]
        stroke = (onset_key, coda_key)
        result = sb.strokesToString((stroke,))
        assert "-" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Plover integration: keyDisplayName / strokesToRTFCRE
# ═══════════════════════════════════════════════════════════════════════════════

class TestKeyDisplayName:

    def test_reserved_keys_use_fixed_symbols(self, starboard: Starboard):
        assert starboard.keyDisplayName(10) == "*"
        assert starboard.keyDisplayName(15) == "#"

    def test_onset_key_gets_trailing_hyphen(self, starboard_with_layout: Starboard):
        # setIrelandEnglishLayout assigns "s" to onset key (2,)
        assert starboard_with_layout.keyDisplayName(2) == "s-"

    def test_coda_key_gets_leading_hyphen(self, starboard_with_layout: Starboard):
        # setIrelandEnglishLayout assigns ["f", "v"] to coda key (16,); first wins.
        assert starboard_with_layout.keyDisplayName(16) == "-f"

    def test_nucleus_left_thumb_gets_trailing_hyphen(self, starboard_with_layout: Starboard):
        # (11,) -> "a", left thumb
        assert starboard_with_layout.keyDisplayName(11) == "a-"

    def test_nucleus_right_thumb_gets_leading_hyphen(self, starboard_with_layout: Starboard):
        # (13,) -> "e", right thumb
        assert starboard_with_layout.keyDisplayName(13) == "-e"

    def test_missing_single_key_phoneme_raises(self, starboard: Starboard):
        with pytest.raises(KeyError):
            starboard.keyDisplayName(2)  # empty layout, no phoneme assigned yet

    def test_all_26_names_are_unique(self):
        sb = Starboard.fromJSONFile("starboard3h.json")
        assert sb is not None
        names = sb.keyDisplayNames()
        assert len(names) == 26
        assert len(set(names)) == 26


class TestStrokesToRTFCRE:

    def test_matches_strokes_to_string_shape(self, starboard_with_layout: Starboard):
        sb = starboard_with_layout
        stroke = sb.getStrokeOfSyllableByPart({"onset": ["s"], "nucleus": ["a"], "coda": ["t"]})
        result = sb.strokesToRTFCRE((stroke,))
        assert result == "sat"

    def test_no_nucleus_inserts_dash(self, starboard_with_layout: Starboard):
        sb = starboard_with_layout
        onset_key = sb.keyIDinSyllabicPart["onset"][0]
        coda_key = sb.keyIDinSyllabicPart["coda"][0]
        result = sb.strokesToRTFCRE(((onset_key, coda_key),))
        assert "-" in result

    def test_multiple_strokes_separated_by_slash(self, starboard_with_layout: Starboard):
        sb = starboard_with_layout
        stroke1 = sb.getStrokeOfSyllableByPart({"onset": ["s"], "nucleus": ["a"], "coda": []})
        stroke2 = sb.getStrokeOfSyllableByPart({"onset": [], "nucleus": ["e"], "coda": ["t"]})
        result = sb.strokesToRTFCRE((stroke1, stroke2))
        assert "/" in result


# ═══════════════════════════════════════════════════════════════════════════════
# JSON serialization
# ═══════════════════════════════════════════════════════════════════════════════

class TestJSONSerialization:

    def test_round_trip(self, starboard_with_layout: Starboard, tmp_path):
        filepath = str(tmp_path / "test_keyboard.json")
        starboard_with_layout.toJSONFile(filepath)
        loaded = Starboard.fromJSONFile(filepath)
        assert loaded is not None
        # Verify layout preserved
        assert loaded.phonemesAssignedToStroke is not None
        assert len(loaded.phonemesAssignedToStroke) > 0

    def test_from_nonexistent_file(self):
        result = Starboard.fromJSONFile("/nonexistent/path.json")
        assert result is None

    def test_to_json_creates_file(self, starboard: Starboard, tmp_path):
        filepath = str(tmp_path / "test.json")
        starboard.toJSONFile(filepath)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            data = json.load(f)
        assert isinstance(data, dict)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
